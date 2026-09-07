"""Local deterministic conversational layer — regression tests (M6 Phase 4).

Proves:
- general conversation ("hi", "hello", "thanks", "bye", "what can you do?",
  Hindi greetings, acknowledgements) is answered locally, deterministically;
- the boundary rule: any message carrying a genuine legal/IP/regulatory
  request is NEVER intercepted and continues through the existing pipeline;
- follow-up behaviour is preserved ("Thanks" after a legal answer may be
  local; substantive follow-ups stay in the legal pipeline);
- safety: local responses carry no citations, the standing disclaimer, and
  abstention/legal behaviour is unchanged.
"""
import pytest
from fastapi.testclient import TestClient

from m1.assistant import handle_query
from m1.api import app
from m1.config import Config, reset_config, set_config
from m1.conversation import (
    ACKNOWLEDGEMENT,
    GOODBYE,
    GREETING,
    HELP,
    THANKS,
    detect_intent,
    local_response,
)
from m1.models import Message, QueryRequest

# Boundary queries: conversational words + a genuine legal/IP/regulatory
# request — must ALWAYS continue through the legal pipeline.
BOUNDARY_QUERIES = (
    "Hi, can I patent a classical Ayurvedic formulation?",
    "Hello, what is Section 3(p) of the Patents Act?",
    "Thanks, but can you explain PCT?",
    "Okay, how do I register a GI for my Ayurvedic product?",
    "Hey, what ABS requirements apply to this plant?",
    "Thank you. What is the Madrid System?",
)


def make_req(query=None, **overrides):
    data = dict(id="conv-1", query=query or "hi", jurisdiction="India",
                language="en")
    data.update(overrides)
    return QueryRequest(**data)


def cfg():
    return Config()  # hermetic: extractive generator, specialists not wired


def is_local(result) -> bool:
    return result.generator_used == "local-conversation"


# --- intent detection ---------------------------------------------------------

@pytest.mark.parametrize("message, intent", [
    ("hi", GREETING),
    ("Hi", GREETING),
    ("hello", GREETING),
    ("hey", GREETING),
    ("good morning", GREETING),
    ("Good afternoon!", GREETING),
    ("good evening", GREETING),
    ("namaste", GREETING),
    ("नमस्ते", GREETING),
    ("thanks", THANKS),
    ("thank you", THANKS),
    ("Thank you so much!", THANKS),
    ("धन्यवाद", THANKS),
    ("bye", GOODBYE),
    ("goodbye", GOODBYE),
    ("see you", GOODBYE),
    ("see you later", GOODBYE),
    ("help", HELP),
    ("what can you do?", HELP),
    ("what can you help with?", HELP),
    ("how can you help?", HELP),
    ("who are you?", HELP),
    ("what is IP-SAKTI?", HELP),
    ("what is IP-SAKTI Sahayak?", HELP),
    ("okay", ACKNOWLEDGEMENT),
    ("ok", ACKNOWLEDGEMENT),
    ("got it", ACKNOWLEDGEMENT),
    ("alright", ACKNOWLEDGEMENT),
])
def test_supported_intents_detected(message, intent):
    assert detect_intent(message) == intent


@pytest.mark.parametrize("message", [
    *BOUNDARY_QUERIES,
    # follow-ups and ambiguous fragments must stay in the legal pipeline
    "What about trademarks?",
    "Okay, what about Madrid?",
    "what about that?",
    "good",
    "it",
    "kya hai TKDL?",
    "",
])
def test_non_conversational_messages_not_detected(message):
    assert detect_intent(message) is None


# --- required general-conversation tests 1–6 ----------------------------------

@pytest.mark.parametrize("message", ["hi", "hello"])
def test_greeting_answered_locally(message):
    result = handle_query(make_req(message), cfg())
    assert is_local(result)
    assert result.status == "ok"
    assert result.response.answer.startswith("Hello! I'm IP-SAKTI Sahayak")
    assert result.routing.domain.value == "GENERAL"


def test_thanks_answered_locally():
    result = handle_query(make_req("thanks"), cfg())
    assert is_local(result)
    assert "You're welcome" in result.response.answer


def test_bye_answered_locally():
    result = handle_query(make_req("bye"), cfg())
    assert is_local(result)
    assert result.response.answer.startswith("Goodbye")


def test_capability_question_answered_locally():
    result = handle_query(make_req("what can you do?"), cfg())
    assert is_local(result)
    answer = result.response.answer
    # capabilities actually implemented by the pipeline — nothing invented
    assert "classification" in answer.lower()
    assert "India IP" in answer
    assert "TKDL" in answer
    assert "PCT" in answer and "Madrid" in answer
    assert "abstain" in answer.lower()
    assert "citations" in answer.lower()


def test_hindi_greeting_gets_hindi_local_response():
    result = handle_query(make_req("नमस्ते", language="hi"), cfg())
    assert is_local(result)
    assert result.response.answer.startswith("नमस्ते! मैं IP-SAKTI Sahayak")
    assert "कानूनी सलाह" in result.response.disclaimer


def test_hindi_language_toggle_picks_hindi_response():
    result = handle_query(make_req("thanks", language="hi"), cfg())
    assert is_local(result)
    assert "स्वागत है" in result.response.answer


def test_acknowledgement_answered_locally():
    for message in ("okay", "ok", "got it", "alright"):
        result = handle_query(make_req(message), cfg())
        assert is_local(result), message
        assert result.response.answer.startswith("Got it")


def test_detect_is_deterministic():
    assert [detect_intent(m) for m in ("hi", "thanks", "bye", "help", "ok")] == [
        detect_intent(m) for m in ("hi", "thanks", "bye", "help", "ok")
    ]


# --- required legal-boundary tests 7–10 ---------------------------------------

@pytest.mark.parametrize("message", BOUNDARY_QUERIES)
def test_boundary_queries_never_intercepted(message):
    """A conversational word plus a genuine legal request stays in the legal
    pipeline — the local layer does not fire at all."""
    result = handle_query(make_req(message), cfg())
    assert not is_local(result)
    assert local_response(make_req(message)) is None


def test_boundary_query_routes_to_legal_domain():
    result = handle_query(
        make_req("Hi, can I patent a classical Ayurvedic formulation?"), cfg()
    )
    assert result.routing.domain.value == "INDIA_IP"


def test_abs_boundary_query_reaches_legal_pipeline():
    """The ABS requirement is a genuine legal request: never intercepted, and
    routed to a specialist legal domain (M1's keyword heuristic decides which)."""
    result = handle_query(make_req("Hey, what ABS requirements apply?"), cfg())
    assert not is_local(result)
    assert result.routing.domain.value in {
        "INDIA_IP", "ABS_TK", "INTERNATIONAL_IP", "CLASSIFICATION",
    }


# --- required follow-up tests 11–12 -------------------------------------------

def test_thanks_after_legal_answer_is_local():
    first_query = ("Can I patent a classical Ayurvedic formulation from an "
                   "authoritative text?")
    first = handle_query(make_req(first_query), cfg())
    assert not is_local(first)
    follow_up = make_req(
        "Thanks",
        history=[
            Message(role="user", content=first_query),
            Message(role="assistant", content=first.response.answer),
        ],
    )
    result = handle_query(follow_up, cfg())
    assert is_local(result)
    assert "You're welcome" in result.response.answer


def test_substantive_followup_stays_in_legal_pipeline():
    first_query = ("Can I patent a classical Ayurvedic formulation from an "
                   "authoritative text?")
    first = handle_query(make_req(first_query), cfg())
    assert not is_local(first)
    follow_up = make_req(
        "What about trademarks?",
        history=[
            Message(role="user", content=first_query),
            Message(role="assistant", content=first.response.answer),
        ],
    )
    result = handle_query(follow_up, cfg())
    assert not is_local(result)


def test_madrid_followup_after_legal_answer_stays_legal():
    follow_up = make_req(
        "Okay, what about Madrid?",
        history=[
            Message(role="user", content="Here is information about the PCT…"),
            Message(role="assistant", content="Here is information about the PCT…"),
        ],
    )
    result = handle_query(follow_up, cfg())
    assert not is_local(result)


# --- required safety tests 13–15 ----------------------------------------------

@pytest.mark.parametrize("message, language", [
    ("hi", "en"), ("hello", "en"), ("thanks", "en"), ("bye", "en"),
    ("what can you do?", "en"), ("ok", "en"),
    ("नमस्ते", "hi"), ("dhanyavad", "hi"),
])
def test_local_responses_have_no_citations_and_stand_disclaimer(message, language):
    response = local_response(make_req(message, language=language))
    assert response is not None
    assert response.citations == []
    assert response.abstention is False
    assert response.abstention_reason is None
    assert response.confidence == "HIGH"
    assert 0.0 <= response.confidence_score <= 1.0
    assert response.disclaimer.strip()
    assert response.escalation_available is False


def test_local_response_serves_full_contract_over_api():
    set_config(Config())
    try:
        with TestClient(app) as client:
            resp = client.post(
                "/api/query",
                json={"id": "conv-api-1", "query": "hi"},
            )
            assert resp.status_code == 200
            body = resp.json()
            for field in ("id", "answer", "citations", "confidence",
                          "confidence_score", "abstention",
                          "abstention_reason", "escalation_available",
                          "disclaimer"):
                assert field in body
            assert body["citations"] == []
            assert body["abstention"] is False
            assert body["disclaimer"].strip()
    finally:
        reset_config()


def test_legal_pipeline_unchanged_for_golden_query():
    """Safety test 14: a legal query produces the same pipeline behaviour as
    before the conversational layer existed (corpus answer with citations)."""
    result = handle_query(
        make_req("Can I patent a classical Ayurvedic formulation from an "
                 "authoritative text?"),
        cfg(),
    )
    assert not is_local(result)
    assert result.status == "ok"
    assert result.response.citations
    assert "3(p)" in result.response.answer


def test_abstention_behaviour_unchanged_for_off_scope_query():
    """Safety test 15: an off-scope legal question still abstains exactly as
    before (HTTP 200 abstention via the pipeline, not a local answer)."""
    result = handle_query(
        make_req("What is the airspeed of an unladen swallow?"), cfg()
    )
    assert not is_local(result)
    assert result.response.abstention is True
    assert result.response.abstention_reason
    assert result.response.citations == []
