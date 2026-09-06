"""Member 4 Phase 2 — standalone ABS/TK guidance feature.

Turns the verified Phase 1 corpus into a guidance feature with:

- deterministic, explainable ABS/TK relevance determination (classify_query)
- deterministic evidence retrieval (reuses Phase 1 retrieval.retrieve)
- conservative evidence sufficiency + explainable confidence (no LLM
  self-assessment)
- grounded guidance generation: hosted LLM when credentials exist
  (llm_client.HostedLLM), deterministic evidence-only composer otherwise
  (offline stand-in; never presented as an LLM)
- citation validation against stored records (unknown ids, fabricated URLs,
  altered sections/excerpts, missing fields all rejected)
- content validation: fabricated URLs, invented fees/amounts, fabricated
  TKDL specifics and section/article/rule claims not present in cited
  evidence all cause abstention
- safe TKDL pointer (public-level description only; tkdl.res.in)
- abstention: status "abstained" with an honest reason; never a fabricated
  partial answer
- exact Member 4 result contract:
    answer, citations, confidence, confidence_score, abstention,
    abstention_reason, status, tkdl_pointer

This module imports nothing from Members 1, 2, 3 or 5.
"""

import json
import re

import corpus
import hindi
import llm_client
import retrieval

# --------------------------------------------------------------------------
# 1. Relevance determination (deterministic, explainable)
# --------------------------------------------------------------------------

STRONG_ABS_PHRASES = (
    "biological resource", "bio-resource", "biological diversity",
    "biodiversity management committee", "national biodiversity authority",
    "state biodiversity board", "benefit sharing", "access and benefit sharing",
    "biological diversity act", "biological diversity rules", "nagoya",
    "prior informed consent", "mutually agreed terms", "bio-piracy",
    "biopiracy", "genetic resource", "bio-survey", "bio-utilisation",
    "bio utilization", "fair and equitable",
)
STRONG_ABS_TOKENS = {"nba", "sbb", "bmc", "abs", "tkdl", "nagoya", "bda", "biodiversity", "biopiracy"}

TK_PHRASES = (
    "traditional knowledge", "tkdl", "prior art", "codified traditional knowledge",
    "classical formulation", "classical ayurvedic", "authoritative text",
    "first schedule", "ayurvedic text", "folk variety",
)

# Weak (contextual) ABS signals: not sufficient alone to assert strong ABS
# authority claims, but enough to treat the query as ABS-relevant and let the
# evidence sufficiency gate decide whether we can actually answer.
WEAK_ABS_TOKENS = {
    "plant", "plants", "herbal", "herb", "herbs", "medicinal", "seed", "seeds",
    "neem", "tulsi", "ashwagandha", "turmeric", "amla", "formulation",
    "formulations", "commercialisation", "commercialization", "commercialise",
    "commercialize", "cultivated", "cultivation", "farmer", "farmers",
    "cultivator", "vaids", "hakims", "vaidya", "forest", "access",
}

# Other-IP domains are NOT Member 4's (they belong to M3/M5). Specific
# multi-word phrases (checked before weak ABS signals) always route away:
# e.g. "plant variety" is PPV&FRA, not ABS, even though it contains "plant".
# Bare IP tokens ("patent") are deliberately weaker: a query that names a
# biological resource AND a patent is a genuine ABS/IPR intersection
# (Biological Diversity Act s.6) and stays in this workstream, whereas bare
# "trademark"/"copyright" involve no biological-resource access and always
# route away.
OTHER_IP_PHRASES = (
    "plant variety", "trade mark", "trademark", "copyright", "gi tag",
    "geographical indication", "design registration",
    "madrid protocol", "madrid system", "hague system", "hague agreement",
    "pct application", "patent application", "patentability", "patent office",
    "patent cooperation treaty", "designs act", "trade marks act",
    "ip india", "inpass",
)
OTHER_IP_TOKENS = {"trademark", "patent", "copyright", "madrid", "hague", "pct"}

DOMAIN_ABS = "ABS"
DOMAIN_TK = "TK"
DOMAIN_OTHER_IP = "OTHER_IP"
DOMAIN_UNCLEAR = "UNCLEAR"


class Relevance:
    """Explainable classification result for one query."""

    def __init__(self, domain, signals, rationale, language, shadow,
                 other_ip_signals=()):
        self.domain = domain
        self.signals = signals
        self.rationale = rationale
        self.language = language
        self.shadow = shadow
        # Co-present other-IP tokens (e.g. "patent") when the query is still
        # classified ABS/TK - used for the explicit boundary note.
        self.other_ip_signals = list(other_ip_signals)

    def __repr__(self):  # pragma: no cover - debug aid
        return f"Relevance({self.domain!r}, signals={self.signals!r}, lang={self.language!r})"


def _contains_phrase(text_lower, phrases):
    return [p for p in phrases if p in text_lower]


def _lexicon_token_hits(tokens, lexicon):
    """Prefix-aware lexicon matching (same matcher as retrieval), so e.g.
    "patenting" hits the "patent" signal and "plants" hits "plant"."""
    return sorted({
        entry
        for entry in lexicon
        if any(retrieval._matches(token, entry) for token in tokens)
    })


def classify_query(query):
    """Classify a query into ABS / TK / OTHER_IP / UNCLEAR with matched signals.

    Deterministic and purely lexicon/phrase based; the Hindi shadow query is
    used for Devanagari input so both languages follow one code path.
    """
    language = hindi.detect_language(query)
    shadow = hindi.shadow_query(query)
    low = " ".join(shadow.lower().split())

    tk_hits = _contains_phrase(low, TK_PHRASES)
    strong_hits = _contains_phrase(low, STRONG_ABS_PHRASES)
    tokens = set(retrieval._tokenize(low))
    strong_token_hits = _lexicon_token_hits(tokens, STRONG_ABS_TOKENS)
    other_ip_phrase_hits = _contains_phrase(low, OTHER_IP_PHRASES)
    other_ip_token_hits = _lexicon_token_hits(tokens, OTHER_IP_TOKENS)
    weak_hits = _lexicon_token_hits(tokens, WEAK_ABS_TOKENS)

    # Case-specific exemption determinations ("is X exempt?") are never
    # answerable from the curated corpus - always abstain, never guess.
    exemption_intent = bool(_EXEMPTION_INTENT_RE.search(low))

    if strong_hits or strong_token_hits:
        signals = strong_hits + strong_token_hits + (tk_hits if tk_hits else [])
        domain = DOMAIN_ABS
        rationale = "strong ABS signal(s): " + ", ".join(signals)
    elif tk_hits:
        domain = DOMAIN_TK
        signals = tk_hits
        rationale = "traditional-knowledge / prior-art signal(s): " + ", ".join(tk_hits)
    elif other_ip_phrase_hits:
        signals = other_ip_phrase_hits
        domain = DOMAIN_OTHER_IP
        rationale = "other-IP signal(s) with no ABS/TK signal: " + ", ".join(signals)
    elif weak_hits:
        domain = DOMAIN_ABS
        signals = weak_hits
        rationale = "contextual biological-resource signal(s): " + ", ".join(weak_hits)
    elif other_ip_token_hits:
        signals = other_ip_token_hits
        domain = DOMAIN_OTHER_IP
        rationale = "other-IP signal(s) with no ABS/TK signal: " + ", ".join(signals)
    else:
        domain = DOMAIN_UNCLEAR
        signals = []
        rationale = "no ABS/TK or other-IP signal recognized"

    other_ip_signals = other_ip_token_hits if domain in (DOMAIN_ABS, DOMAIN_TK) else []
    relevance = Relevance(domain, signals, rationale, language, shadow,
                          other_ip_signals=other_ip_signals)
    relevance.exemption_intent = exemption_intent
    return relevance


# --------------------------------------------------------------------------
# 2. Evidence, sufficiency, confidence (all deterministic)
# --------------------------------------------------------------------------

TOP_K = 5
SUFFICIENT_TOP_SCORE = 6.0     # a top record must be strongly relevant
CORROBORATION_FLOOR = 4.5      # a second record must at least clear retrieval
MIN_CONFIDENCE_TO_ANSWER = 0.5


def get_evidence(shadow_query_text):
    return retrieval.retrieve(shadow_query_text, top_k=TOP_K)


def compute_confidence(evidence, relevance):
    """Deterministic, explainable confidence from evidence quality/alignment.

    base from top record score, + corroboration from additional records
    clearing the retrieval floor, + jurisdiction/scope alignment.
    Never derived from any LLM self-assessment.
    """
    if not evidence:
        return "LOW", 0.0
    top = evidence[0]["score"]
    base = 0.45 if top >= 10.0 else 0.32 if top >= 8.0 else 0.25
    corroborators = sum(1 for item in evidence[1:] if item["score"] >= CORROBORATION_FLOOR)
    score = base + 0.12 * min(corroborators, 2)

    jurisdictions = {item["record"]["jurisdiction"] for item in evidence}
    if relevance.domain == DOMAIN_TK:
        # TK/pointer queries legitimately mix India (TKDL) and treaty records.
        score += 0.12
    elif "International" in jurisdictions and _treaty_signal(relevance):
        score += 0.12
    elif "India" in jurisdictions and not _treaty_signal(relevance):
        score += 0.12

    score = max(0.05, min(0.95, round(score, 2)))
    label = "HIGH" if score >= 0.75 else "MEDIUM" if score >= 0.5 else "LOW"
    return label, score


def _treaty_signal(relevance):
    text = " ".join(relevance.signals).lower()
    return "nagoya" in text or "genetic resource" in text or "prior informed consent" in text


# --------------------------------------------------------------------------
# 3. TKDL pointer (public-level description only)
# --------------------------------------------------------------------------

def build_tkdl_pointer(lang):
    return hindi.tkdl_pointer(lang)


# --------------------------------------------------------------------------
# 4. Grounded generation
# --------------------------------------------------------------------------

SYSTEM_CONSTRAINTS = (
    "You are the ABS/TK guidance component of IP-SAKTI Sahayak (Member 4). "
    "Answer ONLY from the numbered evidence records provided. You MUST NOT "
    "invent or imply: legal provisions, section/article/rule numbers, "
    "approval requirements, fees, amounts, timelines, obligations, "
    "authorities, URLs, treaty requirements, or any TKDL database content "
    "(no counts, records, entries, or outcomes attributed to TKDL - TKDL is "
    "pointer-only). Use only section/article/rule numbers that appear in the "
    "cited evidence. Output strict JSON: {\"answer\": string, "
    "\"citation_ids\": [record ids you used], \"citations\": optional list of "
    "citation objects copied verbatim from the evidence}. Answer in the "
    "requested language. Never claim to be a lawyer; the caller appends the "
    "information-not-legal-advice disclaimer."
)


def build_prompt(query, lang, evidence):
    """Build (system, user) messages constraining the model to the evidence."""
    blocks = []
    for i, item in enumerate(evidence, 1):
        r = item["record"]
        blocks.append(
            f"[{i}] id={r['id']}\nsource_name={r['source_name']}\n"
            f"source_type={r['source_type']}\nsection={r['section']}\n"
            f"url={r['url']}\neffective_date={r['effective_date']}\n"
            f"excerpt={r['excerpt']}\nscope_note={r['scope']}"
        )
    language_name = "Hindi (Devanagari)" if lang == "hi" else "English"
    user = (
        f"Query ({language_name}): {query}\n\n"
        f"Curated evidence records (the ONLY permitted knowledge source):\n"
        + "\n\n".join(blocks)
        + "\n\nWrite a short grounded guidance answer in "
        + language_name
        + " using only the facts in these records, and list the ids you used "
        "as citation_ids. If the evidence does not support an answer, say so "
        "in the JSON by returning an empty citation_ids list and an answer "
        "that declines."
    )
    return SYSTEM_CONSTRAINTS, user


# --- offline stand-in composer (deterministic, evidence-only) -------------

# One template per record id; a template is only used when that record was
# actually retrieved, so every claim in a composed answer maps to a cited,
# verified record. Hindi templates exist for the core India records; treaty
# records fall back to English wording with the statutory name kept in
# English (never translated into invented Hindi legal terms).
RECORD_TEMPLATES = {
    "M4-SRC-001": {
        "en": (
            "Section 3(1), Biological Diversity Act 2002: a person covered by "
            "section 3(2) - non-citizens, non-resident citizens, and bodies "
            "corporate not incorporated/registered in India or with foreign "
            "control - must obtain prior approval of the National Biodiversity "
            "Authority to obtain any biological resource occurring in India, "
            "or associated knowledge, for research, commercial utilization, "
            "bio-survey or bio-utilisation."
        ),
        "hi": (
            "धारा 3(1), Biological Diversity Act 2002: धारा 3(2) में आने वाले "
            "व्यक्ति - गैर-भारतीय नागरिक, अप्रवासी भारतीय नागरिक, तथा विदेशी "
            "नियंत्रण वाले संस्थान - को भारत में पाए जाने वाले किसी जैव संसाधन "
            "या उससे जुड़े ज्ञान को अनुसंधान, व्यावसायिक उपयोग (commercial "
            "utilization), बायो-सर्वे या बायो-यूटिलाइजेशन हेतु प्राप्त करने से "
            "पहले राष्ट्रीय जैव विविधता प्राधिकरण (NBA) की पूर्व अनुमति लेनी "
            "होगी।"
        ),
    },
    "M4-SRC-002": {
        "en": (
            "Amended section 6 (Biological Diversity (Amendment) Act 2023): "
            "Indian persons must register with the NBA before grant of an "
            "intellectual property right based on biological resources "
            "accessed from India or associated traditional knowledge, and "
            "obtain prior NBA approval at the time of commercialisation; "
            "foreign-controlled persons need prior NBA approval before grant "
            "(section 6(1))."
        ),
        "hi": (
            "संशोधित धारा 6 (Biological Diversity (Amendment) Act 2023): "
            "भारतीय व्यक्तियों को भारत से प्राप्त जैव संसाधनों या संबद्ध "
            "पारंपरिक ज्ञान पर आधारित किसी बौद्धिक संपदा अधिकार के grant से "
            "पहले NBA में पंजीकरण कराना होगा और व्यावसायीकरण (commercialisation) "
            "के समय NBA की पूर्व अनुमति लेनी होगी; विदेशी नियंत्रित व्यक्तियों "
            "को grant से पहले NBA की पूर्व अनुमति चाहिए (धारा 6(1))।"
        ),
    },
    "M4-SRC-003": {
        "en": (
            "Substituted section 7 (in force 1 April 2024): a person accessing "
            "biological resources and associated knowledge for commercial "
            "utilisation must first give prior intimation to the concerned "
            "State Biodiversity Board; the section does not apply to codified "
            "traditional knowledge, cultivated medicinal plants and their "
            "products, local people and communities, and vaids, hakims and "
            "registered AYUSH practitioners practising indigenous medicine for "
            "sustenance and livelihood. For cultivated medicinal plants the "
            "exemption requires a certificate of origin from the Biodiversity "
            "Management Committee (section 7(2)-(3))."
        ),
        "hi": (
            "प्रतिस्थापित धारा 7 (1 अप्रैल 2024 से लागू): व्यावसायिक उपयोग "
            "(commercial utilisation) के लिए जैव संसाधन और संबद्ध ज्ञान का "
            "उपयोग करने से पहले संबंधित राज्य जैव विविधता बोर्ड को पूर्व सूचना "
            "देना अनिवार्य है; संहिताबद्ध पारंपरिक ज्ञान (codified traditional "
            "knowledge), उगाई गई औषधीय पौधे और उनके उत्पाद, स्थानीय लोग व "
            "समुदाय, तथा आजीविका हेतु देशी चिकित्सा का अभ्यास करने वाले वैद्य, "
            "हकीम और पंजीकृत AYUSH चिकित्सक इस धारा के दायरे से बाहर हैं। उगाई "
            "गई औषधीय पौधों की छूट हेतु जैव विविधता प्रबंधन समिति से "
            "प्रमाण-पत्र (certificate of origin) आवश्यक है (धारा 7(2)-(3))।"
        ),
    },
    "M4-SRC-004": {
        "en": (
            "Section 21(1): while determining benefit sharing for approvals, "
            "the NBA must ensure the terms secure fair and equitable sharing "
            "of benefits arising from the use of accessed biological "
            "resources, their derivatives, innovations, practices and "
            "knowledge, in accordance with mutually agreed terms."
        ),
        "hi": (
            "धारा 21(1): अनुमोदन हेतु लाभ साझेदारी (benefit sharing) तय करते "
            "समय NBA यह सुनिश्चित करेगा कि शर्तें प्राप्त जैव संसाधनों, उनके "
            "डेरिवेटिव, नवाचारों, पद्धतियों और ज्ञान के उपयोग से उत्पन्न लाभों "
            "की निष्पक्ष और न्यायसंगत साझेदारी - परस्पर सहमत शर्तों के अनुसार - "
            "सुनिश्चित करें।"
        ),
    },
    "M4-SRC-005": {
        "en": (
            "Rule 13(1), Biological Diversity Rules 2024: persons covered "
            "under section 3(2) apply through the NBA web portal - Form 1 for "
            "research or bio-survey and bio-utilisation, Form 2 for "
            "commercial utilisation; every application carries the specified "
            "fee paid electronically to the National Biodiversity Fund "
            "(Rule 13(3))."
        ),
        "hi": (
            "नियम 13(1), Biological Diversity Rules 2024: धारा 3(2) में आने "
            "वाले व्यक्ति NBA के वेब पोर्टल के माध्यम से आवेदन करते हैं - "
            "अनुसंधान या बायो-सर्वे तथा बायो-यूटिलाइजेशन हेतु फॉर्म 1, व्यावसायिक "
            "उपयोग हेतु फॉर्म 2; प्रत्येक आवेदन के साथ निर्धारित शुल्क "
            "इलेक्ट्रॉनिक रूप से राष्ट्रीय जैव विविधता कोष में जमा करना होता "
            "है (नियम 13(3))।"
        ),
    },
    "M4-SRC-006": {
        "en": (
            "Nagoya Protocol Article 5(5): benefits arising from the "
            "utilization of traditional knowledge associated with genetic "
            "resources must be shared in a fair and equitable way with the "
            "indigenous and local communities holding that knowledge, upon "
            "mutually agreed terms."
        ),
        "hi": (
            "नागोया प्रोटोकॉल अनुच्छेद 5(5): जैव विविधता संबंधी ज्ञान हेतु - "
            "genetic resources से जुड़े पारंपरिक ज्ञान के उपयोग से उत्पन्न लाभ "
            "उस ज्ञान रखने वाले स्वदेशी और स्थानीय समुदायों के साथ परस्पर "
            "सहमत शर्तों के आधार पर निष्पक्ष और न्यायसंगत रूप से साझा किए जाएँ।"
        ),
    },
    "M4-SRC-007": {
        "en": (
            "Nagoya Protocol Article 6(1): access to genetic resources for "
            "their utilization is subject to the prior informed consent of "
            "the Party providing the resources (the country of origin or a "
            "Party that acquired them in accordance with the Convention), "
            "unless that Party determines otherwise."
        ),
    },
    "M4-SRC-008": {
        "en": (
            "Nagoya Protocol Article 7: traditional knowledge associated with "
            "genetic resources and held by indigenous and local communities "
            "must be accessed with the prior and informed consent or approval "
            "and involvement of those communities, with mutually agreed terms "
            "established."
        ),
    },
    "M4-SRC-009": {
        "en": (
            "CBD Article 8(j): subject to national legislation, Parties "
            "should respect, preserve and maintain the knowledge, innovations "
            "and practices of indigenous and local communities embodying "
            "traditional lifestyles, promote their wider application with the "
            "holders' approval and involvement, and encourage equitable "
            "sharing of benefits from their utilization."
        ),
    },
    "M4-SRC-010": {
        "en": (
            "TKDL (https://tkdl.res.in) is an initiative of CSIR and the "
            "Ministry of Ayush maintaining a representative database of "
            "Ayurvedic, Unani, Siddha and Sowarigpa formulations; access to "
            "the full database is available to patent offices only under the "
            "TKDL Access Agreement."
        ),
    },
}

_FRAMING_EN = (
    "Based on the curated ABS/TK evidence, the applicable Biological "
    "Diversity / Access-and-Benefit-Sharing framework is:"
)
_FRAMING_HI = (
    "उपलब्ध सत्यापित ABS/पारंपरिक-ज्ञान साक्ष्य के आधार पर लागू Biological "
    "Diversity / ABS ढाँचा इस प्रकार है:"
)
_CLOSING_EN = (
    "Which approvals apply depends on who is accessing the biological "
    "resource (Indian person vs foreign-controlled entity), the purpose "
    "(research vs commercial utilisation) and whether intellectual property "
    "rights are involved - see the cited provisions. Verify current "
    "requirements with the National Biodiversity Authority before acting."
)
_CLOSING_HI = (
    "कौन-से अनुमोदन लागू होंगे, यह इस बात पर निर्भर करता है कि जैव संसाधन कौन "
    "प्राप्त कर रहा है (भारतीय व्यक्ति या विदेशी नियंत्रित संस्था), उद्देश्य "
    "क्या है (अनुसंधान या व्यावसायिक उपयोग) और बौद्धिक संपदा अधिकार जुड़े हैं "
    "या नहीं - देखें उद्धृत प्रावधान। कार्रवाई से पहले राष्ट्रीय जैव विविधता "
    "प्राधिकरण से वर्तमान आवश्यकताओं की पुष्टि करें।"
)
_TK_OPEN_EN = (
    "Your question involves traditional knowledge. From the curated evidence:"
)
_TK_OPEN_HI = "आपका प्रश्न पारंपरिक ज्ञान से जुड़ा है। उपलब्ध साक्ष्य के आधार पर:"
_TK_CLOSE_EN = (
    "Whether this knowledge is prior art against a specific patent claim is a "
    "determination this workstream does not make - consult TKDL (see pointer) "
    "via the relevant patent examiner or a qualified patent professional."
)
_TK_CLOSE_HI = (
    "यह ज्ञान किसी विशेष पेटेंट क्लेम के विरुद्ध prior art है या नहीं - यह "
    "निर्णय यह वर्कस्ट्रीम नहीं देता; TKDL (पॉइंटर देखें) / संबंधित पेटेंट "
    "परीक्षक या योग्य पेटेंट विशेषज्ञ से परामर्श करें।"
)
_PATENT_NOTE_EN = (
    "Note: the patent/trademark aspect of this question is outside this "
    "workstream's evidence; the ABS requirements above apply independently, "
    "and for the patentability or IPR-filing aspects consult a qualified "
    "patent professional."
)
_PATENT_NOTE_HI = (
    "ध्यान दें: इस प्रश्न का पेटेंट/ट्रेडमार्क पक्ष इस वर्कस्ट्रीम के साक्ष्य "
    "से बाहर है; ऊपर दी गई ABS आवश्यकताएँ स्वतंत्र रूप से लागू होती हैं, तथा "
    "पेटेंट/बौद्धिक संपदा पक्ष हेतु योग्य पेटेंट विशेषज्ञ से परामर्श करें।"
)


def compose_offline(relevance, evidence, lang):
    """Deterministic stand-in composer: only retrieved records are used, so
    every claim maps to a cited, verified record. NOT an LLM."""
    ids = [item["record"]["id"] for item in evidence]
    open_line = _TK_OPEN_HI if lang == "hi" else _TK_OPEN_EN
    close_line = _TK_CLOSE_HI if lang == "hi" else _TK_CLOSE_EN
    bullets = []
    for record_id in ids:
        template = RECORD_TEMPLATES[record_id].get(lang) or RECORD_TEMPLATES[record_id]["en"]
        bullets.append(f"- {template}")
    framing = _FRAMING_HI if lang == "hi" else _FRAMING_EN
    if relevance.domain == DOMAIN_TK:
        parts = [open_line] + bullets + [close_line]
    else:
        closing = _CLOSING_HI if lang == "hi" else _CLOSING_EN
        parts = [framing] + bullets + [closing]
    if relevance.other_ip_signals:
        parts.append(_PATENT_NOTE_HI if lang == "hi" else _PATENT_NOTE_EN)
    answer = "\n".join(parts)
    return {"answer": answer, "citation_ids": ids}


def parse_llm_output(raw):
    """Parse the model's JSON (tolerating code fences). Raises ValueError."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"```\s*$", "", text).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"malformed model output: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("answer"), str):
        raise ValueError("model output missing string 'answer'")
    return data


# --------------------------------------------------------------------------
# 5. Citation + content validation
# --------------------------------------------------------------------------

REQUIRED_CITATION_FIELDS = (
    "id", "source_name", "source_type", "section", "excerpt", "url",
    "effective_date",
)


def validate_citation(citation):
    """Reject unknown ids, fabricated URLs, altered sections/excerpts,
    missing fields. Returns (ok, reason)."""
    if not isinstance(citation, dict):
        return False, "citation is not an object"
    for field in REQUIRED_CITATION_FIELDS:
        if field not in citation:
            return False, f"citation missing required field: {field}"
    record = corpus.get_record(citation["id"])
    if record is None:
        return False, f"unknown citation id: {citation['id']}"
    expected = corpus.to_citation(record)
    for field in REQUIRED_CITATION_FIELDS:
        if citation[field] != expected[field]:
            return False, f"citation field '{field}' does not match the stored record"
    return True, ""


def citations_from_ids(ids):
    """Build citations ONLY from stored records (LLM supplies ids at most)."""
    citations = []
    for record_id in ids or []:
        record = corpus.get_record(record_id)
        if record is not None:
            citations.append(corpus.to_citation(record))
    return citations


_URL_RE = re.compile(r"https?://[^\s)\"']+")
_AMOUNT_RE = re.compile(
    r"[₹$€]\s?\d|Rs\.?\s*\d|\bINR\s*\d|\bUSD\s*\d|\bEUR\s*\d|\bGBP\s*\d"
    r"|\d+\s*(?:rupees|dollars|euros|lakh|crore)"
)
_COUNT_RE = re.compile(
    r"\b\d[\d,\.]*\s+(?:formulations?|records?|entries|manuscripts?|texts)\b",
    re.IGNORECASE,
)
_TKDL_FABRICATION_RE = re.compile(
    r"tkdl\s+(?:says|contains|has|lists|documents|holds|includes|shows)\b"
    r"|tkdl\s+(?:database\s+)?(?:entry|record)\b"
    r"|tkdl\s+.{0,60}?(?:revoked|rejected|granted)\b",
    re.IGNORECASE,
)
_CLAIM_RE = re.compile(
    r"(?:section|article|rule)\s+\d+(?:\([0-9a-zA-Z]+\))*", re.IGNORECASE
)
_HI_CLAIM_RE = re.compile(r"(?:धारा|नियम|अनुच्छेद)\s*\d+")

# Fee/cost intent: the curated corpus deliberately contains no amounts, so
# fee questions must abstain rather than risk an invented figure.
_FEE_INTENT_RE = re.compile(
    r"\b(?:fee|fees|cost|costs|price|charges?|amount payable|shulk)\b|शुल्क|फीस",
    re.IGNORECASE,
)

# Case-specific exemption determinations ("is X exempt?"): the corpus states
# the general statutory exemptions but cannot decide them for a specific
# resource or case - such questions must abstain.
_EXEMPTION_INTENT_RE = re.compile(
    r"\b(?:exempt|exemption|excluded|carve[- ]?out|not\s+(?:apply|applies|"
    r"applicable|covered))\b|छूट",
    re.IGNORECASE,
)

_ALLOWED_POINTER_HOST = "tkdl.res.in"


def _evidence_has_amount(evidence):
    pattern = re.compile(r"[₹$€]\s?\d|Rs\.?\s*\d|\bINR\s*\d|\bUSD\s*\d|\d+\s*(?:rupees|dollars)")
    for item in evidence:
        blob = (item["record"].get("excerpt") or "") + " " + (item["record"].get("scope") or "")
        if pattern.search(blob):
            return True
    return False


def validate_generated(answer_text, citations):
    """Deterministic content guards applied to every generated answer
    (offline and hosted alike). Returns (ok, reason)."""
    text = answer_text or ""
    if not text.strip():
        return False, "empty answer"

    # No fabricated URLs: every URL in the answer must belong to a cited
    # stored record or be the TKDL pointer site.
    allowed_urls = {c["url"] for c in citations} | {f"https://{_ALLOWED_POINTER_HOST}/"}
    for url in _URL_RE.findall(text):
        normalized = url.rstrip("/.") + "/"
        if url not in allowed_urls and normalized not in {u.rstrip('/') + '/' for u in allowed_urls}:
            return False, f"unsupported URL in generated content: {url}"

    # No invented fees/amounts: the verified corpus contains none.
    if _AMOUNT_RE.search(text):
        return False, f"unsupported amount in generated content: {_AMOUNT_RE.search(text).group(0)!r}"

    # No fabricated counts anywhere (evidence contains no counts).
    if _COUNT_RE.search(text):
        return False, "unsupported numeric count in generated content"

    # No fabricated TKDL specifics.
    if _TKDL_FABRICATION_RE.search(text):
        return False, "fabricated TKDL content in generated content"

    # Every section/article/rule claim must exist in a cited record
    # (section marker, excerpt, scope note or source name).
    blobs = []
    for c in citations:
        record = corpus.get_record(c["id"])
        blobs.append(" ".join(
            str(record.get(k) or "") for k in
            ("section", "excerpt", "scope", "source_name")
        ).lower())
    for claim in _CLAIM_RE.findall(text):
        normalized = claim.lower().replace("  ", " ")
        if not any(_claim_in_blob(normalized, blob) for blob in blobs):
            return False, f"legal claim not supported by cited evidence: {claim!r}"
    for claim in _HI_CLAIM_RE.findall(text):
        number = re.search(r"\d+", claim).group(0)
        if not any(re.search(rf"(?:section|article|rule)\s+{number}\b", blob) for blob in blobs):
            return False, f"legal claim not supported by cited evidence: {claim!r}"
    return True, ""


def _claim_in_blob(claim, blob):
    if claim in blob:
        return True
    number = re.search(r"\d+", claim).group(0)
    # "section 7" matches "section 7(2)" style markers
    return re.search(rf"{claim.split()[0]}\s+{number}\b", blob) is not None


# --------------------------------------------------------------------------
# 6. Result construction (exact Member 4 contract)
# --------------------------------------------------------------------------

RESULT_FIELDS = (
    "answer", "citations", "confidence", "confidence_score", "abstention",
    "abstention_reason", "status", "tkdl_pointer",
)


def _result(answer, citations, confidence, confidence_score, abstention,
            abstention_reason, status, tkdl_pointer):
    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "abstention": abstention,
        "abstention_reason": abstention_reason,
        "status": status,
        "tkdl_pointer": tkdl_pointer,
    }


def _abstained(reason_key, detail, lang, tkdl_pointer):
    base = hindi.abstain_text(reason_key, lang)
    answer = base if not detail else base + "\n(" + detail + ")"
    return _result(
        answer=answer,
        citations=[],
        confidence="LOW",
        confidence_score=0.05,
        abstention=True,
        abstention_reason=detail or base,
        status="abstained",
        tkdl_pointer=tkdl_pointer,
    )


# --------------------------------------------------------------------------
# 7. Orchestrator
# --------------------------------------------------------------------------

def answer(query, language=None, llm=None):
    """Answer a free-text query under the Member 4 result contract.

    llm: optional override (used by tests to inject mock models). When None,
    the client is chosen from the environment: hosted LLM when
    M4_LLM_API_KEY is set, deterministic offline stand-in otherwise.
    """
    try:
        relevance = classify_query(query)
        lang = language or relevance.language

        if relevance.domain == DOMAIN_OTHER_IP:
            return _abstained(
                "unrelated",
                "Not classified as ABS/TK: " + relevance.rationale,
                lang,
                tkdl_pointer=None,
            )
        if relevance.domain == DOMAIN_UNCLEAR:
            return _abstained("unclear", relevance.rationale, lang, tkdl_pointer=None)

        evidence = get_evidence(relevance.shadow)
        wants_pointer = relevance.domain == DOMAIN_TK or bool(
            _contains_phrase(" ".join(relevance.signals).lower(), TK_PHRASES)
        )
        tkdl_pointer = build_tkdl_pointer(lang) if wants_pointer else None

        if not evidence:
            return _abstained(
                "no_evidence",
                "insufficient evidence: nothing in the curated corpus matches "
                "this query (" + relevance.rationale + ")",
                lang,
                tkdl_pointer,
            )

        # The curated corpus contains no fee/amount figures; fee questions
        # must abstain rather than risk an invented number.
        if _FEE_INTENT_RE.search(relevance.shadow.lower()) and not _evidence_has_amount(evidence):
            return _abstained(
                "no_evidence",
                "insufficient evidence: the curated corpus contains no fee, "
                "cost or amount figures for this question",
                lang,
                tkdl_pointer,
            )

        # Case-specific exemption determinations are never answerable from
        # the corpus - abstain instead of guessing.
        if getattr(relevance, "exemption_intent", False):
            return _abstained(
                "no_evidence",
                "insufficient evidence: the curated corpus states the general "
                "statutory exemptions but cannot decide a case-specific "
                "exemption determination; consult the NBA or a qualified "
                "professional",
                lang,
                tkdl_pointer,
            )

        confidence_label, confidence_score = compute_confidence(evidence, relevance)
        if evidence[0]["score"] < SUFFICIENT_TOP_SCORE or confidence_score < MIN_CONFIDENCE_TO_ANSWER:
            return _abstained(
                "no_evidence",
                "insufficient evidence (top score %.1f, confidence %.2f)"
                % (evidence[0]["score"], confidence_score),
                lang,
                tkdl_pointer,
            )

        # --- generation ---------------------------------------------------
        if llm is not None:
            mode, client = ("custom", llm)
        else:
            mode, client = llm_client.get_llm_client()

        try:
            if mode == "hosted":
                system, user = build_prompt(query, lang, evidence)
                data = parse_llm_output(client.complete(system, user))
            elif mode == "custom":
                # Test/mock client: same contract as the hosted path.
                system, user = build_prompt(query, lang, evidence)
                data = parse_llm_output(client.complete(system, user))
            else:
                data = compose_offline(relevance, evidence, lang)
        except ValueError as exc:
            # Malformed model output is a validation failure -> abstain.
            return _abstained("validation", f"malformed model output: {exc}", lang, tkdl_pointer)

        # --- validation ---------------------------------------------------
        if "citations" in data and data["citations"] is not None:
            citations = data["citations"]
            for citation in citations:
                ok, reason = validate_citation(citation)
                if not ok:
                    return _abstained(
                        "validation", "citation validation failed: " + reason, lang, tkdl_pointer
                    )
        else:
            citations = citations_from_ids(data.get("citation_ids"))
        if not citations:
            return _abstained(
                "validation", "no valid citations produced for the answer", lang, tkdl_pointer
            )

        answer_text = data["answer"].strip() + "\n" + hindi.disclaimer(lang)
        ok, reason = validate_generated(answer_text, citations)
        if not ok:
            return _abstained("validation", reason, lang, tkdl_pointer)

        return _result(
            answer=answer_text,
            citations=citations,
            confidence=confidence_label,
            confidence_score=confidence_score,
            abstention=False,
            abstention_reason=None,
            status="ok",
            tkdl_pointer=tkdl_pointer,
        )
    except Exception as exc:  # never leak a traceback to the caller
        return _result(
            answer="",
            citations=[],
            confidence="LOW",
            confidence_score=0.05,
            abstention=True,
            abstention_reason=f"processing error: {type(exc).__name__}: {exc}",
            status="processing_error",
            tkdl_pointer=None,
        )
