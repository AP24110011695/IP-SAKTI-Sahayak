"""M6 Phase 4 — local deterministic conversational layer, REAL integration tests.

Runs against the fully wired application (real M1 routing + real M2–M5) and
proves the Phase 4 requirement end to end:

- clearly general conversation ("hi", "what can you do?", "thanks", Hindi
  greetings) is answered locally BEFORE legal routing — no specialist, no
  citations, no fabrication;
- any message carrying a genuine legal/IP/regulatory request is NOT
  intercepted and still reaches the real M3/M4/M5 specialists through the
  unchanged routing priority;
- follow-up behaviour is preserved ("Thanks" after a legal answer may be
  local; "What about trademarks?" stays in the legal follow-up pipeline);
- legal responses and abstention behaviour are unchanged.
"""
import pytest
from fastapi.testclient import TestClient

from integration import contracts
from integration.adapters import wire_m1


@pytest.fixture(scope="module")
def members():
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
    return members["m1"]["assistant"].handle_query


def is_local(result) -> bool:
    return result.generator_used == "local-conversation"


# ---------------------------------------------------------------------------
# General conversation → local deterministic responses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("message", ["Hi", "hello", "hey", "good morning"])
def test_greetings_answered_locally(QueryRequest, handle, message):
    result = handle(QueryRequest(
        id=f"conv-g-{message.replace(' ', '-')}", query=message,
        language="en", jurisdiction="India",
    ))
    assert is_local(result)
    assert result.status == "ok"
    assert result.routing.domain.value == "GENERAL"
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    assert body["answer"].startswith("Hello! I'm IP-SAKTI Sahayak")
    assert body["citations"] == []
    assert body["abstention"] is False


def test_capability_question_answered_locally(QueryRequest, handle):
    result = handle(QueryRequest(
        id="conv-c-1", query="What can you do?",
        language="en", jurisdiction="India",
    ))
    assert is_local(result)
    body = result.response.model_dump()
    assert body["citations"] == [] and body["abstention"] is False
    for capability in ("classification", "India IP", "TKDL", "PCT",
                       "Madrid", "citations", "abstain"):
        assert capability.lower() in body["answer"].lower()


def test_thanks_answered_locally(QueryRequest, handle):
    result = handle(QueryRequest(id="conv-t-1", query="Thanks"))
    assert is_local(result)
    assert "You're welcome" in result.response.answer


def test_hindi_greeting_answered_locally(QueryRequest, handle):
    result = handle(QueryRequest(
        id="conv-h-1", query="नमस्ते", language="hi", jurisdiction="India",
    ))
    assert is_local(result)
    body = result.response.model_dump()
    assert body["answer"].startswith("नमस्ते! मैं IP-SAKTI Sahayak")
    assert "कानूनी सलाह" in body["disclaimer"]
    assert contracts.validate_query_response(body) == []


def test_local_response_over_the_real_api(client):
    resp = client.post("/api/query", json={"id": "conv-api-1", "query": "hi"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].startswith("Hello! I'm IP-SAKTI Sahayak")
    assert body["citations"] == []
    assert body["abstention"] is False
    assert body["disclaimer"].strip()


# ---------------------------------------------------------------------------
# Legal boundary → real specialists, unchanged routing
# ---------------------------------------------------------------------------


def test_patent_question_after_hi_reaches_real_m3(QueryRequest, handle):
    result = handle(QueryRequest(
        id="conv-b-1",
        query="Hi, can I patent a classical Ayurvedic formulation?",
        language="en", jurisdiction="India",
    ))
    assert not is_local(result)
    assert result.routing.domain.value == "INDIA_IP"
    assert result.generator_used == "specialist"
    assert result.status == "ok"
    body = result.response.model_dump()
    assert "3(p)" in body["answer"] and body["citations"]


def test_section_3p_question_after_thanks_reaches_real_m3(QueryRequest, handle):
    result = handle(QueryRequest(
        id="conv-b-2", query="Thanks, can you explain Section 3(p)?",
        language="en", jurisdiction="India",
    ))
    assert not is_local(result)
    assert result.routing.domain.value == "INDIA_IP"
    assert result.generator_used == "specialist"
    assert "3(p)" in result.response.answer


def test_madrid_question_after_okay_reaches_real_m5(QueryRequest, handle):
    result = handle(QueryRequest(
        id="conv-b-3", query="Okay, what is the Madrid System?",
        language="en", jurisdiction="International",
    ))
    assert not is_local(result)
    assert result.routing.domain.value == "INTERNATIONAL_IP"
    assert result.generator_used == "specialist"


def test_abs_question_after_hey_reaches_real_specialist(QueryRequest, handle):
    result = handle(QueryRequest(
        id="conv-b-4",
        query=("I want to commercialise a formulation using a plant "
               "collected in India - what approvals do I need?"),
        language="en", jurisdiction="India",
    ))
    assert not is_local(result)
    assert result.routing.domain.value == "ABS_TK"
    assert result.generator_used == "specialist"
    assert result.response.citations


# ---------------------------------------------------------------------------
# Follow-ups after a REAL legal answer
# ---------------------------------------------------------------------------


def test_thanks_after_real_legal_answer_is_local(QueryRequest, handle):
    first = handle(QueryRequest(
        id="conv-f-1",
        query="Can I patent a classical Ayurvedic formulation from an "
              "authoritative text?",
        language="en", jurisdiction="India",
    ))
    assert not is_local(first)
    follow_up = handle(QueryRequest(
        id="conv-f-2", query="Thanks",
        history=[
            {"role": "user",
             "content": "Can I patent a classical Ayurvedic formulation?"},
            {"role": "assistant", "content": first.response.answer},
        ],
    ))
    assert is_local(follow_up)
    assert "You're welcome" in follow_up.response.answer


def test_trademarks_followup_after_patent_answer_stays_legal(QueryRequest, handle):
    first = handle(QueryRequest(
        id="conv-f-3",
        query="Can I patent a classical Ayurvedic formulation from an "
              "authoritative text?",
        language="en", jurisdiction="India",
    ))
    assert not is_local(first)
    follow_up = handle(QueryRequest(
        id="conv-f-4", query="What about trademarks?",
        history=[
            {"role": "user",
             "content": "Can I patent a classical Ayurvedic formulation?"},
            {"role": "assistant", "content": first.response.answer},
        ],
    ))
    assert not is_local(follow_up)
    assert follow_up.generator_used == "specialist"


# ---------------------------------------------------------------------------
# Legal + abstention behaviour unchanged
# ---------------------------------------------------------------------------


def test_legal_golden_query_response_unchanged(QueryRequest, handle):
    result = handle(QueryRequest(
        id="conv-l-1",
        query="Can I patent a classical Ayurvedic formulation from an "
              "authoritative text?",
        language="en", jurisdiction="India",
    ))
    assert not is_local(result)
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    assert "3(p)" in body["answer"] and "tkdl" in body["answer"].lower()
    assert len(body["citations"]) >= 1


def test_abstention_behaviour_unchanged(QueryRequest, handle):
    result = handle(QueryRequest(
        id="conv-l-2", query="What is the airspeed of an unladen swallow?",
        language="en", jurisdiction="India",
    ))
    assert not is_local(result)
    assert result.response.abstention is True
    assert result.response.abstention_reason
    assert result.response.citations == []
