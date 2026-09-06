"""Member 4 Phase 3 — canonical scenario registry + audits.

Shared by tests/test_phase3.py and demo_phase3.py so the Phase 3 acceptance
scenarios, the citation audit, the contract audit and the TKDL-content audit
are defined once and always run identically.
"""

import re

import corpus
import guidance

GOLDEN_EN = (
    "I want to commercialise a formulation using a plant collected in India "
    "- what approvals do I need?"
)
GOLDEN_HI = (
    "मैं भारत में एकत्रित पौधों से बने फॉर्मूलेशन का व्यावसायिक उपयोग करना "
    "चाहता हूँ - मुझे क्या अनुमोदन चाहिए?"
)
PART_ABS_PATENT = (
    "I want to patent a new herbal formulation using a plant collected from "
    "a forest in India - what approvals do I need?"
)
NBA_BEFORE_PATENT = (
    "Do I need NBA approval before patenting my neem-based product?"
)
SPECIES_QUERY = (
    "I want to commercialise a product using Ashwagandha collected in India "
    "- what approvals do I need?"
)
SPECIES_EXEMPTION_PROBE = "Is Ashwagandha exempt from NBA approval?"
TK_QUERY = "is my ayurvedic traditional knowledge prior art"
TKDL_POINTER_QUERY = (
    "Can I patent a classical Ayurvedic formulation from an authoritative text?"
)
TKDL_DETAILS_QUERY = (
    "How many formulations does TKDL contain and what did TKDL say about turmeric?"
)
TRADEMARK_QUERY = "How do I register a trademark for my Ayurvedic brand?"
INTERNATIONAL_QUERY = (
    "How do I register a trademark internationally under the Madrid Protocol?"
)
INTERNATIONAL_EXPORT_QUERY = (
    "How do I export herbal medicinal products to the EU - what EU "
    "registration do I need?"
)
UNSUPPORTED_FEE_QUERY = "How much is the NBA processing fee for a Form 2 application?"

# (name, query, expectation) - expectation drives the audits:
#   ok:            status ok, citations present and valid
#   ok_pointer:    status ok, citations valid, tkdl_pointer present
#   abstain:       abstained, no citations, reason present
#   abstain_ptr:   abstained, no citations, tkdl_pointer present
SCENARIOS = [
    ("golden_en", GOLDEN_EN, "ok"),
    ("golden_hi", GOLDEN_HI, "ok"),
    ("tk_query", TK_QUERY, "ok_pointer"),
    ("tkdl_pointer_query", TKDL_POINTER_QUERY, "abstain_ptr"),
    ("tkdl_details_query", TKDL_DETAILS_QUERY, "abstain_ptr"),
    ("edge_part_abs_patent", PART_ABS_PATENT, "ok"),
    ("edge_nba_before_patent", NBA_BEFORE_PATENT, "ok"),
    ("edge_species", SPECIES_QUERY, "ok"),
    ("edge_species_exemption_probe", SPECIES_EXEMPTION_PROBE, "abstain"),
    ("edge_unrelated_trademark", TRADEMARK_QUERY, "abstain"),
    ("edge_international_madrid", INTERNATIONAL_QUERY, "abstain"),
    ("edge_international_export", INTERNATIONAL_EXPORT_QUERY, "abstain"),
    ("edge_unsupported_fee", UNSUPPORTED_FEE_QUERY, "abstain"),
]


def run_all():
    """Run every canonical scenario -> [(name, query, expectation, result)]."""
    return [
        (name, query, expectation, guidance.answer(query))
        for name, query, expectation in SCENARIOS
    ]


# ---------------------------------------------------------------------------
# Audits
# ---------------------------------------------------------------------------

# Banned TKDL-specific patterns: any match in an output is a fabrication
# (the verified corpus contains no TKDL counts, records, entries, outcomes
# or restricted content, so none of these can ever be supported).
TKDL_BANNED_PATTERNS = (
    re.compile(r"tkdl\s+(?:says|contains|has|lists|documents|holds|includes|shows)\b", re.I),
    re.compile(r"tkdl\s+(?:database\s+)?(?:entr(?:y|ies)|record)s?\b", re.I),
    re.compile(r"tkdl\s+.{0,60}?(?:revoked|rejected|granted|opposed)\b", re.I),
    re.compile(r"\b\d[\d,\.]*\s+(?:formulations?|records?|entries|manuscripts?)\b", re.I),
    re.compile(r"\b\d[\d,\.]*\s+(?:patent applications?)\s+(?:blocked|revoked|withdrawn)", re.I),
    re.compile(r"\b(?:lakh|crore|million|billion)\s+(?:formulations?|records?|entries)\b", re.I),
)

_ALLOWED_POINTER_HOST = "tkdl.res.in"


def audit_tkdl_output(result):
    """Scan every text field of one result for fabricated TKDL content.
    Returns a list of violation strings (empty = clean)."""
    violations = []
    texts = [result.get("answer") or "", result.get("tkdl_pointer") or "",
             result.get("abstention_reason") or ""]
    texts += [
        str(c.get("excerpt") or "") + " " + str(c.get("section") or "")
        for c in result.get("citations", [])
    ]
    for text in texts:
        for pattern in TKDL_BANNED_PATTERNS:
            found = pattern.search(text)
            if found:
                violations.append(f"TKDL fabrication pattern {found.group(0)!r} in: {text[:80]!r}")
    pointer = result.get("tkdl_pointer")
    if pointer is not None and "tkdl.res.in" not in pointer:
        violations.append("tkdl_pointer present without the tkdl.res.in reference")
    return violations


def audit_citations(result):
    """Every citation must map exactly onto a stored Phase 1 record and the
    generated text must only make claims the cited evidence supports.
    Returns a list of violation strings."""
    violations = []
    ids_seen = set()
    for citation in result.get("citations", []):
        ok_flag, reason = guidance.validate_citation(citation)
        if not ok_flag:
            violations.append(f"citation validation failed: {reason}")
        if citation["id"] in ids_seen:
            violations.append(f"duplicate citation id: {citation['id']}")
        ids_seen.add(citation["id"])
    if result.get("status") == "ok":
        ok_flag, reason = guidance.validate_generated(result["answer"], result["citations"])
        if not ok_flag:
            violations.append(f"content validation failed: {reason}")
        if not result["citations"]:
            violations.append("ok result without citations")
    return violations


def audit_contract(result):
    """Exact Member 4 RAG Result + Citation contract. Returns violations."""
    violations = []
    expected = {"answer", "citations", "confidence", "confidence_score",
                "abstention", "abstention_reason", "status", "tkdl_pointer"}
    if set(result.keys()) != expected:
        violations.append(f"result fields mismatch: {sorted(result.keys())}")
        return violations
    if not isinstance(result["answer"], str):
        violations.append("answer not a string")
    if result["confidence"] not in ("HIGH", "MEDIUM", "LOW"):
        violations.append(f"bad confidence label: {result['confidence']!r}")
    score = result["confidence_score"]
    if not isinstance(score, float) or not 0.0 <= score <= 1.0:
        violations.append(f"confidence_score out of range/type: {score!r}")
    if not isinstance(result["abstention"], bool):
        violations.append("abstention not boolean")
    if result["status"] not in ("ok", "abstained", "processing_error"):
        violations.append(f"bad status: {result['status']!r}")
    if result["tkdl_pointer"] is not None and not isinstance(result["tkdl_pointer"], str):
        violations.append("tkdl_pointer neither null nor string")
    if result["status"] == "ok":
        if result["abstention"] or result["abstention_reason"] is not None:
            violations.append("ok result must not carry abstention flags")
        if not result["citations"]:
            violations.append("ok result without citations")
    elif result["status"] == "abstained":
        if not result["abstention"] or not result["abstention_reason"]:
            violations.append("abstained result must set abstention + reason")
        if result["citations"]:
            violations.append("abstained result must not carry citations")
    if result["status"] == "processing_error" and not result["abstention"]:
        violations.append("processing_error must set abstention")
    for citation in result.get("citations", []):
        if set(citation.keys()) != {"id", "source_name", "source_type", "section",
                                    "excerpt", "url", "effective_date"}:
            violations.append(f"citation field mismatch on {citation.get('id')!r}")
    return violations


def audit_all(results):
    """Full Phase 3 audit over scenario outputs -> {name: [violations]}."""
    report = {}
    for name, _query, expectation, result in results:
        violations = []
        violations += audit_contract(result)
        violations += audit_citations(result)
        violations += audit_tkdl_output(result)
        status = result["status"]
        if expectation == "ok" and status != "ok":
            violations.append(f"expected ok, got {status}: {result['abstention_reason']}")
        if expectation == "ok_pointer" and status != "ok":
            violations.append(f"expected ok_pointer, got {status}: {result['abstention_reason']}")
        if expectation.startswith("ok") and result["tkdl_pointer"] is None and name == "tk_query":
            violations.append("tk_query must carry a TKDL pointer")
        if expectation.startswith("abstain_ptr") and result["tkdl_pointer"] is None:
            violations.append("expected a TKDL pointer alongside abstention")
        if expectation == "abstain" and result["tkdl_pointer"] is not None:
            violations.append("unexpected TKDL pointer on a non-TK abstention")
        report[name] = violations
    return report


def source_audit():
    """Source-correctness audit over the Phase 1 corpus (static checks).
    Returns a list of violation strings."""
    violations = []
    for record in corpus.SOURCE_RECORDS:
        prov = record["provenance"]
        for key in ("verified_on", "verification_method", "document_identity"):
            if not str(prov.get(key) or "").strip():
                violations.append(f"{record['id']} missing provenance.{key}")
        if record["url"] not in {r["url"] for r in corpus.SOURCE_RECORDS}:
            violations.append(f"{record['id']} url mismatch")
    tkdl = corpus.get_record(corpus.TKDL_RECORD_ID)
    if not tkdl["tkdl_pointer_record"] or "POINTER ONLY" not in tkdl["scope"]:
        violations.append("TKDL record is not marked pointer-only")
    if "TKDL Access Agreement" not in tkdl["excerpt"]:
        violations.append("TKDL record lost its verified access-restriction statement")
    # amendment records must carry the verified commencement evidence
    for record in corpus.SOURCE_RECORDS:
        if record["source_type"] == "amendment_act" and record["id"] != "M4-SRC-001":
            if "S.O. 295(E)" not in str(record["provenance"].get("commencement_verification", "")):
                violations.append(f"{record['id']} missing commencement verification")
    return violations
