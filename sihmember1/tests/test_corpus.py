"""Corpus integrity tests: real metadata, authoritative URLs, both
jurisdictions, honest TKDL handling."""
import json
from urllib.parse import urlparse

import pytest

from m1.corpus import ALLOWED_SOURCE_DOMAINS, load_corpus


@pytest.fixture(scope="module")
def corpus():
    return load_corpus()


def test_corpus_size_within_cap(corpus):
    assert 8 <= len(corpus) <= 15


def test_unique_ids(corpus):
    ids = [e.id for e in corpus]
    assert len(ids) == len(set(ids))


def test_complete_metadata(corpus):
    for e in corpus:
        assert e.id
        assert e.source_name
        assert e.source_type
        assert e.section
        assert e.title
        assert len(e.text) >= 40
        assert e.jurisdiction in ("India", "International")
        assert e.url.startswith("https://")
        assert e.effective_date is None or isinstance(e.effective_date, str)


def test_urls_are_authoritative_only(corpus):
    for e in corpus:
        host = urlparse(e.url).netloc.lower()
        assert any(
            host == d or host.endswith("." + d) for d in ALLOWED_SOURCE_DOMAINS
        ), f"non-authoritative URL in corpus: {e.url}"


def test_both_jurisdictions_covered(corpus):
    jurisdictions = {e.jurisdiction for e in corpus}
    assert jurisdictions == {"India", "International"}
    assert sum(1 for e in corpus if e.jurisdiction == "India") >= 3
    assert sum(1 for e in corpus if e.jurisdiction == "International") >= 3


def test_tkdl_entry_is_pointer_not_quoted_content(corpus):
    tkdl = [e for e in corpus if e.id == "in-tkdl-pointer"]
    assert len(tkdl) == 1
    entry = tkdl[0]
    text = entry.text.lower()
    # TKDL full text is NDA-restricted: the entry must describe the
    # restriction and point to the portal, never pretend to quote contents.
    assert "restricted" in text or "non-disclosure" in text
    assert "tkdl.res.in" in entry.url


def test_hindi_renderings_present_for_supported_scenarios(corpus):
    by_id = {e.id: e for e in corpus}
    for entry_id in (
        "in-patents-act-3p",
        "in-patents-act-10-4d",
        "in-patents-rules-2024",
        "in-cgpdtm-ayush-guidelines-2025",
        "in-tkdl-pointer",
        "intl-pct",
    ):
        assert by_id[entry_id].text_hi, f"{entry_id} must carry a Hindi rendering"
        assert len(by_id[entry_id].text_hi) >= 20


def test_hindi_renderings_are_optional_and_validated(corpus):
    for e in corpus:
        assert e.text_hi is None or len(e.text_hi) >= 20


def test_loader_rejects_non_authoritative_url(tmp_path):
    bad = {
        "entries": [
            {
                "id": "x",
                "jurisdiction": "India",
                "source_name": "s",
                "source_type": "t",
                "section": "s",
                "title": "t",
                "text": "x" * 60,
                "url": "https://example.com/law",
                "effective_date": None,
                "keywords": [],
                "keywords_hi": [],
            }
        ]
    }
    p = tmp_path / "corpus.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError):
        load_corpus(p)


def test_loader_rejects_duplicate_ids(tmp_path):
    entry = {
        "id": "dup",
        "jurisdiction": "India",
        "source_name": "s",
        "source_type": "t",
        "section": "s",
        "title": "t",
        "text": "x" * 60,
        "url": "https://ipindia.gov.in",
        "effective_date": None,
        "keywords": [],
        "keywords_hi": [],
    }
    p = tmp_path / "corpus.json"
    p.write_text(json.dumps({"entries": [entry, dict(entry)]}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_corpus(p)
