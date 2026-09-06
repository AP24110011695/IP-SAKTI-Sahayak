"""Run the Phase 1 scenarios against the standalone M1 build and print real
output.

Works without an LLM API key (deterministic extractive mode). Set LLM_API_KEY
(+ optional LLM_BASE_URL / LLM_MODEL) to exercise the hosted-LLM generator on
the same scenarios.

Usage:  python scripts/demo.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from m1.assistant import handle_query  # noqa: E402
from m1.config import Config  # noqa: E402
from m1.models import QueryRequest  # noqa: E402

GOLDEN_1 = (
    "Can I patent a classical Ayurvedic formulation from an authoritative text?"
)
GOLDEN_2 = (
    "I want to file a patent for a new Ayurvedic drug outside India — "
    "what route do I use?"
)
ABS_QUERY = (
    "I want to commercialise a formulation using traditional knowledge and a "
    "biological resource — what benefit sharing applies?"
)

# (title, query, jurisdiction, language, specialists_wired)
SCENARIOS = [
    ("1. Golden India/TK query", GOLDEN_1, "India", "en", False),
    ("2. Golden International/PCT query", GOLDEN_2, "International", "en", False),
    (
        "3. Same patent question, India jurisdiction",
        "How do I file a patent application for my Ayurvedic product?",
        "India",
        "en",
        False,
    ),
    (
        "4. Same patent question, International jurisdiction",
        "How do I file a patent application for my Ayurvedic product?",
        "International",
        "en",
        False,
    ),
    (
        "5. Out-of-corpus query (abstention expected)",
        "What is the airspeed of an unladen swallow?",
        "India",
        "en",
        False,
    ),
    (
        "6. Hindi query (supported scenario)",
        "पारंपरिक ज्ञान पर पेटेंट कर सकते हैं क्या?",
        "India",
        "hi",
        False,
    ),
    (
        "7a. ABS/TK query, specialists NOT wired (standalone demo path)",
        ABS_QUERY,
        "India",
        "en",
        False,
    ),
    (
        "7b. ABS/TK query, specialists wired but unavailable (corpus-safety abstention)",
        ABS_QUERY,
        "India",
        "en",
        True,
    ),
    (
        "8. Weak evidence query (sufficiency-threshold abstention)",
        "act",
        "India",
        "en",
        False,
    ),
]


def show(cfg: Config, title: str, request: QueryRequest) -> None:
    print("=" * 78)
    print(f"SCENARIO {title}")
    print(
        f"  request : jurisdiction={request.jurisdiction} "
        f"language={request.language} specialists_wired={cfg.specialists_wired}"
    )
    print(f"  query   : {request.query}")
    result = handle_query(request, cfg)
    print(f"  routing : {result.routing.domain.value} ({result.routing.rationale})")
    print(f"  status  : {result.status}  generator={result.generator_used}")
    r = result.response
    print(
        f"  answer  : confidence={r.confidence} ({r.confidence_score}) "
        f"abstention={r.abstention}"
    )
    print("  --- response JSON ---")
    print(json.dumps(r.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    default_cfg = Config()
    print(
        f"generator_mode={default_cfg.generator_mode} "
        "(set LLM_API_KEY for hosted-LLM mode)"
    )
    for title, query, jurisdiction, language, wired in SCENARIOS:
        cfg = Config(specialists_wired=wired)
        req = QueryRequest(
            id="demo", query=query, jurisdiction=jurisdiction, language=language
        )
        show(cfg, title, req)
    print("=" * 78)
