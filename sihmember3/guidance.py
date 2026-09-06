"""Member 3 Phase 2 — India guidance pipeline.

The standalone Member 3 feature: free-text India question → routing →
evidence retrieval → grounded generation → citation validation → confidence
→ result. Implemented independently for this workstream (no M1/M2/M4/M5
code), producing the project RAG Result shape (Plan.md Section 7):

    answer            str — always includes the not-legal-advice disclaimer
    citations         Citation[] — built ONLY from stored Phase 1 records
    confidence        "HIGH" | "MEDIUM" | "LOW"
    confidence_score  float 0.0–1.0
    abstention        bool
    abstention_reason str | None — stable machine-readable code + detail
    status            "ok" | "abstained" | "processing_error"

Status semantics (for M6):
    ok               guidance was produced; abstention is False.
    abstained        a SAFE decline (no/weak evidence, out of scope, invalid
                     LLM output, failed citation validation). A successful
                     result — never an error and never a fabricated answer.
    processing_error infrastructure failure (e.g. hosted LLM unreachable).
                     Not an abstention; answer asks the user to retry.

Generation runs in one of two modes:
    hosted LLM (default) — an OpenAI-compatible hosted API configured via the
        M3_LLM_* environment variables (see llm.py). The prompt confines the
        model to the retrieved evidence and demands strict JSON.
    deterministic template — used when no hosted API is configured (or the
        caller forces it with llm="template"). It only restates the retrieved
        provisions verbatim; it never adds interpretation.

Either way the same guards run afterwards: statutory-reference, URL and
amount/date checks against the cited evidence; any unsupported content →
abstention. The LLM never writes citation metadata — citations are built
from the stored records it referenced and are re-validated field-by-field.

Hindi: Devanagari questions are answered in Hindi; routing/retrieval/
confidence are language-independent (the same evidence, scores and
citations). Statute names and section numbers stay in their official English
form in Hindi answers; no Hindi legal terminology is invented.
"""

import json
import re

from . import confidence as confidence_mod
from . import llm as llm_mod
from . import routing
from .citations import build_citation, validate_citations
from .retrieval import retrieve_evidence

RAG_RESULT_FIELDS = (
    "answer",
    "citations",
    "confidence",
    "confidence_score",
    "abstention",
    "abstention_reason",
    "status",
)

STATUS_OK = "ok"
STATUS_ABSTAINED = "abstained"
STATUS_PROCESSING_ERROR = "processing_error"

DISCLAIMER_EN = (
    "Note: This is general information, not legal advice. Please verify with "
    "the official sources or consult a qualified professional."
)
DISCLAIMER_HI = (
    "ध्यान दें: यह सामान्य जानकारी है, कानूनी सलाह नहीं। कृपया आधिकारिक स्रोतों "
    "से सत्यापित करें या योग्य पेशेवर से परामर्श लें।"
)

# The only URL the guidance layer may name that is not a stored record URL:
# the TKDL pointer, which MEMBER_3.md golden scenario 1 requires. PS.md names
# tkdl.res.in as the TKDL portal; its role statement below is limited to what
# the project documents support (defensive prior-art database; detailed
# contents restricted to patent offices). Deep TKDL content is Member 4's.
ALLOWED_POINTER_PREFIXES = ("https://tkdl.res.in", "https://www.tkdl.res.in")
TKDL_POINTER_EN = (
    "For traditional-knowledge patent questions, India's Traditional "
    "Knowledge Digital Library (TKDL, https://tkdl.res.in) is the "
    "defensive-disclosure database used to help prevent erroneous patents on "
    "traditional knowledge; its detailed contents are available to patent "
    "offices, not the general public."
)
TKDL_POINTER_HI = (
    "पारंपरिक ज्ञान से जुड़े पेटेंट प्रश्नों के लिए भारत की Traditional "
    "Knowledge Digital Library (TKDL, https://tkdl.res.in) एक defensive "
    "publications डेटाबेस है जो पारंपरिक ज्ञान पर ग़लत पेटेंट रोकने में "
    "इस्तेमाल होती है; इसकी विस्तृत सामग्री केवल पेटेंट कार्यालयों को "
    "उपलब्ध है, आम जनता को नहीं।"
)

# Records whose score is below this many points of the best record are
# treated as retrieval noise and are not offered to generation.
_NOISE_RATIO = 0.5
_NOISE_FLOOR = 3

# Minimum answer length accepted from the LLM (shorter = malformed).
_MIN_ANSWER_CHARS = 40

# ---------------------------------------------------------------------------
# Result constructors
# ---------------------------------------------------------------------------


def _result(answer, citations, label, score, abstention, reason, status):
    return {
        "answer": answer,
        "citations": citations,
        "confidence": label,
        "confidence_score": score,
        "abstention": abstention,
        "abstention_reason": reason,
        "status": status,
    }


def _abstain(reason_code, detail, language="en", confidence_score=0.0):
    text = {
        "en": (
            "I cannot answer this question from the verified India sources "
            "available to me (%s). Rather than guess, I am declining. You "
            "may re-phrase the question — for example by naming the specific "
            "right or regime involved — or check the official sources "
            "directly." % detail
        ),
        "hi": (
            "मेरे पास उपलब्ध सत्यापित भारत-स्रोतों से इस प्रश्न का उत्तर देना "
            "संभव नहीं है (%s)। अनुमान लगाने के बजाय मैं उत्तर देने से "
            "इंकार कर रहा/रही हूँ। कृपया प्रश्न को दूसरे शब्दों में पूछें "
            "(उदाहरण के लिए संबंधित अधिकार या विधि का नाम बताएं) या "
            "आधिकारिक स्रोत देखें।" % detail
        ),
    }[language]
    reason = "%s: %s" % (reason_code, detail)
    return _result(
        text + " " + (DISCLAIMER_HI if language == "hi" else DISCLAIMER_EN),
        [],
        "LOW",
        round(confidence_score, 4),
        True,
        reason,
        STATUS_ABSTAINED,
    )


def _processing_error(detail):
    return _result(
        "A temporary processing error occurred while generating guidance "
        "(%s). Please retry — nothing was answered, and no partial answer "
        "is provided." % detail,
        [],
        "LOW",
        0.0,
        False,
        None,
        STATUS_PROCESSING_ERROR,
    )


def validate_rag_result(result):
    """Contract validation for the RAG Result shape. Returns a list of
    problems (empty list = valid). Used by tests and available to M6."""
    problems = []
    if not isinstance(result, dict):
        return ["result must be a dict"]
    if tuple(sorted(result.keys())) != tuple(sorted(RAG_RESULT_FIELDS)):
        problems.append(
            "result keys must be exactly %s (got %s)"
            % (list(RAG_RESULT_FIELDS), sorted(result.keys()))
        )
        return problems
    if result["status"] not in (STATUS_OK, STATUS_ABSTAINED, STATUS_PROCESSING_ERROR):
        problems.append("invalid status %r" % result["status"])
    if result["confidence"] not in ("HIGH", "MEDIUM", "LOW"):
        problems.append("invalid confidence label %r" % result["confidence"])
    if not isinstance(result["confidence_score"], (int, float)) or not (
        0.0 <= float(result["confidence_score"]) <= 1.0
    ):
        problems.append("confidence_score must be a number in 0.0–1.0")
    if not isinstance(result["answer"], str) or not result["answer"].strip():
        problems.append("answer must be a non-empty string")
    if not isinstance(result["citations"], list):
        problems.append("citations must be a list")

    if result["status"] == STATUS_OK:
        if result["abstention"] is not False or result["abstention_reason"] is not None:
            problems.append("status ok requires abstention False and reason None")
        if not result["citations"]:
            problems.append("status ok requires at least one citation")
        if DISCLAIMER_EN not in result["answer"] and DISCLAIMER_HI not in result["answer"]:
            problems.append("status ok answer must carry the disclaimer")
    elif result["status"] == STATUS_ABSTAINED:
        if result["abstention"] is not True or not result["abstention_reason"]:
            problems.append("status abstained requires abstention True and a reason")
        if result["citations"]:
            problems.append("status abstained must not carry citations")
    else:  # processing_error
        if result["abstention"] is not False:
            problems.append("processing_error is not an abstention")
        if result["citations"]:
            problems.append("processing_error must not carry citations")

    if result["citations"]:
        problems.extend(
            problem.replace("citations", "citation", 1)
            for problem in validate_citations(result["citations"])
        )
    return problems


# ---------------------------------------------------------------------------
# Evidence preparation
# ---------------------------------------------------------------------------


def _filter_relevant(hits, matched_areas):
    """Drop retrieval noise: keep records scoring >= _NOISE_FLOOR that are
    either within half of the best score or belong to any scope area the
    routing implicated. Deterministic."""
    if not hits:
        return []
    best = max(hit["score"] for hit in hits)
    kept = []
    for hit in hits:
        record, score = hit["record"], hit["score"]
        if score < _NOISE_FLOOR:
            continue
        if 2 * score >= best or record.get("scope_area") in matched_areas:
            kept.append({"record": record, "score": score})
    return kept


def _evidence_blocks(evidence):
    blocks = []
    for index, hit in enumerate(evidence, start=1):
        record = hit["record"]
        blocks.append(
            "[E%d] source: %s\nsection: %s\neffective date: %s\nurl: %s\n"
            "excerpt (verbatim): %s"
            % (
                index,
                record["source_name"],
                record["section"],
                record["effective_date"],
                record["url"],
                record["excerpt"],
            )
        )
    return blocks


# ---------------------------------------------------------------------------
# Generation — hosted LLM mode
# ---------------------------------------------------------------------------

_JSON_RE = re.compile(r"^\s*(?:```(?:json)?\s*)?(.+?)(?:\s*```)?\s*$", re.DOTALL)

_SYSTEM_PROMPT_EN = """You are the India IP & Regulatory Guidance specialist of IP-SAKTI Sahayak, an assistant for Ayurveda intellectual-property and regulatory questions under INDIAN law only.

Hard rules:
1. Use ONLY the facts contained in the evidence blocks provided. Never add any statute, section, rule, regulation, fee, form, procedure, deadline, case or URL from your own knowledge.
2. If the evidence does not fully answer the question, state exactly what the evidence covers and plainly say what it does not cover. Do not fill gaps.
3. Cite evidence inline with the markers [E1], [E2], ... exactly as provided, and place at least one marker in the answer.
4. Quote section numbers and any numbers/dates/amounts EXACTLY as they appear in the evidence (e.g. "Section 3(p)").
5. Never name any URL that does not appear verbatim in the evidence.
6. You are not a lawyer and this is not legal advice; write as general information for a non-expert audience.
7. Keep the answer between 90 and 200 words, plain prose.

Output STRICT JSON only — no markdown, no commentary — exactly in this shape:
{"answer": "...", "evidence_used": ["E1", "E2"]}
"""

_SYSTEM_PROMPT_HI = _SYSTEM_PROMPT_EN.replace(
    "7. Keep the answer between 90 and 200 words, plain prose.",
    "7. Keep the answer between 90 and 200 words, plain prose.\n"
    "8. Write the answer in HINDI (Devanagari script). Keep statute names, "
    "section numbers, and source titles in their original English form "
    "(for example: \"Patents Act, 1970 की धारा 3(p)\"). Do not invent Hindi "
    "names for statutes or regulations.",
)

_TKDL_PROMPT_NOTE = (
    "Context note (permitted pointer only): if the question concerns "
    "patentability of traditional knowledge or classical formulations, you "
    "may mention that India's Traditional Knowledge Digital Library (TKDL, "
    "https://tkdl.res.in) is the defensive-disclosure database used to help "
    "prevent erroneous patents on traditional knowledge and that its "
    "detailed contents are available to patent offices rather than the "
    "public. Do not state any other TKDL detail."
)

_MULTI_REGIME_PROMPT_NOTE = (
    "Multi-regime note: the evidence covers more than one legal area. "
    "Address each area the evidence supports, clearly separated (for example "
    "the patent position and the geographical-indication position), and do "
    "not mix the regimes together."
)


def _extract_json(text):
    """Parse the LLM's strict-JSON reply, tolerantly stripping a single
    markdown fence. Returns the parsed dict or raises ValueError."""
    match = _JSON_RE.match(text or "")
    payload = match.group(1) if match else (text or "")
    return json.loads(payload)


def _parse_llm_output(text, evidence_by_label):
    """Parse and structurally validate the LLM JSON output.
    Returns (answer_text, cited_hit dicts) or raises ValueError with a
    machine-readable detail."""
    try:
        parsed = _extract_json(text)
    except ValueError as error:
        raise ValueError("malformed JSON from LLM (%s)" % error)
    if not isinstance(parsed, dict):
        raise ValueError("LLM output is not a JSON object")
    answer = parsed.get("answer")
    used = parsed.get("evidence_used")
    if not isinstance(answer, str) or len(answer.strip()) < _MIN_ANSWER_CHARS:
        raise ValueError("LLM answer missing or too short to be guidance")
    if not isinstance(used, list) or not used:
        raise ValueError("LLM output does not reference any evidence")
    cited = []
    for label in used:
        hit = evidence_by_label.get(label)
        if hit is None:
            raise ValueError("LLM referenced evidence %r which was not provided" % label)
        if hit not in cited:
            cited.append(hit)
    return answer.strip(), cited


# ---------------------------------------------------------------------------
# Post-generation content guards (apply to BOTH generation modes)
# ---------------------------------------------------------------------------

_SECTION_REF_PATTERNS = (
    re.compile(
        r"(?i)\bsections?\s+(\d+[A-Z]?(?:\s*\(\d+\))?(?:\s*\([a-z0-9\-]{1,5}\))*)"
    ),
    re.compile(r"(?i)\bregulations?\s+(\d+[A-Z]?(?:\s*\([a-z0-9\-]{1,5}\))*)"),
    re.compile(r"(?i)\brules?\s+(\d+[A-Z]?(?:\s*\(\d+\))?(?:\s*\([a-z0-9\-]{1,5}\))*)"),
    re.compile(r"धारा\s*(\d+[A-Z]?(?:\s*\(\d+\))?(?:\s*\([a-z0-9\-]{1,5}\))*)"),
    re.compile(r"(?i)\bschedules?\s+([A-Z0-9][A-Z0-9\-]*)"),
)
_URL_RE = re.compile(r"https?://[^\s\)\]\"'<>]+")
_AMOUNT_RE = re.compile(r"(₹\s*[\d,]+(?:\.\d+)?|Rs\.?\s*[\d,]+|INR\s*[\d,]+|\b[\d,]+(?:\.\d+)?\s*(?:rupees|percent)|\b\d+(?:\.\d+)?\s*%)")
_DURATION_RE = re.compile(r"\b\d+(?:\.\d+)?[-\s]?(?:years?|months?|days?)\b", re.IGNORECASE)


def _normalise(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def check_supported_content(answer, cited_hits):
    """Verify every legal-looking claim in the answer is backed by the cited
    evidence. Returns a list of unsupported-content problems (empty = ok).

    Guards (all deterministic):
    - every statutory/regulation/rule/schedule reference in the answer must
      appear in a cited record's section or excerpt (or effective date);
    - every URL in the answer must be a cited record URL or the TKDL pointer;
    - every monetary amount / percentage must appear verbatim in the cited
      evidence;
    - every duration written in digits must appear verbatim in the cited
      evidence.
    """
    cited_records = [hit["record"] for hit in cited_hits]
    support_text = _normalise(
        " ".join(
            record["source_name"] + " " + record["section"] + " "
            + record["excerpt"] + " " + record["effective_date"]
            for record in cited_records
        )
    )
    problems = []

    for pattern in _SECTION_REF_PATTERNS:
        for match in pattern.finditer(answer):
            reference = _normalise(match.group(0))
            keyword = _normalise(match.group(1))
            if keyword not in support_text:
                problems.append(
                    "answer cites %r which is not present in the cited evidence"
                    % match.group(0).strip()
                )

    for url in _URL_RE.findall(answer):
        url_clean = url.rstrip(".,;")
        allowed = any(
            url_clean == record["url"].rstrip("/") or url_clean.startswith(record["url"].rstrip("/") + "/")
            or record["url"].startswith(url_clean)
            for record in cited_records
        ) or any(url_clean.startswith(prefix) for prefix in ALLOWED_POINTER_PREFIXES)
        if not allowed:
            problems.append("answer names a URL %r that is not cited evidence" % url_clean)

    for amount in _AMOUNT_RE.findall(answer):
        if _normalise(amount) not in support_text:
            problems.append(
                "answer states amount/rate %r which does not appear in the "
                "cited evidence" % amount.strip()
            )

    for duration in _DURATION_RE.findall(answer):
        if _normalise(duration) not in support_text:
            problems.append(
                "answer states duration %r which does not appear in the "
                "cited evidence" % duration.strip()
            )

    return problems


# ---------------------------------------------------------------------------
# Generation — deterministic template mode
# ---------------------------------------------------------------------------


def _template_answer(question, evidence, language, scope_area):
    """Evidence-only answer: restates the retrieved provisions verbatim and
    adds no interpretation of its own."""
    cited_lines = []
    for index, hit in enumerate(evidence, start=1):
        record = hit["record"]
        cited_lines.append(
            "[E%d] %s — %s: \u201c%s\u201d" % (index, record["section"], record["source_name"], record["excerpt"])
        )
    body = "\n\n".join(cited_lines)
    if language == "hi":
        intro = (
            "आपके प्रश्न से संबंधित सत्यापित भारतीय स्रोतों के प्रावधान नीचे "
            "उद्धृत हैं (प्रावधान मूल अंग्रेज़ी पाठ में हैं):"
        )
        closing = (
            "ये प्रावधान इस प्रश्न से संबंधित भारतीय कानूनी सामग्री हैं। उद्धृत "
            "प्रावधानों के अलावा कोई अतिरिक्त व्याख्या नहीं जोड़ी गई है।"
        )
        tkdl = " " + TKDL_POINTER_HI if scope_area == "patents" else ""
    else:
        intro = (
            "The verified India sources retrieved for your question contain "
            "the following directly relevant provisions:"
        )
        closing = (
            "Read together, these are the Indian legal provisions relevant "
            "to your question. No interpretation beyond the quoted "
            "provisions has been added."
        )
        tkdl = " " + TKDL_POINTER_EN if scope_area == "patents" else ""
    return "%s\n\n%s\n\n%s%s" % (intro, body, closing, tkdl)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def answer_india_question(query, language=None, jurisdiction=None, llm=None):
    """Answer one India IP/regulatory question. Returns the RAG Result dict.

    llm: optional injected client with a .complete(system, user) method
    (tests use this), the string "template" to force the deterministic
    evidence-only mode, or None to use the configured hosted API (falling
    back to template mode when M3_LLM_* is not configured).
    """
    try:
        decision = routing.route_query(query, language=language, jurisdiction=jurisdiction)
        lang = decision["language"]

        if decision["route"] == "international_only":
            return _abstain(
                "out_of_scope_international",
                "this is an international/export question, which Member 3's "
                "India corpus deliberately does not cover",
                lang,
            )
        if decision["route"] == "abs_tk_specialist":
            return _abstain(
                "out_of_scope_abs_tk",
                "deep ABS/Nagoya/TKDL-access questions belong to the "
                "ABS/TK specialist, not the India guidance corpus",
                lang,
            )
        if decision["route"] != "india_ip":
            return _abstain(
                "out_of_scope",
                decision["reason"],
                lang,
            )

        hits, sufficiency = retrieve_evidence(query, routing_decision=decision)
        if not sufficiency["sufficient"]:
            return _abstain(
                "insufficient_evidence",
                sufficiency["reason"],
                lang,
                confidence_score=_weak_confidence(hits, decision["scope_area"]),
            )

        evidence = _filter_relevant(hits, decision.get("matched_areas") or [])
        evidence_by_label = {
            "E%d" % index: hit for index, hit in enumerate(evidence, start=1)
        }

        client = llm_mod.get_llm_client() if llm is None else llm
        if client == "template":
            client = None

        if client is not None:
            multi_regime = len(decision.get("matched_areas") or []) > 1
            system_prompt = _SYSTEM_PROMPT_HI if lang == "hi" else _SYSTEM_PROMPT_EN
            user_prompt = (
                "Question: %s\n\nRouted scope area: %s\n\n"
                "Evidence blocks (the ONLY permitted sources):\n\n%s\n\n%s\n\n%s\n\n%s"
                % (
                    query,
                    decision["scope_area"],
                    "\n\n".join(_evidence_blocks(evidence)),
                    _TKDL_PROMPT_NOTE if decision["scope_area"] == "patents" else "",
                    _MULTI_REGIME_PROMPT_NOTE if multi_regime else "",
                    "Respond with the strict JSON object now.",
                )
            )
            raw = client.complete(system_prompt, user_prompt)  # LLMError → processing_error
            try:
                answer_text, cited_hits = _parse_llm_output(raw, evidence_by_label)
            except ValueError as error:
                return _abstain("llm_output_invalid", str(error), lang)
        else:
            answer_text = _template_answer(
                query, evidence, lang, decision["scope_area"]
            )
            cited_hits = list(evidence)

        unsupported = check_supported_content(answer_text, cited_hits)
        if unsupported:
            return _abstain("unsupported_content", "; ".join(unsupported), lang)

        citations = [build_citation(hit["record"]) for hit in cited_hits]
        citation_problems = validate_citations(citations)
        if citation_problems:
            return _abstain(
                "citation_validation_failed", "; ".join(citation_problems), lang
            )

        best_score = max(hit["score"] for hit in hits)
        label, score, _explanation = confidence_mod.compute_confidence(
            [hit["record"] for hit in cited_hits],
            routed_scope_area=decision["scope_area"],
            best_score=best_score,
        )
        if label == "LOW":
            return _abstain(
                "low_confidence",
                "retrieved evidence is not strong enough for confident "
                "guidance (confidence_score %.2f)" % score,
                lang,
                confidence_score=score,
            )

        answer_text = answer_text.rstrip() + "\n\n" + (
            DISCLAIMER_HI if lang == "hi" else DISCLAIMER_EN
        )
        return _result(
            answer_text,
            citations,
            label,
            score,
            False,
            None,
            STATUS_OK,
        )
    except llm_mod.LLMError as error:
        return _processing_error(str(error))
    except Exception as error:  # pragma: no cover — unexpected internal failure
        return _processing_error("%s: %s" % (type(error).__name__, error))


def _weak_confidence(hits, scope_area):
    """Confidence score for a low-evidence abstention (deterministic)."""
    if not hits:
        return 0.0
    label, score, _ = confidence_mod.compute_confidence(
        [hit["record"] for hit in hits[:1]], routed_scope_area=scope_area,
        best_score=hits[0]["score"],
    )
    return score
