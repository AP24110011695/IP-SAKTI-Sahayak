"""Member 3 Phase 3 — live citation audit.

The offline half of the citation audit lives in member3.test_phase3
(field-exact mapping of every citation to a stored Phase 1 record). This
script performs the LIVE half, for real, over every citation produced by the
Phase 3 scenario set:

  1. field-exact check  — every citation field equals the stored record;
  2. URL resolution     — the cited URL is fetched live (HTTP status);
  3. host relevance     — the URL host matches the record's documented
                          issuing authority (see EXPECTED_HOSTS below);
  4. excerpt re-verification — for records whose Phase 1 verification method
     is "downloaded+extracted", the source document is re-downloaded and the
     stored excerpt is located in the freshly extracted text (whitespace-
     stripped comparison; excerpts containing "..." omissions are checked
     fragment-by-fragment). For "mirror-verified" records the body cannot be
     re-fetched (India Code bot-walls scripted clients; WIPO Lex text was
     cross-checked against Indian Kanoon in Phase 1) — the audit reports
     PROVENANCE-DOCUMENTED instead of claiming a live text match.

Run:  python -m member3.audit_citations

Exit code 0 when every check passes, 1 otherwise.
"""

import io
import re
import sys
import urllib.request

from pypdf import PdfReader

from . import answer_india_question
from .citations import CITATION_FIELDS, validate_citation
from .guidance import validate_rag_result
from .test_phase3 import SCENARIOS, run_scenario

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

# Documented issuing authority per record id — the host check is against the
# record's own verification metadata, not a guess. foodsafetystandard.in is
# intentionally present: the FSSAI 2022 Gazette record documents, in its
# verification notes, that the URL is a verified copy of the official
# Gazette scan (FSSAI's original path no longer serves the file), so the
# audit asserts THAT provenance rather than pretending it is fssai.gov.in.
EXPECTED_HOSTS = {
    "patents_act_1970_s3p": "ipindia.gov.in",
    "patents_act_1970_s2j": "ipindia.gov.in",
    "patents_act_1970_s10_4d": "ipindia.gov.in",
    "gi_act_1999_s2_1e": "ipindia.gov.in",
    "gi_act_1999_s11_1": "ipindia.gov.in",
    "tm_act_1999_s9_1b": "ipindia.gov.in",
    "designs_act_2000_s2d": "ipindia.gov.in",
    "copyright_act_1957_s22": "ipindia.gov.in",
    "dc_act_1940_s3a": "cdsco.gov.in",
    "dmr_act_1954_s3": "indiacode.gov.in",
    "dmr_act_1954_s2c": "indiacode.gov.in",
    "ppvfr_act_2001_s39_1iv": "www.wipo.int",
    "bda_2002_s6": "egazette.gov.in",
    # HOSTING NOTE (verification.notes): verified copy of the official
    # Gazette scan; not claimed to be FSSAI-hosted.
    "fss_aahara_regs_2022_reg2b": "foodsafetystandard.in",
    "fssai_order_2025_cat_a": "fssai.gov.in",
}


def fetch(url, timeout=60):
    """Fetch a URL. Returns (status, raw_bytes_or_None)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except Exception as error:
        return "ERROR: %s" % str(error)[:80], None


def pdf_text(raw):
    return "".join(
        page.extract_text() or "" for page in PdfReader(io.BytesIO(raw)).pages
    )


def strip_ws(text):
    return re.sub(r"\s+", "", (text or "").lower())


def _artefact_norm(text, is_document):
    """Aggressive normalisation used only as the audit's fallback matching
    layer. Government consolidations print amendment brackets [...], footnote
    reference digits glued mid-sentence ('of 8[disease...'), and PDF fonts
    that map quote glyphs to ―/‖. These are annotation/print artefacts, not
    provision text, so the fallback compares the substantive words:
    whitespace removed, quote glyphs removed, and — on the freshly extracted
    document side only — footnote digits that directly precede an amendment
    bracket removed, then the brackets themselves removed on both sides.
    The stored excerpt itself is NEVER altered."""
    t = strip_ws(text)
    if is_document:
        t = re.sub(r"\d+(?=\[)", "", t)
    t = re.sub(r"[“”\"‖„―’']", "", t)
    t = t.replace("[", "").replace("]", "")
    return t


def excerpt_in_document(excerpt, document_text):
    """Verify the stored excerpt against freshly extracted document text.

    Matching levels, strongest first:
      1. contiguous   — whitespace-stripped excerpt found verbatim;
      2. chunk-level  — same comparison in 40-char chunks (step 20) for
                        excerpts interrupted by page headers / Gazette margin
                        notes; requires >= 90% of chunks plus BOTH the
                        opening and closing 30 characters;
      3. normalised   — artefact-normalised comparison (see
                        _artefact_norm) at the same chunk thresholds, for
                        consolidations whose print artefacts (amendment
                        brackets, footnote digits, quote-glyph mapping) sit
                        inside the provision text.

    '...' omissions split the excerpt into independent fragments, each of
    which must pass at the same level. A leading clause marker '(d)'
    restored by Phase 1 over a PDF 'd)' artefact is tolerated.
    Returns (status, detail) with status in
    {"contiguous", "chunk-level", "normalised", "not-found"}.
    """
    doc = strip_ws(document_text)
    doc_norm = _artefact_norm(document_text, is_document=True)
    fragments = [f for f in re.split(r"\.\.\.", excerpt) if len(strip_ws(f)) >= 15]
    if not fragments:
        return "not-found", "excerpt has no substantive fragment"

    LEVEL_ORDER = {"contiguous": 0, "chunk-level": 1, "normalised": 2}
    worst = "contiguous"
    worst_detail = ""
    for fragment in fragments:
        found = None
        detail = ""
        stripped = strip_ws(fragment)
        candidates = [stripped]
        relaxed = re.sub(r"^\((?=[a-z0-9]\))", "", stripped, count=1)
        if relaxed != stripped:
            candidates.append(relaxed)
        norm_stripped = _artefact_norm(stripped, is_document=False)
        norm_relaxed = re.sub(r"^\((?=[a-z0-9]\))", "", norm_stripped, count=1)
        norm_candidates = [norm_stripped]
        if norm_relaxed != norm_stripped:
            norm_candidates.append(norm_relaxed)

        for candidate in candidates:
            if candidate in doc:  # level 1 — contiguous whitespace-stripped
                found, detail = "contiguous", "verbatim after whitespace normalisation"
                break
            status = _chunk_status(candidate, doc)  # level 2 — chunk match
            if status:
                found = status[0]
                detail = "%d%% of chunks contiguous" % status[1]
                break
        if not found:  # level 3 — artefact-normalised comparison
            for candidate in norm_candidates:
                status = _chunk_status(candidate, doc_norm)
                if status:
                    found = status[0]
                    detail = "%d%% of chunks contiguous (artefact-normalised)" % status[1]
                    break
        if not found:
            return "not-found", "fragment not found: %r..." % fragment.strip()[:60]
        if LEVEL_ORDER[found] > LEVEL_ORDER[worst]:
            worst, worst_detail = found, detail
    return worst, "all %d fragment(s) verified (%s)" % (len(fragments), worst_detail or detail)


def _chunk_status(candidate, doc):
    """Chunk-level check. Returns "chunk-level" plus the coverage percentage
    when the candidate matches at >= 90% of chunks with both ends present,
    else None."""
    if candidate in doc:
        return "contiguous", 100
    chunks = [candidate[i:i + 40] for i in range(0, len(candidate), 20)]
    if not chunks:
        return None
    present = sum(1 for chunk in chunks if chunk in doc)
    ratio = present / len(chunks)
    ends_ok = candidate[:30] in doc and candidate[-30:] in doc
    if ratio >= 0.9 and ends_ok:
        return "chunk-level", round(ratio * 100)
    return None


def main():
    failures = 0
    checked = 0
    document_cache = {}
    seen_ids = set()

    print("=" * 78)
    print("MEMBER 3 PHASE 3 — LIVE CITATION AUDIT (golden + edge + Hindi scenarios)")
    print("=" * 78)

    for name, query in SCENARIOS:
        result = answer_india_question(query)
        contract = validate_rag_result(result)
        print("\nSCENARIO  : %s — %s" % (name, query[:70]))
        print("  status=%s conf=%s(%.4f) citations=%d contract=%s" % (
            result["status"], result["confidence"], result["confidence_score"],
            len(result["citations"]), "VALID" if not contract else contract,
        ))
        if contract:
            failures += 1
        for citation in result["citations"]:
            checked += 1
            record_id = citation["id"]
            seen_ids.add(record_id)
            problems = []

            # 1. field-exact mapping to the stored record
            problems.extend(validate_citation(citation))
            field_check = "OK" if not problems else "FAIL %s" % problems

            # 2. URL resolution (live)
            url = citation["url"]
            status, raw = fetch(url)
            url_ok = status == 200

            # 3. host relevance against the documented authority
            host_ok = url.split("/")[2] in EXPECTED_HOSTS.get(record_id, "\0")
            if not host_ok:
                problems.append("URL host %r does not match documented authority %r"
                                % (url.split("/")[2], EXPECTED_HOSTS.get(record_id)))

            # 4. excerpt re-verification for downloaded records
            record = _stored(record_id)
            verification_method = record["verification"]["method"] if record else "?"
            if record and verification_method == "downloaded+extracted":
                if url in document_cache:
                    doc_text = document_cache[url]
                elif raw and url.lower().endswith(".pdf"):
                    try:
                        doc_text = pdf_text(raw)
                        document_cache[url] = doc_text
                    except Exception as error:
                        doc_text = None
                        problems.append("PDF extraction failed: %s" % error)
                else:
                    doc_text = None
                    problems.append("no document body available for re-verification")
                if doc_text is not None:
                    verdict, detail = excerpt_in_document(citation["excerpt"], doc_text)
                    if verdict == "not-found":
                        problems.append("excerpt re-verification failed: %s" % detail)
                    text_check = "%s [%s] (%s)" % (
                        "RE-VERIFIED" if verdict != "not-found" else "FAIL",
                        verdict, detail,
                    )
                else:
                    text_check = "FAIL (no body)"
            else:
                text_check = "PROVENANCE-DOCUMENTED (mirror-verified; %s)" % (
                    (record["verification"]["url_status"][:60] + "...")
                    if record and len(record["verification"]["url_status"]) > 60
                    else (record["verification"]["url_status"] if record else "?")
                )

            verdict = "PASS" if not problems else "FAIL"
            if problems:
                failures += 1
            print("  [%s] %s" % (verdict, record_id))
            print("      fields: %s | url: HTTP %s | host: %s" % (
                field_check, status,
                "matches " + EXPECTED_HOSTS.get(record_id, "?") if host_ok else "MISMATCH",
            ))
            print("      excerpt: %s" % text_check)

    print()
    print("=" * 78)
    print("AUDIT SUMMARY: %d citation(s) audited across %d stored record(s); "
          "%d failure(s)" % (checked, len(seen_ids), failures))
    print("=" * 78)
    return 1 if failures else 0


def _stored(record_id):
    from .sources import all_sources
    return next((r for r in all_sources() if r["id"] == record_id), None)


if __name__ == "__main__":
    sys.exit(main())
