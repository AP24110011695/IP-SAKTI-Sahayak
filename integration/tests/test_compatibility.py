"""Task 6 — compatibility checks.

Verifies that the shared vocabulary (language, jurisdiction, formulation
class, confidence, status, IDs, citation schema, tkdl_pointer, history,
clarification fields) is used consistently across the harness, the stub
specialists and — via integration.live_probe — the REAL member code.

The live probe is read-only: it imports each member workstream exactly as
its own code expects, exercises entry points OFFLINE (deterministic
unconfigured modes), and records findings. Hard contract violations fail
this test; documented known mismatches must match the recorded set in
member_interfaces.COMPATIBILITY_FINDINGS (update both together when Phase 2
resolves one).
"""
import pytest

from integration import contracts
from integration.assembler import Assembler
from integration.live_probe import probe_all, summarise
from integration.member_interfaces import COMPATIBILITY_FINDINGS
from integration.stubs import default_stub_specialists, stub_route

# Known mismatches discovered in Phase 1 (ids from COMPATIBILITY_FINDINGS).
# Phase 2 resolves these; when one is fixed, remove it here AND from
# member_interfaces.COMPATIBILITY_FINDINGS in the same change.
EXPECTED_KNOWN_MISMATCH_IDS = {"F-04", "F-06"}


@pytest.fixture(scope="module")
def probe_findings():
    return probe_all()


# ---------------------------------------------------------------------------
# Shared vocabulary across the harness components
# ---------------------------------------------------------------------------


def test_language_and_jurisdiction_values_are_the_contract_values():
    assert contracts.LANGUAGES == ("en", "hi")
    assert contracts.JURISDICTIONS == ("India", "International")


def test_stub_results_use_contract_vocabulary():
    assembler = Assembler(router=stub_route, specialists=default_stub_specialists())
    for domain in ("INDIA_IP", "ABS_TK", "INTERNATIONAL_IP"):
        result = assembler.specialists[domain]({
            "id": "c-1", "query": "", "language": "en",
        })
        assert result["confidence"] in contracts.CONFIDENCE_LEVELS
        assert result["status"] in contracts.RAG_STATUSES
        for citation in result["citations"]:
            assert contracts.validate_citation(citation) == []
    classification = assembler.specialists["CLASSIFICATION"]({"answers": {}})
    assert classification["formulation_class"] in contracts.FORMULATION_CLASSES
    assert classification["confidence"] in contracts.CONFIDENCE_LEVELS


def test_request_id_is_echoed_in_responses():
    assembler = Assembler(router=stub_route, specialists=default_stub_specialists())
    outcome = assembler.handle_query({
        "id": "compat-id-42",
        "query": "How do I register a GI tag for an Ayurvedic product tied to a region?",
        "jurisdiction": "India",
    })
    assert outcome.body["id"] == "compat-id-42"


def test_history_is_accepted_and_forwarded_to_specialists():
    received = {}

    def spy_specialist(request):
        received.update(request)
        return {
            "answer": "Grounded answer.",
            "citations": [{
                "id": "IN-001", "source_name": "Patents Act, 1970",
                "source_type": "statute", "section": "Section 3(p)",
                "excerpt": "Stored evidence excerpt.",
                "url": "https://www.indiacode.nic.in",
                "effective_date": "1970-09-21",
            }],
            "confidence": "HIGH", "confidence_score": 0.9,
            "abstention": False, "abstention_reason": None, "status": "ok",
        }

    assembler = Assembler(router=lambda r: ("INDIA_IP", "test"),
                          specialists={"INDIA_IP": spy_specialist})
    history = [
        {"role": "user", "content": "What is Section 3(p) of the Patents Act?"},
        {"role": "assistant", "content": "It is the traditional-knowledge bar."},
    ]
    outcome = assembler.handle_query({
        "id": "compat-hist", "query": "How does it affect classical formulations?",
        "history": history,
    })
    assert outcome.status_code == 200
    assert received["history"] == history


def test_clarification_fields_on_uncertain_classification():
    assembler = Assembler(router=stub_route, specialists=default_stub_specialists())
    outcome = assembler.handle_classify({"answers": {}})
    body = outcome.body
    assert body["formulation_class"] == "Uncertain"
    assert body["needs_clarification"] is True
    assert isinstance(body["clarification_prompt"], str) and body["clarification_prompt"]


def test_tkdl_pointer_contract():
    """tkdl_pointer must be a pointer naming tkdl.res.in — never TKDL content.
    Checked in its three member forms: M2's ClassificationResult field, M4's
    additive RAG-result field, and M3's answer-text pointer."""
    assembler = Assembler(router=stub_route, specialists=default_stub_specialists())
    # M2 form (Classical)
    result = assembler.handle_classify(
        {"answers": {"primary_purpose": "therapeutic", "text_source": "yes"}}
    ).body
    assert result["tkdl_pointer"] and "tkdl.res.in" in result["tkdl_pointer"]
    # M4 form (additive field on a TK-flavoured ABS result)
    m4 = assembler.specialists["ABS_TK"]({
        "id": "c-2", "query": "My classical ayurvedic formulation is traditional "
                              "knowledge - how is prior art checked?",
        "language": "en",
    })
    assert m4.get("tkdl_pointer") and "tkdl.res.in" in m4["tkdl_pointer"]
    assert not contracts.validate_rag_result(m4)
    # M3 form (answer-text pointer) is verified by the live probe (probe_m3).


def test_hindi_language_flows_through_the_assembler():
    assembler = Assembler(router=stub_route, specialists=default_stub_specialists())
    outcome = assembler.handle_query({
        "id": "compat-hi",
        "query": "क्या मैं किसी प्रामाणिक ग्रंथ से लिए गए शास्त्रीय आयुर्वेदिक फॉर्मूलेशन का पेटेंट कर सकता हूँ?",
        "language": "hi",
        "jurisdiction": "India",
    })
    assert outcome.status_code == 200
    body = outcome.body
    assert contracts.validate_query_response(body) == []
    assert body["disclaimer"] == assembler.disclaimers["hi"]


# ---------------------------------------------------------------------------
# Live probe: the REAL member code vs the contract (offline)
# ---------------------------------------------------------------------------


def test_live_probe_imports_all_five_members(probe_findings):
    for member in ("M1", "M2", "M3", "M4", "M5"):
        imports = [f for f in probe_findings
                   if f["member"] == member and f["check"] == "import"]
        assert imports, f"no import finding for {member}"
        assert imports[0]["status"] == "pass", imports[0]["detail"]


def test_live_probe_contract_values(probe_findings):
    """All enum/shape checks against the real member code must pass."""
    failures = [f for f in probe_findings if f["status"] == "fail"]
    assert not failures, "live probe failures:\n" + summarise(failures)


def test_live_probe_known_mismatches_match_the_recorded_set(probe_findings):
    known = {f["member"] + ":" + f["check"] for f in probe_findings
             if f["status"] == "known_mismatch"}
    expected = {
        f["member"] + ":" + f["check"]
        for f in probe_findings if f["status"] == "known_mismatch"
    }
    assert known == expected  # sanity: the set is well-formed
    # Every known mismatch in the probe must be documented as a finding.
    documented = {finding["id"] for finding in COMPATIBILITY_FINDINGS}
    for mismatch in known:
        member, check = mismatch.split(":", 1)
        finding_id = check.split("(")[-1].rstrip(")")
        assert finding_id in documented, f"undocumented known mismatch: {mismatch}"
    # And the expected set is exactly what the probe currently reports.
    reported_ids = {
        f["check"].split("(")[-1].rstrip(")")
        for f in probe_findings if f["status"] == "known_mismatch"
    }
    assert reported_ids == EXPECTED_KNOWN_MISMATCH_IDS


def test_live_probe_golden_behavior_present_in_real_members(probe_findings):
    """The real members' golden-scenario behavior (M3 patent/TK, M3 GI,
    M4 ABS, M5 PCT) must be present — these are the checks Phase 2 relies on."""
    checks = {f["member"] + ":" + f["check"]: f["status"] for f in probe_findings}
    for required in (
        "M3:golden: classical patent question",
        "M3:international query refusal",
        "M3:golden: GI registration question",
        "M4:golden: ABS commercialisation question",
        "M4:trademark question not flagged ABS",
        "M5:golden: international patent → PCT",
        "M5:trademark → Madrid (not PCT)",
        "M5:India-jurisdiction query refused",
    ):
        assert checks.get(required) == "pass", f"{required}: {checks.get(required)}"
