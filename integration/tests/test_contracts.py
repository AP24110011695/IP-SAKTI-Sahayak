"""Task 3 — contract test harness.

Verifies the target contracts (Plan.md §7 / MEMBER_6.md §3) against
contract-VALID stub payloads AND against systematically malformed ones. The
harness must DETECT: wrong field names, wrong field types, invalid enum
values, missing required fields, malformed citations, invalid status and
invalid confidence values — every case below is a deliberate mutation.
"""
import pytest

from integration import contracts
from integration.stubs import StubClassifier, StubIndiaSpecialist

# ---------------------------------------------------------------------------
# Valid payloads (produced by the stub specialists — proof the stubs
# themselves are contract-shaped)
# ---------------------------------------------------------------------------


def test_valid_stub_rag_result_passes():
    result = StubIndiaSpecialist()({
        "id": "x", "query": "Can I patent a classical Ayurvedic formulation?",
        "language": "en", "jurisdiction": "India",
    })
    assert result["status"] == "ok"
    assert contracts.validate_rag_result(result) == []


def test_valid_stub_classification_result_passes():
    result = StubClassifier()({"answers": {"primary_purpose": "therapeutic",
                                           "text_source": "yes"}})
    assert contracts.validate_classification_result(result) == []


VALID_REQUEST = {
    "id": "req-1",
    "query": "Can I patent a classical Ayurvedic formulation?",
    "language": "en",
    "jurisdiction": "India",
    "formulation_class": None,
    "history": [],
}


# ---------------------------------------------------------------------------
# QueryRequest: field names, types, enums, required fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("drop, add, should_fail", [
    (("query",), {"querry": "hello"}, True),   # wrong field name: query misspelled
    (("id",), {"qid": "req-2"}, True),         # wrong field name: id misspelled
    (("id",), {}, True),                       # missing required id
    (("query",), {}, True),                    # missing required query
    ((), {"id": ""}, True),                    # blank id
    ((), {"query": "   "}, True),              # whitespace-only query
    ((), {"client_tag": "web"}, False),        # extra unknown field tolerated
    ((), {}, False),                           # pure defaults request is valid
])
def test_query_request_mutation_detection(drop, add, should_fail):
    payload = dict(VALID_REQUEST)
    for key in drop:
        del payload[key]
    payload.update(add)
    problems = contracts.validate_query_request(payload)
    assert bool(problems) == should_fail, (drop, add, problems)


def test_query_request_extra_unknown_field_is_tolerated():
    payload = dict(VALID_REQUEST, client_tag="web")
    assert contracts.validate_query_request(payload) == []


@pytest.mark.parametrize("bad_language", ["fr", "english", "EN", "", None, 1])
def test_query_request_invalid_language(bad_language):
    problems = contracts.validate_query_request(dict(VALID_REQUEST, language=bad_language))
    assert any("language" in p for p in problems)


@pytest.mark.parametrize("bad_jurisdiction", ["india", "INTERNATIONAL", "EU", "", None, 2])
def test_query_request_invalid_jurisdiction(bad_jurisdiction):
    problems = contracts.validate_query_request(dict(VALID_REQUEST, jurisdiction=bad_jurisdiction))
    assert any("jurisdiction" in p for p in problems)


@pytest.mark.parametrize("bad_class", [
    "classical", "Ayurveda Aahar", "AyurvedaAahar", "herbal", "", 7,
])
def test_query_request_invalid_formulation_class(bad_class):
    problems = contracts.validate_query_request(
        dict(VALID_REQUEST, formulation_class=bad_class)
    )
    assert any("formulation_class" in p for p in problems)


def test_query_request_all_seven_classes_accepted():
    for formulation_class in contracts.FORMULATION_CLASSES:
        payload = dict(VALID_REQUEST, formulation_class=formulation_class)
        assert contracts.validate_query_request(payload) == [], formulation_class


def test_query_request_history_type_and_message_validation():
    assert contracts.validate_query_request(
        dict(VALID_REQUEST, history="not a list")
    )
    assert contracts.validate_query_request(
        dict(VALID_REQUEST, history=[{"role": "system", "content": "hi"}])
    )
    assert contracts.validate_query_request(
        dict(VALID_REQUEST, history=[{"role": "user", "content": ""}])
    )
    assert contracts.validate_query_request(
        dict(VALID_REQUEST, history=[{"role": "user", "content": "earlier question"}])
    ) == []


def test_query_request_not_a_dict():
    assert contracts.validate_query_request("hello") != []
    assert contracts.validate_query_request(None) != []
    assert contracts.validate_query_request(42) != []


# ---------------------------------------------------------------------------
# QueryResponse
# ---------------------------------------------------------------------------


def valid_query_response(**overrides):
    response = {
        "id": "req-1",
        "answer": "Grounded answer citing stored evidence.",
        "citations": [{
            "id": "IN-001", "source_name": "Patents Act, 1970", "source_type": "statute",
            "section": "Section 3(p)", "excerpt": "Stored evidence excerpt.",
            "url": "https://www.indiacode.nic.in", "effective_date": "1970-09-21",
        }],
        "confidence": "HIGH",
        "confidence_score": 0.9,
        "abstention": False,
        "abstention_reason": None,
        "escalation_available": False,
        "disclaimer": "Information, not legal advice.",
    }
    response.update(overrides)
    return response


def test_valid_query_response_passes():
    assert contracts.validate_query_response(valid_query_response()) == []


@pytest.mark.parametrize("field", list(contracts.QUERY_RESPONSE_FIELDS))
def test_query_response_missing_each_required_field(field):
    payload = valid_query_response()
    del payload[field]
    problems = contracts.validate_query_response(payload)
    assert any(field in p for p in problems), field


def test_query_response_wrong_field_name_detected():
    payload = valid_query_response()
    payload["confindence"] = payload.pop("confidence")
    problems = contracts.validate_query_response(payload)
    assert any("confidence" in p for p in problems)


def test_query_response_wrong_types():
    for overrides in (
        {"id": 5}, {"answer": 1.5}, {"citations": "none"},
        {"confidence_score": "0.9"}, {"abstention": "false"},
        {"escalation_available": 1}, {"disclaimer": None},
    ):
        problems = contracts.validate_query_response(valid_query_response(**overrides))
        assert problems, overrides


@pytest.mark.parametrize("bad_confidence", ["high", "HIGH ", "URGENT", "MEDIUM+", None, 3])
def test_query_response_invalid_confidence_enum(bad_confidence):
    problems = contracts.validate_query_response(
        valid_query_response(confidence=bad_confidence)
    )
    assert any("confidence" in p for p in problems)


@pytest.mark.parametrize("bad_score", [1.5, -0.1, 2, "0.5", None, True])
def test_query_response_invalid_confidence_score(bad_score):
    problems = contracts.validate_query_response(
        valid_query_response(confidence_score=bad_score)
    )
    assert any("confidence_score" in p for p in problems)


def test_query_response_boundary_scores_accepted():
    assert contracts.validate_query_response(valid_query_response(confidence_score=0.0)) == []
    assert contracts.validate_query_response(valid_query_response(confidence_score=1.0)) == []
    assert contracts.validate_query_response(valid_query_response(confidence_score=0.0,
                                                                 confidence="LOW")) == []


def test_abstention_response_consistency():
    good = {
        "id": "req-1", "answer": "Safe fallback text.",
        "citations": [], "confidence": "LOW", "confidence_score": 0.0,
        "abstention": True, "abstention_reason": "insufficient evidence",
        "escalation_available": False, "disclaimer": "Information, not legal advice.",
    }
    assert contracts.validate_query_response(good) == []

    missing_reason = dict(good, abstention_reason=None)
    assert any("abstention_reason" in p
               for p in contracts.validate_query_response(missing_reason))

    with_citations = dict(good, citations=[valid_query_response()["citations"][0]])
    assert any("citations" in p for p in contracts.validate_query_response(with_citations))

    not_abstained_with_reason = dict(valid_query_response(), abstention_reason="why")
    assert any("abstention_reason" in p
               for p in contracts.validate_query_response(not_abstained_with_reason))


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", list(contracts.CITATION_FIELDS))
def test_citation_missing_field_detected(field):
    citation = valid_query_response()["citations"][0]
    if field in ("section", "url", "effective_date"):
        citation[field] = None  # nullable fields stay valid when null
        assert contracts.validate_citation(citation) == []
        del citation[field]     # absent nullable fields are tolerated too
        assert contracts.validate_citation(citation) == []
    else:
        del citation[field]
        assert contracts.validate_citation(citation) != []


@pytest.mark.parametrize("bad_url", [
    "ftp://example.com/x", "www.indiacode.nic.in", "not-a-url", "", 5,
])
def test_malformed_citation_url(bad_url):
    citation = valid_query_response()["citations"][0]
    citation["url"] = bad_url
    problems = contracts.validate_citation(citation)
    assert any("url" in p for p in problems), bad_url


def test_malformed_citation_empty_required_field():
    citation = valid_query_response()["citations"][0]
    citation["excerpt"] = "   "
    assert contracts.validate_citation(citation) != []
    citation["source_name"] = ""
    assert contracts.validate_citation(citation) != []


def test_citation_not_a_dict_and_duplicate_ids():
    assert contracts.validate_citation("Section 3(p)") != []
    duplicate = valid_query_response()["citations"][0]
    problems = contracts.validate_citation_list([duplicate, dict(duplicate)])
    assert any("duplicate" in p for p in problems)


# ---------------------------------------------------------------------------
# ClassificationResult
# ---------------------------------------------------------------------------


def valid_classification_result(**overrides):
    result = {
        "formulation_class": "Classical",
        "description": "Reproduced unchanged from a First-Schedule text.",
        "relevant_regimes": ["Drugs and Cosmetics Act, 1940 (ASU drugs)"],
        "tkdl_pointer": "TKDL pointer — tkdl.res.in (restricted access).",
        "confidence": "HIGH",
        "needs_clarification": False,
        "clarification_prompt": None,
    }
    result.update(overrides)
    return result


def test_valid_classification_result_passes():
    assert contracts.validate_classification_result(valid_classification_result()) == []


def test_classification_result_missing_fields():
    payload = valid_classification_result()
    del payload["formulation_class"]
    assert contracts.validate_classification_result(payload) != []
    assert contracts.validate_classification_result({}) != []


@pytest.mark.parametrize("bad_class", [
    "classical", "Ayurveda Aahar", "Patent", "", None, 9,
])
def test_classification_result_invalid_class(bad_class):
    problems = contracts.validate_classification_result(
        valid_classification_result(formulation_class=bad_class)
    )
    assert any("formulation_class" in p for p in problems)


def test_classification_result_wrong_types_and_enum():
    problems = contracts.validate_classification_result(
        valid_classification_result(relevant_regimes="D&C Act")
    )
    assert any("relevant_regimes" in p for p in problems)
    problems = contracts.validate_classification_result(
        valid_classification_result(confidence="high")
    )
    assert any("confidence" in p for p in problems)
    problems = contracts.validate_classification_result(
        valid_classification_result(needs_clarification="yes")
    )
    assert any("needs_clarification" in p for p in problems)
    problems = contracts.validate_classification_result(
        valid_classification_result(confidence_score=1.2)
    )
    assert any("confidence_score" in p for p in problems)


def test_classification_result_clarification_consistency():
    problems = contracts.validate_classification_result(
        valid_classification_result(needs_clarification=True, clarification_prompt=None)
    )
    assert any("clarification_prompt" in p for p in problems)
    problems = contracts.validate_classification_result(
        valid_classification_result(needs_clarification=False,
                                    clarification_prompt="please clarify")
    )
    assert any("clarification_prompt" in p for p in problems)
    ok = valid_classification_result(
        needs_clarification=True, clarification_prompt="Which track applies?",
        confidence="LOW",
    )
    assert contracts.validate_classification_result(ok) == []


def test_classification_result_additive_extras_tolerated():
    # M2's real Phase-2 extras must not break the integration validator.
    payload = valid_classification_result(
        confidence_score=0.95, jurisdiction="India", language="en",
        category_labels={"en": "Classical", "hi": "क्लासिकल"},
        suggested_questions=[], reasoning=["trace"],
    )
    assert contracts.validate_classification_result(payload) == []


# ---------------------------------------------------------------------------
# RAG Result (internal, M3/M4/M5-shaped)
# ---------------------------------------------------------------------------


def valid_rag_result(**overrides):
    result = {
        "answer": "Grounded guidance with citations.",
        "citations": [{
            "id": "IN-001", "source_name": "Patents Act, 1970", "source_type": "statute",
            "section": "Section 3(p)", "excerpt": "Stored evidence excerpt.",
            "url": "https://www.indiacode.nic.in", "effective_date": "1970-09-21",
        }],
        "confidence": "HIGH",
        "confidence_score": 0.9,
        "abstention": False,
        "abstention_reason": None,
        "status": "ok",
    }
    result.update(overrides)
    return result


def test_valid_rag_result_all_three_statuses():
    assert contracts.validate_rag_result(valid_rag_result()) == []
    abstained = {
        "answer": "I cannot answer this from the verified sources.",
        "citations": [], "confidence": "LOW", "confidence_score": 0.0,
        "abstention": True, "abstention_reason": "insufficient_evidence: nothing matches",
        "status": "abstained",
    }
    assert contracts.validate_rag_result(abstained) == []
    processing_error = {
        "answer": "A temporary processing error occurred. Please retry.",
        "citations": [], "confidence": "LOW", "confidence_score": 0.0,
        "abstention": False, "abstention_reason": None,
        "status": "processing_error",
    }
    assert contracts.validate_rag_result(processing_error) == []


@pytest.mark.parametrize("bad_status", ["OK", "Ok", "error", "abstain", "failed", None, 1])
def test_rag_result_invalid_status(bad_status):
    problems = contracts.validate_rag_result(valid_rag_result(status=bad_status))
    assert any("status" in p for p in problems)


def test_rag_result_status_semantics_enforced():
    # ok must not look like an abstention and must carry citations
    problems = contracts.validate_rag_result(valid_rag_result(citations=[]))
    assert any("citation" in p for p in problems)
    problems = contracts.validate_rag_result(
        valid_rag_result(abstention=True, abstention_reason="unsure")
    )
    assert any("abstention" in p for p in problems)

    # abstained must not carry citations
    problems = contracts.validate_rag_result(
        valid_rag_result(status="abstained", abstention=True,
                         abstention_reason="why", citations=valid_rag_result()["citations"])
    )
    assert any("citations" in p for p in problems)

    # processing_error is NOT an abstention (detects M5's current shape — F-04)
    problems = contracts.validate_rag_result(
        valid_rag_result(status="processing_error", abstention=True,
                         abstention_reason="provider failed", answer="")
    )
    assert any("processing_error" in p or "abstention" in p for p in problems)


def test_rag_result_structure_vs_semantics_split():
    # structurally broken (missing status entirely) → structure problems
    broken = valid_rag_result()
    del broken["status"]
    assert contracts.validate_rag_result_structure(broken) != []
    # structurally fine but semantically unsafe (tampered citation URL)
    unsafe = valid_rag_result()
    unsafe["citations"][0]["url"] = "https://invented-example.invalid/fake"
    assert contracts.validate_rag_result_structure(unsafe) == []
    assert contracts.validate_rag_result_semantics(unsafe) == []  # shape-level only
    # semantic problems surface through the full validation
    assert contracts.validate_rag_result(unsafe) == []  # URL authority is member-side!
    # ...while a fabricated-citation *excerpt* type error is structural
    typebroken = valid_rag_result()
    typebroken["citations"][0]["excerpt"] = 42
    assert contracts.validate_rag_result(typebroken) != []


def test_rag_result_confidence_values():
    problems = contracts.validate_rag_result(valid_rag_result(confidence="Very high"))
    assert any("confidence" in p for p in problems)
    problems = contracts.validate_rag_result(valid_rag_result(confidence_score=7))
    assert any("confidence_score" in p for p in problems)


def test_rag_result_tkdl_pointer_additive_field():
    # M4's additive tkdl_pointer is accepted when it is a legitimate pointer
    result = valid_rag_result(tkdl_pointer="TKDL pointer — see tkdl.res.in (restricted).")
    assert contracts.validate_rag_result(result) == []
    # ...and rejected when it is a non-string
    result = valid_rag_result(tkdl_pointer=42)
    assert contracts.validate_rag_result(result) != []


# ---------------------------------------------------------------------------
# ErrorResponse + status mapping
# ---------------------------------------------------------------------------


def test_error_response_valid_codes_and_mapping():
    for code, status in (
        ("VALIDATION_ERROR", 400),
        ("PROCESSING_ERROR", 502),
        ("SERVICE_UNAVAILABLE", 503),
    ):
        body = contracts.error_response(code, "message")
        assert contracts.validate_error_response(body) == []
        assert contracts.http_status_for(code) == status


def test_error_response_invalid_code():
    problems = contracts.validate_error_response(
        contracts.error_response("BAD_REQUEST", "nope")
    )
    assert any("error" in p for p in problems)


def test_error_response_missing_message():
    assert contracts.validate_error_response({"error": "VALIDATION_ERROR"}) != []
    assert contracts.validate_error_response({"message": "no code"}) != []


def test_valid_abstention_is_http_200_not_an_error():
    """Plan.md §7: a valid abstention is HTTP 200, never an ErrorResponse."""
    abstained = {
        "answer": "Safe fallback text.",
        "citations": [], "confidence": "LOW", "confidence_score": 0.0,
        "abstention": True, "abstention_reason": "insufficient evidence",
        "status": "abstained",
    }
    assert contracts.validate_rag_result(abstained) == []
    # and it is not an ErrorResponse:
    assert contracts.validate_error_response(abstained) != []
