# Member 4 — ABS + TKDL + Traditional Knowledge

Standalone ABS/Traditional-Knowledge workstream of IP-SAKTI Sahayak
(SIH-26045). Independent: imports nothing from Members 1, 2, 3 or 5.

- **Phase 1 (complete):** verified source foundation (10 records) + deterministic retrieval.
- **Phase 2 (complete):** standalone ABS/TK guidance feature — relevance
  determination, grounded guidance, safe TKDL pointer, citations, confidence,
  abstention, Hindi support.
- **Phase 3 (complete):** demo-ready validation — canonical scenario registry
  with contract/citation/TKDL-content/source audits, edge cases
  (part-ABS/part-patent, specific species, unrelated IP, international-only,
  unsupported ABS), Hindi audit, deterministic repeated behavior.

## What is here

```text
m4_abs/
├── corpus.py                  # 10 verified source records (the corpus)
├── retrieval.py               # minimal deterministic retrieval seam
├── guidance.py                # Phase 2: classify -> evidence -> generate -> validate -> result
├── hindi.py                   # Hindi detection, shadow query, user-facing Hindi strings
├── llm_client.py              # hosted LLM path (OpenAI-compatible) + offline stand-in
├── phase3_scenarios.py        # Phase 3: canonical scenarios + audit functions
├── verify_urls.py             # live URL verification -> verification_report.json
├── verification_report.json   # real verification results (generated)
├── golden_check.py            # Phase 1 retrieval demo
├── demo_phase2.py             # Phase 2 end-to-end demo (full result contract)
├── demo_phase3.py             # Phase 3 demo: all scenarios + full audit summary
├── tests/
│   ├── test_phase1.py         # 30 Phase 1 tests
│   ├── test_phase2.py         # 75 Phase 2 tests
│   └── test_phase3.py         # 44 Phase 3 tests
└── tools/                     # verification helpers used on 2026-09-06
```

## The corpus (all records verified 2026-09-06)

| id | source | section/article/rule | url |
|---|---|---|---|
| M4-SRC-001 | Biological Diversity Act, 2002 (Act 18 of 2003) | s. 3(1) | megbiodiversity.nic.in (official NIC-hosted copy; India Code = canonical, scripted access blocked) |
| M4-SRC-002 | BD (Amendment) Act, 2023 (Act 10 of 2023), Gazette | s. 6(1A), 6(1B) | egazette.gov.in/WritereadData/2023/247815.pdf |
| M4-SRC-003 | same Gazette | s. 7 (substituted) | same |
| M4-SRC-004 | same Gazette | s. 21(1) | same |
| M4-SRC-005 | Biological Diversity Rules, 2024 (G.S.R. 665(E)) | Rule 13(1) | nbaindia.nic.in/.../BD_Rules.pdf |
| M4-SRC-006 | Nagoya Protocol | Art. 5(5) | cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf |
| M4-SRC-007 | Nagoya Protocol | Art. 6(1) | same |
| M4-SRC-008 | Nagoya Protocol | Art. 7 | same |
| M4-SRC-009 | Convention on Biological Diversity | Art. 8(j) | cbd.int/doc/legal/cbd-en.pdf |
| M4-SRC-010 | TKDL (CSIR + Ministry of Ayush) | pointer only | tkdl.res.in |

Every record carries: stable id, source name, source type, section marker,
verbatim excerpt, real URL, effective date, jurisdiction (India vs
International kept distinct), scope note, retrieval keywords, and a
`provenance` block recording how it was verified (download method, document
identity, and any normalisation disclosed — e.g. Gazette line-break
artifacts, the elided "Commitee" printing error in s. 21(1)).

**TKDL constraint:** record M4-SRC-010 is a pointer/description built only
from the official public homepage. The TKDL database itself is restricted to
patent offices under the TKDL Access Agreement; no TKDL content, counts or
outcomes are reproduced anywhere in this package, and the tests enforce that
(no digits in the TKDL excerpt, no "TKDL says X", no other record mentions
TKDL).

## How to run

```bash
# from the MEMBER_4 directory
python m4_abs\verify_urls.py      # re-verify every URL live (writes verification_report.json)
python -m unittest discover -s m4_abs\tests -t m4_abs -v   # 149 tests (Phases 1-3)
python m4_abs\demo_phase3.py      # Phase 3 demo: all canonical scenarios + audits
```

Python 3.14, standard library only (pypdf is needed only by the tools/ helpers).

## Phase 2: how guidance works (guidance.py)

```text
query
 -> detect language (Devanagari -> Hindi shadow query; one code path)
 -> classify_query: deterministic lexicon/phrases -> ABS | TK | OTHER_IP | UNCLEAR
      OTHER_IP / UNCLEAR -> status "abstained" (never ABS guidance)
 -> retrieval.retrieve(shadow) over the verified corpus (deterministic)
 -> sufficiency gate: top score >= 6.0 AND confidence_score >= 0.5
      fee/amount questions always abstain (corpus contains no amounts)
 -> generate: hosted LLM if M4_LLM_API_KEY set, else deterministic
      evidence-only composer (offline stand-in, never presented as an LLM)
 -> validate: citations strictly against stored records (unknown id,
      fabricated URL, altered section/excerpt, missing field -> reject);
      content guards (unsupported URLs, invented amounts, numeric counts,
      TKDL fabrication, legal claims not present in cited evidence)
 -> result: exact Member 4 contract
```

Result contract (exact 8 fields; disclaimer appended to `answer`):

```json
{
  "answer": "...",
  "citations": [{"id", "source_name", "source_type", "section", "excerpt", "url", "effective_date"}],
  "confidence": "HIGH| MEDIUM | LOW",
  "confidence_score": 0.0-1.0,
  "abstention": false,
  "abstention_reason": null,
  "status": "ok | abstained | processing_error",
  "tkdl_pointer": null | "pointer/description text (tkdl.res.in)"
}
```

**Hosted LLM:** set `M4_LLM_API_KEY` (optionally `M4_LLM_BASE_URL`,
`M4_LLM_MODEL`) to enable the hosted path (OpenAI-compatible chat
completions, temperature 0). The model sees only the numbered evidence
records and must return JSON `{"answer", "citation_ids"}`; citation metadata
is always rebuilt from stored records. Without credentials the pipeline uses
the deterministic stand-in — documented honestly, never claimed as a live
LLM call. During the Phase 2 build no API credentials were available, so all
verification ran in stand-in mode.

**TKDL:** `tkdl_pointer` is populated only for TK/prior-art queries and is
built solely from the official public homepage description (tkdl.res.in).
No TKDL database content, counts, records or outcomes are ever reproduced;
the content validators reject any such fabrication (tested).

## Interface notes for Member 6

- `guidance.answer(query, language=None)` — the standalone entry point
  returning the contract above (language auto-detected; "en"/"hi" override).
- `corpus.SOURCE_RECORDS`, `corpus.to_citation(record)`, `retrieval.retrieve(query)` — Phase 1 seams, unchanged.
- `guidance.classify_query(query)` — explainable relevance object
  (`.domain`, `.signals`, `.rationale`) if M1/M6 want the routing signal.

## Status

- **Phase 1: READY** — 10 verified records, 6/6 URLs live, 30 tests.
- **Phase 2: READY** — guidance feature, 75 tests.
- **Phase 3: READY** — 149 tests total pass; all 13 canonical scenarios
  (golden EN/HI, TK, TKDL pointer, TKDL-details abstention, part-ABS/patent
  ×2, species ×2, unrelated trademark, international ×2, unsupported fee)
  pass contract + citation + TKDL audits with zero violations; source audit
  clean; demo-ready standalone via `guidance.answer(query)`.

Member 4 workstream COMPLETE. M6 integration NOT started.

Phase 1 seams still available to M6: `corpus.SOURCE_RECORDS` (schema in
corpus.py docstring), `corpus.to_citation(record)`,
`retrieval.retrieve(query, top_k=5)` (deterministic; `[]` = no evidence),
`corpus.TKDL_RECORD_ID` (pointer record with `pointer_guidance`).
Phase 3 audit helpers: `phase3_scenarios.audit_all(run_all())`,
`.audit_contract(result)`, `.audit_citations(result)`,
`.audit_tkdl_output(result)`, `.source_audit()`.
