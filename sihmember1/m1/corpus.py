"""Standalone demo corpus loading and validation for M1.

The corpus is a small controlled set of REAL authoritative-source excerpts
with real metadata (MEMBER_1.md §3), used only for independent development,
testing and controlled demo fallback. The loader enforces that every entry
carries complete metadata and that every URL points at an allow-listed
authoritative domain — the corpus file cannot silently introduce a
non-authoritative or invented source.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

CORPUS_PATH = Path(__file__).parent / "data" / "corpus.json"

# Authoritative public-source domains this workstream may cite (Research.md §D.1,
# PS.md dataset links). Hosts may carry "www." or other subdomains.
ALLOWED_SOURCE_DOMAINS = (
    "indiacode.nic.in",
    "ipindia.gov.in",
    "tkdl.res.in",
    "wipo.int",
    "wto.org",
    "nbaindia.org",
    "nbaindia.nic.in",
    "fssai.gov.in",
    "cdsco.gov.in",
)

VALID_JURISDICTIONS = ("India", "International")

REQUIRED_FIELDS = (
    "id",
    "jurisdiction",
    "source_name",
    "source_type",
    "section",
    "title",
    "text",
    "url",
    "effective_date",
    "keywords",
    "keywords_hi",
)


@dataclass
class Evidence:
    id: str
    jurisdiction: str
    source_name: str
    source_type: str
    section: str
    title: str
    text: str
    url: str
    effective_date: Optional[str]
    keywords: List[str] = field(default_factory=list)
    keywords_hi: List[str] = field(default_factory=list)
    verbatim: bool = False
    provenance: str = ""
    # Hindi rendering of the same curated excerpt (supported MVP scenarios
    # only). Always optional; the authoritative text is `text` at the URL.
    text_hi: Optional[str] = None


def _url_host_allowed(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_SOURCE_DOMAINS)


def validate_entry(raw: dict, index: int) -> None:
    where = f"corpus entry #{index} (id={raw.get('id', '?')!r})"
    missing = [k for k in REQUIRED_FIELDS if k not in raw]
    if missing:
        raise ValueError(f"{where}: missing required field(s): {missing}")
    if raw["jurisdiction"] not in VALID_JURISDICTIONS:
        raise ValueError(f"{where}: jurisdiction must be one of {VALID_JURISDICTIONS}")
    if not raw["url"].startswith("https://"):
        raise ValueError(f"{where}: url must be an https URL, got {raw['url']!r}")
    if not _url_host_allowed(raw["url"]):
        raise ValueError(
            f"{where}: url host {urlparse(raw['url']).netloc!r} is not in the "
            "authoritative-domain allow-list"
        )
    if len(raw["text"]) < 40:
        raise ValueError(f"{where}: excerpt text too short to be usable")
    if not isinstance(raw["keywords"], list) or not isinstance(raw["keywords_hi"], list):
        raise ValueError(f"{where}: keywords/keywords_hi must be lists")
    if "text_hi" in raw and raw["text_hi"] is not None and len(raw["text_hi"]) < 20:
        raise ValueError(f"{where}: text_hi present but too short to be usable")


def load_corpus(path: Path | str = CORPUS_PATH) -> List[Evidence]:
    """Load and validate the standalone corpus. Raises ValueError on any
    structural problem — the corpus is small, so failing fast is the safest
    behaviour for a demo-critical file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries: List[Evidence] = []
    seen_ids: set[str] = set()
    for i, raw in enumerate(data.get("entries", [])):
        validate_entry(raw, i)
        if raw["id"] in seen_ids:
            raise ValueError(f"corpus entry #{i}: duplicate id {raw['id']!r}")
        seen_ids.add(raw["id"])
        entries.append(
            Evidence(
                id=raw["id"],
                jurisdiction=raw["jurisdiction"],
                source_name=raw["source_name"],
                source_type=raw["source_type"],
                section=raw["section"],
                title=raw["title"],
                text=raw["text"],
                url=raw["url"],
                effective_date=raw["effective_date"],
                keywords=[k.lower() for k in raw["keywords"]],
                keywords_hi=list(raw["keywords_hi"]),
                verbatim=bool(raw.get("verbatim", False)),
                provenance=raw.get("provenance", ""),
                text_hi=raw.get("text_hi"),
            )
        )
    if not entries:
        raise ValueError("corpus is empty")
    return entries
