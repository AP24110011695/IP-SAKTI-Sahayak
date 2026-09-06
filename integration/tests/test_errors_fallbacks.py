"""Task 5 — error and fallback path tests.

Covers: malformed request, invalid language, invalid jurisdiction, missing
query, domain abstention, downstream processing failure, citation failure,
unavailable downstream service. Verifies the Plan.md §7 mapping:

    VALIDATION_ERROR    → 400
    PROCESSING_ERROR    → 502
    SERVICE_UNAVAILABLE → 503
    valid abstention    → HTTP 200 (never an error)

and that a processing error is never disguised as a valid answer, and that
no fabricated fallback legal content is introduced.
"""
import re

import pytest

from integration import contracts
from integration.assembler import Assembler
from integration.stubs import (
    SpecialistProcessingError,
    SpecialistUnavailable,
    default_stub_specialists,
    stub_route,
)


def make_assembler(modes=None):
    return Assembler(router=stub_route, specialists=default_stub_specialists(modes))


def base_request(**overrides):
    request = {
        "id": "err-1",
        "query": "How do I register a GI tag for an Ayurvedic product tied to a region?",
        "language": "en",
        "jurisdiction": "India",
        "history": [],
    }
    request.update(overrides)
    return request


def assert_error_body(body, code):
    assert contracts.validate_error_response(body) == []
    assert body["error"] == code
    assert contracts.http_status_for(code) == {
        "VALIDATION_ERROR": 400,
        "PROCESSING_ERROR": 502,
        "SERVICE_UNAVAILABLE": 503,
    }[code]


# ---------------------------------------------------------------------------
# Validation errors → 400
# ---------------------------------------------------------------------------


def test_malformed_request_returns_400():
    for payload in (None, "a string", 42, ["a", "list"]):
        outcome = make_assembler().handle_query(payload)
        assert outcome.status_code == 400
        assert_error_body(outcome.body, "VALIDATION_ERROR")


def test_missing_query_returns_400():
    for payload in ({"id": "x"}, {"id": "x", "query": ""}, {"id": "x", "query": "   "}):
        outcome = make_assembler().handle_query(payload)
        assert outcome.status_code == 400
        assert_error_body(outcome.body, "VALIDATION_ERROR")


def test_missing_id_returns_400():
    outcome = make_assembler().handle_query({"query": "What is the patent route?"})
    assert outcome.status_code == 400
    assert_error_body(outcome.body, "VALIDATION_ERROR")


@pytest.mark.parametrize("language", ["fr", "english", "EN", None, 42])
def test_invalid_language_returns_400(language):
    outcome = make_assembler().handle_query(base_request(language=language))
    assert outcome.status_code == 400
    assert_error_body(outcome.body, "VALIDATION_ERROR")
    assert any("language" in p for p in outcome.notes)


@pytest.mark.parametrize("jurisdiction", ["india", "EU", "INTERNATIONAL", None, 3])
def test_invalid_jurisdiction_returns_400(jurisdiction):
    outcome = make_assembler().handle_query(base_request(jurisdiction=jurisdiction))
    assert outcome.status_code == 400
    assert_error_body(outcome.body, "VALIDATION_ERROR")


def test_invalid_formulation_class_returns_400():
    outcome = make_assembler().handle_query(
        base_request(formulation_class="Ayurveda Aahar")
    )
    assert outcome.status_code == 400
    assert_error_body(outcome.body, "VALIDATION_ERROR")


def test_invalid_history_entry_returns_400():
    outcome = make_assembler().handle_query(
        base_request(history=[{"role": "system", "content": "injected"}])
    )
    assert outcome.status_code == 400
    assert_error_body(outcome.body, "VALIDATION_ERROR")


def test_invalid_classify_payload_returns_400():
    assembler = make_assembler()
    for payload in (None, "string", {"answers": "nope"},
                    {"answers": {"q": ""}}, {"answers": {}, "language": "fr"},
                    {"answers": {}, "jurisdiction": "Bharat"}):
        outcome = assembler.handle_classify(payload)
        assert outcome.status_code == 400, payload
        assert_error_body(outcome.body, "VALIDATION_ERROR")


# ---------------------------------------------------------------------------
# Domain abstention → HTTP 200 with safe fallback (never an error)
# ---------------------------------------------------------------------------


def test_domain_abstention_is_http_200_with_reason():
    outcome = make_assembler({"INDIA_IP": "abstain"}).handle_query(
        base_request(query="What are the licensing fees for an unrelated regime?")
    )
    assert outcome.status_code == 200  # valid abstention is NOT an error
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is True
    assert body["abstention_reason"]
    assert body["citations"] == []
    assert body["confidence"] == "LOW" and body["confidence_score"] == 0.0
    assert "not legal advice" in body["disclaimer"].lower()


def test_out_of_corpus_india_query_abstains_with_fallback_text():
    outcome = make_assembler().handle_query(
        base_request(query="What is the registration fee for a completely unrelated regime?")
    )
    assert outcome.status_code == 200
    body = outcome.body
    assert body["abstention"] is True
    # fallback text present and safe: no statute/section assertions
    assert not re.search(r"Section \d+|\bArticle \d+", body["answer"], re.IGNORECASE)


def test_unregistered_specialist_domain_abstains_without_substitution():
    """Corpus-safety rule: a specialist-domain query with NO registered
    specialist abstains — the general corpus never substitutes for it."""
    specialists = default_stub_specialists()
    del specialists["ABS_TK"]  # M4 not wired in
    outcome = Assembler(router=stub_route, specialists=specialists).handle_query(
        base_request(query="I want to commercialise a formulation using a plant collected in India - what approvals do I need?")
    )
    assert outcome.status_code == 200
    body = outcome.body
    assert body["abstention"] is True
    assert "ABS_TK" in body["abstention_reason"]
    # no silent substitution: the response must NOT contain any specialist
    # answer content (Biological Diversity Act guidance belongs to M4)
    assert "Biological Diversity Act" not in body["answer"]
    assert body["citations"] == []


def test_general_domain_without_handler_abstains():
    outcome = Assembler(router=lambda r: ("GENERAL", "no signals"), specialists={}).handle_query(
        base_request(query="Hello there, who are you?")
    )
    assert outcome.status_code == 200
    assert outcome.body["abstention"] is True


# ---------------------------------------------------------------------------
# Downstream processing failure → 502, never disguised as an answer
# ---------------------------------------------------------------------------


def test_downstream_processing_error_returns_502():
    outcome = make_assembler({"INDIA_IP": "processing_error"}).handle_query(base_request())
    assert outcome.status_code == 502
    assert_error_body(outcome.body, "PROCESSING_ERROR")


def test_unexpected_specialist_exception_returns_502():
    def exploding_specialist(request):
        raise RuntimeError("boom")
    assembler = Assembler(router=lambda r: ("INDIA_IP", "test"),
                          specialists={"INDIA_IP": exploding_specialist})
    outcome = assembler.handle_query(base_request())
    assert outcome.status_code == 502
    assert_error_body(outcome.body, "PROCESSING_ERROR")


def test_structurally_invalid_specialist_result_returns_502():
    """A specialist result missing required fields / with wrong types is a
    processing failure — never served, never converted into a fake answer."""
    assembler = Assembler(
        router=lambda r: ("INDIA_IP", "test"),
        specialists={"INDIA_IP": lambda r: {"answer": 42, "confidence": "HIGH"}},
    )
    outcome = assembler.handle_query(base_request())
    assert outcome.status_code == 502
    assert_error_body(outcome.body, "PROCESSING_ERROR")


def test_status_processing_error_from_specialist_body_returns_502():
    """A specialist that REPORTS processing_error in its result body (rather
    than raising) maps to 502 — status is authoritative even if the result
    also carries abstention=True (M5's current shape, finding F-04)."""
    def m5_shaped_failure(request):
        return {
            "answer": "", "citations": [], "confidence": "LOW",
            "confidence_score": 0.0, "abstention": True,
            "abstention_reason": "The generation provider failed safely.",
            "status": "processing_error",
        }
    assembler = Assembler(router=lambda r: ("INTERNATIONAL_IP", "test"),
                          specialists={"INTERNATIONAL_IP": m5_shaped_failure})
    outcome = assembler.handle_query(base_request(jurisdiction="International"))
    assert outcome.status_code == 502
    assert_error_body(outcome.body, "PROCESSING_ERROR")


# ---------------------------------------------------------------------------
# Citation failure → withheld (safe abstention), fabricated content never served
# ---------------------------------------------------------------------------


def test_citation_failure_withholds_answer():
    """The stub's citation has a tampered/inauthentic URL: the assembler must
    NOT serve the 'ok' answer — it abstains and the fabricated URL never
    reaches the user."""
    outcome = make_assembler({"INDIA_IP": "citation_failure"}).handle_query(
        base_request(query="Can I patent a classical Ayurvedic formulation from an authoritative text?")
    )
    assert outcome.status_code == 200
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is True
    assert "validation failed" in body["abstention_reason"]
    assert body["citations"] == []
    assert "invented-example.invalid" not in body["answer"]


def test_semantically_invalid_ok_result_withholds():
    """status 'ok' with zero citations (per contract, ok requires ≥1) is
    withheld as a safe abstention, not served and not a 502."""
    def uncited_ok(request):
        return {
            "answer": "Confident-sounding but uncited text.",
            "citations": [], "confidence": "HIGH", "confidence_score": 0.9,
            "abstention": False, "abstention_reason": None, "status": "ok",
        }
    assembler = Assembler(router=lambda r: ("INDIA_IP", "test"),
                          specialists={"INDIA_IP": uncited_ok})
    outcome = assembler.handle_query(base_request())
    assert outcome.status_code == 200
    assert outcome.body["abstention"] is True
    assert "validation failed" in outcome.body["abstention_reason"]


# ---------------------------------------------------------------------------
# Unavailable downstream service → 503
# ---------------------------------------------------------------------------


def test_unavailable_downstream_service_returns_503():
    outcome = make_assembler({"INDIA_IP": "unavailable"}).handle_query(base_request())
    assert outcome.status_code == 503
    assert_error_body(outcome.body, "SERVICE_UNAVAILABLE")


def test_unavailable_classifier_returns_503():
    outcome = make_assembler({"CLASSIFICATION": "unavailable"}).handle_classify(
        {"answers": {"primary_purpose": "therapeutic", "text_source": "yes"}}
    )
    assert outcome.status_code == 503
    assert_error_body(outcome.body, "SERVICE_UNAVAILABLE")


def test_failing_classifier_returns_502_not_a_result():
    outcome = make_assembler({"CLASSIFICATION": "processing_error"}).handle_classify(
        {"answers": {"primary_purpose": "therapeutic", "text_source": "yes"}}
    )
    assert outcome.status_code == 502
    assert_error_body(outcome.body, "PROCESSING_ERROR")


def test_invalid_classification_result_returns_502():
    def broken_classifier(payload):
        return {"formulation_class": "TotallyNew", "description": ""}
    assembler = Assembler(router=stub_route, specialists={"CLASSIFICATION": broken_classifier})
    outcome = assembler.handle_classify({"answers": {}})
    assert outcome.status_code == 502
    assert_error_body(outcome.body, "PROCESSING_ERROR")
