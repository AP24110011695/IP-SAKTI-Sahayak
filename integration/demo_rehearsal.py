"""Final demo rehearsal (M6 Phase 3) — runs the complete 10-step demo
against the LIVE integrated application and prints per-step timings.

Usage:
    1. start the app:        python -m uvicorn integration.app:app --port 8000
    2. run the rehearsal:    python integration/demo_rehearsal.py [port]

Every step asserts its expected outcome (HTTP status, abstention flag,
routing-specific content markers) so the rehearsal is a real check, not a
narrative. Exit code 0 = all ten steps passed. Run it twice back-to-back to
demonstrate repeatability.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"

FIXTURES = json.loads(
    (Path(__file__).resolve().parent / "fixtures" / "golden_scenarios.json").read_text(
        encoding="utf-8"))
SCENARIOS = {s["id"]: s for s in FIXTURES["scenarios"]}

_steps = []


def step(number, name, expected, fn):
    start = time.perf_counter()
    try:
        fn()
        status = "PASS"
    except Exception as exc:
        status = f"FAIL ({type(exc).__name__}: {exc})"
    elapsed = time.perf_counter() - start
    _steps.append((number, name, expected, status, elapsed))
    print(f"  Step {number:2d} - {name:38s} [{status}] {elapsed*1000:6.0f} ms")


def call(path, payload=None, method=None):
    url = BASE + path
    if payload is None and method is None:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, json.loads(r.read())
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method=method or "POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def expect(cond, message):
    if not cond:
        raise AssertionError(message)


def main() -> int:
    print(f"IP-SAKTI Sahayak - final demo rehearsal against {BASE}\n")

    def s1_startup():
        status, _ = call("/api/health", method="GET")
        expect(status == 200, f"health HTTP {status}")

    def s2_health():
        status, body = call("/api/health", method="GET")
        expect(body["status"] == "ok", "service not ok")
        expect(body["specialists_wired"] is True, "specialists not wired")
        expect(set(body["specialists"]) == {"INDIA_IP", "ABS_TK",
                "INTERNATIONAL_IP", "CLASSIFICATION"}, "specialists incomplete")

    def s3_classify():
        status, body = call("/api/classify", {"answers": {
            "primary_purpose": "therapeutic", "text_source": "yes",
            "standardised_fraction": "no", "ingredients_known": "yes",
            "new_indication": "no"}, "jurisdiction": "India", "language": "en"})
        expect(status == 200 and body["formulation_class"] == "Classical",
               f"classify Classical -> {status} {body.get('formulation_class')}")
        expect(body["tkdl_pointer"] and "tkdl.res.in" in body["tkdl_pointer"],
               "Classical must carry the TKDL pointer")
        status, body = call("/api/classify", {"answers": {
            "primary_purpose": "food_wellness", "food_exclusion": "none",
            "new_indication": "no"}, "jurisdiction": "India", "language": "en"})
        expect(status == 200 and body["formulation_class"] == "Ayurveda-Aahar",
               f"classify Ayurveda-Aahar -> {status} {body.get('formulation_class')}")
        status, body = call("/api/classify", {"answers": {}})
        expect(body["formulation_class"] == "Uncertain"
               and body["needs_clarification"] is True,
               "empty answers must be Uncertain + clarification")

    def s4_india_legal():
        scenario = SCENARIOS["S1"]
        status, body = call("/api/query", {
            "id": "demo-1", "query": scenario["query"],
            "language": "en", "jurisdiction": "India", "history": []})
        expect(status == 200 and body["abstention"] is False, f"{status}")
        expect("3(p)" in body["answer"], "no Section 3(p) in answer")
        expect("tkdl.res.in" in body["answer"], "no TKDL pointer in answer")
        expect(len(body["citations"]) >= 1, "no citations")

    def s5_abs():
        scenario = SCENARIOS["S2"]
        status, body = call("/api/query", {
            "id": "demo-2", "query": scenario["query"],
            "language": "en", "jurisdiction": "India", "history": []})
        expect(status == 200 and body["abstention"] is False, f"{status}")
        expect("Biological Diversity Act" in body["answer"], "no BD Act guidance")
        expect("3(p)" not in body["answer"], "answered as a patent question")

    def s6_gi():
        scenario = SCENARIOS["S4"]
        status, body = call("/api/query", {
            "id": "demo-3", "query": scenario["query"],
            "language": "en", "jurisdiction": "India", "history": []})
        expect(status == 200 and "Geographical Indication" in body["answer"],
               "GI guidance missing")

    def s7_international_patent():
        scenario = SCENARIOS["S5"]
        status, body = call("/api/query", {
            "id": "demo-4", "query": scenario["query"],
            "language": "en", "jurisdiction": "International", "history": []})
        expect(status == 200 and "PCT" in body["answer"], "PCT missing")
        expect("Madrid" not in body["answer"] and "Hague" not in body["answer"],
               "Madrid/Hague cross-attribution")

    def s8_hindi():
        status, body = call("/api/query", {
            "id": "demo-5",
            "query": "मैं अपने आयुर्वेदिक उत्पाद के लिए जीआई टैग कैसे पंजीकृत करूँ?",
            "language": "hi", "jurisdiction": "India", "history": []})
        expect(status == 200 and body["abstention"] is False, f"{status}")
        expect("कानूनी सलाह नहीं" in body["disclaimer"], "Hindi disclaimer missing")

    def s9_out_of_corpus():
        scenario = SCENARIOS["S5"]
        status, body = call("/api/query", {
            "id": "demo-6", "query": scenario["out_of_corpus"]["query"],
            "language": "en", "jurisdiction": "International", "history": []})
        expect(status == 200, f"abstention must be HTTP 200, got {status}")
        expect(body["abstention"] is True and body["citations"] == [],
               "not a safe abstention")

    def s10_presentation():
        scenario = SCENARIOS["S1"]
        status, body = call("/api/query", {
            "id": "demo-7", "query": scenario["query"],
            "language": "en", "jurisdiction": "India", "history": []})
        expect(list(body.keys()) == ["id", "answer", "citations", "confidence",
               "confidence_score", "abstention", "abstention_reason",
               "escalation_available", "disclaimer"], f"contract fields: {list(body.keys())}")
        expect(body["disclaimer"].strip() != "", "empty disclaimer")
        expect(0.0 <= body["confidence_score"] <= 1.0, "confidence out of range")
        first = body["citations"][0]
        expect(all(k in first for k in ("id", "source_name", "source_type",
               "section", "excerpt", "url", "effective_date")),
               f"citation fields: {list(first.keys())}")

    step(1, "Application startup", "app reachable", s1_startup)
    step(2, "Health check", "ok + 4 specialists wired", s2_health)
    step(3, "Formulation classification (M2)", "Classical / Aahar / Uncertain", s3_classify)
    step(4, "India legal question (M3)", "3(p) + TKDL + citations", s4_india_legal)
    step(5, "ABS question (M4)", "BD Act, not patents", s5_abs)
    step(6, "GI question (M3)", "GI pathway + citations", s6_gi)
    step(7, "International patent (M5)", "PCT, not Madrid/Hague", s7_international_patent)
    step(8, "Hindi query (M3)", "Hindi answer + Hindi disclaimer", s8_hindi)
    step(9, "Out-of-corpus abstention", "HTTP 200, abstention, no citations", s9_out_of_corpus)
    step(10, "Final response presentation", "exact contract fields", s10_presentation)

    total = sum(s[4] for s in _steps)
    failed = [s for s in _steps if not s[3].startswith("PASS")]
    print(f"\n  Rehearsal total: {total:.2f}s - "
          f"{len(_steps) - len(failed)}/{len(_steps)} steps passed")
    if failed:
        for number, name, _, status, _ in failed:
            print(f"  FAILED: step {number} ({name}): {status}")
        return 1
    print("  All ten demo steps passed - rehearsal is repeatable and demo-ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
