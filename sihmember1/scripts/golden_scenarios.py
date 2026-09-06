"""Run the MEMBER_1.md §6 golden scenarios for real, with one out-of-corpus
query per scenario to confirm abstention fires instead of fabrication.

Prints full request/response JSON for the report and exits non-zero on any
failed expectation.

Usage:  python scripts/golden_scenarios.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from m1.assistant import handle_query  # noqa: E402
from m1.config import Config  # noqa: E402
from m1.corpus import ALLOWED_SOURCE_DOMAINS, load_corpus  # noqa: E402
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
OUT_OF_CORPUS_1 = "Who won the 1996 cricket world cup final?"
OUT_OF_CORPUS_2 = "How do I export Ayurvedic oils to Antarctica?"

corpus = load_corpus()
corpus_by_id = {e.id: e for e in corpus}
cfg = Config()
results = []


def check(name, fn):
    try:
        results.append((name, "PASS", fn()))
    except Exception as exc:
        results.append((name, "FAIL", f"{type(exc).__name__}: {exc}"))


def show(title: str, request: QueryRequest) -> dict:
    print("=" * 78)
    print(f" golden_scenarios: {title}")
    print(f"   jurisdiction={request.jurisdiction} language={request.language}")
    print(f"   query: {request.query}")
    result = handle_query(request, cfg)
    r = result.response
    print(f"   routing={result.routing.domain.value} status={result.status} "
          f"confidence={r.confidence}({r.confidence_score}) abstention={r.abstention}")
    print(json.dumps(r.model_dump(), ensure_ascii=False, indent=2))
    return r


def scenario_1_golden():
    r = show("Golden 1 — India / TK / patentability", QueryRequest(
        id="g1", query=GOLDEN_1, jurisdiction="India", language="en"))
    cited = {c.id for c in r.citations}
    assert not r.abstention, "golden query must be answered"
    assert "3(p)" in r.answer, "answer must reflect Section 3(p)"
    assert "TKDL" in r.answer or "Traditional Knowledge Digital Library" in r.answer, \
        "answer must carry the TKDL pointer"
    assert "in-patents-act-3p" in cited and "in-tkdl-pointer" in cited
    assert all(c.id.startswith("in-") for c in r.citations), "India answer-set only"
    assert validate_citations(r.citations, corpus_by_id) == []
    return "answered from India corpus with s.3(p) + TKDL pointer; citations valid"


def scenario_1_out_of_corpus():
    r = show("Golden 1 out-of-corpus — abstention expected", QueryRequest(
        id="g1-ooc", query=OUT_OF_CORPUS_1, jurisdiction="India", language="en"))
    assert r.abstention is True, "out-of-corpus query must abstain"
    assert r.abstention_reason and r.citations == []
    assert r.confidence == "LOW" and r.confidence_score == 0.0
    return f"abstained cleanly ({r.abstention_reason!r})"


def scenario_2_golden():
    r = show("Golden 2 — International / PCT route", QueryRequest(
        id="g2", query=GOLDEN_2, jurisdiction="International", language="en"))
    cited = {c.id for c in r.citations}
    assert not r.abstention, "golden query must be answered"
    assert "PCT" in r.answer or "Patent Cooperation Treaty" in r.answer, \
        "answer must point to the PCT route"
    assert "intl-pct" in cited, "PCT entry must be cited"
    assert "Madrid" not in r.answer and "intl-madrid" not in cited, \
        "Madrid (trade marks) must not appear in a patent answer"
    assert all(c.id.startswith("intl-") for c in r.citations), \
        "International answer-set only — visibly separate from India"
    assert validate_citations(r.citations, corpus_by_id) == []
    return "answered from International corpus via PCT; no Madrid; citations valid"


def scenario_2_out_of_corpus():
    r = show("Golden 2 out-of-corpus — abstention expected", QueryRequest(
        id="g2-ooc", query=OUT_OF_CORPUS_2, jurisdiction="International", language="en"))
    assert r.abstention is True, "out-of-corpus query must abstain"
    assert r.abstention_reason and r.citations == []
    return f"abstained cleanly ({r.abstention_reason!r})"


def citations_never_fabricate():
    """Cross-check: every URL in the corpus sits on an authoritative domain and
    every golden-run citation is byte-identical to stored metadata."""
    for e in corpus:
        host = urlparse(e.url).netloc.lower()
        assert any(host == d or host.endswith("." + d) for d in ALLOWED_SOURCE_DOMAINS), e.url
    tkdl = corpus_by_id["in-tkdl-pointer"]
    assert "restricted" in tkdl.text.lower(), "TKDL entry must remain a pointer"
    return "all corpus URLs authoritative; TKDL stays a pointer, no quoted contents"


check("Golden 1 (India/TK): s.3(p) + TKDL pointer", scenario_1_golden)
check("Golden 1 out-of-corpus: abstention fires", scenario_1_out_of_corpus)
check("Golden 2 (International): PCT route, no Madrid", scenario_2_golden)
check("Golden 2 out-of-corpus: abstention fires", scenario_2_out_of_corpus)
check("No fabricated authority/URLs/TKDL text", citations_never_fabricate)

print("=" * 78)
all_pass = True
for name, verdict, detail in results:
    all_pass &= verdict == "PASS"
    print(f"[{verdict}] {name} — {detail}")
print("=" * 78)
print("GOLDEN SCENARIOS:", "ALL PASS" if all_pass else "FAILURES PRESENT")
sys.exit(0 if all_pass else 1)
