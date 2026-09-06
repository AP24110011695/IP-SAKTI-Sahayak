"""Trust & safety layer for M1 (Phase 2, MEMBER_1.md "Phase 2 — Trust and
Safety"). Implements, for this workstream, the common safety rules of
Plan.md §9 / MEMBER_1.md §5:

- evidence-sufficiency threshold (assess_sufficiency): below it → abstain,
  not guess;
- citation mapping (map_citations): an answer earns citations only through
  [E#] tags that resolve to stored evidence — citation metadata is copied
  from stored corpus entries and can never be invented;
- citation validation (validate_citations): every served citation is
  re-checked field-by-field against the stored corpus entry and its URL
  against the authoritative-domain allow-list;
- confidence scoring (confidence_from): HIGH/MEDIUM/LOW + numeric score that
  varies with evidence strength;
- response guards (assert_response_safe): the disclaimer is standing on every
  response and abstention reasons are always set.

Citation granularity is the evidence excerpt: each answer block is tied to a
whole stored excerpt via its [E#] tag (claim-level mapping is beyond MVP scope).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .corpus import Evidence, ALLOWED_SOURCE_DOMAINS
from .models import Citation, QueryResponse
from .retrieval import ScoredEvidence
from urllib.parse import urlparse

_TAG_RE = re.compile(r"\[E(\d+)\]")


@dataclass
class Sufficiency:
    sufficient: bool
    reason: Optional[str]


def assess_sufficiency(
    scored: Sequence[ScoredEvidence], sufficiency_threshold: float
) -> Sufficiency:
    """Evidence-sufficiency gate: answer only when the top ranked evidence is
    strong enough; otherwise abstain rather than guess."""
    if not scored:
        return Sufficiency(
            sufficient=False,
            reason="no relevant evidence in the standalone corpus",
        )
    top = scored[0].score
    if top < sufficiency_threshold:
        return Sufficiency(
            sufficient=False,
            reason=(
                f"retrieved evidence is below the sufficiency threshold "
                f"(top score {top} < {sufficiency_threshold}); abstaining "
                f"rather than guessing"
            ),
        )
    return Sufficiency(sufficient=True, reason=None)


def map_citations(answer_text: str, evidence: Sequence[Evidence]) -> List[Citation]:
    """Map the [E1..En] tags in an answer to stored evidence.

    Only evidence actually referenced by a tag becomes a citation, and every
    citation field is copied verbatim from the stored evidence entry — the
    generator cannot inject citation metadata. Answers with no resolvable
    tags map to zero citations (the caller must then withhold the answer).
    """
    refs = sorted({int(m) for m in _TAG_RE.findall(answer_text)})
    citations: List[Citation] = []
    for ref in refs:
        if 1 <= ref <= len(evidence):
            ev = evidence[ref - 1]
            citations.append(
                Citation(
                    id=ev.id,
                    source_name=ev.source_name,
                    source_type=ev.source_type,
                    section=ev.section,
                    excerpt=ev.text,
                    url=ev.url,
                    effective_date=ev.effective_date,
                )
            )
    return citations


def validate_citations(
    citations: Sequence[Citation], corpus_by_id: Dict[str, Evidence]
) -> List[str]:
    """Re-check every citation field against the stored corpus entry.

    Returns a list of failure descriptions (empty = all valid). A citation is
    valid only when its id exists in the corpus and its source_name, section,
    excerpt, url and effective_date equal the stored values, and its URL is an
    https URL on an authoritative domain.
    """
    failures: List[str] = []
    for c in citations:
        src = corpus_by_id.get(c.id)
        if src is None:
            failures.append(f"{c.id}: not present in the corpus")
            continue
        if c.source_name != src.source_name:
            failures.append(f"{c.id}: source_name does not match stored metadata")
        if c.section != src.section:
            failures.append(f"{c.id}: section does not match stored metadata")
        if c.excerpt != src.text:
            failures.append(f"{c.id}: excerpt does not match stored metadata")
        if c.url != src.url:
            failures.append(f"{c.id}: url does not match stored metadata")
        if c.effective_date != src.effective_date:
            failures.append(f"{c.id}: effective_date does not match stored metadata")
        if c.url:
            host = urlparse(c.url).netloc.lower()
            allowed = any(
                host == d or host.endswith("." + d) for d in ALLOWED_SOURCE_DOMAINS
            )
            if not c.url.startswith("https://") or not allowed:
                failures.append(f"{c.id}: url is not an authoritative https URL")
    return failures


def confidence_from(scored: Sequence[ScoredEvidence]) -> Tuple[str, float]:
    """Confidence scoring (HIGH/MEDIUM/LOW + 0.0–1.0).

    Combines the strength of the top evidence with corroboration from
    additional supporting pieces. Answered queries land in HIGH or MEDIUM;
    LOW (with score 0.0) is reserved for abstentions, where nothing was
    confidently established.
    """
    if not scored:
        return "LOW", 0.0
    top = scored[0].score
    base = min(1.0, top / 10.0)
    corroboration = min(2, max(0, len(scored) - 1)) * 0.1
    score = round(min(1.0, base + corroboration), 2)
    label = "HIGH" if score >= 0.5 else "MEDIUM" if score >= 0.25 else "LOW"
    return label, score


def assert_response_safe(response: QueryResponse) -> None:
    """Final contract guards applied to every response before it is served.

    Raises ValueError on violation — the caller converts this into a
    processing error rather than serving an unsafe response.
    """
    if not response.disclaimer or not response.disclaimer.strip():
        raise ValueError("every response must carry the information-not-legal-advice disclaimer")
    if response.abstention:
        if not response.abstention_reason or not response.abstention_reason.strip():
            raise ValueError("abstention must always carry an abstention_reason")
        if response.citations:
            raise ValueError("abstention responses must not carry citations")
    else:
        if response.abstention_reason is not None:
            raise ValueError("non-abstention responses must have a null abstention_reason")
        if not response.answer or not response.answer.strip():
            raise ValueError("non-abstention responses must carry an answer")
