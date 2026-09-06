"""Member 3 Phase 2 — deterministic confidence scoring.

Confidence is computed ONLY from evidence quality/relevance — never from the
LLM's own self-assessment (self-reported confidence is not evidence). The
score is a weighted sum of four explainable, deterministic components:

    relevance        best retrieval score of the cited evidence, saturated at
                     8 keyword points (weights: best_score / 8, capped at 1.0)
    corroboration    how many records the answer actually rests on:
                     (n_cited - 1) / 2, capped at 1.0
    source_quality   mean over cited records: 1.0 for excerpts the project
                     downloaded and extracted from the official document,
                     0.75 for mirror-verified ones
    scope_alignment  1.0 when the cited evidence contains a record from the
                     routed scope area, else 0.5

    confidence_score = 0.50*relevance + 0.20*corroboration
                     + 0.20*source_quality + 0.10*scope_alignment

Labels: HIGH >= 0.75, MEDIUM >= 0.50, LOW < 0.50. The guidance layer treats
a LOW score as insufficient evidence and abstains. Language never enters the
calculation, so English and Hindi runs of the same question score the same.
"""

from .sources import all_sources  # noqa: F401  (re-exported for convenience)

HIGH_THRESHOLD = 0.75
MEDIUM_THRESHOLD = 0.50

# Relevance saturation: with +2 per tag keyword, 4 distinct keyword hits is a
# strong match; scores at or above 8 points are all treated as fully relevant.
_RELEVANCE_SATURATION = 8.0

_WEIGHTS = {
    "relevance": 0.50,
    "corroboration": 0.20,
    "source_quality": 0.20,
    "scope_alignment": 0.10,
}

_MIRROR_QUALITY = 0.75
_DOWNLOAD_QUALITY = 1.0
_NO_SCOPE_ALIGNMENT = 0.5


def label_for_score(score):
    if score >= HIGH_THRESHOLD:
        return "HIGH"
    if score >= MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def compute_confidence(cited_records, routed_scope_area=None, best_score=0.0,
                       sources=None):
    """Compute (label, confidence_score, explanation) for a guidance result.

    cited_records: the corpus records actually cited by the answer.
    routed_scope_area: scope area from routing (for alignment).
    best_score: best retrieval score among the retrieved evidence (use the
                retrieved best even if the LLM cited a subset — relevance
                measures evidence strength, corroboration measures spread).
    """
    if not cited_records:
        return "LOW", 0.0, "no cited evidence"

    relevance = min(1.0, float(best_score) / _RELEVANCE_SATURATION)
    corroboration = min(1.0, (len(cited_records) - 1) / 2.0)
    qualities = [
        _DOWNLOAD_QUALITY
        if record.get("verification", {}).get("method") == "downloaded+extracted"
        else _MIRROR_QUALITY
        for record in cited_records
    ]
    source_quality = sum(qualities) / len(qualities)
    alignment = (
        1.0
        if routed_scope_area
        and any(r.get("scope_area") == routed_scope_area for r in cited_records)
        else _NO_SCOPE_ALIGNMENT
    )

    score = (
        _WEIGHTS["relevance"] * relevance
        + _WEIGHTS["corroboration"] * corroboration
        + _WEIGHTS["source_quality"] * source_quality
        + _WEIGHTS["scope_alignment"] * alignment
    )
    score = round(min(1.0, max(0.0, score)), 4)

    explanation = (
        "relevance=%.2f (best evidence score %s), corroboration=%.2f (%d "
        "record(s) cited), source_quality=%.2f (%s), scope_alignment=%.2f "
        "(%s); weights relevance 0.50, corroboration 0.20, source_quality "
        "0.20, scope_alignment 0.10"
        % (
            relevance,
            best_score,
            corroboration,
            len(cited_records),
            source_quality,
            "official download" if source_quality == 1.0 else "incl. mirror-verified",
            alignment,
            "cited evidence covers the routed scope" if alignment == 1.0 else "scope mismatch",
        )
    )
    return label_for_score(score), score, explanation
