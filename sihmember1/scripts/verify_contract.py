"""Verify M1's actual interface shapes against the contract in MEMBER_1.md §4
(= Plan.md §7), plus the public API surface. Prints PASS/FAIL per check and a
deviations list for M6. Exits non-zero on any hard mismatch.

Usage:  python scripts/verify_contract.py
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.routing import APIRoute  # noqa: E402

from m1.api import app  # noqa: E402
from m1.assistant import handle_query  # noqa: E402
from m1.config import Config  # noqa: E402
from m1.models import Citation, FormulationClass, QueryRequest, QueryResponse  # noqa: E402

results = []
deviations = []

GOLDEN_1 = (
    "Can I patent a classical Ayurvedic formulation from an authoritative text?"
)


def check(name, fn):
    try:
        results.append((name, "PASS", fn()))
    except Exception as exc:
        results.append((name, "FAIL", f"{type(exc).__name__}: {exc}"))


# Contract field sets (MEMBER_1.md §4 / Plan.md §7)
REQUEST_FIELDS = {"id", "query", "language", "jurisdiction", "formulation_class", "history"}
RESPONSE_FIELDS = {
    "id", "answer", "citations", "confidence", "confidence_score",
    "abstention", "abstention_reason", "escalation_available", "disclaimer",
}
CITATION_FIELDS = {"id", "source_name", "source_type", "section", "excerpt", "url", "effective_date"}
MESSAGE_FIELDS = {"role", "content"}
LANGUAGES = {"en", "hi"}
JURISDICTIONS = {"India", "International"}
CLASSES = {"Classical", "Proprietary", "Phytopharmaceutical", "Ayurveda-Aahar", "Cosmetic", "New Drug", "Uncertain"}
CONFIDENCE = {"HIGH", "MEDIUM", "LOW"}


def fields_of(model):
    return set(model.model_fields.keys())


def check_request_shape():
    got = fields_of(QueryRequest)
    assert got == REQUEST_FIELDS, f"field mismatch: extra={got - REQUEST_FIELDS}, missing={REQUEST_FIELDS - got}"
    annotations = {k: str(v.outer_type_ if hasattr(v, "outer_type_") else v.annotation)
                   for k, v in QueryRequest.model_fields.items()}
    assert annotations["language"].startswith("typing.Literal"), annotations["language"]
    assert annotations["jurisdiction"].startswith("typing.Literal"), annotations["jurisdiction"]
    return f"QueryRequest fields match exactly: {sorted(got)}"


def check_response_shape():
    got = fields_of(QueryResponse)
    assert got == RESPONSE_FIELDS, f"field mismatch: extra={got - RESPONSE_FIELDS}, missing={RESPONSE_FIELDS - got}"
    return f"QueryResponse fields match exactly: {sorted(got)}"


def check_citation_shape():
    got = fields_of(Citation)
    assert got == CITATION_FIELDS, f"field mismatch: extra={got - CITATION_FIELDS}, missing={CITATION_FIELDS - got}"
    return f"Citation fields match exactly: {sorted(got)}"


def check_message_shape():
    from m1.models import Message
    got = fields_of(Message)
    assert got == MESSAGE_FIELDS, f"field mismatch: {got}"
    return "Message fields match: role(user|assistant), content"


def check_enums():
    assert {fc.value for fc in FormulationClass} == CLASSES
    req = QueryRequest(id="c1", query="x", language="hi", jurisdiction="International")
    assert req.language in LANGUAGES and req.jurisdiction in JURISDICTIONS
    return "language en|hi; jurisdiction India|International; all 7 FormulationClass values present"


def check_live_response_contract():
    result = handle_query(QueryRequest(id="c-live", query=GOLDEN_1, jurisdiction="India"), Config())
    r = result.response.model_dump()
    assert set(r.keys()) == RESPONSE_FIELDS
    assert r["id"] == "c-live"
    assert isinstance(r["answer"], str) and r["answer"].strip()
    assert r["confidence"] in CONFIDENCE
    assert isinstance(r["confidence_score"], float) and 0.0 <= r["confidence_score"] <= 1.0
    assert isinstance(r["abstention"], bool)
    assert r["abstention_reason"] is None and r["abstention"] is False
    assert isinstance(r["escalation_available"], bool)
    assert isinstance(r["disclaimer"], str) and r["disclaimer"].strip()
    for c in r["citations"]:
        assert set(c.keys()) == CITATION_FIELDS
    if r["escalation_available"] is False:
        deviations.append(
            "escalation_available is always False in the standalone build — the "
            "human IP-facilitator path is not part of M1's three phases"
        )
    return "live QueryResponse serialises exactly to the contract shape"


def check_abstained_response_contract():
    r = handle_query(
        QueryRequest(id="c-abs", query="quantum chromodynamics strawberry spaceship"),
        Config(),
    ).response.model_dump()
    assert set(r.keys()) == RESPONSE_FIELDS
    assert r["abstention"] is True and isinstance(r["abstention_reason"], str) and r["abstention_reason"]
    assert r["citations"] == [] and r["confidence"] == "LOW"
    return "abstained response is contract-shaped with reason set (HTTP 200, not an error)"


def check_api_surface():
    routes = {f"{sorted(r.methods - {'HEAD', 'OPTIONS'})} {r.path}": r for r in app.routes
              if isinstance(r, APIRoute)}
    assert "['POST'] /api/query" in routes, sorted(routes)
    assert "['GET'] /api/health" in routes, sorted(routes)
    return "public API exposes POST /api/query and GET /api/health"


def check_implementation_notes():
    deviations.append(
        "jurisdiction defaults to 'India' when the toggle is omitted (safe "
        "domestic default); any other value is rejected with VALIDATION_ERROR"
    )
    deviations.append(
        "internal RAG 'status' (ok/abstained, Plan.md §7) is carried on the "
        "AssistantResult wrapper, not on QueryResponse — the HTTP body matches "
        "the QueryResponse contract exactly"
    )
    deviations.append(
        "history is capped at 20 messages and Message.role is restricted to "
        "user|assistant (system messages rejected)"
    )
    return "implementation notes collected for M6"


check("QueryRequest matches the contract shape", check_request_shape)
check("QueryResponse matches the contract shape", check_response_shape)
check("Citation matches the contract shape", check_citation_shape)
check("Message matches the contract shape", check_message_shape)
check("Enum values match the contract", check_enums)
check("Live response serialises to the contract", check_live_response_contract)
check("Abstained response serialises to the contract", check_abstained_response_contract)
check("Public API surface (POST /api/query, GET /api/health)", check_api_surface)
check("Implementation notes for M6 collected", check_implementation_notes)

width = max(len(n) for n, _, _ in results)
print("=" * 100)
print("INTEGRATION CONTRACT VERIFICATION — Member 1 (IP-SAKTI Sahayak) vs MEMBER_1.md §4 / Plan.md §7")
print("=" * 100)
all_pass = True
for name, verdict, detail in results:
    all_pass &= verdict == "PASS"
    print(f"[{verdict}] {name.ljust(width)}  —  {detail}")
print("-" * 100)
print(f"Deviations/notes for M6 ({len(deviations)}):")
for i, d in enumerate(deviations, 1):
    print(f"  {i}. {d}")
print("=" * 100)
print("CONTRACT VERIFICATION:", "PASS" if all_pass else "FAIL")
sys.exit(0 if all_pass else 1)
