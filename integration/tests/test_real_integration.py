"""Phase 2 — REAL integration tests (real M1–M5, no stubs).

These tests run the actual integrated application: M1's assistant and FastAPI
app with the real M2/M3/M4/M5 workstreams wired in via
integration.adapters.wire_m1(). Everything here is offline — every member's
unconfigured generation mode is deterministic (no LLM keys, no network, no
faked calls).

Covers the Phase 2 required checks: routing to the real specialists, the
/ api/query + /api/classify + /api/health endpoints, error mapping
(400/502/503), abstention-as-200, citation/confidence preservation, F-03
(ABS routing), F-04 (processing_error normalisation), F-06 (empty abstention
answer), F-09 (M5 weak fee-query regression), M4 TKDL-pointer safety, and
M5 PCT/Madrid/Hague mapping safety.
"""
import sys

import pytest
from fastapi.testclient import TestClient

from integration import contracts
from integration.adapters import (
    AdapterError,
    _validated_rag_result,
    load_members,
    wire_m1,
)


@pytest.fixture(scope="module")
def members():
    """Wire the REAL specialists into M1 once for this module."""
    return wire_m1()


@pytest.fixture(scope="module")
def client(members):
    from integration.adapters import app

    return TestClient(app)


@pytest.fixture(scope="module")
def QueryRequest(members):
    return members["m1"]["models"].QueryRequest


@pytest.fixture(scope="module")
def handle(members):
    assistant = members["m1"]["assistant"]
    return assistant.handle_query


# ---------------------------------------------------------------------------
# Health / endpoints exist
# ---------------------------------------------------------------------------


def test_health_reports_wired_specialists(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["specialists_wired"] is True
    assert set(body["specialists"]) == {
        "INDIA_IP", "ABS_TK", "INTERNATIONAL_IP", "CLASSIFICATION"
    }


# ---------------------------------------------------------------------------
# Real specialist dispatch through M1 (programmatic: routing visible)
# ---------------------------------------------------------------------------


def test_india_query_routes_to_real_m3(QueryRequest, handle):
    result = handle(QueryRequest(
        id="real-1",
        query="Can I patent a classical Ayurvedic formulation from an authoritative text?",
        language="en", jurisdiction="India",
    ))
    assert result.routing.domain.value == "INDIA_IP"
    assert result.generator_used == "specialist"
    assert result.status == "ok"
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    assert "3(p)" in body["answer"] and "tkdl" in body["answer"].lower()
    assert len(body["citations"]) >= 1


def test_abs_golden_query_routes_to_real_m4(QueryRequest, handle):
    """F-03 regression: M1's routing must send the golden ABS query to M4."""
    result = handle(QueryRequest(
        id="real-2",
        query=("I want to commercialise a formulation using a plant collected "
               "in India - what approvals do I need?"),
        language="en", jurisdiction="India",
    ))
    assert result.routing.domain.value == "ABS_TK"
    assert result.generator_used == "specialist"
    assert result.status == "ok"
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    assert "Biological Diversity Act" in body["answer"]
    assert len(body["citations"]) >= 1
    # M4's confidence is preserved as-is (F-07: no re-scoring)
    assert body["confidence"] in ("HIGH", "MEDIUM", "LOW")
    assert 0.0 <= body["confidence_score"] <= 1.0


def test_international_patent_routes_to_real_m5_pct(QueryRequest, handle):
    result = handle(QueryRequest(
        id="real-3",
        query="I want to file a patent for a new Ayurvedic drug outside India - what route do I use?",
        language="en", jurisdiction="International",
    ))
    assert result.routing.domain.value == "INTERNATIONAL_IP"
    assert result.status == "ok"
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    assert "PCT" in body["answer"]
    assert "Madrid" not in body["answer"] and "Hague" not in body["answer"]


def test_international_trademark_routes_to_real_m5_madrid(QueryRequest, handle):
    result = handle(QueryRequest(
        id="real-4",
        query="I want to register my Ayurvedic brand name internationally",
        language="en", jurisdiction="International",
    ))
    assert result.status == "ok"
    assert "Madrid" in result.response.answer
    assert "PCT" not in result.response.answer


def test_international_design_routes_to_real_m5_hague(QueryRequest, handle):
    result = handle(QueryRequest(
        id="real-5",
        query="I want to register the packaging design for my Ayurvedic product internationally",
        language="en", jurisdiction="International",
    ))
    assert result.status == "ok"
    body = result.response.model_dump()
    assert "Hague" in body["answer"]
    assert "PCT" not in body["answer"] and "Madrid" not in body["answer"]


def test_out_of_scope_india_query_abstains_from_real_m3(QueryRequest, handle):
    """M3 refuses international questions itself (India-only separation)."""
    result = handle(QueryRequest(
        id="real-6",
        query="What is the fee for renewing a trademark in Japan under the Madrid Protocol?",
        language="en", jurisdiction="India",
    ))
    assert result.status == "abstained"
    assert result.response.abstention is True
    assert result.response.abstention_reason
    assert result.response.citations == []
    # no fabricated substitute from any corpus
    assert "Madrid" not in result.response.answer


# ---------------------------------------------------------------------------
# HTTP contract: /api/query
# ---------------------------------------------------------------------------


def test_query_endpoint_returns_contract_response(client):
    response = client.post("/api/query", json={
        "id": "http-1",
        "query": "How do I register a GI tag for an Ayurvedic product tied to a region?",
        "language": "en", "jurisdiction": "India", "history": [],
    })
    assert response.status_code == 200
    body = response.json()
    assert contracts.validate_query_response(body) == []
    assert body["id"] == "http-1"
    assert body["abstention"] is False
    assert "Geographical Indication" in body["answer"]


def test_query_endpoint_validates_id_echo_and_disclaimer(client):
    response = client.post("/api/query", json={
        "id": "http-2",
        "query": "I want to file a patent for a new Ayurvedic drug outside India - what route do I use?",
        "jurisdiction": "International",
    })
    body = response.json()
    assert body["id"] == "http-2"
    assert "not legal advice" in body["disclaimer"].lower()


# ---------------------------------------------------------------------------
# HTTP contract: /api/classify (real M2)
# ---------------------------------------------------------------------------


def test_classify_endpoint_food_vs_medicine(client):
    food = client.post("/api/classify", json={
        "answers": {"primary_purpose": "food_wellness", "food_exclusion": "none"},
        "jurisdiction": "India", "language": "en",
    })
    assert food.status_code == 200
    food_body = food.json()
    assert contracts.validate_classification_result(food_body) == []
    assert food_body["formulation_class"] == "Ayurveda-Aahar"
    assert any("FSSAI" in r for r in food_body["relevant_regimes"])

    medicine = client.post("/api/classify", json={
        "answers": {"primary_purpose": "therapeutic", "text_source": "yes",
                    "standardised_fraction": "no", "ingredients_known": "yes",
                    "new_indication": "no"},
        "jurisdiction": "India", "language": "en",
    })
    assert medicine.status_code == 200
    medicine_body = medicine.json()
    assert medicine_body["formulation_class"] == "Classical"
    assert any("Section 3(p)" in r for r in medicine_body["relevant_regimes"])
    assert medicine_body["tkdl_pointer"] and "tkdl.res.in" in medicine_body["tkdl_pointer"]
    assert food_body["relevant_regimes"] != medicine_body["relevant_regimes"]


def test_classify_endpoint_all_seven_categories(client):
    cases = {
        "Classical": {"primary_purpose": "therapeutic", "text_source": "yes",
                      "standardised_fraction": "no", "ingredients_known": "yes",
                      "new_indication": "no"},
        "Proprietary": {"primary_purpose": "therapeutic", "text_source": "no",
                        "standardised_fraction": "no", "ingredients_known": "yes",
                        "new_indication": "no"},
        "Phytopharmaceutical": {"primary_purpose": "therapeutic", "text_source": "no",
                                "standardised_fraction": "yes"},
        "New Drug": {"primary_purpose": "therapeutic", "text_source": "no",
                     "standardised_fraction": "no", "ingredients_known": "no"},
        "Ayurveda-Aahar": {"primary_purpose": "food_wellness", "food_exclusion": "none",
                           "new_indication": "no"},
        "Cosmetic": {"primary_purpose": "external_cosmetic", "new_indication": "no"},
        "Uncertain": {},
    }
    for expected, answers in cases.items():
        response = client.post("/api/classify", json={
            "answers": answers, "jurisdiction": "India", "language": "en"})
        assert response.status_code == 200, expected
        body = response.json()
        assert contracts.validate_classification_result(body) == [], expected
        assert body["formulation_class"] == expected, expected


def test_classify_endpoint_uncertain_asks_for_clarification(client):
    body = client.post("/api/classify", json={"answers": {}}).json()
    assert body["formulation_class"] == "Uncertain"
    assert body["needs_clarification"] is True
    assert body["clarification_prompt"]


def test_classify_endpoint_invalid_answer_value_is_400(client):
    response = client.post("/api/classify", json={
        "answers": {"primary_purpose": "become-a-lawyer"}})
    assert response.status_code == 400
    assert response.json()["error"] == "VALIDATION_ERROR"


def test_classify_endpoint_unknown_question_id_is_400(client):
    response = client.post("/api/classify", json={"answers": {"not_a_question": "yes"}})
    assert response.status_code == 400


def test_classify_endpoint_without_handler_is_503(client, members):
    """Standalone M1 (no classification handler) serves 503, not a fake result."""
    assistant = members["m1"]["assistant"]
    routing = members["m1"]["routing"]
    saved_handler = assistant.registered_specialist_handler(routing.Domain.CLASSIFICATION)
    saved_name = routing.registered_specialist(routing.Domain.CLASSIFICATION)
    assistant._SPECIALIST_HANDLERS.pop(routing.Domain.CLASSIFICATION, None)
    routing._SPECIALISTS.pop(routing.Domain.CLASSIFICATION, None)
    try:
        response = client.post("/api/classify", json={"answers": {}})
        assert response.status_code == 503
        assert response.json()["error"] == "SERVICE_UNAVAILABLE"
    finally:
        if saved_handler:
            assistant.register_specialist_handler(routing.Domain.CLASSIFICATION, saved_handler)
        if saved_name:
            routing.register_specialist(routing.Domain.CLASSIFICATION, saved_name)


def test_classify_endpoint_failure_is_502(client, members):
    assistant = members["m1"]["assistant"]
    routing = members["m1"]["routing"]

    def broken(payload):
        raise RuntimeError("classifier exploded")

    saved_handler = assistant.registered_specialist_handler(routing.Domain.CLASSIFICATION)
    assistant.register_specialist_handler(routing.Domain.CLASSIFICATION, broken)
    try:
        response = client.post("/api/classify", json={"answers": {}})
        assert response.status_code == 502
        assert response.json()["error"] == "PROCESSING_ERROR"
    finally:
        assistant.register_specialist_handler(routing.Domain.CLASSIFICATION, saved_handler)


# ---------------------------------------------------------------------------
# Error / fallback policy over HTTP
# ---------------------------------------------------------------------------


def test_malformed_requests_are_400(client):
    for payload in ({}, {"id": "x"}, {"id": "x", "query": ""}, "not-a-dict"):
        response = client.post("/api/query", json=payload)
        assert response.status_code == 400, payload
        body = response.json()
        assert contracts.validate_error_response(body) == []
        assert body["error"] == "VALIDATION_ERROR"


def test_invalid_language_and_jurisdiction_are_400(client):
    assert client.post("/api/query", json={
        "id": "x", "query": "hello", "language": "fr"}).status_code == 400
    assert client.post("/api/query", json={
        "id": "x", "query": "hello", "jurisdiction": "EU"}).status_code == 400


def test_specialist_processing_failure_is_502_not_a_fake_answer(client, members):
    assistant = members["m1"]["assistant"]
    routing = members["m1"]["routing"]

    def broken(request):
        raise RuntimeError("specialist backend down")

    saved = assistant.registered_specialist_handler(routing.Domain.INDIA_IP)
    assistant.register_specialist_handler(routing.Domain.INDIA_IP, broken)
    try:
        response = client.post("/api/query", json={
            "id": "err-1",
            "query": "How do I register a GI tag for an Ayurvedic product tied to a region?",
            "jurisdiction": "India"})
        assert response.status_code == 502
        body = response.json()
        assert body["error"] == "PROCESSING_ERROR"
        assert "answer" not in body and "citations" not in body
    finally:
        assistant.register_specialist_handler(routing.Domain.INDIA_IP, saved)


def test_processing_error_status_from_real_member_is_502(members):
    """F-04 normalisation: a REAL M5 result produced by a failing generation
    client (status=processing_error, abstention=True — M5's actual shape) is
    converted by the boundary into an error, never served as a 200."""
    m5 = members["m5"]["pkg"]
    from member5.llm import GenerationError

    class FailingClient:
        def generate(self, **kwargs):
            raise GenerationError("simulated provider failure")

    raw = m5.guide(
        "I want to file a patent for a new Ayurvedic drug outside India",
        client=FailingClient(),
    )
    assert raw["status"] == "processing_error" and raw["abstention"] is True
    with pytest.raises(AdapterError, match="processing error"):
        _validated_rag_result(raw, "M5")


def test_m4_processing_error_status_is_also_normalised(members):
    """M4's failure path has the same shape (abstention=True + status=
    processing_error): status must stay authoritative for every member."""
    guidance = members["m4"]["guidance"]

    class BrokenLLM:
        def complete(self, system, user):
            raise RuntimeError("M4 backend down")

    raw = guidance.answer(
        "I want to commercialise a formulation using a plant collected in India "
        "- what approvals do I need?",
        llm=BrokenLLM(),
    )
    assert raw["status"] == "processing_error"
    with pytest.raises(AdapterError, match="processing error"):
        _validated_rag_result(raw, "M4")


def test_structurally_invalid_result_is_502(members):
    with pytest.raises(AdapterError, match="structurally invalid"):
        _validated_rag_result({"answer": 42, "confidence": "HIGH"}, "M3")


def test_semantically_unsafe_ok_result_is_withheld_as_abstention(members):
    """An 'ok' result carrying a contract-invalid citation (missing required
    field) is withheld: converted into a clean abstention, never served."""
    unsafe = {
        "answer": "Answer text.",
        "citations": [{"id": "X", "source_name": "S", "source_type": "statute"}],  # no excerpt
        "confidence": "HIGH", "confidence_score": 0.9,
        "abstention": False, "abstention_reason": None, "status": "ok",
    }
    result = _validated_rag_result(unsafe, "M3")
    assert result["status"] == "abstained" and result["abstention"] is True
    assert result["citations"] == []


def test_f09_weak_fee_query_abstains_over_http(client):
    """F-09 regression: the previously-answered weak patent query
    ('filing fee for patents in Antarctica?') must now abstain instead of
    receiving generic PCT text."""
    response = client.post("/api/query", json={
        "id": "f09-1",
        "query": "What is the filing fee for patents in Antarctica?",
        "language": "en", "jurisdiction": "International",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["abstention"] is True
    assert body["abstention_reason"]
    assert body["citations"] == []
    assert "PCT" not in body["answer"]
    assert "not legal advice" in body["disclaimer"].lower()


def test_f06_empty_specialist_abstention_gets_fallback_text(QueryRequest, handle):
    """F-06 normalisation: M5's abstention (answer="") becomes an HTTP 200
    abstention carrying M1's safe fallback text, not an empty string."""
    result = handle(QueryRequest(
        id="f06-1",
        query="What is the filing fee for patents in Antarctica?",
        language="en", jurisdiction="International",
    ))
    assert result.status == "abstained"
    assert result.response.abstention is True
    assert result.response.answer.strip()  # fallback text substituted
    assert result.response.abstention_reason


# ---------------------------------------------------------------------------
# M4 TKDL pointer safety through the integrated boundary
# ---------------------------------------------------------------------------


def test_m4_tkdl_pointer_preserved_and_safe(QueryRequest, handle):
    """M4's tkdl_pointer survives the QueryResponse boundary (surfaced in the
    answer text — F-05) and contains only the public-level description."""
    result = handle(QueryRequest(
        id="tkdl-1",
        query="My classical ayurvedic formulation is traditional knowledge - how is prior art checked?",
        language="en", jurisdiction="India",
    ))
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    answer = body["answer"]
    # M4's pointer is description-only: it names TKDL and its portal and
    # never reproduces database content.
    assert "TKDL" in answer and "tkdl.res.in" in answer
    assert "never reproduces its database content" in answer


# ---------------------------------------------------------------------------
# Hindi flow through the real specialists
# ---------------------------------------------------------------------------


def test_hindi_india_query_answered_in_hindi_by_m3(QueryRequest, handle):
    result = handle(QueryRequest(
        id="hi-1",
        query="मैं अपने आयुर्वेदिक उत्पाद के लिए जीआई टैग कैसे पंजीकृत करूँ?",
        language="hi", jurisdiction="India",
    ))
    assert result.status == "ok"
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    # M3 answers Devanagari questions in Hindi; disclaimer in Hindi
    assert "कानूनी सलाह नहीं" in body["disclaimer"]
    assert body["citations"]


def test_hindi_abs_signal_routes_to_m4(QueryRequest, handle):
    result = handle(QueryRequest(
        id="hi-2",
        query="पारंपरिक ज्ञान वाले फॉर्मूलेशन के लिए अनुमतियाँ क्या चाहिए?",
        language="hi", jurisdiction="India",
    ))
    assert result.routing.domain.value == "ABS_TK"
    assert result.status in ("ok", "abstained")


# ---------------------------------------------------------------------------
# Corpus-safety: no silent substitution
# ---------------------------------------------------------------------------


def test_unwired_flag_still_answers_via_corpus_demo_mode(members):
    """specialists_wired=False is the standalone demo mode (documented M1
    behaviour): the corpus may answer. This test pins the distinction."""
    config = members["m1"]["config"]
    models = members["m1"]["models"]
    assistant = members["m1"]["assistant"]
    saved = config.get_config()
    config.set_config(config.Config(specialists_wired=False))
    try:
        result = assistant.handle_query(models.QueryRequest(
            id="demo-1",
            query="Can I patent a classical Ayurvedic formulation from an authoritative text?",
            language="en", jurisdiction="India",
        ))
        # demo mode: answered from M1's own corpus, not the specialist
        assert result.generator_used != "specialist"
    finally:
        config.set_config(saved)


def test_wired_mode_never_answers_specialist_domain_from_corpus(QueryRequest, handle):
    """With specialists wired, an out-of-scope specialist query must abstain —
    M1's corpus must NOT substitute (corpus-safety rule). The specialist
    serving the abstention is correct; a corpus-generated answer is not."""
    result = handle(QueryRequest(
        id="safety-1",
        query="What is the fee for renewing a trademark in Japan under the Madrid Protocol?",
        language="en", jurisdiction="India",
    ))
    assert result.status == "abstained"
    assert result.response.abstention is True
    assert result.response.citations == []
    # M3's own refusal reason — not an M1-corpus answer about Madrid
    assert "out_of_scope_international" in result.response.abstention_reason
    assert "Japan" not in result.response.answer


# ---------------------------------------------------------------------------
# Citation / confidence / traceability preservation
# ---------------------------------------------------------------------------


def test_specialist_citations_survive_unchanged(QueryRequest, handle, members):
    """Every citation in an integrated response is byte-identical to the
    specialist's own stored record (no invented metadata anywhere)."""
    result = handle(QueryRequest(
        id="cite-1",
        query="I want to commercialise a formulation using a plant collected in India - what approvals do I need?",
        language="en", jurisdiction="India",
    ))
    assert result.status == "ok"
    m4_corpus = members["m4"]["corpus"]
    for citation in result.response.citations:
        record = m4_corpus.get_record(citation.id)
        assert record is not None, f"citation {citation.id} not in M4 corpus"
        assert citation.source_name == record["source_name"]
        assert citation.excerpt == record["excerpt"]
        assert citation.url == record["url"]
        assert citation.section == record["section"]
        # and the citation passes the contract validator
        assert contracts.validate_citation(citation.model_dump()) == []


def test_confidence_is_preserved_from_specialist_result(QueryRequest, handle, members):
    m5 = members["m5"]["pkg"]
    raw = m5.guide(
        "I want to file a patent for a new Ayurvedic drug outside India - what route do I use?",
        language="en", jurisdiction="International",
    )
    result = handle(QueryRequest(
        id="conf-1",
        query="I want to file a patent for a new Ayurvedic drug outside India - what route do I use?",
        language="en", jurisdiction="International",
    ))
    assert result.response.confidence == raw["confidence"]
    assert result.response.confidence_score == raw["confidence_score"]
