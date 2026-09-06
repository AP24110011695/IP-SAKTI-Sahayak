"""Phase 2 — the five golden demo scenarios through the REAL integrated app.

Runs each Plan.md §13 scenario over HTTP against the wired application
(real M1 routing + real M2/M3/M4/M5), plus one out-of-corpus variant per
scenario, which must abstain safely (HTTP 200, abstention=true, no
citations, no fabricated content).

All offline: every member's unconfigured generation mode is deterministic
(M3 evidence-only template, M4 offline stand-in, M5 deterministic client).
"""
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from integration import contracts
from integration.adapters import wire_m1

FIXTURES = json.loads(
    (Path(__file__).resolve().parent.parent / "fixtures" / "golden_scenarios.json").read_text(
        encoding="utf-8"
    )
)
SCENARIOS = {s["id"]: s for s in FIXTURES["scenarios"]}

_STATUTE_PATTERN = re.compile(r"Section \d+|\bArticle \d+", re.IGNORECASE)
_OFFICIAL_HOSTS = (
    "ipindia.gov.in", "indiacode.nic.in", "wipo.int", "tkdl.res.in",
    "nbaindia.org", "fssai.gov.in", "cdsco.gov.in", "wto.org", "csir.res.in",
)


@pytest.fixture(scope="module")
def client():
    wire_m1()
    from integration.adapters import app

    return TestClient(app)


def query(scenario, key="query", qid=None):
    return {
        "id": qid or f"golden-real-{scenario['id']}",
        "query": scenario[key] if key == "query" else scenario[key],
        "language": scenario["language"],
        "jurisdiction": scenario["jurisdiction"],
        "history": [],
    }


def assert_contract_ok(body):
    assert contracts.validate_query_response(body) == []


def assert_safe_abstention(body):
    assert_contract_ok(body)
    assert body["abstention"] is True and body["abstention_reason"]
    assert body["citations"] == []
    assert not _STATUTE_PATTERN.search(body["answer"]), body["answer"]
    for url in re.findall(r"https?://[^\s\)\]]+", body["answer"]):
        assert any(host in url for host in _OFFICIAL_HOSTS), url


# ---------------------------------------------------------------------------
# Golden 1 — classical formulation patentability: Section 3(p) + TKDL (M3)
# ---------------------------------------------------------------------------


def test_golden_1_classical_patent_section_3p_tkdl(client):
    scenario = SCENARIOS["S1"]
    response = client.post("/api/query", json=query(scenario))
    assert response.status_code == 200
    body = response.json()
    assert_contract_ok(body)
    assert body["abstention"] is False
    assert "3(p)" in body["answer"]
    assert "tkdl.res.in" in body["answer"]  # TKDL pointer behaviour preserved
    assert len(body["citations"]) >= 1
    assert body["confidence"] in ("HIGH", "MEDIUM")
    # India/International separation: never the trademark/design systems
    assert "Madrid" not in body["answer"] and "Hague" not in body["answer"]


def test_golden_1_out_of_corpus_abstains(client):
    scenario = SCENARIOS["S1"]
    request = query(scenario, key="query", qid="golden-real-S1-ooc")
    request["query"] = scenario["out_of_corpus"]["query"]
    response = client.post("/api/query", json=request)
    assert response.status_code == 200
    assert_safe_abstention(response.json())


# ---------------------------------------------------------------------------
# Golden 2 — ABS route via M4 (F-03 regression: M1 must route it to M4)
# ---------------------------------------------------------------------------


def test_golden_2_abs_question_answered_by_m4_not_as_patents(client):
    scenario = SCENARIOS["S2"]
    response = client.post("/api/query", json=query(scenario))
    assert response.status_code == 200
    body = response.json()
    assert_contract_ok(body)
    assert body["abstention"] is False
    assert "Biological Diversity Act" in body["answer"]
    assert len(body["citations"]) >= 1
    # NOT patent-only guidance: BD Act sections are expected (prior
    # intimation etc.), but the patentability answer (Patents Act 3(p))
    # must not appear.
    assert "3(p)" not in body["answer"]
    assert "Patents Act" not in body["answer"]


def test_golden_2_out_of_corpus_fee_question_abstains(client):
    """M4's fee rule: the corpus holds no amounts, so the fee variant must
    abstain rather than invent figures (mirrors M4's own suite)."""
    scenario = SCENARIOS["S2"]
    request = query(scenario, qid="golden-real-S2-ooc")
    request["query"] = scenario["out_of_corpus"]["query"]
    response = client.post("/api/query", json=request)
    assert response.status_code == 200
    body = response.json()
    assert_safe_abstention(body)
    assert not re.search(r"[₹]\s*\d|\b\d+\s*(rupees|dollars)", body["answer"], re.I)


# ---------------------------------------------------------------------------
# Golden 3 — classification: food (Ayurveda-Aahar) vs classical medicine (M2)
# ---------------------------------------------------------------------------


def test_golden_3_classification_food_vs_medicine(client):
    scenario = SCENARIOS["S3"]
    expect = scenario["expect"]

    food = client.post("/api/classify", json={
        "answers": expect["classify_food"]["answers"],
        "jurisdiction": "India", "language": "en",
    })
    assert food.status_code == 200
    food_body = food.json()
    assert contracts.validate_classification_result(food_body) == []
    assert food_body["formulation_class"] == "Ayurveda-Aahar"

    medicine = client.post("/api/classify", json={
        "answers": expect["classify_medicine"]["answers"],
        "jurisdiction": "India", "language": "en",
    })
    assert medicine.status_code == 200
    medicine_body = medicine.json()
    assert medicine_body["formulation_class"] == "Classical"
    assert medicine_body["tkdl_pointer"] and "tkdl.res.in" in medicine_body["tkdl_pointer"]

    # the classifier discriminates: different classes AND different regimes
    assert food_body["relevant_regimes"] != medicine_body["relevant_regimes"]

    # and the free-text health-claim question reaches M1 and abstains toward
    # the guided flow rather than being guessed
    routed = client.post("/api/query", json=query(scenario, qid="golden-real-S3-flow"))
    assert routed.status_code == 200
    flow_body = routed.json()
    assert_contract_ok(flow_body)
    assert flow_body["abstention"] is True
    assert "classify" in flow_body["abstention_reason"].lower()


def test_golden_3_out_of_corpus_answers_yield_uncertain(client):
    scenario = SCENARIOS["S3"]
    response = client.post("/api/classify", json={
        "answers": scenario["out_of_corpus"]["answers"],
        "jurisdiction": "India", "language": "en",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["formulation_class"] == "Uncertain"
    assert body["needs_clarification"] is True and body["clarification_prompt"]


# ---------------------------------------------------------------------------
# Golden 4 — GI registration (M3)
# ---------------------------------------------------------------------------


def test_golden_4_gi_registration_india(client):
    scenario = SCENARIOS["S4"]
    response = client.post("/api/query", json=query(scenario))
    assert response.status_code == 200
    body = response.json()
    assert_contract_ok(body)
    assert body["abstention"] is False
    assert "Geographical Indication" in body["answer"]
    assert len(body["citations"]) >= 1


def test_golden_4_out_of_corpus_abstains(client):
    scenario = SCENARIOS["S4"]
    request = query(scenario, qid="golden-real-S4-ooc")
    request["query"] = scenario["out_of_corpus"]["query"]
    response = client.post("/api/query", json=request)
    assert response.status_code == 200
    assert_safe_abstention(response.json())


# ---------------------------------------------------------------------------
# Golden 5 — international patent: PCT, NOT Madrid, NOT Hague (M5)
# ---------------------------------------------------------------------------


def test_golden_5_international_patent_pct_only(client):
    scenario = SCENARIOS["S5"]
    response = client.post("/api/query", json=query(scenario))
    assert response.status_code == 200
    body = response.json()
    assert_contract_ok(body)
    assert body["abstention"] is False
    assert "PCT" in body["answer"]
    assert "Madrid" not in body["answer"] and "Hague" not in body["answer"]
    assert len(body["citations"]) >= 1
    # no India procedure blended into the international answer
    assert not re.search(r"Section 3\(p\)|Patents Act, 1970", body["answer"])


def test_golden_5_out_of_corpus_abstains(client):
    scenario = SCENARIOS["S5"]
    request = query(scenario, qid="golden-real-S5-ooc")
    request["query"] = scenario["out_of_corpus"]["query"]
    response = client.post("/api/query", json=request)
    assert response.status_code == 200
    assert_safe_abstention(response.json())
