#!/usr/bin/env python3
"""Run the complete Member 5 golden and safety scenario set."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from member5.guidance import guide  # noqa: E402
from member5.llm import DeterministicEvidenceClient  # noqa: E402


SCENARIOS = [
    ("patent_golden", "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?", "en"),
    ("trademark", "I want to register my Ayurvedic brand name internationally.", "en"),
    ("industrial_design", "How can I protect my packaging as an industrial design internationally?", "en"),
    ("out_of_corpus", "How is spacecraft lease depreciation taxed?", "en"),
    ("unsupported_export", "What approvals and labels do I need to export an Ayurvedic supplement to Japan?", "en"),
    ("patent_and_trademark", "How do I protect both the patent and trademark for my Ayurvedic product internationally?", "en"),
    ("all_three_rights", "I need patent, trademark, and industrial design protection internationally.", "en"),
    ("india_only", "What is the patent filing procedure in India?", "en"),
    ("ambiguous", "How can I protect my Ayurvedic product internationally?", "en"),
    ("patent_hi", "मैं अपनी नई आयुर्वेदिक दवा के लिए भारत के बाहर पेटेंट दाखिल करना चाहता हूँ।", "hi"),
    ("trademark_hi", "मैं अपना आयुर्वेदिक ब्रांड अंतरराष्ट्रीय रूप से पंजीकृत करना चाहता हूँ।", "hi"),
]


def main() -> None:
    client = DeterministicEvidenceClient()
    for name, query, language in SCENARIOS:
        result = guide(query, language=language, client=client)
        print(
            json.dumps(
                {
                    "scenario": name,
                    "status": result["status"],
                    "answer": result["answer"],
                    "citation_ids": [item["id"] for item in result["citations"]],
                    "confidence": result["confidence"],
                    "confidence_score": result["confidence_score"],
                    "abstention": result["abstention"],
                    "abstention_reason": result["abstention_reason"],
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()

