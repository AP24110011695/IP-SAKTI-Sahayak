"""Standalone, source-grounded international IP guidance for Member 5."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .corpus import SYSTEM_RIGHTS, load_sources
from .llm import GenerationClient, GenerationError, default_generation_client


CITATION_FIELDS = (
    "id",
    "source_name",
    "source_type",
    "section",
    "excerpt",
    "url",
    "effective_date",
)
CITATION_FIELD_SET = set(CITATION_FIELDS)
DISCLAIMER = {
    "en": "This is general information, not legal advice. Verify current requirements with the relevant official authority or a qualified professional.",
    "hi": "यह केवल सामान्य जानकारी है, कानूनी सलाह नहीं। वर्तमान आवश्यकताओं की पुष्टि संबंधित आधिकारिक प्राधिकरण या योग्य विशेषज्ञ से करें।",
}

RIGHT_MARKERS = {
    "patent": ("patent", "patents", "invention", "inventions", "पेटेंट", "आविष्कार"),
    "trademark": ("trademark", "trademarks", "brand", "brands", "logo", "trade mark", "ट्रेडमार्क", "ब्रांड", "चिह्न"),
    "industrial_design": ("design", "designs", "industrial design", "packaging design", "ornamental design", "डिज़ाइन", "डिजाइन", "पैकेजिंग"),
}
SYSTEM_MARKERS = {
    "PCT": ("pct", "पीसीटी"),
    "Madrid": ("madrid", "मैड्रिड"),
    "Hague": ("hague", "हेग"),
}
REGION_MARKERS = {
    "United States": ("united states", "usa", "u.s.", "america", "अमेरिका"),
    "European Union": ("european union", " eu ", "यूरोपीय संघ"),
    "United Kingdom": ("united kingdom", " uk ", "britain", "ब्रिटेन"),
    "ASEAN": ("asean", "आसियान"),
    "Middle East": ("middle east", "मध्य पूर्व"),
    "Brazil": ("brazil", "ब्राज़ील", "ब्राजील"),
    "Japan": ("japan", "जापान"),
    "China": ("china", "चीन"),
    "Canada": ("canada", "कनाडा"),
    "Australia": ("australia", "ऑस्ट्रेलिया"),
    "United Arab Emirates": ("united arab emirates", "uae", "यूएई"),
    "Saudi Arabia": ("saudi arabia", "सऊदी अरब"),
}
TRIPS_CONTEXT = (
    "agreement",
    "article",
    "treaty",
    "wto",
    "patentability",
    "plant",
    "plants",
    "variety",
    "varieties",
    "sui generis",
)


@dataclass(frozen=True)
class RouteDecision:
    supported: bool
    intent: str | None
    ip_right: str | None
    system: str | None
    evidence_ids: tuple[str, ...]
    region: str | None
    reason: str | None
    specificity: float


def _contains(text: str, markers: tuple[str, ...] | list[str]) -> bool:
    return any(marker in text for marker in markers)


def _detected_rights(text: str) -> list[str]:
    return [right for right, markers in RIGHT_MARKERS.items() if _contains(text, markers)]


def _detected_systems(text: str) -> list[str]:
    return [system for system, markers in SYSTEM_MARKERS.items() if _contains(text, markers)]


def _detect_region(text: str) -> str | None:
    padded = f" {text} "
    for region, markers in REGION_MARKERS.items():
        if _contains(padded, markers):
            return region
    return None


def _mentions_trips_treaty(raw_query: str, text: str) -> bool:
    """Match treaty TRIPS without firing on the ordinary travel word "trips"."""

    if not re.search(r"\btrips\b", text):
        return False
    if "TRIPS" in raw_query:
        return True
    return _contains(text, TRIPS_CONTEXT)


def route_query(query: str, jurisdiction: str | None = "International") -> RouteDecision:
    text = " ".join(query.casefold().split())
    region = _detect_region(text)
    if not text:
        return RouteDecision(False, None, None, None, (), region, "The query is empty.", 0.0)

    if jurisdiction is None:
        if _contains(text, ["international", "internationally", "outside india", "abroad", "विदेश", "अंतरराष्ट्रीय", "भारत के बाहर"]):
            jurisdiction = "International"
        else:
            return RouteDecision(False, None, None, None, (), region, "Jurisdiction is ambiguous; select International for Member 5 guidance.", 0.0)
    if jurisdiction.casefold() != "international":
        return RouteDecision(False, None, None, None, (), region, "Member 5 handles International jurisdiction only.", 0.0)

    # Fee/cost questions must abstain (integration finding F-09; the same rule
    # Member 4 enforces): the curated corpus contains no fee, cost or amount
    # figures, so a fee question would otherwise receive generic route
    # guidance that does not actually answer it. Word-boundary matching so
    # "feeling"/"coffee" do not false-positive (Phase 3 fix).
    if re.search(r"\b(?:fee|fees|cost|costs|price|pricing|charge|charges)\b|शुल्क|फीस|कीमत", text):
        return RouteDecision(False, None, None, None, (), region, "The verified international corpus contains no fee, cost or amount figures for this question.", 0.0)

    # Term/duration questions must abstain (Phase 3, watch item on F-09): the
    # corpus holds no term, expiry or renewal information, and the mapping
    # guardrail forbids durations in answers — so such questions could only
    # ever receive evasive generic guidance.
    if _contains(
        text,
        ["expire", "expires", "expiry", "expiration", "renew", "renewal", "renewing", "how long is", "how long does"],
    ):
        return RouteDecision(False, None, None, None, (), region, "The verified international corpus contains no term, expiry or renewal information for this question.", 0.0)

    outside_india = _contains(text, ["outside india", "भारत के बाहर", "भारत से बाहर"])
    india_only = _contains(
        text,
        ["under indian law", "in india", "india-only", "india patent office", "ip india", "indian patents act", "भारत में", "भारतीय कानून", "आईपी इंडिया"],
    )
    if india_only and not outside_india:
        return RouteDecision(False, None, None, None, (), region, "The query asks for India-specific procedure, which is outside Member 5's international scope.", 0.0)

    market_access = _contains(
        text,
        ["market access", "export", "sell", "label", "labelling", "labeling", "fda", "novel food", "dietary supplement", "निर्यात", "बेचना", "लेबल"],
    )
    if market_access:
        detail = f" for {region}" if region else ""
        return RouteDecision(False, None, None, None, (), region, f"Country/region-specific market-access requirements{detail} are not in the verified corpus.", 0.0)

    domestic_law = _contains(
        text,
        ["local law", "patent law", "trademark law", "design law", "procedure", "court", "national office", "घरेलू कानून", "प्रक्रिया"],
    )
    if region and domestic_law:
        return RouteDecision(False, None, None, None, (), region, f"Domestic {region} law is not in the verified international corpus.", 0.0)

    rights = _detected_rights(text)
    systems = _detected_systems(text)
    if len(rights) > 1:
        return RouteDecision(False, None, None, None, (), region, "The query combines multiple IP rights; ask about one right at a time for this standalone module.", 0.25)
    right = rights[0] if rights else None

    if systems:
        if len(systems) > 1:
            return RouteDecision(False, None, right, None, (), region, "Multiple international filing systems were named ambiguously.", 0.0)
        system = systems[0]
        expected_right = SYSTEM_RIGHTS[system]
        if right and right != expected_right:
            return RouteDecision(False, None, right, system, (), region, f"Unsafe mapping detected: {system} does not govern {right} rights.", 0.0)
        right = expected_right
        ids = {
            "PCT": ("pct-system-overview", "pct-national-phase"),
            "Madrid": ("madrid-system-overview",),
            "Hague": ("hague-system-overview",),
        }[system]
        return RouteDecision(True, f"{system.lower()}_route", right, system, ids, region, None, 1.0)

    if len(re.findall(r"\w+", text, flags=re.UNICODE)) < 2:
        return RouteDecision(False, None, right, None, (), region, "The query is too weak to select reliable evidence.", 0.2)

    # Route-intent gate (Phase 3, watch item on F-09): the plain
    # right→system routes (PCT/Madrid/Hague) are only meaningful for queries
    # that are actually about filing/registering/protecting internationally.
    # A query that merely contains the word "patent" with no filing intent
    # and no international-scope marker would otherwise receive generic route
    # guidance that does not answer it. Queries that name a system explicitly,
    # or match the GRATK/TRIPS/Nagoya/CBD evidence, are unaffected.
    route_intent = (
        _contains(
            text,
            ["file", "filing", "register", "registration", "route", "protect", "protection", "seek"],
        )
        or _contains(
            text,
            ["internationally", "international", "abroad", "foreign", "outside india", "विदेश", "अंतरराष्ट्रीय", "भारत के बाहर"],
        )
        or region is not None
    )

    if right == "trademark" and route_intent:
        return RouteDecision(True, "madrid_route", right, "Madrid", ("madrid-system-overview",), region, None, 0.95)
    if right == "industrial_design" and route_intent:
        return RouteDecision(True, "hague_route", right, "Hague", ("hague-system-overview",), region, None, 0.95)
    if right == "patent":
        if _contains(text, ["genetic resource", "genetic resources", "traditional knowledge", "आनुवंशिक संसाधन", "पारंपरिक ज्ञान", "gratk"]):
            return RouteDecision(True, "gratk_disclosure", right, None, ("gratk-art-3-1", "gratk-art-3-2"), region, None, 0.9)
        if _mentions_trips_treaty(query, text) or _contains(text, ["27.3", "plant patentability", "पौधे की पेटेंट"]):
            return RouteDecision(True, "trips_patentability", right, None, ("trips-art-27-3-b",), region, None, 0.9)
        if route_intent:
            return RouteDecision(True, "pct_route", right, "PCT", ("pct-system-overview", "pct-national-phase"), region, None, 0.95)

    if _contains(text, ["gratk", "genetic resource disclosure", "traditional knowledge disclosure"]):
        return RouteDecision(True, "gratk_disclosure", "patent", None, ("gratk-art-3-1", "gratk-art-3-2", "gratk-art-17"), region, None, 0.9)
    if _mentions_trips_treaty(query, text) or _contains(text, ["27.3"]):
        return RouteDecision(True, "trips_patentability", "patent", None, ("trips-art-27-3-b",), region, None, 0.9)
    if _contains(text, ["nagoya", "benefit sharing", "benefit-sharing", "लाभ साझा", "लाभ-साझाकरण"]):
        return RouteDecision(True, "nagoya_benefit_sharing", "other", None, ("nagoya-art-5-1",), region, None, 0.85)
    if _contains(text, ["biodiversity", "genetic resources", "prior informed consent", "जैव विविधता", "आनुवंशिक संसाधन", "पूर्व सूचित सहमति"]):
        return RouteDecision(True, "cbd_nagoya_access", "other", None, ("cbd-art-15-1", "cbd-art-15-5", "nagoya-art-6-1"), region, None, 0.82)

    return RouteDecision(False, None, None, None, (), region, "No sufficiently relevant evidence exists in the curated international corpus.", 0.0)


def select_evidence(decision: RouteDecision) -> list[dict[str, Any]]:
    by_id = {source["id"]: source for source in load_sources()}
    return [by_id[source_id] for source_id in decision.evidence_ids if source_id in by_id]


def citation_from_source(source: dict[str, Any]) -> dict[str, Any]:
    return {field: source[field] for field in CITATION_FIELDS}


def validate_citations(citations: Any) -> bool:
    if not isinstance(citations, list) or not citations:
        return False
    source_index = {source["id"]: source for source in load_sources()}
    for citation in citations:
        if not isinstance(citation, dict) or set(citation) != CITATION_FIELD_SET:
            return False
        source = source_index.get(citation.get("id"))
        if source is None:
            return False
        if any(citation[field] != source[field] for field in CITATION_FIELDS):
            return False
    return True


def confidence_for(decision: RouteDecision, evidence: list[dict[str, Any]]) -> tuple[str, float]:
    if not decision.supported or not evidence:
        score = min(0.35, decision.specificity)
    else:
        authoritative = all(item["verification"]["status"] == "verified" for item in evidence)
        completeness = len(evidence) == len(decision.evidence_ids)
        score = 0.55 + (0.25 * decision.specificity) + (0.1 if authoritative else 0.0) + (0.05 if completeness else 0.0)
        score = min(score, 0.95)
    score = round(score, 2)
    label = "HIGH" if score >= 0.85 else "MEDIUM" if score >= 0.65 else "LOW"
    return label, score


def _abstained(reason: str, *, score: float = 0.0, status: str = "abstained") -> dict[str, Any]:
    return {
        "answer": "",
        "citations": [],
        "confidence": "LOW",
        "confidence_score": round(score, 2),
        "abstention": True,
        "abstention_reason": reason,
        "status": status,
    }


def _valid_generation(output: Any, selected_ids: set[str]) -> bool:
    if not isinstance(output, dict) or set(output) != {"answer", "citation_ids"}:
        return False
    if not isinstance(output["answer"], str) or not output["answer"].strip():
        return False
    ids = output["citation_ids"]
    if not isinstance(ids, list) or not ids or not all(isinstance(item, str) for item in ids):
        return False
    return len(ids) == len(set(ids)) and set(ids).issubset(selected_ids)


def _mapping_guardrail(answer: str, decision: RouteDecision, citations: list[dict[str, Any]]) -> bool:
    text = answer.casefold()
    mentioned = _detected_systems(text)
    for system in mentioned:
        expected_right = SYSTEM_RIGHTS[system]
        if decision.ip_right != expected_right:
            return False
    for citation in citations:
        source = next(item for item in load_sources() if item["id"] == citation["id"])
        if source["system"] in SYSTEM_RIGHTS and decision.ip_right != source["ip_right"]:
            return False
    urls = re.findall(r"https?://\S+", answer)
    if any(url.rstrip(".,)") not in {item["url"] for item in citations} for url in urls):
        return False
    if re.search(r"(?:[$€£₹]|\b\d+\s*(?:days?|months?|years?)\b)", text):
        return False
    sections = [str(citation["section"]).casefold() for citation in citations]
    for match in re.finditer(r"\barticles?\s+\d[\w().]*", text):
        reference = re.sub(r"^articles\b", "article", match.group(0))
        if not any(reference in section for section in sections):
            return False
    return True


def guide(
    query: str,
    *,
    language: str = "en",
    jurisdiction: str | None = "International",
    client: GenerationClient | None = None,
) -> dict[str, Any]:
    """Return a standalone RAG Result for a supported international query."""

    if language not in DISCLAIMER:
        return _abstained("Supported languages are 'en' and 'hi'.")

    decision = route_query(query, jurisdiction)
    evidence = select_evidence(decision) if decision.supported else []
    confidence, score = confidence_for(decision, evidence)
    if not decision.supported or not evidence or score < 0.65:
        return _abstained(decision.reason or "Evidence is insufficient.", score=score)

    generation_client = client or default_generation_client()
    try:
        output = generation_client.generate(
            query=query,
            evidence=evidence,
            language=language,
            region=decision.region,
        )
    except GenerationError as error:
        return _abstained(str(error), score=0.0, status="processing_error")
    except Exception:
        return _abstained("The generation provider failed safely.", score=0.0, status="processing_error")

    selected_ids = {item["id"] for item in evidence}
    if not _valid_generation(output, selected_ids):
        return _abstained("The model returned malformed or unsupported output.")

    source_index = {item["id"]: item for item in evidence}
    citations = [citation_from_source(source_index[source_id]) for source_id in output["citation_ids"]]
    if not validate_citations(citations):
        return _abstained("Citation validation failed.")
    if not _mapping_guardrail(output["answer"], decision, citations):
        return _abstained("The generated answer failed the IP-right/system safety guardrail.")

    return {
        "answer": f"{output['answer'].strip()}\n\n{DISCLAIMER[language]}",
        "citations": citations,
        "confidence": confidence,
        "confidence_score": score,
        "abstention": False,
        "abstention_reason": None,
        "status": "ok",
    }
