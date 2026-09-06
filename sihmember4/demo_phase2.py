"""Member 4 — Phase 2 verification run (real output for the phase report).

Runs the required scenarios through the full guidance pipeline and prints
the complete Member 4 result contract. Runs in offline stand-in mode (no LLM
credentials configured in this environment; the hosted path is implemented
but no live API call is made or faked).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import guidance  # noqa: E402
import llm_client  # noqa: E402

SCENARIOS = [
    ("1. ABS GOLDEN (EN)", "I want to commercialise a formulation using a plant collected in India - what approvals do I need?"),
    ("2. ABS GOLDEN (HI)", "मैं भारत में एकत्रित पौधों से बने फॉर्मूलेशन का व्यावसायिक उपयोग करना चाहता हूँ - मुझे क्या अनुमोदन चाहिए?"),
    ("3. UNRELATED TRADEMARK (EN)", "How do I register a trademark for my Ayurvedic brand?"),
    ("4. OUT-OF-CORPUS ABS", "How do I export herbal medicinal products to the EU - what EU registration do I need?"),
    ("5. TRADITIONAL KNOWLEDGE / TKDL POINTER", "Can I patent a classical Ayurvedic formulation from an authoritative text?"),
    ("6. UNSUPPORTED FEE QUESTION", "How much is the NBA processing fee for a Form 2 application?"),
    ("7. TK PRIOR-ART QUERY (answered + pointer)", "is my ayurvedic traditional knowledge prior art"),
]


def main():
    mode, _ = llm_client.get_llm_client()
    print(f"LLM MODE: {mode} (hosted path implemented; no live API call made)\n")
    for title, query in SCENARIOS:
        result = guidance.answer(query)
        print("=" * 78)
        print(f"SCENARIO: {title}")
        print(f"QUERY: {query}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()


if __name__ == "__main__":
    main()
