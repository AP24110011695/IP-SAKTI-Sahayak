"""Programmatic verification of the MEMBER_1.md Phase 2 (Trust and Safety)
acceptance criteria. Run:  python scripts/verify_acceptance_phase2.py

Prints PASS/FAIL per criterion with real evidence from live queries.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from m1.assistant import handle_query  # noqa: E402
from m1.config import Config  # noqa: E402
from m1.corpus import load_corpus  # noqa: E402
from m1.models import QueryRequest  # noqa: E402
from m1.safety import confidence_from, validate_citations  # noqa: E402

GOLDEN_1 = (
    "Can I patent a classical Ayurvedic formulation from an authoritative text?"
)
GOLDEN_2 = (
    "I want to file a patent for a new Ayurvedic drug outside India — "
    "what route do I use?"
)
HINDI_TK = "पारंपरिक ज्ञान पर पेटेंट कर सकते हैं क्या?"

cfg = Config()
corpus = load_corpus()
corpus_by_id = {e.id: e for e in corpus}
results = []


def check(name, fn):
    try:
        results.append((name, "PASS", fn()))
    except Exception as exc:
        results.append((name, "FAIL", f"{type(exc).__name__}: {exc}"))


def ac1_citations_map_to_real_evidence():
    r = handle_query(QueryRequest(id="p2-1", query=GOLDEN_1, jurisdiction="India"), cfg).response
    assert r.citations, "no citations"
    for c in r.citations:
        src = corpus_by_id[c.id]
        assert (c.source_name, c.source_type, c.section, c.url, c.effective_date) == (
            src.source_name, src.source_type, src.section, src.url, src.effective_date,
        ), f"citation {c.id} metadata differs from stored evidence"
        assert c.excerpt == src.text
        assert f"[E" in r.answer, "answer must reference evidence tags"
    return (
        f"{len(r.citations)} citations ({', '.join(c.id for c in r.citations)}) "
        f"resolve to stored evidence via [E#] tags in the answer"
    )


def ac2_urls_from_stored_metadata_only():
    r = handle_query(QueryRequest(id="p2-2", query=GOLDEN_2, jurisdiction="International"), cfg).response
    assert r.citations
    for c in r.citations:
        assert c.url == corpus_by_id[c.id].url, "url not from stored metadata"
    assert validate_citations(r.citations, corpus_by_id) == []
    # Tamper test: any modified citation field is rejected by the validator.
    from m1.models import Citation
    tampered = r.citations[0].model_copy(update={"url": "https://invented.example/law"})
    failures = validate_citations([tampered], corpus_by_id)
    assert failures, "validator must reject an invented URL"
    return (
        "served URLs equal stored corpus URLs; validator rejects a tampered URL "
        f"({failures[0]})"
    )


def ac3_insufficient_evidence_abstains():
    none_at_all = handle_query(
        QueryRequest(id="p2-3a", query="quantum chromodynamics strawberry spaceship"),
        cfg,
    ).response
    weak = handle_query(QueryRequest(id="p2-3b", query="act", jurisdiction="India"), cfg).response
    llm_dead = handle_query(
        QueryRequest(id="p2-3c", query=GOLDEN_1),
        Config(llm_api_key="k", llm_base_url="http://127.0.0.1:1", llm_timeout_secs=2),
    ).response
    for name, r in (("none", none_at_all), ("weak", weak), ("llm-failure", llm_dead)):
        assert r.abstention is True, f"{name}: must abstain"
        assert r.abstention_reason, f"{name}: reason required"
        assert r.citations == [], f"{name}: no citations on abstention"
        assert r.confidence == "LOW" and r.confidence_score == 0.0
        assert r.answer.strip(), f"{name}: safe fallback text required"
        assert "not legal advice" in r.disclaimer
    return (
        "no-evidence, weak-evidence (sufficiency threshold) and failed-LLM "
        "queries all abstain with reasons + safe fallback, never a guess"
    )


def ac4_confidence_varies_sensibly():
    strong = handle_query(QueryRequest(id="p2-4a", query=GOLDEN_1, jurisdiction="India"), cfg).response
    weaker = handle_query(QueryRequest(id="p2-4b", query="tkdl", jurisdiction="India"), cfg).response
    abstained = handle_query(QueryRequest(id="p2-4c", query="act"), cfg).response
    assert strong.confidence in ("HIGH", "MEDIUM") and strong.confidence_score >= 0.25
    assert weaker.confidence in ("MEDIUM", "HIGH")
    assert strong.confidence_score > weaker.confidence_score, "stronger evidence must score higher"
    assert (abstained.confidence, abstained.confidence_score) == ("LOW", 0.0)
    # Band behaviour on synthetic strengths (unit-level evidence):
    assert confidence_from([]) == ("LOW", 0.0)
    return (
        f"golden query {strong.confidence}({strong.confidence_score}) > "
        f"'tkdl' query {weaker.confidence}({weaker.confidence_score}); "
        f"abstention = LOW(0.0)"
    )


def ac5_hindi_works_for_supported_scenarios():
    r = handle_query(
        QueryRequest(id="p2-5", query=HINDI_TK, language="hi", jurisdiction="India"), cfg
    ).response
    assert not r.abstention and r.answer.strip()
    p3 = corpus_by_id["in-patents-act-3p"]
    assert p3.text_hi in r.answer, "answer must be built from the Hindi rendering"
    assert "कानूनी सलाह नहीं" in r.answer and "कानूनी सलाह" in r.disclaimer
    assert "in-patents-act-3p" in {c.id for c in r.citations}
    # English answer for the same scenario stays in English:
    en = handle_query(QueryRequest(id="p2-5e", query=GOLDEN_1, jurisdiction="India"), cfg).response
    assert p3.text in en.answer and p3.text_hi not in en.answer
    return (
        "Hindi query on the s.3(p) scenario returns a Hindi answer (Hindi "
        "excerpt + Hindi disclaimer); English query stays English"
    )


def ac6_safety_tests_pass():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=300,
    )
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout else proc.stderr[-200:]
    assert proc.returncode == 0, tail
    return tail


check("AC1 Citations map to real evidence", ac1_citations_map_to_real_evidence)
check("AC2 URLs come from stored metadata, never invented", ac2_urls_from_stored_metadata_only)
check("AC3 Insufficient evidence triggers abstention, not a guess", ac3_insufficient_evidence_abstains)
check("AC4 Confidence works and varies sensibly with evidence strength", ac4_confidence_varies_sensibly)
check("AC5 Hindi works for supported scenarios", ac5_hindi_works_for_supported_scenarios)
check("AC6 Safety tests pass", ac6_safety_tests_pass)

width = max(len(n) for n, _, _ in results)
print("=" * 100)
print("PHASE 2 ACCEPTANCE CRITERIA VERIFICATION — Member 1 (IP-SAKTI Sahayak)")
print("=" * 100)
all_pass = True
for name, verdict, detail in results:
    all_pass &= verdict == "PASS"
    print(f"[{verdict}] {name.ljust(width)}  —  {detail}")
print("=" * 100)
print("ALL ACCEPTANCE CRITERIA:", "PASS" if all_pass else "FAIL")
sys.exit(0 if all_pass else 1)
