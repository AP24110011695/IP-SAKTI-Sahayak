"""Load and deterministically search the curated Phase 1 source corpus.

This module deliberately performs no answer generation.  Its small lexical search
function is only a stable seam for Phase 1 validation and later Phase 2 extension.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CORPUS_PATH = Path(__file__).with_name("data") / "international_sources.json"

SYSTEM_RIGHTS = {
    "PCT": "patent",
    "Madrid": "trademark",
    "Hague": "industrial_design",
}

RIGHT_TERMS = {
    "patent": {"patent", "patents", "invention", "inventions"},
    "trademark": {"trademark", "trademarks", "brand", "brands", "logo", "mark"},
    "industrial_design": {
        "design",
        "designs",
        "packaging",
        "shape",
        "appearance",
        "ornamental",
    },
}


def load_sources(path: Path = CORPUS_PATH) -> list[dict[str, Any]]:
    """Return corpus records in their stored order."""

    with path.open(encoding="utf-8") as corpus_file:
        payload = json.load(corpus_file)
    return payload["sources"]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _requested_right(query_tokens: set[str]) -> str | None:
    matches = [
        right for right, terms in RIGHT_TERMS.items() if query_tokens.intersection(terms)
    ]
    return matches[0] if len(matches) == 1 else None


def retrieve_sources(
    query: str, *, limit: int = 4, minimum_score: int = 2
) -> list[dict[str, Any]]:
    """Return deterministic lexical matches without producing legal guidance.

    If a query clearly names one IP right, records for the other two filing systems
    are excluded.  This makes the PCT/Madrid/Hague mapping invariant explicit at
    the retrieval boundary.
    """

    query_tokens = _tokens(query)
    requested_right = _requested_right(query_tokens)
    scored: list[tuple[int, int, dict[str, Any]]] = []

    for position, source in enumerate(load_sources()):
        system = source["system"]
        if requested_right and system in SYSTEM_RIGHTS:
            if source["ip_right"] != requested_right:
                continue

        keyword_score = len(query_tokens.intersection(set(source["keywords"])))
        right_bonus = 3 if requested_right == source["ip_right"] else 0
        score = keyword_score + right_bonus
        if score >= minimum_score:
            scored.append((score, position, source))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [source for _, _, source in scored[:limit]]

