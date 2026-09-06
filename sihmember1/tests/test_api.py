"""API-layer tests: contract endpoints, error mapping, HTTP-200 abstention."""
import pytest
from fastapi.testclient import TestClient

from m1.api import app
from m1.config import Config, reset_config, set_config


@pytest.fixture()
def client():
    set_config(Config())  # hermetic: extractive generator, specialists not wired
    with TestClient(app) as c:
        yield c
    reset_config()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "m1-assistant"
    assert body["generator_mode"] == "extractive"


def test_query_returns_full_contract(client):
    resp = client.post(
        "/api/query",
        json={
            "id": "api-1",
            "query": "Can I patent a classical Ayurvedic formulation from an authoritative text?",
            "language": "en",
            "jurisdiction": "India",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    for field in (
        "id",
        "answer",
        "citations",
        "confidence",
        "confidence_score",
        "abstention",
        "abstention_reason",
        "escalation_available",
        "disclaimer",
    ):
        assert field in body, f"missing contract field {field}"
    assert body["id"] == "api-1"
    assert body["answer"].strip()
    assert body["citations"]
    assert body["disclaimer"].strip()


def test_query_validation_error_is_400(client):
    resp = client.post(
        "/api/query",
        json={"id": "api-2", "query": "x", "language": "fr"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"] == "VALIDATION_ERROR"


def test_query_missing_fields_is_400(client):
    resp = client.post("/api/query", json={"id": "api-3"})
    assert resp.status_code == 400
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_query_empty_body_is_400(client):
    resp = client.post("/api/query", json={})
    assert resp.status_code == 400
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_abstention_is_http_200_not_error(client):
    resp = client.post(
        "/api/query",
        json={
            "id": "api-4",
            "query": "What is the airspeed of an unladen swallow?",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["abstention"] is True
    assert body["abstention_reason"]
    assert body["citations"] == []


def test_international_query_retrieves_international_evidence(client):
    resp = client.post(
        "/api/query",
        json={
            "id": "api-5",
            "query": "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?",
            "jurisdiction": "International",
        },
    )
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()["citations"]]
    assert "intl-pct" in ids


def test_hindi_query_accepted(client):
    resp = client.post(
        "/api/query",
        json={
            "id": "api-6",
            "query": "पारंपरिक ज्ञान पर पेटेंट कर सकते हैं क्या?",
            "language": "hi",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].strip()
    assert "कानूनी सलाह" in body["disclaimer"]
    assert "in-patents-act-3p" in {c["id"] for c in body["citations"]}


# --- Phase 3 edge cases -------------------------------------------------------


def test_missing_jurisdiction_defaults_to_india(client):
    """A request without the jurisdiction toggle falls back to the safe
    domestic default and behaves as India (in-* evidence only)."""
    resp = client.post(
        "/api/query",
        json={
            "id": "api-7",
            "query": "How do I file a patent application for my Ayurvedic product?",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["citations"]
    assert all(c["id"].startswith("in-") for c in body["citations"])


def test_empty_query_is_400(client):
    resp = client.post("/api/query", json={"id": "api-8", "query": ""})
    assert resp.status_code == 400
    assert resp.json()["error"] == "VALIDATION_ERROR"


def test_unsupported_language_is_400(client):
    resp = client.post(
        "/api/query",
        json={"id": "api-9", "query": "vanakkam", "language": "ta"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"] == "VALIDATION_ERROR"
