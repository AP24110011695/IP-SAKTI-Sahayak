"""Domain-routing decision for the central assistant (MEMBER_1.md §1, §3).

The assistant's flow is: intent/context → decide which specialised domain is
relevant → evidence retrieval → grounded answer. This module owns the
"decide which specialized domain is relevant" step as a clean, swappable seam:

- Phase 1 (standalone): `route()` classifies the query into a specialist
  domain with a simple, transparent keyword heuristic. No specialist is
  registered, so `assistant.handle_query` may answer from M1's own standalone
  corpus for independent dev/demo purposes.
- At integration: M6 registers the real specialists (M2 classification,
  M3 India, M4 ABS/TK, M5 International) via `register_specialist` and flips
  `Config.specialists_wired`. The corpus-safety rule then applies: a query
  routed to a specialist domain whose specialist is unavailable must abstain,
  never silently answer from M1's demo corpus.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class Domain(str, Enum):
    INDIA_IP = "INDIA_IP"
    ABS_TK = "ABS_TK"
    INTERNATIONAL_IP = "INTERNATIONAL_IP"
    CLASSIFICATION = "CLASSIFICATION"
    GENERAL = "GENERAL"


# Routing signals (M6 Phase 4, routing-intent fix). The original flat
# ABS_TK_SIGNALS list sent ANY query containing "traditional knowledge"/"tkdl"
# to the ABS/TK specialist even when the query's intent was patentability
# (e.g. "Can traditional knowledge documented in TKDL affect the
# patentability of my invention in India?"), which M3 — the India-IP
# specialist that owns the Section 3(p)/2(1)(j) analysis and carries the
# legitimate TKDL pointer — never saw. The lists are now split by intent:
#
#   ABS_DOMAIN_SIGNALS   genuine access-and-benefit-sharing / biological-
#                        resource matters (M4's documented domain; a query
#                        naming a biological resource AND a patent is a real
#                        ABS/IPR intersection and stays here — MEMBER_4.md);
#   TK_AWARENESS_SIGNALS traditional-knowledge/TKDL awareness — routes to M4
#                        ONLY when no patentability intent is present, so
#                        ordinary TK questions still reach M4;
#   PATENT_INTENT_SIGNALS patentability intent — with TK awareness present,
#                        the query falls through to the jurisdiction toggle:
#                        India → M3 (which answers with the TKDL pointer),
#                        International → M5 (WIPO GRATK disclosure route).
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

# Substrings that signal the formulation-classification flow (M2's area).
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
    Domain.INDIA_IP: "India IP & regulatory (M3)",
    Domain.ABS_TK: "ABS / traditional knowledge (M4)",
    Domain.INTERNATIONAL_IP: "International IP (M5)",
    Domain.CLASSIFICATION: "Formulation classification (M2)",
    Domain.GENERAL: "general assistant",
}


@dataclass
class RoutingDecision:
    domain: Domain
    specialist_registered: bool
    rationale: str


# Specialist registry: domain -> human-readable specialist identifier.
# Deliberately empty in Phase 1 — M2–M5 are not wired in yet. M6 fills this
# at integration.
_SPECIALISTS: Dict[Domain, str] = {}


def register_specialist(domain: Domain, name: str) -> None:
    """Integration seam (M6): register a real specialist capability for a
    domain. Not used during standalone development."""
    _SPECIALISTS[domain] = name


def registered_specialist(domain: Domain) -> Optional[str]:
    return _SPECIALISTS.get(domain)


def route(request) -> RoutingDecision:
    """Classify which specialised domain the query belongs to.

    Phase 1 heuristic (transparent and swappable), refined at integration for
    routing intent: genuine ABS/biological-resource signals win; TK-awareness
    (TKDL / traditional knowledge) routes to the ABS/TK specialist ONLY when
    the query carries no patentability intent — a TK+patentability question is
    an India-IP (or, internationally, GRATK) question that the India or
    International specialist answers with the legitimate TKDL pointer;
    classification signals come next; otherwise the explicit jurisdiction
    toggle from the QueryRequest decides India vs International. The
    jurisdiction toggle is authoritative — per the problem statement the two
    answer-sets are never conflated.
    """
    q = request.query.lower()
    has_abs_domain = any(signal in q for signal in ABS_DOMAIN_SIGNALS)
    has_tk_awareness = any(signal in q for signal in TK_AWARENESS_SIGNALS)
    has_patent_intent = any(signal in q for signal in PATENT_INTENT_SIGNALS)

    if has_abs_domain:
        return RoutingDecision(
            domain=Domain.ABS_TK,
            specialist_registered=Domain.ABS_TK in _SPECIALISTS,
            rationale="matched ABS/biological-resource signal",
        )
    if has_tk_awareness and not has_patent_intent:
        return RoutingDecision(
            domain=Domain.ABS_TK,
            specialist_registered=Domain.ABS_TK in _SPECIALISTS,
            rationale="matched TK-awareness signal with no patentability intent",
        )

    for signal in CLASSIFICATION_SIGNALS:
        if signal in q:
            return RoutingDecision(
                domain=Domain.CLASSIFICATION,
                specialist_registered=Domain.CLASSIFICATION in _SPECIALISTS,
                rationale=f"matched classification signal {signal!r}",
            )

    if request.jurisdiction == "International":
        return RoutingDecision(
            domain=Domain.INTERNATIONAL_IP,
            specialist_registered=Domain.INTERNATIONAL_IP in _SPECIALISTS,
            rationale="jurisdiction toggle set to International",
        )
    return RoutingDecision(
        domain=Domain.INDIA_IP,
        specialist_registered=Domain.INDIA_IP in _SPECIALISTS,
        rationale="jurisdiction toggle set to India",
    )
