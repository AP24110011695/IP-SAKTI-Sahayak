"""Retrieval and evidence-ranking tests: jurisdiction hard filter, ranking
order, Hindi keyword matching, and no-evidence behaviour."""
import pytest

from m1 import retrieval
from m1.corpus import load_corpus
from m1.models import QueryRequest

GOLDEN_2 = (
    "I want to file a patent for a new Ayurvedic drug outside India — "
    "what route do I use?"
)


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


def make_req(query, jurisdiction="India", language="en"):
    return QueryRequest(
        id="t", query=query, jurisdiction=jurisdiction, language=language
    )


def test_jurisdiction_hard_filter(corpus):
    for jur in ("India", "International"):
        req = make_req("patent", jurisdiction=jur)
        results = retrieval.retrieve(req, corpus)
        assert results, f"expected results for jurisdiction {jur}"
        assert all(s.evidence.jurisdiction == jur for s in results)


def test_pct_ranks_top_for_international_patent_route(corpus):
    req = make_req(GOLDEN_2, jurisdiction="International")
    results = retrieval.retrieve(req, corpus)
    assert results[0].evidence.id == "intl-pct"


def test_madrid_not_in_international_patent_answer_set(corpus):
    req = make_req(GOLDEN_2, jurisdiction="International")
    results = retrieval.keep_relevant(retrieval.retrieve(req, corpus))
    assert "intl-madrid" not in [s.evidence.id for s in results]


def test_madrid_ranks_top_for_trademark_query(corpus):
    req = make_req("register my brand internationally", jurisdiction="International")
    results = retrieval.retrieve(req, corpus)
    assert results, "trademark query should retrieve something"
    assert results[0].evidence.id == "intl-madrid"


def test_3p_retrieved_for_india_tk_patentability_query(corpus):
    req = make_req(
        "Can I patent a classical Ayurvedic formulation from an authoritative text?"
    )
    results = retrieval.retrieve(req, corpus)
    ids = [s.evidence.id for s in results]
    assert "in-patents-act-3p" in ids[:2]


def test_tkdl_pointer_retrieved_for_india_tk_query(corpus):
    req = make_req(
        "Can I patent a classical Ayurvedic formulation from an authoritative text?"
    )
    results = retrieval.keep_relevant(retrieval.retrieve(req, corpus))
    ids = [s.evidence.id for s in results]
    assert "in-tkdl-pointer" in ids
    assert "in-patents-act-3p" in ids


def test_hindi_keyword_match(corpus):
    req = make_req("पारंपरिक ज्ञान पर पेटेंट", language="hi")
    results = retrieval.retrieve(req, corpus)
    ids = [s.evidence.id for s in results]
    assert "in-patents-act-3p" in ids


def test_ranking_sorted_descending(corpus):
    req = make_req(
        "patent treaty exclusion plants", jurisdiction="International"
    )
    results = retrieval.retrieve(req, corpus)
    scores = [s.score for s in results]
    assert scores == sorted(scores, reverse=True)


def test_keep_relevant_always_keeps_top(corpus):
    req = make_req(GOLDEN_2, jurisdiction="International")
    retrieved = retrieval.retrieve(req, corpus)
    kept = retrieval.keep_relevant(retrieved)
    assert kept
    assert kept[0].evidence.id == retrieved[0].evidence.id


def test_out_of_corpus_query_returns_nothing(corpus):
    req = make_req("quantum chromodynamics strawberry spaceship")
    assert retrieval.retrieve(req, corpus) == []
