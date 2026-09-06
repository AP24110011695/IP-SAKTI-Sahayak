"""Member 4 — Phase 3 demo run (real output for the phase report).

Runs every canonical Phase 3 scenario through the full pipeline, prints the
complete result contract, and executes the citation, TKDL-content, contract
and source audits. Offline stand-in mode (no LLM credentials configured; the
hosted path is implemented but no live API call is made or faked).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")

import guidance  # noqa: E402
import llm_client  # noqa: E402
import phase3_scenarios as p3  # noqa: E402


def main():
    mode, _ = llm_client.get_llm_client()
    print(f"LLM MODE: {mode} (hosted path implemented; no live API call made)\n")
    results = p3.run_all()
    for name, query, expectation, result in results:
        print("=" * 78)
        print(f"SCENARIO: {name}  (expectation: {expectation})")
        print(f"QUERY: {query}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()

    print("#" * 78)
    report = p3.audit_all(results)
    total_violations = sum(len(v) for v in report.values())
    print(f"CITATION + CONTRACT + TKDL AUDIT: {total_violations} violation(s)")
    for name, violations in report.items():
        print(f"  {name}: {'CLEAN' if not violations else violations}")
    source = p3.source_audit()
    print(f"SOURCE-CORRECTNESS AUDIT: {len(source)} violation(s)")
    for v in source:
        print("  ", v)


if __name__ == "__main__":
    main()
