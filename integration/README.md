# Member 6 — Integration (Phases 1–3)

**Project:** IP-SAKTI Sahayak (SIH-26045) — CyberSapien
**Phase 1:** integration foundation (contracts, stub harness, fixtures) — complete.
**Phase 2:** the REAL M1–M5 workstreams wired together through M1's routing seam — complete.
**Phase 3:** final QA (17-point checklist) + demo rehearsal — complete.

---

## Final QA + demo rehearsal (Phase 3)

```bash
python -m pytest integration/tests/test_final_qa.py -v   # 17-point checklist (37 tests)

# timed demo rehearsal against the LIVE app (run twice for repeatability):
python -m uvicorn integration.app:app --port 8000
python integration/demo_rehearsal.py 8000
```

Phase 3 QA results (2026-09-07): 231 integration tests + 555 member tests
pass; live URL audits — M3 21 citations 0 failures (URLs re-fetched, excerpts
re-verified inside freshly downloaded official PDFs), M4/M5 URL checks pass;
substituted BD Act section 7(2)-(3) content re-verified against the actual
Gazette of India PDF (egazette.gov.in CG-DL-E-03082023-247815). No LLM
credentials were available, so every run used the members' deterministic
offline modes; the hosted-LLM paths remain implemented and are test-verified
by each member's own suite with stand-in clients — no live LLM call occurred.

---

## Run the integrated application (Phase 2)

```bash
cd C:\Projects\SIH2026                    # repo root

# the combined app: M1's FastAPI app with the real M2–M5 wired in
python -m uvicorn integration.app:app --port 8000
#   POST /api/query     routed to the real M3 / M4 / M5 specialists
#   POST /api/classify  the real M2 classifier
#   GET  /api/health    service + specialist registration status

# or equivalently:
python -m uvicorn integration.adapters:app --port 8000
```

Offline by default: without LLM credentials every member uses its own
deterministic generation mode (M1 extractive, M3 evidence-only template,
M4 offline stand-in, M5 deterministic client). Set the optional LLM env
vars (table below) to upgrade narrative generation — nothing else changes.
`wire_m1()` forces `specialists_wired=True` when the specialists are
registered, so the corpus-safety rule is always active in the combined app.

M1 standalone (own corpus, demo mode) remains available:
`cd sihmember1 && uvicorn m1.api:app` — there `/api/classify` returns 503
(no classifier registered) and specialist domains answer from M1's corpus
for demo purposes only.

## Run the test harness

```bash
python -m pytest integration/tests -v            # everything (194 tests)
#   Phase 1 (stubs):  contracts 99 · golden stubs 12 · errors 30 · compat 11
#   Phase 2 (real):   real integration 32 · real golden scenarios 10
python -m integration.live_probe                 # read-only member probe (31 checks)

# all five member suites (verified green 2026-09-07):
python -m pytest sihmember1/tests -q                                   # 131
python -m unittest discover -s sihmember4/tests -t sihmember4          # 149
python -m unittest discover -s sihmember5/tests                        # 64
# M2/M3 suites use legacy package names — run via the alias shim:
python -c "from integration.adapters import alias_legacy_member_packages as a; a()"
# then see integration/live_probe.py's discovery pattern, or simply:
python -m pytest integration/tests/test_compatibility.py -v            # live-probes M1–M5
```

---

## Phase 1 layout (foundation)

```text
integration/
├── contracts.py           target contract shapes (Plan.md §7) + stdlib
│                          validators + ErrorResponse/HTTP-status mapping
├── stubs.py               stub specialists (M3/M4/M5 RAG results, M2
│                          ClassificationResult), stub router, failure
│                          modes for the error-path tests
├── assembler.py           Phase 1 reference flow: validate → route →
│                          dispatch → assemble (still used by the stub
│                          harness; Phase 2's real path lives in M1)
├── member_interfaces.py   the ACTUAL entry points, import mechanics and
│                          result shapes of M1–M5 + findings F-01…F-11
│                          with their Phase 2 resolutions
├── live_probe.py          read-only probes of the real member code
├── adapters.py            PHASE 2: member loaders (F-01 shim), the four
│                          real adapters, boundary validation/normalisation
│                          (F-04/F-05/F-06), wire_m1(), combined app
├── app.py                 PHASE 2: uvicorn entry (integration.app:app)
├── fixtures/
│   └── golden_scenarios.json   five golden scenarios + out-of-corpus variants
└── tests/
    ├── test_contracts.py            Task 3: contract validation incl. mutations
    ├── test_golden_scenarios.py     Task 4: five golden scenarios vs stubs
    ├── test_errors_fallbacks.py     Task 5: 400/502/503/abstention-200 paths
    ├── test_compatibility.py        Task 6: vocabulary + live-probe checks
    ├── test_real_integration.py     Phase 2: real specialists through M1
    └── test_golden_scenarios_real.py Phase 2: five golden scenarios, real app
```

Content safety: stub texts are fixtures; legal references they contain are
real names from PS.md/Research.md and excerpts are explicit placeholders.
No legal authority is invented anywhere in the harness or the adapters.

---

## Target contracts (Plan.md §7 — enforced by `contracts.py`)

```text
Public API      POST /api/query · POST /api/classify · GET /api/health
QueryRequest    id, query, language(en|hi), jurisdiction(India|International),
                formulation_class(FormulationClass|null), history(Message[])
QueryResponse   id, answer, citations[], confidence(HIGH|MEDIUM|LOW),
                confidence_score(0.0–1.0), abstention, abstention_reason,
                escalation_available, disclaimer
Citation        id, source_name, source_type, section, excerpt, url,
                effective_date
ClassificationResult  formulation_class, description, relevant_regimes,
                tkdl_pointer, confidence, needs_clarification,
                clarification_prompt
RAG Result      answer, citations[], confidence, confidence_score,
                abstention, abstention_reason, status(ok|abstained|
                processing_error)      [+ M4 additive: tkdl_pointer]
ErrorResponse   VALIDATION_ERROR→400 · PROCESSING_ERROR→502 ·
                SERVICE_UNAVAILABLE→503    (valid abstention = HTTP 200)
```

Validation policy (deliberate): required fields enforced with types;
extra/additive fields tolerated (M2 extras, M4's `tkdl_pointer`);
`confidence_score` range-checked only — label↔score thresholds stay
member-specific; URL shape checked here, URL **authority** stays with each
member's own allow-list.

---

## How the combined app starts (Task 7 — startup documentation)

There is exactly **one server** in the final MVP: M1's FastAPI app. M2–M5
are libraries imported into adapters; they run no services. Nothing is
deployed in this round.

### Required runtime

- Python 3.12+ (verified on 3.12.10).
- `pip install -r sihmember1/requirements.txt` (fastapi, uvicorn, pydantic,
  httpx, pytest). M2–M5 need nothing beyond the stdlib.
- Optional `pypdf` for M3/M4 audit tooling only.

### Environment variables

| Variable | Workstream | Purpose | Required? |
|---|---|---|---|
| `LLM_API_KEY` | M1 | hosted LLM for answer generation; empty → deterministic extractive mode | no |
| `LLM_BASE_URL` / `LLM_MODEL` / `LLM_TIMEOUT_SECS` | M1 | OpenAI-compatible endpoint config | no |
| `RETRIEVAL_TOP_K` / `MIN_EVIDENCE_SCORE` / `SUFFICIENCY_THRESHOLD` | M1 | retrieval/sufficiency tuning | no |
| `SPECIALISTS_WIRED` | M1 | **M6 flips this to `1` in Phase 2** — activates the corpus-safety rule | Phase 2 |
| `M3_LLM_BASE_URL` / `M3_LLM_API_KEY` / `M3_LLM_MODEL` / `M3_LLM_TIMEOUT` | M3 | hosted LLM; absent → deterministic evidence-only mode | no |
| `M4_LLM_API_KEY` / `M4_LLM_BASE_URL` / `M4_LLM_MODEL` | M4 | hosted LLM; absent → offline stand-in | no |
| `OPENAI_API_KEY` + `OPENAI_MODEL` | M5 | hosted generation; absent → deterministic client | no |

Every workstream runs fully offline (deterministic generation) without any
of these — an API key only upgrades the narrative generation. No database,
no queue, no external service is required to start.

### Startup order

1. No external services to boot — start the app directly.
2. Phase 2 wiring (inside the combined app, before `uvicorn` serves):
   register specialists via M1's seam, then start:

```python
# Phase 2 sketch — the mechanical path this foundation prepares
from m1.routing import register_specialist, Domain
register_specialist(Domain.INDIA_IP, "m3.india_adapter")
register_specialist(Domain.ABS_TK, "m4.abs_adapter")
register_specialist(Domain.INTERNATIONAL_IP, "m5.international_adapter")
register_specialist(Domain.CLASSIFICATION, "m2.classifier_adapter")
# then run with SPECIALISTS_WIRED=1
```

3. Serve: `uvicorn m1.api:app --port 8000` (or the Phase 2 integration app
   that adds `POST /api/classify` — M1's app does not expose it yet,
   finding F-02).

### Health check

`GET /api/health` → `{"status": "ok", "service": "m1-assistant", "version": ...,
"generator_mode": "llm"|"extractive", "specialists_wired": true|false}`.
Phase 2's combined app should also report each specialist's availability.

### Per-member standalone entry points (verified 2026-09-07)

```bash
python -m pytest sihmember1/tests -q                                  # M1: 131 passed
python -m unittest discover -s sihmember4/tests -t sihmember4         # M4: 149 passed
python -m unittest discover -s sihmember5/tests                       # M5: 64 passed
# M2/M3 self-test suites reference legacy package names ('member2'/'member3'):
# run via the sys.modules alias shown in integration/live_probe.py (F-01).
```

---

## Phase 2 architecture (as built)

The combined app is M1's FastAPI application with the real specialists
wired into its existing seams — no second framework layer:

```text
POST /api/query  → m1.assistant.handle_query
                     ├─ route (m1.routing; F-03 signal fix included)
                     ├─ specialist registered? ──► adapter (integration/adapters.py)
                     │       INDIA_IP          → sihmember3.answer_india_question
                     │       ABS_TK            → sihmember4.guidance.answer
                     │       INTERNATIONAL_IP  → member5.guide
                     │   adapter validates the result against the contract and
                     │   normalises at the boundary:
                     │       status=processing_error → AdapterError → HTTP 502 (F-04,
                     │                                 covers M4 and M5)
                     │       structurally invalid    → AdapterError → HTTP 502
                     │       semantically unsafe     → withheld → HTTP 200 abstention
                     │       M4 tkdl_pointer         → surfaced in answer text (F-05)
                     │       empty abstention answer → M1 fallback text (F-06)
                     ├─ specialist registered by name only → safe abstention
                     ├─ GENERAL domain → M1's own corpus (fallback scope)
                     └─ specialists not wired (demo mode) → M1's own corpus

POST /api/classify → real sihmember2.classify via the handler seam (F-02);
                     ValueError from M2's validation → 400; classifier
                     failure → 502; no classifier registered → 503.
                     Free-text /api/query traffic routed to CLASSIFICATION
                     abstains toward the guided flow (M2 is answers-driven).

GET  /api/health   → status + specialists_wired + registered specialist names
```

Member-code changes made at integration (all minimal, safety-preserving):
- `sihmember1/m1/routing.py`: ABS_TK_SIGNALS += "plant collected",
  "collected in india" (F-03, data-only).
- `sihmember1/m1/assistant.py`: specialist-handler registry + dispatch step
  after routing (wired specialists serve their domain; corpus-safety rule
  intact; GENERAL falls through to the corpus as the fallback scope).
- `sihmember1/m1/api.py`: POST /api/classify added (F-02) + health reports
  the registered specialists.
- `sihmember1/m1/models.py`: ClassifyRequest model.
- `sihmember5/member5/guidance.py`: fee/cost questions abstain in
  route_query (F-09 — same documented rule M4 enforces).

Everything else in M2–M5 is untouched; each member's own safety behaviour
(citation validation, confidence, abstention, TKDL pointer discipline,
PCT/Madrid/Hague mapping) is preserved and covered by regression tests.

## Known compatibility findings (Task 6 — full detail in `member_interfaces.py`)

| ID | Area | Severity | One-line summary |
|---|---|---|---|
| F-01 | M2/M3 package naming | RESOLVED | adapters use real names; `alias_legacy_member_packages()` shims the legacy names for their self-tests |
| F-02 | /api/classify | RESOLVED | endpoint added to M1's app; serves the real M2 via the handler seam |
| F-03 | routing | RESOLVED | M1's ABS_TK_SIGNALS extended; golden ABS query routes ABS_TK (regression-tested) |
| F-04 | M5 + M4 status shape | RESOLVED | boundary treats status as authoritative → HTTP 502; regression tests for both members |
| F-05 | tkdl_pointer | record | M4 adds the field; M3 embeds the pointer in answer text; M2 sets it for Classical |
| F-06 | abstention text | RESOLVED | M1 substitutes its fallback text for empty specialist abstentions (regression-tested) |
| F-07 | confidence | record | label↔score thresholds differ per member — by design, not harmonised |
| F-08 | citation optionality | record | M1 allows null section/url/effective_date; M3–M5 always populate |
| F-09 | M5 abstention gate | RESOLVED | fee/cost guard added to M5's route_query; weak fee query now abstains (regression-tested); broader gate breadth remains a Phase 3 QA watch item |
| F-10 | 503 semantics | record | no member emits 503; integration policy: unregistered→200 abstain, unreachable→503, failure→502 |
| F-11 | duplicate disclaimer | record | M3–M5 embed a disclaimer in answer text; QueryResponse adds one — accepted for the MVP, presentation polish in Phase 3 |

Member files changed: only the five minimal items listed above (M1's four
integration-seam files and M5's one routing guard); M2/M3/M4 code and all
corpora untouched.
