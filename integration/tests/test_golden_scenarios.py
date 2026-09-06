"""Task 4 — the five golden demo scenarios as executable integration tests.

Executed against STUBBED domain responses (Phase 1): the stubs replicate each
member's actual result shape and encode the documented golden-scenario
behavior, so the machinery — routing, dispatch, validation, assembly,
abstention — is verified end-to-end. In Phase 2 the same fixtures in
fixtures/golden_scenarios.json run against the real wired specialists.

Each scenario also runs an out-of-corpus variant that MUST abstain safely
(HTTP 200, abstention=true, no citations, no fabricated legal content).
"""
import json
import re
from pathlib import Path

import pytest

from integration import contracts
from integration.assembler import Assembler
from integration.stubs import default_stub_specialists, stub_route

FIXTURES = json.loads(
    (Path(__file__).resolve().parent.parent / "fixtures" / "golden_scenarios.json").read_text(
        encoding="utf-8"
    )
)
SCENARIOS = {s["id"]: s for s in FIXTURES["scenarios"]}

# Real official portals (PS.md dataset list) — the only URLs allowed in
# fallback/abstention texts.
OFFICIAL_URL_HOSTS = (
    "ipindia.gov.in", "indiacode.nic.in", "wipo.int", "tkdl.res.in",
    "nbaindia.org", "fssai.gov.in", "cdsco.gov.in", "wto.org",
)
_STATUTE_PATTERN = re.compile(r"Section \d+|\bArticle \d+", re.IGNORECASE)


@pytest.fixture()
def assembler():
    return Assembler(router=stub_route, specialists=default_stub_specialists())


def query_for(scenario):
    return {
        "id": f"golden-{scenario['id']}",
        "query": scenario["query"],
        "language": scenario["language"],
        "jurisdiction": scenario["jurisdiction"],
        "history": [],
    }


def assert_no_fabricated_content(body):
    """An abstention must be a SAFE fallback: no citations, no statute/section
    or treaty-article assertions, and no URLs outside the official portals."""
    assert body["citations"] == []
    assert not _STATUTE_PATTERN.search(body["answer"]), body["answer"]
    for url in re.findall(r"https?://[^\s\)\]]+", body["answer"]):
        assert any(host in url for host in OFFICIAL_URL_HOSTS), url


# ---------------------------------------------------------------------------
# Scenario 1 — classical formulation patentability: Section 3(p) + TKDL
# ---------------------------------------------------------------------------


def test_scenario_1_classical_patent_section_3p_and_tkdl(assembler):
    scenario = SCENARIOS["S1"]
    outcome = assembler.handle_query(query_for(scenario))

    assert outcome.status_code == 200
    assert outcome.domain == scenario["expected_domain"] == "INDIA_IP"
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is False
    assert "3(p)" in body["answer"], "answer must invoke Section 3(p)"
    # TKDL pointer behavior: named in the answer text (M3 form) — or, once
    # M4 is wired in Phase 2, present via M4's tkdl_pointer field (F-05).
    assert "tkdl" in body["answer"].lower() and "tkdl.res.in" in body["answer"]
    assert len(body["citations"]) >= 1
    # India/International separation: a patent answer must never name the
    # trademark/design systems.
    assert "Madrid" not in body["answer"] and "Hague" not in body["answer"]


def test_scenario_1_out_of_corpus_abstains(assembler):
    scenario = SCENARIOS["S1"]
    request = query_for(scenario)
    request["query"] = scenario["out_of_corpus"]["query"]
    outcome = assembler.handle_query(request)

    assert outcome.status_code == 200  # valid abstention is HTTP 200
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is True and body["abstention_reason"]
    assert_no_fabricated_content(body)


# ---------------------------------------------------------------------------
# Scenario 2 — ABS route, NOT a patents question
# ---------------------------------------------------------------------------


def test_scenario_2_abs_route_not_patents(assembler):
    scenario = SCENARIOS["S2"]
    outcome = assembler.handle_query(query_for(scenario))

    assert outcome.status_code == 200
    assert outcome.domain == scenario["expected_domain"] == "ABS_TK"
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is False
    assert "Biological Diversity Act" in body["answer"]
    # NOT treated as a simple patents question: no Section 3(p) patentability
    # answer for a biological-resource access/commercialisation question.
    assert not _STATUTE_PATTERN.search(body["answer"].replace(
        "Biological Diversity Act, 2002", ""))
    assert len(body["citations"]) >= 1


def test_scenario_2_out_of_corpus_abstains(assembler):
    scenario = SCENARIOS["S2"]
    request = query_for(scenario)
    request["query"] = scenario["out_of_corpus"]["query"]
    outcome = assembler.handle_query(request)

    assert outcome.status_code == 200
    body = outcome.body
    assert body["abstention"] is True and body["abstention_reason"]
    assert_no_fabricated_content(body)


# ---------------------------------------------------------------------------
# Scenario 3 — classification: food (Ayurveda-Aahar) vs classical medicine
# ---------------------------------------------------------------------------


def test_scenario_3_query_flow_points_to_guided_classification(assembler):
    scenario = SCENARIOS["S3"]
    outcome = assembler.handle_query(query_for(scenario))

    assert outcome.domain == "CLASSIFICATION"
    assert outcome.status_code == 200
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    # M2 is answers-driven: a free-text query cannot honestly be classified —
    # the flow abstains toward the guided classify flow instead of guessing.
    assert body["abstention"] is True
    assert "classify" in body["abstention_reason"].lower()


def test_scenario_3_classifier_discriminates_food_vs_medicine(assembler):
    scenario = SCENARIOS["S3"]
    food = assembler.handle_classify(
        {"answers": scenario["expect"]["classify_food"]["answers"],
         "jurisdiction": "India", "language": "en"}
    )
    medicine = assembler.handle_classify(
        {"answers": scenario["expect"]["classify_medicine"]["answers"],
         "jurisdiction": "India", "language": "en"}
    )

    assert food.status_code == 200 and medicine.status_code == 200
    assert contracts.validate_classification_result(food.body) == []
    assert contracts.validate_classification_result(medicine.body) == []

    assert food.body["formulation_class"] == "Ayurveda-Aahar"
    assert medicine.body["formulation_class"] == "Classical"
    # The classifier actually discriminates: different categories AND regimes.
    assert food.body["relevant_regimes"] != medicine.body["relevant_regimes"]
    assert any("FSSAI" in regime for regime in food.body["relevant_regimes"])
    assert any("Drugs and Cosmetics" in regime for regime in medicine.body["relevant_regimes"])
    # Classical carries the TKDL pointer; the food category does not.
    assert food.body["tkdl_pointer"] is None
    assert medicine.body["tkdl_pointer"] and "tkdl.res.in" in medicine.body["tkdl_pointer"]


def test_scenario_3_out_of_corpus_answers_yield_uncertain(assembler):
    scenario = SCENARIOS["S3"]
    outcome = assembler.handle_classify(
        {"answers": scenario["out_of_corpus"]["answers"],
         "jurisdiction": "India", "language": "en"}
    )

    assert outcome.status_code == 200
    body = outcome.body
    assert contracts.validate_classification_result(body) == []
    assert body["formulation_class"] == "Uncertain"
    assert body["needs_clarification"] is True
    assert body["clarification_prompt"]


# ---------------------------------------------------------------------------
# Scenario 4 — GI registration (India, M3)
# ---------------------------------------------------------------------------


def test_scenario_4_gi_registration_india(assembler):
    scenario = SCENARIOS["S4"]
    outcome = assembler.handle_query(query_for(scenario))

    assert outcome.status_code == 200
    assert outcome.domain == "INDIA_IP"
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is False
    assert "Geographical Indication" in body["answer"]
    assert len(body["citations"]) >= 1


def test_scenario_4_out_of_corpus_abstains(assembler):
    scenario = SCENARIOS["S4"]
    request = query_for(scenario)
    request["query"] = scenario["out_of_corpus"]["query"]
    outcome = assembler.handle_query(request)

    assert outcome.status_code == 200
    body = outcome.body
    assert body["abstention"] is True
    assert_no_fabricated_content(body)


# ---------------------------------------------------------------------------
# Scenario 5 — international patent: PCT, NOT Madrid, NOT Hague
# ---------------------------------------------------------------------------


def test_scenario_5_international_patent_pct_only(assembler):
    scenario = SCENARIOS["S5"]
    outcome = assembler.handle_query(query_for(scenario))

    assert outcome.status_code == 200
    assert outcome.domain == "INTERNATIONAL_IP"
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is False
    assert "PCT" in body["answer"]
    assert "Madrid" not in body["answer"], "Madrid is trademarks, not patents"
    assert "Hague" not in body["answer"], "Hague is industrial designs, not patents"
    assert len(body["citations"]) >= 1


def test_scenario_5_out_of_corpus_abstains(assembler):
    scenario = SCENARIOS["S5"]
    request = query_for(scenario)
    request["query"] = scenario["out_of_corpus"]["query"]
    outcome = assembler.handle_query(request)

    assert outcome.status_code == 200
    body = outcome.body
    assert body["abstention"] is True
    assert_no_fabricated_content(body)


# ---------------------------------------------------------------------------
# Every golden response echoes the request id (ID compatibility)
# ---------------------------------------------------------------------------


def test_all_golden_responses_echo_request_id(assembler):
    for scenario in SCENARIOS.values():
        outcome = assembler.handle_query(query_for(scenario))
        if isinstance(outcome.body, dict) and "answer" in outcome.body:
            assert outcome.body["id"] == f"golden-{scenario['id']}"
