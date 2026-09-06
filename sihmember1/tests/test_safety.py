"""Unit tests for the Phase 2 trust & safety layer (m1/safety.py):
sufficiency threshold, citation mapping, citation validation, confidence
scoring and response guards."""
import pytest

from m1.config import Config
from m1.corpus import load_corpus
from m1.models import Citation, QueryResponse
from m1.retrieval import ScoredEvidence
from m1.safety import (
    assert_response_safe,
    assess_sufficiency,
    confidence_from,
    map_citations,
    validate_citations,
)
from m1.corpus import Evidence


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


@pytest.fixture(scope="module")
def corpus_by_id(corpus):
    return {e.id: e for e in corpus}


def scored(top, count=1):
    """Synthetic scored-evidence list for confidence/sufficiency tests."""
    base = [
        ScoredEvidence(evidence=Evidence(
            id=f"syn-{i}", jurisdiction="India", source_name="s", source_type="t",
            section="s", title="t", text="x" * 50, url="https://ipindia.gov.in",
            effective_date=None,
        ), score=max(0.0, top - 0.5 * i))
        for i in range(count)
    ]
    return base


# --- evidence sufficiency -------------------------------------------------

def test_sufficiency_empty_is_insufficient():
    s = assess_sufficiency([], 2.5)
    assert not s.sufficient
    assert s.reason


def test_sufficiency_weak_evidence_abstains():
    s = assess_sufficiency(scored(1.5), 2.5)
    assert not s.sufficient
    assert "sufficiency threshold" in s.reason


def test_sufficiency_strong_evidence_passes():
    s = assess_sufficiency(scored(9.0, count=3), 2.5)
    assert s.sufficient
    assert s.reason is None


def test_sufficiency_boundary_is_inclusive():
    assert assess_sufficiency(scored(2.5), 2.5).sufficient
    assert not assess_sufficiency(scored(2.49), 2.5).sufficient


# --- citation mapping -------------------------------------------------------

def test_map_citations_all_tags(corpus):
    evidence = corpus[5:8]
    answer = "The PCT route applies [E1]; TRIPS flexibilities [E2]; and [E3]."
    citations = map_citations(answer, evidence)
    assert [c.id for c in citations] == [e.id for e in evidence]
    for c, ev in zip(citations, evidence):
        assert c.source_name == ev.source_name
        assert c.url == ev.url
        assert c.excerpt == ev.text
        assert c.section == ev.section
        assert c.effective_date == ev.effective_date


def test_map_citations_subset_only(corpus):
    evidence = corpus[5:8]
    answer = "Only the PCT matters here [E2]."
    citations = map_citations(answer, evidence)
    assert [c.id for c in citations] == [evidence[1].id]


def test_map_citations_ignores_out_of_range_tags(corpus):
    evidence = corpus[5:7]
    citations = map_citations("see [E1] and [E9]", evidence)
    assert [c.id for c in citations] == [evidence[0].id]


def test_map_citations_no_tags_maps_to_nothing(corpus):
    assert map_citations("groundless prose", corpus[:3]) == []


def test_map_citations_deduplicates_repeated_tags(corpus):
    evidence = corpus[5:6]
    citations = map_citations("[E1] ... [E1] ... [E1]", evidence)
    assert len(citations) == 1


# --- citation validation ----------------------------------------------------

def test_validate_citations_accepts_corpus_built_citations(corpus, corpus_by_id):
    citations = map_citations("[E1] [E2]", corpus[:2])
    assert validate_citations(citations, corpus_by_id) == []


def test_validate_citations_rejects_unknown_id(corpus_by_id):
    bad = Citation(
        id="made-up-id", source_name="Ghost Act", source_type="statute",
        section="s.99", excerpt="fabricated text", url="https://ipindia.gov.in",
        effective_date=None,
    )
    failures = validate_citations([bad], corpus_by_id)
    assert failures and "not present in the corpus" in failures[0]


def test_validate_citations_rejects_tampered_fields(corpus, corpus_by_id):
    ev = corpus[0]
    tampered = Citation(
        id=ev.id, source_name=ev.source_name, source_type=ev.source_type,
        section="Section 999(zz)",  # tampered
        excerpt=ev.text, url=ev.url, effective_date=ev.effective_date,
    )
    failures = validate_citations([tampered], corpus_by_id)
    assert failures and "section" in failures[0]

    tampered_url = Citation(
        id=ev.id, source_name=ev.source_name, source_type=ev.source_type,
        section=ev.section, excerpt=ev.text,
        url="https://totally-not-authoritative.example/act",  # tampered
        effective_date=ev.effective_date,
    )
    failures = validate_citations([tampered_url], corpus_by_id)
    assert failures and "url" in failures[0]

    tampered_excerpt = Citation(
        id=ev.id, source_name=ev.source_name, source_type=ev.source_type,
        section=ev.section, excerpt="invented quotation", url=ev.url,
        effective_date=ev.effective_date,
    )
    failures = validate_citations([tampered_excerpt], corpus_by_id)
    assert failures and "excerpt" in failures[0]


def test_validate_citations_rejects_non_https_url(corpus, corpus_by_id):
    ev = corpus[0]
    bad = Citation(
        id=ev.id, source_name=ev.source_name, source_type=ev.source_type,
        section=ev.section, excerpt=ev.text, url="http://ipindia.gov.in/x",
        effective_date=ev.effective_date,
    )
    failures = validate_citations([bad], corpus_by_id)
    assert failures and "authoritative" in " ".join(failures)


# --- confidence scoring -------------------------------------------------------

def test_confidence_empty_is_low_zero():
    assert confidence_from([]) == ("LOW", 0.0)


def test_confidence_strong_evidence_is_high():
    label, score = confidence_from(scored(9.0, count=3))
    assert label == "HIGH"
    assert score == 1.0


def test_confidence_moderate_evidence_is_medium():
    label, score = confidence_from(scored(3.0, count=1))
    assert label == "MEDIUM"
    assert 0.25 <= score < 0.5


def test_confidence_weak_evidence_is_low():
    label, score = confidence_from(scored(1.0, count=1))
    assert label == "LOW"
    assert score < 0.25


def test_confidence_varies_monotonically_with_evidence_strength():
    strong = confidence_from(scored(12.0, count=3))
    medium = confidence_from(scored(3.5, count=1))
    weak = confidence_from(scored(2.6, count=1))
    assert strong[1] > medium[1] > weak[1]
    assert strong[0] == "HIGH"
    assert medium[0] == "MEDIUM"
    assert weak[0] in ("MEDIUM", "LOW")


def test_confidence_corroboration_lifts_score():
    solo = confidence_from(scored(5.0, count=1))
    corroborated = confidence_from(scored(5.0, count=3))
    assert corroborated[1] > solo[1]


# --- response guards ----------------------------------------------------------

def ok_response(**overrides):
    data = dict(
        id="r-1",
        answer="grounded answer [E1]",
        citations=[Citation(
            id="in-patents-act-3p", source_name="s", source_type="statute",
            section="s.3(p)", excerpt="e", url="https://ipindia.gov.in",
            effective_date=None,
        )],
        confidence="HIGH",
        confidence_score=0.8,
        abstention=False,
        abstention_reason=None,
        escalation_available=False,
        disclaimer="Disclaimer: information, not legal advice.",
    )
    data.update(overrides)
    return QueryResponse(**data)


def abstained_response(**overrides):
    data = dict(
        id="r-2",
        answer="safe fallback text",
        citations=[],
        confidence="LOW",
        confidence_score=0.0,
        abstention=True,
        abstention_reason="no relevant evidence in the standalone corpus",
        escalation_available=False,
        disclaimer="Disclaimer: information, not legal advice.",
    )
    data.update(overrides)
    return QueryResponse(**data)


def test_guard_accepts_well_formed_responses():
    assert_response_safe(ok_response())
    assert_response_safe(abstained_response())


def test_guard_requires_disclaimer_on_every_response():
    with pytest.raises(ValueError, match="disclaimer"):
        assert_response_safe(ok_response(disclaimer=""))
    with pytest.raises(ValueError, match="disclaimer"):
        assert_response_safe(abstained_response(disclaimer="  "))


def test_guard_requires_reason_on_abstention():
    with pytest.raises(ValueError, match="abstention_reason"):
        assert_response_safe(abstained_response(abstention_reason=None))


def test_guard_forbids_citations_on_abstention():
    with pytest.raises(ValueError, match="citations"):
        assert_response_safe(abstained_response(citations=ok_response().citations))


def test_guard_forbids_reason_on_non_abstention():
    with pytest.raises(ValueError, match="null abstention_reason"):
        assert_response_safe(ok_response(abstention_reason="why is this here"))


def test_guard_requires_answer_on_non_abstention():
    with pytest.raises(ValueError, match="answer"):
        assert_response_safe(ok_response(answer="  "))
