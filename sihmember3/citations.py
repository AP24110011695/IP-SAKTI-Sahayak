"""Member 3 Phase 2 — citations and citation validation.

Citations are the project Citation shape (Plan.md Section 7):

    id, source_name, source_type, section, excerpt, url, effective_date

The LLM NEVER produces citation metadata. Citations are built here, strictly
from stored Phase 1 corpus records, and every citation is validated against
the stored record before a result is returned: every one of the seven fields
must exist and match the stored record exactly. Any mismatch — an invented
URL, a tampered section number, a truncated excerpt — is rejected, and the
guidance layer abstains rather than ship an untraceable citation.
"""

from .sources import SOURCE_TYPES, all_sources

CITATION_FIELDS = (
    "id",
    "source_name",
    "source_type",
    "section",
    "excerpt",
    "url",
    "effective_date",
)


def build_citation(record):
    """Build a Citation dict from a stored corpus record (exact 7 fields)."""
    return {field: record[field] for field in CITATION_FIELDS}


def build_citations(records):
    """Build citations for an ordered list of corpus records."""
    return [build_citation(record) for record in records]


def _corpus_by_id(sources=None):
    return {record["id"]: record for record in (sources if sources is not None else all_sources())}


def validate_citation(citation, corpus_by_id=None):
    """Validate one citation against the stored corpus.

    Returns a list of problems (empty list = valid). A citation is valid only
    if its id maps to a real stored record AND every field matches that
    record exactly — so any fabricated metadata is caught."""
    if not isinstance(citation, dict):
        return ["citation must be a dict, got %s" % type(citation).__name__]
    problems = []
    if citation.get("id") is None:
        return ["citation missing id"]
    lookup = corpus_by_id if corpus_by_id is not None else _corpus_by_id()
    record = lookup.get(citation["id"])
    if record is None:
        return ["citation id %r does not map to any stored source record" % (citation["id"],)]
    for field in CITATION_FIELDS:
        if field not in citation:
            problems.append("missing citation field: %s" % field)
            continue
        if citation[field] != record[field]:
            problems.append(
                "citation field %r does not match the stored record (fabricated "
                "or altered metadata)" % field
            )
    return problems


def validate_citations(citations, corpus_by_id=None):
    """Validate a list of citations. Returns a flat list of problems, each
    prefixed with the offending citation id (empty list = all valid)."""
    lookup = corpus_by_id if corpus_by_id is not None else _corpus_by_id()
    problems = []
    seen_ids = set()
    for position, citation in enumerate(citations):
        for problem in validate_citation(citation, lookup):
            problems.append("citations[%d] (%r): %s" % (position, citation.get("id"), problem))
        if isinstance(citation, dict):
            if citation.get("id") in seen_ids:
                problems.append(
                    "citations[%d]: duplicate citation id %r" % (position, citation.get("id"))
                )
            seen_ids.add(citation.get("id"))
            if citation.get("source_type") not in SOURCE_TYPES:
                problems.append(
                    "citations[%d] (%r): unknown source_type %r"
                    % (position, citation.get("id"), citation.get("source_type"))
                )
    return problems
