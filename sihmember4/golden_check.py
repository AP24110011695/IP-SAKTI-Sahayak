"""Member 4 — Phase 1 verification run (real output for the phase report).

Demonstrates the retrieval seam against the Section 7 golden ABS scenario and
the safety checks, using only the verified Phase 1 corpus. Phase 2 will turn
retrieved evidence into guidance; this script only shows what evidence is
found (or not found).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import corpus
import retrieval

SCENARIOS = [
    ("GOLDEN ABS (Plan.md section 13 #2)",
     "I want to commercialise a formulation using a plant collected in India "
     "- what approvals do I need?"),
    ("OUT-OF-CORPUS ABS TOPIC (must return no evidence)",
     "How do I export herbal medicinal products to the EU - what EU "
     "registration do I need?"),
    ("UNRELATED TRADEMARK-ONLY (must not be flagged ABS)",
     "How do I register a trademark for my herbal tea brand in India?"),
    ("NAGOYA / TK (treaty layer support)",
     "Nagoya Protocol prior informed consent for genetic resources"),
    ("PRIOR-ART / TKDL POINTER (pointer behaviour)",
     "is my ayurvedic traditional knowledge prior art"),
]


def main():
    for title, query in SCENARIOS:
        print("=" * 78)
        print(f"SCENARIO: {title}")
        print(f"QUERY: {query}")
        results = retrieval.retrieve(query)
        if not results:
            print("RESULT: NO EVIDENCE in the M4 corpus (Phase 2 must abstain, not answer)")
            continue
        print(f"RESULT: {len(results)} record(s) retrieved")
        for item in results:
            record = item["record"]
            print(f"  - {record['id']}  score={item['score']:.1f}  "
                  f"[{record['source_type']}/{record['jurisdiction']}]")
            print(f"    {record['source_name']}")
            print(f"    {record['section']}")
            print(f"    url: {record['url']}")
            if record["tkdl_pointer_record"]:
                print(f"    TKDL POINTER: {record['pointer_guidance']}")
        print()


if __name__ == "__main__":
    main()
