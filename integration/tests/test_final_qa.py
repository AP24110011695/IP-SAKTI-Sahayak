"""Phase 3 — Final QA test suite (MEMBER_6.md 17-point checklist).

Runs the complete integrated application (real M1 routing + real M2–M5) and
automates every checklist item that can be asserted offline, plus the Phase 2
watch items. All offline/deterministic: no LLM credentials exist in this
environment, so every member runs its own deterministic generation mode —
no live LLM call is faked anywhere.

Item map (checklist # → tests):
  1  startup               test_01_application_startup
  2  health                test_02_health
  3  classifier            test_03_classify_*
  4  English flow          test_04_english_flow
  5  Hindi flow            test_05_hindi_flow
  6  India flow            test_06_india_flow
  7  International flow    test_07_international_flow
  8  citations present     test_08_citations_present (part of the sweep)
  9  citation validity     test_09_citation_validity_full_sweep
 10  confidence            test_10_confidence_*
 11  abstention            test_11_abstention_*
 12  safe fallback         test_12_processing_errors_not_disguised
 13  ABS/TKDL              test_13_abs_tkdl_scenario
 14  Indian IP             test_14_indian_ip_scenario
 15  international mapping test_15_pct_madrid_hague_mapping
 16  golden scenarios      covered by test_golden_scenarios_real.py (re-run
                           in the same suite) + the citation sweep here
 17  invalid inputs        test_17_invalid_inputs
Watch items: test_w1_m5_weak_query_regressions, test_w2_disclaimer_rendering,
             test_w3_alias_compat, test_w4_m4_module_loading
"""
import re

import pytest
from fastapi.testclient import TestClient

from integration import contracts
from integration.adapters import load_members, wire_m1


@pytest.fixture(scope="module")
def members():
    return wire_m1()


@pytest.fixture(scope="module")
def client(members):
    from integration.adapters import app

    return TestClient(app)


@pytest.fixture(scope="module")
def handle(members):
    return members["m1"]["assistant"].handle_query


@pytest.fixture(scope="module")
def QueryRequest(members):
    return members["m1"]["models"].QueryRequest


def q(qid, query, language="en", jurisdiction="India"):
    return {"id": qid, "query": query, "language": language,
            "jurisdiction": jurisdiction, "history": []}


# ---------------------------------------------------------------------------
# 1. Application startup / 2. health
# ---------------------------------------------------------------------------


def test_01_application_startup(members):
    """The combined app imports and builds with no startup/import failures."""
    from integration.adapters import app, is_wired

    assert app is not None
    assert is_wired() is True
    assert app.routes, "FastAPI app has no routes"


def test_02_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["specialists_wired"] is True
    assert set(body["specialists"]) == {
        "INDIA_IP", "ABS_TK", "INTERNATIONAL_IP", "CLASSIFICATION"}
    assert body["generator_mode"] == "extractive"  # no LLM key: documented mode


# ---------------------------------------------------------------------------
# 3. Classifier: all six categories + Uncertain, real M2, clarification
# ---------------------------------------------------------------------------


ALL_CLASS_CASES = {
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


@pytest.mark.parametrize("expected,answers", sorted(ALL_CLASS_CASES.items()))
def test_03_classify_all_categories(client, expected, answers):
    response = client.post("/api/classify", json={
        "answers": answers, "jurisdiction": "India", "language": "en"})
    assert response.status_code == 200
    body = response.json()
    assert contracts.validate_classification_result(body) == []
    assert body["formulation_class"] == expected
    # the REAL M2 signature is visible: machine values, additive extras present
    assert body["confidence"] in ("HIGH", "MEDIUM", "LOW")
    assert "confidence_score" in body and "category_labels" in body


def test_03_classify_clarification_on_uncertain(client):
    body = client.post("/api/classify", json={
        "answers": {}, "jurisdiction": "India", "language": "en"}).json()
    assert body["formulation_class"] == "Uncertain"
    assert body["needs_clarification"] is True
    assert body["clarification_prompt"]
    ids = body.get("clarification_question_ids") or []
    assert ids, "Uncertain must name the blocking guided question(s)"


def test_03_classify_one_round_clarification_then_resolves(client):
    """M2's clarification behaviour through the endpoint: a partially
    answered food product is borderline (the new-indication cross-check is
    unanswered) and asks one targeted question; a fully answered set is
    clear-cut."""
    borderline = client.post("/api/classify", json={
        "answers": {"primary_purpose": "food_wellness", "food_exclusion": "none"}}).json()
    assert borderline["formulation_class"] == "Ayurveda-Aahar"
    assert borderline["needs_clarification"] is True  # M2's conservative cross-check
    assert borderline["clarification_prompt"]

    resolved = client.post("/api/classify", json={
        "answers": {"primary_purpose": "food_wellness", "food_exclusion": "none",
                    "new_indication": "no"}}).json()
    assert resolved["formulation_class"] == "Ayurveda-Aahar"
    assert resolved["needs_clarification"] is False
    assert resolved["clarification_prompt"] is None


# ---------------------------------------------------------------------------
# 4-7. Language / jurisdiction flows
# ---------------------------------------------------------------------------


def test_04_english_flow(handle, QueryRequest):
    result = handle(QueryRequest(
        id="qa-en", language="en", jurisdiction="India",
        query="Can I patent a classical Ayurvedic formulation from an authoritative text?"))
    assert result.status == "ok"
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    assert "3(p)" in body["answer"] and body["citations"]


def test_05_hindi_flow(client):
    """Supported Hindi scenario through the real integrated app."""
    response = client.post("/api/query", json=q(
        "qa-hi", "मैं अपने आयुर्वेदिक उत्पाद के लिए जीआई टैग कैसे पंजीकृत करूँ?",
        language="hi"))
    assert response.status_code == 200
    body = response.json()
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is False
    assert body["citations"]
    assert "कानूनी सलाह नहीं" in body["disclaimer"]
    assert re.search(r"[\u0900-\u097F]", body["answer"]), "answer should be Hindi"


def test_05_hindi_abs_signal_routes_to_m4(handle, QueryRequest):
    result = handle(QueryRequest(
        id="qa-hi-abs", language="hi", jurisdiction="India",
        query="पारंपरिक ज्ञान वाले फॉर्मूलेशन के लिए अनुमतियाँ क्या चाहिए?"))
    assert result.routing.domain.value == "ABS_TK"
    assert result.status in ("ok", "abstained")


def test_06_india_flow(handle, QueryRequest):
    """India questions land with the India/ABS specialists, never M5."""
    for query_text, expected_domain in (
        ("Can I patent a classical Ayurvedic formulation from an authoritative text?", "INDIA_IP"),
        ("I want to commercialise a formulation using a plant collected in India - what approvals do I need?", "ABS_TK"),
        ("How do I register a GI tag for an Ayurvedic product tied to a region?", "INDIA_IP"),
    ):
        result = handle(QueryRequest(
            id="qa-in", query=query_text, language="en", jurisdiction="India"))
        assert result.routing.domain.value == expected_domain, query_text
        assert result.routing.domain.value != "INTERNATIONAL_IP"


def test_07_international_flow_no_india_blending(handle, QueryRequest):
    result = handle(QueryRequest(
        id="qa-int", language="en", jurisdiction="International",
        query="I want to file a patent for a new Ayurvedic drug outside India - what route do I use?"))
    assert result.routing.domain.value == "INTERNATIONAL_IP"
    body = result.response.model_dump()
    assert "PCT" in body["answer"]
    # India procedure is not silently mixed into the international answer
    assert "Section 3(p)" not in body["answer"]
    assert "Patents Act, 1970" not in body["answer"]
    assert "Indian Patent Office" not in body["answer"]


def test_07_international_jurisdiction_answered_by_m5_only(handle, QueryRequest):
    for query_text in (
        "I want to register my Ayurvedic brand name internationally",
        "How can I protect my packaging as an industrial design internationally?",
    ):
        result = handle(QueryRequest(
            id="qa-int2", query=query_text, language="en", jurisdiction="International"))
        assert result.routing.domain.value == "INTERNATIONAL_IP"
        assert result.status == "ok"


# ---------------------------------------------------------------------------
# 8-9. Citations: presence + validity against real stored records (full sweep)
# ---------------------------------------------------------------------------


SWEEP_QUERIES = [
    ("golden-1", "Can I patent a classical Ayurvedic formulation from an authoritative text?", "India"),
    ("golden-2", "I want to commercialise a formulation using a plant collected in India - what approvals do I need?", "India"),
    ("golden-4", "How do I register a GI tag for an Ayurvedic product tied to a region?", "India"),
    ("golden-5", "I want to file a patent for a new Ayurvedic drug outside India - what route do I use?", "International"),
    ("trademark", "I want to register my Ayurvedic brand name internationally", "International"),
    ("design", "How can I protect my packaging as an industrial design internationally?", "International"),
]


def test_08_citations_present(handle, QueryRequest):
    for qid, query_text, jurisdiction in SWEEP_QUERIES:
        result = handle(QueryRequest(
            id=f"cite-{qid}", query=query_text, language="en", jurisdiction=jurisdiction))
        assert result.status == "ok", qid
        assert result.response.citations, f"no citations for {qid}"


def test_09_citation_validity_full_sweep(handle, QueryRequest, members):
    """Every citation in every supported answer maps byte-exact to a real
    stored source record of the owning specialist — no fabricated URLs,
    sections, excerpts or metadata anywhere."""
    m3_sources = {r["id"]: r for r in members["m3"]["pkg"].all_sources()}
    m4_corpus = members["m4"]["corpus"]
    m5_sources = {r["id"]: r for r in members["m5"]["pkg"].load_sources()}

    checked = 0
    for qid, query_text, jurisdiction in SWEEP_QUERIES:
        result = handle(QueryRequest(
            id=f"valid-{qid}", query=query_text, language="en", jurisdiction=jurisdiction))
        assert result.status == "ok", qid
        domain = result.routing.domain.value
        for citation in result.response.citations:
            if domain == "INDIA_IP":
                record = m3_sources.get(citation.id)
            elif domain == "ABS_TK":
                record = m4_corpus.get_record(citation.id)
            else:
                record = m5_sources.get(citation.id)
            assert record is not None, f"{qid}: citation {citation.id} not in {domain} corpus"
            assert citation.source_name == record["source_name"], citation.id
            assert citation.section == record["section"], citation.id
            assert citation.excerpt == record["excerpt"], citation.id
            assert citation.url == record["url"], citation.id
            assert citation.effective_date == record.get("effective_date"), citation.id
            assert citation.url.startswith("https://"), citation.id
            checked += 1
    assert checked >= 10, f"expected a meaningful sweep, checked {checked}"


# ---------------------------------------------------------------------------
# 10. Confidence
# ---------------------------------------------------------------------------


def test_10_confidence_present_and_in_range(handle, QueryRequest):
    result = handle(QueryRequest(
        id="conf-qa", language="en", jurisdiction="India",
        query="How do I register a GI tag for an Ayurvedic product tied to a region?"))
    body = result.response.model_dump()
    assert body["confidence"] in ("HIGH", "MEDIUM", "LOW")
    assert isinstance(body["confidence_score"], float)
    assert 0.0 <= body["confidence_score"] <= 1.0


def test_10_confidence_is_deterministic_not_llm_invented(handle, QueryRequest):
    """Offline deterministic modes: the same query yields the identical
    confidence twice — scores are computed, never invented by a model."""
    scores = []
    for i in range(2):
        result = handle(QueryRequest(
            id=f"conf-det-{i}", language="en", jurisdiction="India",
            query="I want to commercialise a formulation using a plant collected in India - what approvals do I need?"))
        scores.append((result.response.confidence, result.response.confidence_score))
    assert scores[0] == scores[1]
    assert scores[0][0] in ("HIGH", "MEDIUM", "LOW")


def test_10_confidence_varies_with_evidence_strength(handle, QueryRequest):
    """Answered queries score above abstentions; the classifier's Uncertain
    outcome scores below its clear-cut outcomes."""
    answered = handle(QueryRequest(
        id="conf-strong", language="en", jurisdiction="India",
        query="How do I register a GI tag for an Ayurvedic product tied to a region?"))
    abstained = handle(QueryRequest(
        id="conf-weak", language="en", jurisdiction="India",
        query="What is the fee for renewing a trademark in Japan under the Madrid Protocol?"))
    assert abstained.response.abstention is True
    assert abstained.response.confidence == "LOW"
    assert abstained.response.confidence_score == 0.0
    assert answered.response.confidence_score > abstained.response.confidence_score

    clear = client_post_classify = None  # classification variance:
    m2 = load_members()["m2"]["pkg"]
    high = m2.classify(ALL_CLASS_CASES["Classical"])
    uncertain = m2.classify({})
    assert high["confidence"] == "HIGH" and high["confidence_score"] > uncertain["confidence_score"]
    assert uncertain["confidence"] == "LOW"
    del clear, client_post_classify


# ---------------------------------------------------------------------------
# 11. Abstention / 12. safe fallback
# ---------------------------------------------------------------------------


def test_11_abstention_out_of_corpus_http_200(client):
    response = client.post("/api/query", json=q(
        "qa-ooc", "How is spacecraft lease depreciation taxed?",
        jurisdiction="International"))
    assert response.status_code == 200  # valid abstention is NOT an error
    body = response.json()
    assert contracts.validate_query_response(body) == []
    assert body["abstention"] is True and body["abstention_reason"]
    assert body["citations"] == []
    assert not re.search(r"Section \d+|\bArticle \d+", body["answer"])


def test_11_abstention_insufficient_evidence(handle, QueryRequest):
    """A same-domain but unsupported question (fee intent inside the ABS
    domain) abstains instead of inventing figures."""
    result = handle(QueryRequest(
        id="qa-insufficient", language="en", jurisdiction="India",
        query="What is the NBA approval fee for commercialising a plant-based formulation?"))
    assert result.status == "abstained"
    assert result.response.abstention is True
    assert result.response.citations == []
    assert not re.search(r"[₹]\s*\d|\b\d+\s*(rupees|dollars)", result.response.answer, re.I)


def test_12_processing_errors_not_disguised(client, members):
    """A failing specialist produces HTTP 502 PROCESSING_ERROR — never a
    successful-looking answer and never a fabricated 200."""
    assistant = members["m1"]["assistant"]
    routing = members["m1"]["routing"]

    def broken(request):
        raise RuntimeError("simulated specialist outage")

    saved = assistant.registered_specialist_handler(routing.Domain.INDIA_IP)
    assistant.register_specialist_handler(routing.Domain.INDIA_IP, broken)
    try:
        response = client.post("/api/query", json=q(
            "qa-502", "How do I register a GI tag for an Ayurvedic product tied to a region?"))
        assert response.status_code == 502
        body = response.json()
        assert body["error"] == "PROCESSING_ERROR"
        assert "answer" not in body and "citations" not in body
    finally:
        assistant.register_specialist_handler(routing.Domain.INDIA_IP, saved)


# ---------------------------------------------------------------------------
# 13-15. Domain scenarios + mapping safety
# ---------------------------------------------------------------------------


def test_13_abs_tkdl_scenario(handle, QueryRequest):
    result = handle(QueryRequest(
        id="qa-abs", language="en", jurisdiction="India",
        query="I want to commercialise a formulation using a plant collected in India - what approvals do I need?"))
    assert result.routing.domain.value == "ABS_TK"
    assert result.status == "ok"
    body = result.response.model_dump()
    assert "Biological Diversity Act" in body["answer"]
    assert "3(p)" not in body["answer"] and "Patents Act" not in body["answer"]


def test_13_tkdl_pointer_never_fabricates(handle, QueryRequest):
    """TK questions surface only the public-level TKDL pointer: the portal
    URL and its restriction description — never TKDL database content."""
    result = handle(QueryRequest(
        id="qa-tkdl", language="en", jurisdiction="India",
        query="My classical ayurvedic formulation is traditional knowledge - how is prior art checked?"))
    answer = result.response.answer
    assert "tkdl.res.in" in answer
    # fabrication guards: no invented TKDL entry numbers/formulation contents
    assert not re.search(r"TKDL\s+(?:entry|record|number)\s*[:#]?\s*\d+", answer, re.I)
    # M2's Classical pointer also names the restriction
    m2 = load_members()["m2"]["pkg"]
    pointer = m2.classify(ALL_CLASS_CASES["Classical"])["tkdl_pointer"]
    assert "tkdl.res.in" in pointer and "restricted" in pointer


def test_14_indian_ip_scenario_is_india_specific(handle, QueryRequest):
    result = handle(QueryRequest(
        id="qa-india-ip", language="en", jurisdiction="India",
        query="How do I register a GI tag for an Ayurvedic product tied to a region?"))
    assert result.routing.domain.value == "INDIA_IP"
    body = result.response.model_dump()
    assert "Geographical Indication" in body["answer"]
    assert "PCT" not in body["answer"] and "Madrid" not in body["answer"]
    assert all("wipo" not in (c.url or "").lower() for c in result.response.citations)


def test_15_pct_madrid_hague_mapping(handle, QueryRequest):
    cases = [
        ("I want to file a patent for a new Ayurvedic drug outside India - what route do I use?",
         "PCT", ["Madrid", "Hague"]),
        ("I want to register my Ayurvedic brand name internationally",
         "Madrid", ["PCT", "Hague"]),
        ("How can I protect my packaging as an industrial design internationally?",
         "Hague", ["PCT", "Madrid"]),
    ]
    for query_text, expected, forbidden in cases:
        result = handle(QueryRequest(
            id="qa-map", query=query_text, language="en", jurisdiction="International"))
        assert result.status == "ok", query_text
        answer = result.response.answer
        assert expected in answer, (query_text, expected)
        for bad in forbidden:
            assert bad not in answer, (query_text, bad)


# ---------------------------------------------------------------------------
# 17. Invalid / malformed inputs
# ---------------------------------------------------------------------------


def test_17_invalid_inputs_fail_safely(client):
    cases = [
        {"id": "x"},                                        # missing query
        {"id": "x", "query": ""},                           # empty query
        {"id": "x", "query": "hello", "language": "fr"},    # invalid language
        {"id": "x", "query": "hello", "jurisdiction": "Mars"},
        {"id": "", "query": "hello"},                       # blank id
        {"id": "x", "query": "hello", "history": "oops"},   # malformed history
        {"id": "x", "query": "hello", "formulation_class": "NotAClass"},
    ]
    for payload in cases:
        response = client.post("/api/query", json=payload)
        assert response.status_code == 400, payload
        assert response.json()["error"] == "VALIDATION_ERROR"
    # malformed classification input
    response = client.post("/api/classify", json={"answers": {"nope": "x"}})
    assert response.status_code == 400
    # structurally invalid specialist result → 502 (from the boundary tests)
    from integration.adapters import AdapterError, _validated_rag_result
    with pytest.raises(AdapterError):
        _validated_rag_result({"answer": 42}, "M3")


# ---------------------------------------------------------------------------
# Phase 2 watch items
# ---------------------------------------------------------------------------


def test_w1_m5_weak_query_regressions(client):
    """Watch item 1: weakly-related international queries must NOT receive
    generic PCT/Madrid/Hague answers (Phase 2 F-09 follow-up)."""
    weak = [
        "What color should I paint my patent documents?",
        "My patent application is feeling sad, what should I do?",
        "Can I patent the chocolate cake recipe for my restaurant menu?",
        "Do patents expire on weekends or holidays?",
        "How long is a patent valid for?",
    ]
    for query_text in weak:
        response = client.post("/api/query", json=q(
            "qa-w1", query_text, jurisdiction="International"))
        assert response.status_code == 200, query_text
        body = response.json()
        assert body["abstention"] is True, (query_text, body["answer"][:80])
        assert body["citations"] == []
        assert "PCT" not in body["answer"] and "Madrid" not in body["answer"]
    # fee-guard substring bug fixed: 'coffee'/'feeling' no longer trip it
    m5 = load_members()["m5"]["pkg"]
    coffee = m5.guide("Can I trademark coffee flavoured drinks internationally?")
    assert coffee["status"] == "ok", coffee["abstention_reason"]


def test_w2_disclaimer_rendering(handle, QueryRequest):
    """Watch item 2: specialist answers may embed their own disclaimer text
    while the QueryResponse also carries the standing disclaimer FIELD. The
    contract field must always be present and well-formed; the duplication is
    accepted MVP behaviour (documented, presentation polish only)."""
    result = handle(QueryRequest(
        id="qa-w2", language="en", jurisdiction="India",
        query="How do I register a GI tag for an Ayurvedic product tied to a region?"))
    body = result.response.model_dump()
    assert contracts.validate_query_response(body) == []
    assert "not legal advice" in body["disclaimer"].lower()
    assert body["disclaimer"].strip() == body["disclaimer"]  # well-formed field


def test_w3_alias_compat():
    """Watch item 3: the F-01 alias shim works from the clean integrated app
    and keeps M2/M3 importable under BOTH names."""
    from integration.adapters import alias_legacy_member_packages
    alias_legacy_member_packages()
    import member2  # noqa: F401  (legacy alias)
    import member3  # noqa: F401
    import sihmember2
    import sihmember3
    assert sys_modules_member2_is_sihmember2()
    result = sihmember2.classify({"primary_purpose": "external_cosmetic"})
    assert result["formulation_class"] == "Cosmetic"
    india = sihmember3.answer_india_question(
        "Can I patent a classical Ayurvedic formulation from an authoritative text?")
    assert india["status"] == "ok"


def sys_modules_member2_is_sihmember2():
    import sys
    return sys.modules["member2"] is sys.modules["sihmember2"]


def test_w4_m4_module_loading_no_collisions(members):
    """Watch item 4: M4's absolute-import modules coexist with the other
    members in one process. (The live probe intentionally pops M4's generic
    top-level names from sys.modules after probing, so this checks FUNCTIONAL
    isolation rather than sys.modules contents.)"""
    import importlib
    import sys

    # the other members' packages remain fully functional alongside M4
    m3 = members["m3"]["pkg"]
    assert m3.answer_india_question(
        "How do I register a GI tag for an Ayurvedic product tied to a region?"
    )["status"] == "ok"
    m2 = members["m2"]["pkg"]
    assert m2.classify({})["formulation_class"] == "Uncertain"
    m5 = members["m5"]["pkg"]
    assert m5.guide("I want to register my Ayurvedic brand name internationally")["status"] == "ok"
    # M4 still answers from its own corpus (nothing shadowed it)
    guidance = members["m4"]["guidance"]
    result = guidance.answer(
        "I want to commercialise a formulation using a plant collected in India "
        "- what approvals do I need?")
    assert result["status"] == "ok"
    assert "Biological Diversity Act" in result["answer"]
    # a fresh sihmember3.retrieval import is untouched by M4's top-level 'retrieval'
    m3_retrieval = importlib.import_module("sihmember3.retrieval")
    assert hasattr(m3_retrieval, "retrieve_evidence")
    del sys


# ---------------------------------------------------------------------------
# Final Safety Checklist (Plan.md §14) — automated portion
# ---------------------------------------------------------------------------


def test_safety_no_invented_authority_in_answers(handle, QueryRequest, members):
    """Sweep every supported golden/scenario answer: every statutory
    reference must appear in the owning specialist's stored evidence."""
    m3_sources = list(members["m3"]["pkg"].all_sources())
    m4_corpus = members["m4"]["corpus"]
    m5_sources = members["m5"]["pkg"].load_sources()

    for qid, query_text, jurisdiction in SWEEP_QUERIES:
        result = handle(QueryRequest(
            id=f"safety-{qid}", query=query_text, language="en", jurisdiction=jurisdiction))
        assert result.status == "ok", qid
        answer = result.response.answer
        domain = result.routing.domain.value
        if domain == "INDIA_IP":
            evidence = m3_sources
        elif domain == "ABS_TK":
            # M4's composer draws on the record's own verified `scope`
            # summary as well as the verbatim excerpt (M4-SRC-003's
            # section 7(2)-(3) certificate-of-origin claim was re-verified
            # against the actual Gazette PDF during Phase 3 QA).
            evidence = [dict(m4_corpus.get_record(c.id) or {}, scope=(m4_corpus.get_record(c.id) or {}).get("scope", "")) for c in result.response.citations]
        else:
            evidence = m5_sources
        blob = " ".join(
            (r.get("section") or "") + " " + (r.get("excerpt") or "") + " "
            + (r.get("scope") or "")
            for r in evidence if r
        ).lower()
        for match in re.finditer(r"sections?\s+(\d+[A-Z]?(?:\(\w+\))?)", answer, re.I):
            ref = match.group(0).lower().replace("sections", "section")
            keyword = match.group(1).lower()
            assert keyword in blob, f"{qid}: reference {match.group(0)!r} not in stored evidence"


def test_safety_india_international_distinct(handle, QueryRequest):
    india = handle(QueryRequest(
        id="saf-in", language="en", jurisdiction="India",
        query="Can I patent a classical Ayurvedic formulation from an authoritative text?"))
    international = handle(QueryRequest(
        id="saf-int", language="en", jurisdiction="International",
        query="I want to file a patent for a new Ayurvedic drug outside India - what route do I use?"))
    assert "PCT" not in india.response.answer
    assert "Section 3(p)" not in international.response.answer
    assert india.routing.domain.value == "INDIA_IP"
    assert international.routing.domain.value == "INTERNATIONAL_IP"


def test_safety_uncertainty_never_presented_as_certainty():
    m2 = load_members()["m2"]["pkg"]
    uncertain = m2.classify({"primary_purpose": "food_wellness"})  # missing exclusion
    assert uncertain["formulation_class"] == "Uncertain"
    assert uncertain["confidence"] == "LOW"
    assert uncertain["needs_clarification"] is True
