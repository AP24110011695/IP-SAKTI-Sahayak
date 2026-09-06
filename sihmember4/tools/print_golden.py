"""Print the final clean golden-scenario output for the phase report."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import guidance  # noqa: E402

result = guidance.answer(
    "I want to commercialise a formulation using a plant collected in India "
    "- what approvals do I need?"
)
print("ANSWER:")
print(result["answer"])
print()
print("IDS:", [c["id"] for c in result["citations"]])
print("CONF:", result["confidence"], result["confidence_score"])
print("STATUS:", result["status"], "| TKDL POINTER:", result["tkdl_pointer"])
