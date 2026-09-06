# Member 3 — Indian IP & Regulatory Guidance (IP-SAKTI Sahayak, SIH-26045)

Standalone India-domain specialist for the CyberSapien team's internal-round
MVP. Answers India IP/regulatory questions about Ayurveda products with
real, traceable citations, deterministic confidence, and safe abstention.
**Information, not legal advice** — every answer says so.

This is Member 3's own implementation: it imports nothing from M1 (assistant),
M2 (classifier), M4 (ABS/TKDL), or M5 (international). Phase 3 = standalone
completion; the interface M6 will call is documented below.

---

## How to run standalone

Requires Python 3.10+ and `pypdf` (for the audit tooling only). From the
project root:

```bash
# full test suite (Phase 1 + 2 + 3)
python -m unittest member3.test_sources member3.test_phase2 member3.test_phase3

# every golden scenario + edge case + Hindi, live, with real output
python -m member3.run_phase3_checks

# live citation audit: re-fetches every cited URL, checks the host matches
# the documented authority, and re-verifies the stored excerpt inside the
# freshly downloaded official PDF (exit code 0 = all checks passed)
python -m member3.audit_citations

# quick URL-only check of the whole corpus
python -m member3.verify_urls
```

Single question from code:

```python
from member3 import answer_india_question

result = answer_india_question(
    "Can I patent a classical Ayurvedic formulation from an authoritative text?"
)
print(result["answer"], result["citations"], result["confidence"])
```

Hosted LLM (recommended by Plan.md §4.5, optional at runtime). The pipeline
calls a hosted LLM for narrative generation when configured, and otherwise
uses its built-in deterministic evidence-only mode (the provisions are quoted
verbatim; no interpretation is added). No code change is needed to switch:

```bash
export M3_LLM_BASE_URL=https://<any-openai-compatible-endpoint>/v1
export M3_LLM_API_KEY=<key>
export M3_LLM_MODEL=<model>
```

Known environment limitation: no hosted-LLM credentials were available in the
development environment, so the hosted path is implemented and its interface,
guards, and failure handling are test-verified with a stand-in client
(`member3/test_phase3.py::TestHostedLLMClient`), but no live external call has
been executed. Authentication is never bypassed and live results are never
faked.

## Result shape consumed by M6

`answer_india_question(query, language=None, jurisdiction=None, llm=None)`
returns exactly this dict (the project `RAG Result` shape):

```text
answer            str    — always ends with the not-legal-advice disclaimer
citations         Citation[] — empty for abstentions/errors
confidence        "HIGH" | "MEDIUM" | "LOW"
confidence_score  float 0.0–1.0 (deterministic; never LLM self-reported)
abstention        bool
abstention_reason str | None — stable machine-readable code + detail
status            "ok" | "abstained" | "processing_error"
```

Each `Citation` has exactly: `id, source_name, source_type, section, excerpt,
url, effective_date` — copied field-for-field from the stored Phase 1 record
and re-validated before returning. The LLM never writes citation metadata.

Status semantics for M6: `ok` = guidance produced (abstention False, ≥1
citation, disclaimer present). `abstained` = safe decline (abstention True,
reason set, no citations) — a successful result, HTTP 200 at integration, not
an error. `processing_error` = infrastructure failure (e.g. hosted LLM
unreachable) — not an abstention; the answer invites a retry and nothing was
answered.

`abstention_reason` codes: `out_of_scope`, `out_of_scope_international`
(M5's domain), `out_of_scope_abs_tk` (M4's domain), `insufficient_evidence`,
`low_confidence`, `llm_output_invalid`, `unsupported_content`,
`citation_validation_failed`.

Callers may pass `language` ("en"/"hi", else auto-detected) and
`jurisdiction` — an explicit non-India jurisdiction is refused with an
abstention, keeping M3 strictly India-only at the interface level.

## Supported India scope

Ten curated areas over a 15-record verified corpus (`member3/sources.py`):
patents (incl. the Section 3(p) traditional-knowledge bar and the
biological-material disclosure duty), geographical indications, trademarks,
copyright, designs, plant variety & farmers' rights, Drugs & Cosmetics
(ASU drug definition), Drugs & Magic Remedies (objectionable advertisements),
FSSAI Ayurveda Aahara (incl. the food/drug boundary exclusions), and the
Biological Diversity Act's intellectual-property intersection (Section 6 as
amended in 2023). Hindi questions work for all supported flows; statute
names and section numbers stay in their official English form.

Deliberately NOT covered (abstains, pointing at the owning member):
international/export questions (M5), deep ABS/Nagoya/TKDL-access mechanics
(M4), formulation classification (M2), and anything outside the curated
corpus.

## Abstention behavior

The pipeline abstains — returning a successful `status="abstained"` result,
never a guessed answer — when: routing finds no India IP/regulatory scope;
the question is international-only or ABS/TK-specialist; retrieval evidence
is too weak (conservative sufficiency rule: best keyword score ≥ 4 with an
in-scope record); confidence computes LOW; the LLM emits malformed or
unsupported output; invented content is detected (statutory references not
present in the cited evidence, non-evidence URLs, invented fees/amounts/
durations); or citation validation fails. LLM/API failures are
`processing_error`, never fabricated answers.

## Source / citation provenance rules

- Every record carries: source name, type, issuing authority, exact section,
  verbatim excerpt, real URL, effective date, explicit India jurisdiction,
  and a verification entry describing how the URL/excerpt was checked
  (2026-09-06).
- `downloaded+extracted`: excerpt extracted verbatim from the official
  document (the audit re-downloads and re-locates it). `mirror-verified`:
  official page is bot-walled to scripted clients, so text was verified
  against a documented mirror (Indian Kanoon) and the recorded URL is the
  canonical official page — the audit reports this provenance instead of
  claiming a live text match.
- FSSAI 2022 Ayurveda-Aahara Gazette: FSSAI's original URL no longer serves
  the file; the record points to a verified copy of the official Gazette
  scan and says exactly that (never presented as fssai.gov.in hosting). The
  live official FSSAI order of 25-07-2025 (fssai.gov.in) corroborates it.
- BD Act Section 6: re-verified against the Official Gazette of the
  Biological Diversity (Amendment) Act, 2023 (egazette.gov.in); the record
  quotes the substituted Section 6(1)/(1A) (approval/registration timing
  moved to *before grant*; commercialisation approval in 6(1B)). The
  pre-amendment mirror wording is documented as superseded.
- TKDL: pointer only (role + https://tkdl.res.in + patent-office access
  restriction). No TKDL contents, counts, or access detail are stated; TKDL
  is never a citation record. No 2024 Patent Rules text is quoted anywhere.
- Corpus corrections are logged in the record's `verification.notes`
  (e.g. removal of the misleading "variety registration" tag on the PPV&FRA
  record in Phase 3).
