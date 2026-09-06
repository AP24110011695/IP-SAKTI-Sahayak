"""End-to-end assistant tests — Phase 1 pipeline scenarios plus the required
Phase 2 tests:

1. a query with strong evidence returns HIGH/MEDIUM confidence and valid
   citations;
2. a query with no matching evidence abstains cleanly (HTTP 200, abstention:
   true — asserted at API level too);
3. a Hindi query for a supported scenario returns a Hindi answer.

Plus: sufficiency-threshold abstention, confidence variation, citation
validation end-to-end, and abstention when the configured LLM fails.
"""
import pytest

from m1.assistant import handle_query
from m1.config import Config
from m1.corpus import load_corpus
from m1.models import QueryRequest
from m1.safety import validate_citations

GOLDEN_1 = (
    "Can I patent a classical Ayurvedic formulation from an authoritative text?"
)
GOLDEN_2 = (
    "I want to file a patent for a new Ayurvedic drug outside India — "
    "what route do I use?"
)
FILING_QUERY = "How do I file a patent application for my Ayurvedic product?"
ABS_QUERY = (
    "I want to commercialise a formulation using traditional knowledge and a "
    "biological resource — what benefit sharing applies?"
)
HINDI_TK_QUERY = "पारंपरिक ज्ञान पर पेटेंट कर सकते हैं क्या?"


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


@pytest.fixture(scope="module")
def corpus_by_id(corpus):
    return {e.id: e for e in corpus}


def make_req(**overrides):
    data = dict(id="a-1", query=GOLDEN_1, jurisdiction="India", language="en")
    data.update(overrides)
    return QueryRequest(**data)


def cfg():
    return Config()  # hermetic: extractive generator, specialists not wired


# --- required Phase 2 test 1 -------------------------------------------------

def test_strong_evidence_returns_high_or_medium_with_valid_citations(corpus, corpus_by_id):
    result = handle_query(make_req(), cfg())
    assert result.status == "ok"
    r = result.response
    assert not r.abstention
    assert r.answer.strip()
    assert r.confidence in ("HIGH", "MEDIUM"), r.confidence
    assert 0.25 <= r.confidence_score <= 1.0
    assert r.citations
    assert validate_citations(r.citations, corpus_by_id) == []
    assert r.disclaimer.strip()


# --- required Phase 2 test 2 (HTTP 200 behaviour asserted at API level) ------

def test_no_matching_evidence_abstains_cleanly(corpus_by_id):
    r = handle_query(
        make_req(id="a-2", query="What is the airspeed of an unladen swallow?"), cfg()
    ).response
    assert r.abstention is True
    assert r.abstention_reason
    assert r.citations == []
    assert r.confidence == "LOW"
    assert r.confidence_score == 0.0
    assert r.answer.strip(), "safe fallback text, never a guess"


# --- required Phase 2 test 3 ---------------------------------------------------

def test_hindi_supported_scenario_returns_hindi_answer(corpus, corpus_by_id):
    result = handle_query(
        make_req(id="a-5", query=HINDI_TK_QUERY, language="hi"), cfg()
    )
    assert result.status == "ok"
    r = result.response
    assert not r.abstention
    assert r.answer.strip()
    # The supported scenario (traditional knowledge / s.3(p)) is answered from
    # entries that carry Hindi renderings → the answer is genuinely Hindi.
    assert "कानूनी सलाह नहीं" in r.answer
    assert corpus_by_id["in-patents-act-3p"].text_hi in r.answer
    assert "अंग्रेज़ी" not in r.answer  # no "some text is English" note needed
    assert "कानूनी सलाह" in r.disclaimer
    cited = {c.id for c in r.citations}
    assert "in-patents-act-3p" in cited


# --- evidence sufficiency threshold -------------------------------------------

def test_weak_evidence_abstains_via_sufficiency_threshold():
    """'act' matches corpus text weakly (above the retrieval floor but below
    the sufficiency threshold) → abstain, not a guess."""
    r = handle_query(make_req(id="a-6", query="act"), cfg()).response
    assert r.abstention is True
    assert "sufficiency threshold" in r.abstention_reason
    assert r.citations == []
    assert r.confidence == "LOW"


def test_no_evidence_at_all_abstains():
    r = handle_query(
        make_req(id="a-7", query="quantum chromodynamics strawberry spaceship"), cfg()
    ).response
    assert r.abstention is True
    assert r.abstention_reason == "no relevant evidence in the standalone corpus"


# --- confidence varies sensibly with evidence strength --------------------------

def test_confidence_varies_with_evidence_strength():
    strong = handle_query(make_req(), cfg()).response
    weaker = handle_query(make_req(id="a-8", query="tkdl"), cfg()).response
    assert strong.confidence == "HIGH"
    assert weaker.confidence in ("MEDIUM", "HIGH")
    assert weaker.confidence_score < strong.confidence_score
    assert strong.confidence_score > weaker.confidence_score >= 0.25


# --- citations map to real evidence, URLs from stored metadata -------------------

def test_citations_map_to_real_stored_evidence(corpus, corpus_by_id):
    r = handle_query(make_req(), cfg()).response
    assert r.citations
    for c in r.citations:
        src = corpus_by_id[c.id]
        assert c.source_name == src.source_name
        assert c.source_type == src.source_type
        assert c.section == src.section
        assert c.excerpt == src.text
        assert c.url == src.url
        assert c.effective_date == src.effective_date


def test_answer_is_grounded_in_cited_evidence():
    """Every served citation is referenced in the answer and its excerpt is
    quoted there (extractive mode is grounded by construction)."""
    r = handle_query(make_req(), cfg()).response
    for i, c in enumerate(r.citations, start=1):
        assert f"[E{i}]" in r.answer
        assert c.excerpt in r.answer


# --- configured-LLM failure → abstain (no silent fallback, no fabrication) ------

def test_llm_failure_abstains_at_assistant_level():
    cfg_llm_dead = Config(
        llm_api_key="k",
        llm_base_url="http://127.0.0.1:1",  # closed port → immediate refusal
        llm_timeout_secs=2,
    )
    result = handle_query(make_req(id="a-9"), cfg_llm_dead)
    assert result.status == "abstained"
    r = result.response
    assert r.abstention is True
    assert r.abstention_reason
    assert r.citations == []


# --- standing disclaimer on every response ---------------------------------------

def test_disclaimer_stands_on_every_response_shape():
    ok = handle_query(make_req(), cfg()).response
    abstained = handle_query(make_req(id="a-10", query="zzz qqq xyzzy"), cfg()).response
    hindi = handle_query(make_req(id="a-11", query=HINDI_TK_QUERY, language="hi"), cfg()).response
    assert "not legal advice" in ok.disclaimer
    assert "not legal advice" in abstained.disclaimer
    assert "कानूनी सलाह नहीं" in hindi.disclaimer


# --- contract shape / other Phase 1 behaviour intact ------------------------------

def test_end_to_end_contract_fields():
    r = handle_query(make_req(), cfg()).response
    assert r.answer.strip()
    assert r.abstention is False
    assert r.abstention_reason is None
    assert r.confidence in ("HIGH", "MEDIUM", "LOW")
    assert 0.0 <= r.confidence_score <= 1.0
    assert r.escalation_available is False
    assert r.id == "a-1"


def test_evidence_retrieved_from_own_corpus(corpus):
    corpus_by_id = {e.id: e for e in corpus}
    r = handle_query(make_req(), cfg()).response
    assert r.citations, "expected citations from the standalone corpus"
    assert all(c.id in corpus_by_id for c in r.citations)


def test_india_vs_international_changes_retrieval_and_answer():
    india = handle_query(
        make_req(id="a-i", query=FILING_QUERY, jurisdiction="India"), cfg()
    ).response
    intl = handle_query(
        make_req(id="a-x", query=FILING_QUERY, jurisdiction="International"), cfg()
    ).response

    india_ids = {c.id for c in india.citations}
    intl_ids = {c.id for c in intl.citations}
    assert india_ids, "India side should retrieve evidence"
    assert intl_ids, "International side should retrieve evidence"
    assert all(i.startswith("in-") for i in india_ids)
    assert all(i.startswith("intl-") for i in intl_ids)
    assert india_ids != intl_ids
    assert india.answer != intl.answer


def test_golden2_points_to_pct_not_madrid():
    r = handle_query(
        make_req(query=GOLDEN_2, jurisdiction="International"), cfg()
    ).response
    assert not r.abstention
    cited = {c.id for c in r.citations}
    assert "intl-pct" in cited
    assert "intl-madrid" not in cited
    assert "Madrid" not in r.answer, "Madrid is trademarks, not a patent route"
    assert "PCT" in r.answer


def test_golden1_reflects_3p_and_tkdl_pointer():
    r = handle_query(make_req(query=GOLDEN_1), cfg()).response
    assert not r.abstention
    cited = {c.id for c in r.citations}
    assert "in-patents-act-3p" in cited
    assert "in-tkdl-pointer" in cited
    assert "3(p)" in r.answer
    assert "TKDL" in r.answer or "Traditional Knowledge Digital Library" in r.answer


def test_specialist_domain_abstains_when_wired_but_unavailable():
    """Corpus-safety rule: with the integration switch on, a specialist-domain
    query with no registered specialist must abstain, not answer from the
    standalone corpus."""
    result = handle_query(
        make_req(id="a-3", query=ABS_QUERY), Config(specialists_wired=True)
    )
    assert result.status == "abstained"
    r = result.response
    assert r.abstention is True
    assert "specialist" in r.abstention_reason.lower()
    assert "specialist" in r.answer.lower()
    assert r.citations == []


def test_same_query_answers_from_own_corpus_when_not_wired():
    """Standalone development: the demo path may answer from the own corpus."""
    result = handle_query(make_req(id="a-4", query=ABS_QUERY), cfg())
    assert result.status == "ok"


def test_routing_decision_recorded():
    result = handle_query(make_req(), cfg())
    assert result.routing.domain.value in {
        "INDIA_IP",
        "ABS_TK",
        "INTERNATIONAL_IP",
        "CLASSIFICATION",
        "GENERAL",
    }
    assert result.routing.rationale


def test_history_accepted():
    req = make_req(
        history=[
            {"role": "user", "content": "What is the PCT?"},
            {"role": "assistant", "content": "The PCT is the Patent Cooperation Treaty."},
        ]
    )
    result = handle_query(req, cfg())
    assert result.status == "ok"


# --- Phase 3: conversational follow-up handling ---------------------------------

def test_followup_resolves_context_from_history():
    """A short elliptical follow-up after the India/TK question, asked under
    the International toggle, must resolve to the PCT route via history
    carry-over instead of abstaining."""
    turn1 = handle_query(make_req(id="f-1"), cfg()).response
    assert not turn1.abstention

    followup = handle_query(
        make_req(
            id="f-2",
            query="What about outside India?",
            jurisdiction="International",
            history=[{"role": "user", "content": GOLDEN_1}],
        ),
        cfg(),
    )
    assert followup.status == "ok", followup.response.abstention_reason
    r = followup.response
    assert not r.abstention
    assert "intl-pct" in {c.id for c in r.citations}
    assert "PCT" in r.answer


def test_same_short_query_without_history_abstains():
    """Contrast: the bare follow-up has no retrievable subject on its own."""
    r = handle_query(
        make_req(id="f-3", query="What about outside India?", jurisdiction="International"),
        cfg(),
    ).response
    assert r.abstention is True


def test_routing_uses_conversation_context():
    """The routing decision consumes the resolved context, so a follow-up
    about the prior ABS/TK subject routes to the ABS/TK domain."""
    result = handle_query(
        make_req(
            id="f-4",
            query="what approvals do I need?",
            history=[{"role": "user", "content": ABS_QUERY}],
        ),
        cfg(),
    )
    assert result.routing.domain.value == "ABS_TK"


def test_self_contained_query_with_history_not_expanded():
    """A long, self-contained query must be retrieved as-is even with history
    (the prior turn must not distort a complete question)."""
    result = handle_query(
        make_req(
            id="f-5",
            query=GOLDEN_2,
            jurisdiction="International",
            history=[{"role": "user", "content": ABS_QUERY}],
        ),
        cfg(),
    )
    assert result.status == "ok"
    assert "intl-pct" in {c.id for c in result.response.citations}
