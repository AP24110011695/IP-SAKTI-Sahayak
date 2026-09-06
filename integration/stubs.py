"""Deterministic stub specialists and stub router for the Phase 1 harness.

These stubs stand in for the real M2–M5 workstreams so the contract tests,
golden scenarios and error-path tests are executable BEFORE Phase 2 wires the
real implementations. Each stub replicates the ACTUAL result shape of the
member it stands in for (see member_interfaces.py for the real interfaces):

    stub_india_specialist      → M3's 7-field RAG Result
                                 (sihmember3.answer_india_question)
    stub_abs_tk_specialist     → M4's 8-field RAG Result (+ tkdl_pointer)
                                 (sihmember4.guidance.answer)
    stub_international_specialist → M5's 7-field RAG Result
                                 (sihmember5.member5.guide)
    stub_classifier            → M2's ClassificationResult
                                 (sihmember2.classify)

In Phase 2 each stub is replaced by a thin adapter that calls the real
member and returns its result unchanged; the assembler, validators and tests
stay as they are.

CONTENT POLICY (safety): stub answer texts and citations are TEST FIXTURES.
Every legal reference they contain is a real name drawn from PS.md /
Research.md / the members' own corpora (Patents Act Section 3(p), TKDL at
tkdl.res.in, the GI Act 1999, the Biological Diversity Act, PCT/Madrid/
Hague, official portal URLs named in PS.md). Citation excerpts are explicit
placeholders — no legal text is fabricated, and stub abstention texts carry
no legal content at all.
"""
from __future__ import annotations

import re

from . import contracts

# ---------------------------------------------------------------------------
# Failure signals a specialist adapter may raise (mapped by the assembler to
# the Plan.md §7 ErrorResponse codes).
# ---------------------------------------------------------------------------


class SpecialistUnavailable(Exception):
    """A registered specialist's backing capability is unreachable → 503."""


class SpecialistProcessingError(Exception):
    """A registered specialist failed while processing → 502."""


# ---------------------------------------------------------------------------
# Stub citation helper
# ---------------------------------------------------------------------------

_STUB_EXCERPT = (
    "Integration stub excerpt — replace with the member workstream's stored "
    "evidence record in Phase 2."
)


def _citation(cid, source_name, source_type, section, url, effective_date=None):
    return {
        "id": cid,
        "source_name": source_name,
        "source_type": source_type,
        "section": section,
        "excerpt": _STUB_EXCERPT,
        "url": url,
        "effective_date": effective_date,
    }


# Real portal URLs exactly as named in PS.md's dataset list / Research.md D.1.
URL_INDIA_CODE = "https://www.indiacode.nic.in"
URL_IP_INDIA = "https://ipindia.gov.in"
URL_TKDL = "https://tkdl.res.in"
URL_NBA = "https://nbaindia.org"
URL_WIPO = "https://www.wipo.int"
URL_WTO = "https://www.wto.org"

_DISCLAIMER_EN = (
    "Disclaimer: IP-SAKTI Sahayak provides general legal information, not "
    "legal advice. Verify against official sources and consult a qualified "
    "IP professional before acting."
)
_DISCLAIMER_HI = (
    "अस्वीकरण: IP-SAKTI सहायक सामान्य कानूनी जानकारी देता है, यह कानूनी सलाह "
    "नहीं है। कोई भी कदम उठाने से पहले आधिकारिक स्रोतों से जानकारी सत्यापित "
    "करें और योग्य विशेषज्ञ से परामर्श लें।"
)
# Copied from sihmember1/m1/config.py — the assembling member owns these
# texts; Phase 2 imports them directly instead of this copy.
DISCLAIMERS = {"en": _DISCLAIMER_EN, "hi": _DISCLAIMER_HI}
FALLBACKS = {
    "en": (
        "I could not find relevant information in my curated corpus for this "
        "question, so I will not guess. Please rephrase the question, consult "
        "the official sources directly, or speak to a qualified professional."
    ),
    "hi": (
        "मेरे चुनिंदा स्रोत-संग्रह में इस प्रश्न से संबंधित जानकारी नहीं मिली, "
        "इसलिए मैं अनुमान नहीं लगाऊंगा। कृपया प्रश्न दूसरे शब्दों में पूछें या "
        "योग्य विशेषज्ञ से परामर्श लें।"
    ),
}


def _rag_result(answer, citations, confidence, confidence_score, abstention,
                abstention_reason, status, **extra):
    result = {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
        "confidence_score": confidence_score,
        "abstention": abstention,
        "abstention_reason": abstention_reason,
        "status": status,
    }
    result.update(extra)
    return result


def _abstain(reason, language="en", **extra):
    return _rag_result(
        answer="",
        citations=[],
        confidence="LOW",
        confidence_score=0.0,
        abstention=True,
        abstention_reason=reason,
        status="abstained",
        **extra,
    )


# ---------------------------------------------------------------------------
# Stub M3 — India IP & regulatory guidance
# ---------------------------------------------------------------------------

_PATENT_TK_KEYWORDS = ("classical", "authoritative text", "traditional knowledge",
                       "classical formulation")
_GI_KEYWORDS = ("gi ", "gi tag", "gi registry", "geographical indication")


class StubIndiaSpecialist:
    """Stands in for sihmember3.answer_india_question (7-field RAG Result).

    modes: ok | abstain | processing_error | unavailable | citation_failure
    """

    domain = contracts.DOMAINS[0]  # INDIA_IP

    def __init__(self, mode: str = "ok"):
        self.mode = mode

    def __call__(self, request: dict) -> dict:
        if self.mode == "unavailable":
            raise SpecialistUnavailable("stub M3 backend is unreachable")
        if self.mode == "processing_error":
            raise SpecialistProcessingError("stub M3 internal failure")
        if self.mode == "abstain":
            return _abstain("insufficient_evidence: stub forced abstention")

        query = request["query"].lower()

        if "patent" in query and any(k in query for k in _PATENT_TK_KEYWORDS):
            result = _rag_result(
                answer=(
                    "A formulation reproduced unchanged from an authoritative "
                    "First-Schedule text is traditional knowledge: Section 3(p) "
                    "of the Patents Act, 1970 bars patents on inventions that "
                    "are, in effect, traditional knowledge or aggregations of "
                    "known properties of traditionally known components. The "
                    "Traditional Knowledge Digital Library (TKDL, "
                    "https://tkdl.res.in) is India's defensive-disclosure "
                    "database used to help prevent erroneous patents on "
                    "traditional knowledge. " + _DISCLAIMER_EN
                ),
                citations=[
                    _citation(
                        "STUB-IN-PATENTS-3P",
                        "Patents Act, 1970",
                        "statute",
                        "Section 3(p)",
                        URL_INDIA_CODE,
                        "1970-09-21",
                    ),
                ],
                confidence="HIGH",
                confidence_score=0.9,
                abstention=False,
                abstention_reason=None,
                status="ok",
            )
            if self.mode == "citation_failure":
                # Break the contract detectably: drop a required citation
                # field, so the integration validator withholds the answer.
                # (A merely invented URL domain is NOT detectable at the
                # integration layer by design — URL authority is each
                # member's own allow-list responsibility.)
                del result["citations"][0]["excerpt"]
            return result

        if any(k in query for k in _GI_KEYWORDS):
            return _rag_result(
                answer=(
                    "Geographical indications are registered in India under the "
                    "Geographical Indications of Goods (Registration and "
                    "Protection) Act, 1999, administered through the GI Registry "
                    "at IP India. " + _DISCLAIMER_EN
                ),
                citations=[
                    _citation(
                        "STUB-IN-GI-ACT",
                        "Geographical Indications of Goods (Registration and Protection) Act, 1999",
                        "statute",
                        "Registration procedure",
                        URL_IP_INDIA,
                        "2003-09-15",
                    ),
                ],
                confidence="HIGH",
                confidence_score=0.85,
                abstention=False,
                abstention_reason=None,
                status="ok",
            )

        return _abstain(
            "insufficient_evidence: no curated India source matches this query"
        )


# ---------------------------------------------------------------------------
# Stub M4 — ABS / TKDL / traditional knowledge
# ---------------------------------------------------------------------------

_ABS_KEYWORDS = ("benefit sharing", "biodiversity", "biological diversity",
                 "biological resource", "nagoya", "nba", "plant collected",
                 "collected in india", "bio-piracy", "biopiracy")
_TK_KEYWORDS = ("traditional knowledge", "tkdl", "classical formulation",
                "classical ayurvedic", "authoritative text", "prior art")
_OTHER_IP_KEYWORDS = ("trademark", "trade mark", "copyright", "gi tag",
                      "geographical indication", "patent")


class StubAbsTkSpecialist:
    """Stands in for sihmember4.guidance.answer (8-field RAG Result with
    tkdl_pointer)."""

    domain = contracts.DOMAINS[1]  # ABS_TK

    def __init__(self, mode: str = "ok"):
        self.mode = mode

    def __call__(self, request: dict) -> dict:
        if self.mode == "unavailable":
            raise SpecialistUnavailable("stub M4 backend is unreachable")
        if self.mode == "processing_error":
            raise SpecialistProcessingError("stub M4 internal failure")
        if self.mode == "abstain":
            return _abstain("insufficient_evidence: stub forced abstention")

        query = request["query"].lower()

        if any(k in query for k in _OTHER_IP_KEYWORDS) and not any(
            k in query for k in _ABS_KEYWORDS
        ):
            # Mirror M4's out-of-scope protection: never answer other-IP
            # questions as ABS guidance.
            return _abstain(
                "unrelated: not classified as ABS/TK "
                "(other-IP signal with no ABS/TK signal)"
            )

        if any(k in query for k in _TK_KEYWORDS) and not any(
            k in query for k in _ABS_KEYWORDS
        ):
            # Mirror real M4's TK-only behavior: a TK/prior-art question gets
            # the safe TKDL pointer and abstains from substantive guidance
            # (their own suite: "tk patentability query gets safe pointer
            # and abstains").
            return _abstain(
                "insufficient_evidence: traditional-knowledge guidance is "
                "pointer-only in this corpus",
                tkdl_pointer=(
                    "Traditional Knowledge Digital Library (TKDL) — tkdl.res.in. "
                    "TKDL documents traditional-knowledge formulations for "
                    "patent-office prior-art search; full-text access is "
                    "restricted to patent offices under NDA. This is a pointer, "
                    "not TKDL content."
                ),
            )

        if any(k in query for k in _ABS_KEYWORDS):
            # Mirror real M4's documented rule: fee/cost questions always
            # abstain (the curated corpus contains no fee or amount figures,
            # so any number would be invented).
            if re.search(r"\bfee\b|\bcost\b|\bfees\b|charges|₹|\brupees\b", query):
                return _abstain(
                    "insufficient_evidence: the curated ABS/TK corpus contains "
                    "no fee, cost or amount figures for this question"
                )
            wants_pointer = any(k in query for k in _TK_KEYWORDS)
            pointer = (
                "Traditional Knowledge Digital Library (TKDL) — tkdl.res.in. "
                "TKDL documents traditional-knowledge formulations for "
                "patent-office prior-art search; full-text access is "
                "restricted to patent offices under NDA. This is a pointer, "
                "not TKDL content."
            ) if wants_pointer else None
            result = _rag_result(
                answer=(
                    "Commercialising a formulation that uses a biological "
                    "resource collected in India implicates the Biological "
                    "Diversity Act, 2002 (as amended in 2023): access to "
                    "biological resources for commercial utilisation is "
                    "regulated through the National Biodiversity Authority / "
                    "State Biodiversity Boards, with benefit-sharing "
                    "obligations. This is an ABS question, not a patents "
                    "question. " + _DISCLAIMER_EN
                ),
                citations=[
                    _citation(
                        "STUB-ABS-BDA",
                        "Biological Diversity Act, 2002 (as amended 2023)",
                        "statute",
                        "Access to biological resources for commercial utilisation",
                        URL_NBA,
                        "2024-04-01",
                    ),
                ],
                confidence="HIGH",
                confidence_score=0.88,
                abstention=False,
                abstention_reason=None,
                status="ok",
                tkdl_pointer=pointer,
            )
            if self.mode == "citation_failure":
                result["citations"][0]["excerpt"] = "Tampered excerpt not in any stored record."
            return result

        return _abstain(
            "insufficient_evidence: no curated ABS/TK source matches this query"
        )


# ---------------------------------------------------------------------------
# Stub M5 — International IP guidance
# ---------------------------------------------------------------------------


class StubInternationalSpecialist:
    """Stands in for sihmember5.member5.guide (7-field RAG Result).

    Encodes the PCT/Madrid/Hague mapping guardrail the real M5 enforces:
    patent → PCT; trademark → Madrid; design → Hague — never crossed.
    """

    domain = contracts.DOMAINS[2]  # INTERNATIONAL_IP

    def __init__(self, mode: str = "ok"):
        self.mode = mode

    def __call__(self, request: dict) -> dict:
        if self.mode == "unavailable":
            raise SpecialistUnavailable("stub M5 backend is unreachable")
        if self.mode == "processing_error":
            raise SpecialistProcessingError("stub M5 internal failure")
        if self.mode == "abstain":
            return _abstain("insufficient_evidence: stub forced abstention")

        query = request["query"].lower()

        if "trademark" in query or "trade mark" in query or "brand" in query:
            return _rag_result(
                answer=(
                    "The relevant international system for seeking trademark "
                    "protection for a brand in multiple jurisdictions is the "
                    "Madrid System (WIPO). It is not a patent filing system. "
                    + _DISCLAIMER_EN
                ),
                citations=[
                    _citation(
                        "STUB-INT-MADRID",
                        "Protocol Relating to the Madrid Agreement (Madrid Protocol)",
                        "treaty",
                        "International registration of marks",
                        URL_WIPO,
                        "2013-04-07",
                    ),
                ],
                confidence="HIGH",
                confidence_score=0.86,
                abstention=False,
                abstention_reason=None,
                status="ok",
            )

        if "patent" in query:
            return _rag_result(
                answer=(
                    "The relevant international filing route for seeking "
                    "patent protection for an invention in multiple countries "
                    "is the Patent Cooperation Treaty (PCT). The PCT does not "
                    "itself grant a worldwide patent; national Offices grant "
                    "patents during the national phase. " + _DISCLAIMER_EN
                ),
                citations=[
                    _citation(
                        "STUB-INT-PCT",
                        "Patent Cooperation Treaty (PCT)",
                        "treaty",
                        "International filing route",
                        URL_WIPO,
                        "1978-01-24",
                    ),
                ],
                confidence="HIGH",
                confidence_score=0.9,
                abstention=False,
                abstention_reason=None,
                status="ok",
            )

        return _abstain(
            "insufficient_evidence: no curated international source matches "
            "this query"
        )


# ---------------------------------------------------------------------------
# Stub M2 — formulation classifier
# ---------------------------------------------------------------------------


class StubClassifier:
    """Stands in for sihmember2.classify (ClassificationResult dict).

    Accepts the handle_classify payload {answers, jurisdiction, language} and
    applies a minimal deterministic slice of M2's documented decision rules —
    just enough to demonstrate the food-vs-medicine discrimination and the
    Uncertain/clarification path. Phase 2 replaces this with the real
    sihmember2.classify call.
    """

    domain = contracts.DOMAINS[3]  # CLASSIFICATION

    def __init__(self, mode: str = "ok"):
        self.mode = mode

    def __call__(self, payload: dict) -> dict:
        if self.mode == "unavailable":
            raise SpecialistUnavailable("stub M2 classifier is unreachable")
        if self.mode == "processing_error":
            raise SpecialistProcessingError("stub M2 internal failure")

        answers = payload.get("answers") or {}
        jurisdiction = payload.get("jurisdiction", "India")
        language = payload.get("language", "en")

        purpose = answers.get("primary_purpose")
        if purpose == "food_wellness" and answers.get("food_exclusion") == "none":
            category = "Ayurveda-Aahar"
            description = (
                "Food prepared according to recipes, ingredients or processes "
                "in authoritative Ayurveda texts, regulated by FSSAI."
            )
            regimes = [
                "FSSAI (Ayurveda Aahara) Regulations, 2022",
                "Food Safety and Standards Act, 2006",
            ]
        elif purpose == "therapeutic" and answers.get("text_source") == "yes":
            category = "Classical"
            description = (
                "Formulation and preparation method reproduced unchanged from "
                "a First-Schedule authoritative Ayurveda text."
            )
            regimes = [
                "Drugs and Cosmetics Act, 1940 (ASU drugs)",
                "Patents Act, 1970 — Section 3(p) exposure",
                "TKDL — defensive publication of traditional-knowledge formulations",
            ]
        elif purpose == "therapeutic" and answers.get("standardised_fraction") == "yes":
            category = "Phytopharmaceutical"
            description = (
                "Standardised plant-based fraction with defined active "
                "markers, regulated as a new drug by CDSCO."
            )
            regimes = [
                "Drugs and Cosmetics Act, 1940 (phytopharmaceutical new drug)",
                "CDSCO central approval",
            ]
        elif purpose == "external_cosmetic":
            category = "Cosmetic"
            description = "Applied externally for cleansing or beautification."
            regimes = ["Drugs and Cosmetics Act, 1940 (Cosmetic Rules)"]
        elif purpose == "therapeutic" and answers.get("text_source") == "no" \
                and answers.get("ingredients_known") == "yes":
            category = "Proprietary"
            description = (
                "New formulation of ingredients already established in "
                "Ayurvedic use, with no new therapeutic claim."
            )
            regimes = [
                "Drugs and Cosmetics Act, 1940 (proprietary ASU medicines)",
                "Patents Act, 1970 — patentability to be assessed",
            ]
        else:
            # Uncertain: incomplete or contradictory answers — ask, never guess.
            category = "Uncertain"
            description = (
                "The provided answers are insufficient to choose between the "
                "medicine, food and cosmetic regulatory tracks."
            )
            regimes = []
        tkdl_pointer = (
            "Traditional Knowledge Digital Library (TKDL) — tkdl.res.in. "
            "TKDL documents traditional-knowledge formulations for "
            "patent-office prior-art search; full-text access is restricted "
            "to patent offices under NDA."
        ) if category == "Classical" else None

        uncertain = category == "Uncertain"
        return {
            "formulation_class": category,
            "description": description,
            "relevant_regimes": regimes,
            "tkdl_pointer": tkdl_pointer,
            "confidence": "LOW" if uncertain else "HIGH",
            "confidence_score": 0.45 if uncertain else 0.95,
            "needs_clarification": uncertain,
            "clarification_prompt": (
                "Please answer the guided classification questions — in "
                "particular the product's primary intended use — so the "
                "formulation can be classified."
            ) if uncertain else None,
            "jurisdiction": jurisdiction,
            "language": language,
        }


# ---------------------------------------------------------------------------
# Stub router (stands in for M1's m1.routing.route)
# ---------------------------------------------------------------------------

# Stub router signals — mirror M1's m1/routing.py signal split (M6 Phase 4
# routing-intent fix): ABS-domain signals vs TK-awareness signals vs
# patentability intent. The stub keeps its own copy so the Phase 1 stub
# harness stays independent of member imports.
ABS_DOMAIN_SIGNALS = (
    "benefit sharing",
    "access and benefit",
    "biodiversity",
    "biological diversity",
    "biological resource",
    "nagoya",
    "nba ",
    "plant collected",
    "collected in india",
    "बायो विविधता",
)
TK_AWARENESS_SIGNALS = (
    "tkdl",
    "traditional knowledge",
    "पारंपरिक ज्ञान",
)
PATENT_INTENT_SIGNALS = (
    "patent",
    "inventive step",
    "invention",
    "पेटेंट",
    "पेटेन्ट",
)

# M1's classification-flow signals, unchanged.
CLASSIFICATION_SIGNALS = (
    "classify",
    "classification",
    "which category",
    "what category",
    "is my product",
    "food or cosmetic",
    "food or medicine",
    "classical or proprietary",
    "वर्गीकरण",
)

DOMAIN_LABELS = {
    "INDIA_IP": "India IP & regulatory (M3)",
    "ABS_TK": "ABS / traditional knowledge (M4)",
    "INTERNATIONAL_IP": "International IP (M5)",
    "CLASSIFICATION": "Formulation classification (M2)",
    "GENERAL": "general assistant",
}


def stub_route(request: dict):
    """Mirror M1's documented routing order: ABS/biological-resource signals
    win; TK-awareness routes ABS/TK only without patentability intent (a
    TK+patent question belongs to the India/International IP specialist);
    then classification signals; then the authoritative jurisdiction toggle.
    Returns (domain, rationale)."""
    q = request["query"].lower()
    if any(s in q for s in ABS_DOMAIN_SIGNALS):
        return "ABS_TK", "matched ABS/biological-resource signal"
    if any(s in q for s in TK_AWARENESS_SIGNALS) and not any(
        s in q for s in PATENT_INTENT_SIGNALS
    ):
        return "ABS_TK", "matched TK-awareness signal with no patentability intent"
    for signal in CLASSIFICATION_SIGNALS:
        if signal in q:
            return "CLASSIFICATION", f"matched classification signal {signal!r}"
    if request.get("jurisdiction") == "International":
        return "INTERNATIONAL_IP", "jurisdiction toggle set to International"
    return "INDIA_IP", "jurisdiction toggle set to India"


# ---------------------------------------------------------------------------
# Default stub specialist registry (what the harness tests wire in)
# ---------------------------------------------------------------------------

def default_stub_specialists(modes: dict | None = None) -> dict:
    """Return {domain: callable} covering the four specialist domains.
    ``modes`` optionally overrides the failure mode per domain key."""
    modes = modes or {}
    return {
        "INDIA_IP": StubIndiaSpecialist(modes.get("INDIA_IP", "ok")),
        "ABS_TK": StubAbsTkSpecialist(modes.get("ABS_TK", "ok")),
        "INTERNATIONAL_IP": StubInternationalSpecialist(modes.get("INTERNATIONAL_IP", "ok")),
        "CLASSIFICATION": StubClassifier(modes.get("CLASSIFICATION", "ok")),
    }
