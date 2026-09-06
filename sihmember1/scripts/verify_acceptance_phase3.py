"""Programmatic verification of the MEMBER_1.md Phase 3 (Standalone
Completion) acceptance criteria. Run:  python scripts/verify_acceptance_phase3.py

Prints PASS/FAIL per criterion with real evidence; exits non-zero on failure.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from m1.assistant import handle_query  # noqa: E402
from m1.config import Config  # noqa: E402
from m1.corpus import ALLOWED_SOURCE_DOMAINS, load_corpus  # noqa: E402
from m1.followup import effective_retrieval_query  # noqa: E402
from m1.models import QueryRequest  # noqa: E402
from m1.safety import validate_citations  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

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


def ac1_works_without_other_members():
    """The full flow runs standalone: extractive generator, specialists not
    wired, and no M2–M5 modules imported anywhere in this process."""
    assert cfg.generator_mode == "extractive"
    assert cfg.specialists_wired is False
    banned = {"m2", "m3", "m4", "m5", "member2", "member3", "member4", "member5"}
    imported = banned & set(sys.modules)
    assert not imported, f"unexpected cross-member imports: {imported}"
    for req in (
        QueryRequest(id="p3-1a", query=GOLDEN_1, jurisdiction="India"),
        QueryRequest(id="p3-1b", query=GOLDEN_2, jurisdiction="International"),
        QueryRequest(id="p3-1c", query=HINDI_TK, jurisdiction="India", language="hi"),
        QueryRequest(
            id="p3-1d",
            query="What about outside India?",
            jurisdiction="International",
            history=[{"role": "user", "content": GOLDEN_1}],
        ),
        QueryRequest(id="p3-1e", query="Who won the 1996 cricket world cup final?"),
    ):
        result = handle_query(req, cfg)
        assert result.status in ("ok", "abstained")
        assert result.response.disclaimer.strip()
    return "full flow (query→routing→retrieval→sufficiency→answer→citations→"
    "confidence→abstention) runs with zero M2–M5 dependencies"


def ac2_golden_queries_pass():
    g1 = handle_query(QueryRequest(id="p3-2a", query=GOLDEN_1, jurisdiction="India"), cfg).response
    g2 = handle_query(QueryRequest(id="p3-2b", query=GOLDEN_2, jurisdiction="International"), cfg).response
    assert not g1.abstention and "3(p)" in g1.answer
    assert "TKDL" in g1.answer or "Traditional Knowledge Digital Library" in g1.answer
    assert "in-patents-act-3p" in {c.id for c in g1.citations}
    assert not g2.abstention and "PCT" in g2.answer
    assert "intl-pct" in {c.id for c in g2.citations}
    assert "Madrid" not in g2.answer and "intl-madrid" not in {c.id for c in g2.citations}
    assert {c.id for c in g1.citations}.isdisjoint({c.id for c in g2.citations})
    return "golden 1 → s.3(p)+TKDL (India); golden 2 → PCT, no Madrid (International); sets disjoint"


def ac3_citations_valid_no_fabrication():
    checked = 0
    for req in (
        QueryRequest(id="p3-3a", query=GOLDEN_1, jurisdiction="India"),
        QueryRequest(id="p3-3b", query=GOLDEN_2, jurisdiction="International"),
        QueryRequest(id="p3-3c", query="register my brand internationally", jurisdiction="International"),
        QueryRequest(id="p3-3d", query=HINDI_TK, jurisdiction="India", language="hi"),
        QueryRequest(
            id="p3-3e",
            query="What about outside India?",
            jurisdiction="International",
            history=[{"role": "user", "content": GOLDEN_1}],
        ),
    ):
        r = handle_query(req, cfg).response
        for c in r.citations:
            assert validate_citations([c], corpus_by_id) == [], f"invalid citation {c.id}"
            host = urlparse(c.url).netloc.lower()
            assert any(host == d or host.endswith("." + d) for d in ALLOWED_SOURCE_DOMAINS)
            checked += 1
    tkdl = corpus_by_id["in-tkdl-pointer"]
    assert "restricted" in tkdl.text.lower() or "non-disclosure" in tkdl.text.lower()
    assert "tkdl.res.in" in tkdl.url
    return (
        f"{checked} served citations across 5 runs all byte-match stored metadata "
        f"with authoritative https URLs; TKDL stays a pointer (NDA-restricted)"
    )


def ac4_abstention_works():
    # Out-of-corpus query per golden scenario (MEMBER_1.md §6 instruction)
    ooc1 = handle_query(
        QueryRequest(id="p3-4a", query="Who won the 1996 cricket world cup final?", jurisdiction="India"), cfg
    ).response
    ooc2 = handle_query(
        QueryRequest(id="p3-4b", query="How do I export Ayurvedic oils to Antarctica?", jurisdiction="International"), cfg
    ).response
    weak = handle_query(QueryRequest(id="p3-4c", query="act", jurisdiction="India"), cfg).response
    for name, r in (("golden1-ooc", ooc1), ("golden2-ooc", ooc2), ("weak", weak)):
        assert r.abstention is True and r.abstention_reason and r.citations == []
        assert (r.confidence, r.confidence_score) == ("LOW", 0.0)
        assert r.answer.strip()
    # Validation edge cases: empty query / unsupported language / bad values
    from pydantic import ValidationError
    for bad in (
        {"id": "x", "query": ""},
        {"id": "x", "query": "   "},
        {"id": "x", "query": "q", "language": "ta"},
        {"id": "x", "query": "q", "jurisdiction": "USA"},
    ):
        try:
            QueryRequest(**bad)
            raise AssertionError(f"{bad} should have been rejected")
        except ValidationError:
            pass
    # Missing jurisdiction falls back to the safe domestic default
    missing = handle_query(QueryRequest(id="p3-4d", query=GOLDEN_1), cfg).response
    assert not missing.abstention
    assert all(c.id.startswith("in-") for c in missing.citations)
    return (
        "out-of-corpus per golden scenario, weak evidence and edge cases "
        "(empty query, unsupported language, bad jurisdiction → 400-equivalent; "
        "missing jurisdiction → India default) all behave safely"
    )


def ac5_final_tests_pass():
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


def ac5b_followups_and_contract():
    from m1.models import Message
    expanded = effective_retrieval_query(
        "What about outside India?",
        [Message(role="user", content=GOLDEN_1)],
    )
    assert "patent" in expanded and "outside" in expanded
    proc = subprocess.run(
        [sys.executable, "scripts/verify_contract.py"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout[-500:]
    return "follow-up expansion works; contract verification PASS"


check("AC1 Works completely without M2–M5 present", ac1_works_without_other_members)
check("AC2 Golden queries pass", ac2_golden_queries_pass)
check("AC3 Citations valid, no fabricated authority/URLs/TKDL text", ac3_citations_valid_no_fabrication)
check("AC4 Abstention works", ac4_abstention_works)
check("AC5 Follow-ups + integration contract verified", ac5b_followups_and_contract)
check("AC6 Final tests pass", ac5_final_tests_pass)

width = max(len(n) for n, _, _ in results)
print("=" * 100)
print("PHASE 3 ACCEPTANCE CRITERIA VERIFICATION — Member 1 (IP-SAKTI Sahayak)")
print("=" * 100)
all_pass = True
for name, verdict, detail in results:
    all_pass &= verdict == "PASS"
    print(f"[{verdict}] {name.ljust(width)}  —  {detail}")
print("=" * 100)
print("ALL ACCEPTANCE CRITERIA:", "PASS" if all_pass else "FAIL")
sys.exit(0 if all_pass else 1)
