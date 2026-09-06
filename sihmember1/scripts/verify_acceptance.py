"""Programmatic verification of the MEMBER_1.md Phase 1 acceptance criteria.

Run:  python scripts/verify_acceptance.py
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

GOLDEN_1 = (
    "Can I patent a classical Ayurvedic formulation from an authoritative text?"
)
GOLDEN_2 = (
    "I want to file a patent for a new Ayurvedic drug outside India — "
    "what route do I use?"
)
FILING_QUERY = "How do I file a patent application for my Ayurvedic product?"

cfg = Config()
corpus = load_corpus()
corpus_by_id = {e.id: e for e in corpus}
results = []


def check(name, fn):
    try:
        results.append((name, "PASS", fn()))
    except Exception as exc:
        results.append((name, "FAIL", f"{type(exc).__name__}: {exc}"))


def ac1_end_to_end():
    r = handle_query(
        QueryRequest(id="ac1", query=GOLDEN_1, jurisdiction="India"), cfg
    ).response
    assert r.answer.strip(), "empty answer"
    assert r.abstention is False
    assert r.confidence in ("HIGH", "MEDIUM", "LOW")
    assert 0.0 <= r.confidence_score <= 1.0
    assert r.disclaimer.strip()
    return (
        f"answer {len(r.answer)} chars, confidence={r.confidence} "
        f"({r.confidence_score}), {len(r.citations)} citations, disclaimer present"
    )


def ac2_evidence_from_own_corpus():
    r = handle_query(
        QueryRequest(id="ac2", query=GOLDEN_1, jurisdiction="India"), cfg
    ).response
    assert r.citations, "no citations returned"
    for c in r.citations:
        assert c.id in corpus_by_id, f"citation {c.id} not in standalone corpus"
        src = corpus_by_id[c.id]
        assert c.url == src.url and c.excerpt == src.text and c.section == src.section
    return f"citations {sorted({c.id for c in r.citations})} map to corpus entries (URL/section/excerpt verbatim)"


def ac3_grounding():
    r = handle_query(
        QueryRequest(id="ac3", query=GOLDEN_2, jurisdiction="International"), cfg
    ).response
    assert not r.abstention and r.citations
    for c in r.citations:
        assert c.excerpt in r.answer, f"citation {c.id} excerpt absent from answer"
    return (
        f"every citation excerpt appears verbatim in the answer "
        f"({len(r.citations)} citation(s); extractive generator quotes evidence only)"
    )


def ac4_jurisdiction_separation():
    india = handle_query(
        QueryRequest(id="ac4i", query=FILING_QUERY, jurisdiction="India"), cfg
    ).response
    intl_same = handle_query(
        QueryRequest(id="ac4x", query=FILING_QUERY, jurisdiction="International"), cfg
    ).response
    intl_golden = handle_query(
        QueryRequest(id="ac4g", query=GOLDEN_2, jurisdiction="International"), cfg
    ).response
    i_ids = {c.id for c in india.citations}
    x_ids = {c.id for c in intl_same.citations}
    g_ids = {c.id for c in intl_golden.citations}
    assert i_ids and x_ids, "both sides must retrieve evidence"
    assert all(i.startswith("in-") for i in i_ids), i_ids
    assert all(i.startswith("intl-") for i in x_ids), x_ids
    assert i_ids != x_ids and india.answer != intl_same.answer
    assert "intl-pct" in g_ids, "golden international query must cite PCT"
    assert "intl-madrid" not in g_ids, "Madrid must not be cited for a patent query"
    assert "Madrid" not in intl_golden.answer
    return (
        f"India cites {sorted(i_ids)}; International cites {sorted(x_ids)}; "
        f"golden international query cites {sorted(g_ids)} with no Madrid mention"
    )


def ac5_tests_pass():
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


check("AC1 Query works end-to-end", ac1_end_to_end)
check("AC2 Evidence can be retrieved from own corpus", ac2_evidence_from_own_corpus)
check("AC3 Answer is grounded in retrieved evidence", ac3_grounding)
check("AC4 India/International state is respected", ac4_jurisdiction_separation)
check("AC5 Tests pass", ac5_tests_pass)

width = max(len(n) for n, _, _ in results)
print("=" * 100)
print("PHASE 1 ACCEPTANCE CRITERIA VERIFICATION — Member 1 (IP-SAKTI Sahayak)")
print("=" * 100)
all_pass = True
for name, verdict, detail in results:
    all_pass &= verdict == "PASS"
    print(f"[{verdict}] {name.ljust(width)}  —  {detail}")
print("=" * 100)
print("ALL ACCEPTANCE CRITERIA:", "PASS" if all_pass else "FAIL")
sys.exit(0 if all_pass else 1)
