"""Contract-model validation tests (QueryRequest / Message / FormulationClass)."""
import pytest
from pydantic import ValidationError

from m1.models import FormulationClass, QueryRequest


def valid_request(**overrides):
    data = dict(id="q-1", query="Can I patent a classical Ayurvedic formulation?")
    data.update(overrides)
    return data


def test_valid_request_defaults():
    r = QueryRequest(**valid_request())
    assert r.language == "en"
    assert r.jurisdiction == "India"
    assert r.formulation_class is None
    assert r.history == []


def test_accepts_full_contract():
    r = QueryRequest(
        **valid_request(
            language="hi",
            jurisdiction="International",
            formulation_class="Classical",
            history=[{"role": "user", "content": "नमस्ते"}],
        )
    )
    assert r.language == "hi"
    assert r.jurisdiction == "International"
    assert r.formulation_class is FormulationClass.CLASSICAL
    assert r.history[0].role == "user"


@pytest.mark.parametrize(
    "field,value",
    [
        ("language", "fr"),
        ("language", ""),
        ("jurisdiction", "USA"),
        ("jurisdiction", "international"),
        ("formulation_class", "Beverage"),
    ],
)
def test_invalid_enum_values_rejected(field, value):
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(**{field: value}))


def test_empty_query_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(query="   "))


def test_missing_id_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(**{"query": "some question"})


def test_blank_id_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(id="   "))


def test_query_too_long_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(query="x" * 2001))


def test_history_bad_role_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(history=[{"role": "system", "content": "hi"}]))


def test_history_blank_content_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(history=[{"role": "user", "content": "  "}]))


def test_all_formulation_classes_accepted():
    for fc in FormulationClass:
        r = QueryRequest(**valid_request(formulation_class=fc.value))
        assert r.formulation_class is fc


# --- Phase 3 edge cases -------------------------------------------------------


def test_empty_query_string_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(query=""))


@pytest.mark.parametrize("lang", ["ta", "de", "en-IN", "EN", "HI"])
def test_unsupported_languages_rejected(lang):
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(language=lang))


def test_empty_jurisdiction_string_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(jurisdiction=""))


def test_history_over_twenty_messages_rejected():
    big_history = [{"role": "user", "content": f"turn {i}"} for i in range(21)]
    with pytest.raises(ValidationError):
        QueryRequest(**valid_request(history=big_history))


def test_history_twenty_messages_accepted():
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"turn {i}"}
        for i in range(20)
    ]
    r = QueryRequest(**valid_request(history=history))
    assert len(r.history) == 20
