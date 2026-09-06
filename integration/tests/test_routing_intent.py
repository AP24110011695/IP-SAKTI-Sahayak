"""Routing-intent regression tests (Phase 4 fix).

Root cause being pinned: M1's flat ABS/TK keyword list sent ANY query
containing "traditional knowledge"/"tkdl" to the ABS/TK specialist (M4) even
when the query's intent was patentability, which belongs to the India-IP
specialist (M3) — the specialist that owns the Section 3(p)/2(1)(j)
analysis and carries the legitimate TKDL pointer.

The fix splits M1's signals by intent:
  ABS/biological-resource signals  → M4 (unchanged, incl. the documented
                                     resource+patent intersection);
  TK-awareness signals alone       → M4 (ordinary TK questions still reach M4);
  TK-awareness + patentability     → jurisdiction toggle: India → M3,
    intent                           International → M5 (WIPO GRATK route).

Regression cases required (review request):
  1. Section 3(p) + TKDL patentability query → M3
  2. inventive-step + TK query → M3
  3. pure ABS commercialisation query → M4
  4. genuine mixed patent + biological-resource query → documented behavior (M4)
  5. no duplicate specialist answer in QueryResponse
  6. existing five golden scenarios remain green (covered by
     test_golden_scenarios_real.py, re-run in the same suite)
"""
import sys

import pytest

from integration.adapters import load_members, wire_m1

FAILING_QUERY = (
    "Can traditional knowledge documented in TKDL affect the patentability "
    "of my Ayurvedic invention in India?"
)


@pytest.fixture(scope="module")
def members():
    return wire_m1()


@pytest.fixture(scope="module")
def QueryRequest(members):
    return members["m1"]["models"].QueryRequest


@pytest.fixture(scope="module")
def handle(members):
    return members["m1"]["assistant"].handle_query


def route_of(handle, QueryRequest, query, jurisdiction="India", history=None):
    request = QueryRequest(
        id="routing-fix", query=query, language="en",
        jurisdiction=jurisdiction, history=history or [])
    return handle(request)


# ---------------------------------------------------------------------------
# 1. Patentability + TKDL → M3 (the exact failing query)
# ---------------------------------------------------------------------------


def test_failing_query_routes_to_m3_with_coherent_answer(handle, QueryRequest, members):
    result = route_of(handle, QueryRequest, FAILING_QUERY)
    assert result.routing.domain.value == "INDIA_IP", result.routing.rationale
    assert result.generator_used == "specialist"
    assert result.status == "ok"
    body = result.response.model_dump()
    # M3's patentability analysis is present…
    assert "3(p)" in body["answer"]
    # …with the legitimate TKDL pointer…
    assert "tkdl.res.in" in body["answer"]
    # …and M4's ABS-composer content is NOT appended.
    assert "Based on the curated ABS/TK evidence" not in body["answer"]
    assert "Benefit sharing" not in body["answer"] and "benefit-sharing" not in body["answer"]
    # citations belong to M3's India-patent corpus (no ABS-only records)
    m3_ids = {r["id"] for r in members["m3"]["pkg"].all_sources()}
    assert body["citations"], "M3 answer must carry citations"
    assert all(c["id"] in m3_ids for c in body["citations"])


def test_tkdl_patentability_variant_routes_to_m3(handle, QueryRequest):
    result = route_of(handle, QueryRequest,
                      "Does TKDL prior art block a patent on my herbal formulation in India?")
    assert result.routing.domain.value == "INDIA_IP"


# ---------------------------------------------------------------------------
# 2. Inventive-step + TK query → M3
# ---------------------------------------------------------------------------


def test_inventive_step_tk_query_routes_to_m3(handle, QueryRequest):
    result = route_of(
        handle, QueryRequest,
        "My Ayurvedic invention shows an inventive step over traditional "
        "knowledge documented in classical texts — is it patentable in India?")
    assert result.routing.domain.value == "INDIA_IP"
    assert result.status == "ok"
    assert "3(p)" in result.response.answer or "inventive" in result.response.answer.lower()


# ---------------------------------------------------------------------------
# 3. Pure ABS query → M4 (ordinary TK questions still reach M4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("query", [
    ("I want to commercialise a formulation using a plant collected in India "
     "- what approvals do I need?"),
    "How does benefit sharing work under the Biological Diversity Act?",
    "What is the procedure for access to a biological resource for research?",
    # ordinary TK question with no patentability intent stays with M4
    "How is traditional knowledge protected against bio-piracy in India?",
])
def test_abs_and_plain_tk_queries_route_to_m4(handle, QueryRequest, query):
    result = route_of(handle, QueryRequest, query)
    assert result.routing.domain.value == "ABS_TK", (query, result.routing.rationale)


# ---------------------------------------------------------------------------
# 4. Genuine mixed patent + biological-resource query → documented M4 behavior
# ---------------------------------------------------------------------------


def test_mixed_resource_and_patent_query_stays_with_m4(handle, QueryRequest):
    """MEMBER_4.md documents that a query naming a biological resource AND a
    patent is a genuine ABS/IPR intersection (BD Act s.6) and stays with M4.
    The routing-intent fix must not weaken that."""
    result = route_of(
        handle, QueryRequest,
        "Do I need NBA approval before filing a patent application for a "
        "formulation using a plant collected in India?")
    assert result.routing.domain.value == "ABS_TK"
    assert result.status == "ok"
    assert "Biological Diversity Act" in result.response.answer or \
        "NBA" in result.response.answer or \
        "National Biodiversity Authority" in result.response.answer


def test_international_patentability_tk_query_routes_to_m5(handle, QueryRequest):
    """TK-awareness + patentability intent outside India falls through to the
    jurisdiction toggle → M5's WIPO GRATK disclosure route."""
    result = route_of(
        handle, QueryRequest,
        "Does traditional knowledge documented in TKDL affect the "
        "patentability of my invention abroad?",
        jurisdiction="International")
    assert result.routing.domain.value == "INTERNATIONAL_IP"
    assert result.status == "ok"
    # M5's GRATK route: disclosure obligations, patent framing, no India act
    text = result.response.answer.lower()
    assert "gratk" in text or "disclosure" in text or "traditional knowledge" in text


# ---------------------------------------------------------------------------
# 5. No duplicate specialist answer — exactly one specialist dispatch
# ---------------------------------------------------------------------------


def test_exactly_one_specialist_dispatched_per_query(handle, QueryRequest, members):
    """Wrap every registered specialist handler with a call counter: one
    /api/query must invoke exactly ONE specialist — the assembled
    QueryResponse can never contain two specialists' answers."""
    assistant = members["m1"]["assistant"]
    routing = members["m1"]["routing"]
    calls = []

    originals = {}
    for domain in routing.Domain:
        handler = assistant.registered_specialist_handler(domain)
        if handler is None:
            continue
        originals[domain] = handler

        def counting_wrapper(request, _handler=handler, _name=domain.value):
            calls.append(_name)
            return _handler(request)

        assistant.register_specialist_handler(domain, counting_wrapper)
    try:
        result = route_of(handle, QueryRequest, FAILING_QUERY)
        assert result.routing.domain.value == "INDIA_IP"
        # exactly one specialist produced this response
        assert calls == ["INDIA_IP"], calls
        # and the response text carries no second specialist's content
        text = result.response.answer
        assert "Based on the curated ABS/TK evidence" not in text
    finally:
        for domain, handler in originals.items():
            assistant.register_specialist_handler(domain, handler)


# ---------------------------------------------------------------------------
# 6. Golden scenarios unaffected (quick re-assertions here; the full set
#    runs in test_golden_scenarios_real.py in the same suite)
# ---------------------------------------------------------------------------


def test_golden_scenarios_still_route_correctly(handle, QueryRequest):
    expectations = [
        ("Can I patent a classical Ayurvedic formulation from an authoritative text?",
         "India", "INDIA_IP"),
        ("I want to commercialise a formulation using a plant collected in India "
         "- what approvals do I need?", "India", "ABS_TK"),
        ("How do I register a GI tag for an Ayurvedic product tied to a region?",
         "India", "INDIA_IP"),
        ("I want to file a patent for a new Ayurvedic drug outside India - what "
         "route do I use?", "International", "INTERNATIONAL_IP"),
    ]
    for query, jurisdiction, expected in expectations:
        result = route_of(handle, QueryRequest, query, jurisdiction=jurisdiction)
        assert result.routing.domain.value == expected, (query, result.routing.rationale)
