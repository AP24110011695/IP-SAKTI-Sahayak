# Member 1 — Main Legal AI Assistant (IP-SAKTI Sahayak, SIH-26045)

Standalone **Phase 1–3** build (demo-ready): the complete central conversational
assistant — routing decision, evidence retrieval, trust-and-safety layer,
follow-up handling — runnable and testable without Members 2–5.
Full workstream instructions: `../MEMBER_1.md`; architecture: `../Plan.md`.

## Layout

```text
member1/
├── m1/
│   ├── models.py       # QueryRequest / QueryResponse / Citation contract models
│   ├── config.py       # env-driven config, disclaimers, fallback texts
│   ├── corpus.py       # standalone corpus loading + validation (authoritative-URL allow-list)
│   ├── data/corpus.json# 10 curated real-source excerpts (5 India, 5 International; Hindi renderings)
│   ├── retrieval.py    # jurisdiction-filtered lexical retrieval + evidence ranking
│   ├── followup.py     # Phase 3: history-based context resolution for follow-ups
│   ├── generation.py   # grounded prompt + hosted-LLM generator + extractive fallback
│   ├── safety.py       # Phase 2: sufficiency, citation mapping/validation, confidence, guards
│   ├── routing.py      # domain-routing decision (swappable; M6 wires M2–M5 here)
│   ├── assistant.py    # orchestration: request → answer → QueryResponse
│   └── api.py          # POST /api/query, GET /api/health
├── tests/              # pytest suite (131 tests)
├── scripts/
│   ├── demo.py                   # Phase 1+2 walkthrough scenarios
│   ├── golden_scenarios.py       # §6 golden scenarios + out-of-corpus abstention, with assertions
│   ├── verify_contract.py        # actual shapes vs MEMBER_1.md §4 / Plan.md §7 + deviations for M6
│   ├── verify_acceptance.py      # Phase 1 acceptance checks
│   ├── verify_acceptance_phase2.py  # Phase 2 acceptance checks
│   └── verify_acceptance_phase3.py  # Phase 3 acceptance checks
└── requirements.txt
```

## Run

```bash
cd member1
pip install -r requirements.txt   # fastapi, uvicorn, pydantic, httpx, pytest
python -m pytest tests/ -q                   # test suite
python scripts/golden_scenarios.py           # §6 golden scenarios, real output
python scripts/demo.py                       # walkthrough scenarios
python scripts/verify_contract.py            # contract shape check for M6
python scripts/verify_acceptance_phase3.py   # Phase 3 acceptance checks
uvicorn m1.api:app --port 8000    # serve POST /api/query, GET /api/health
```

## Assistant flow (as built)

```text
QueryRequest
 → intent/context handling        followup.effective_retrieval_query: short
 │                                follow-ups are resolved against the most recent
 │                                user turn (retrieval/routing context only)
 → routing decision               routing.route(): which specialist domain the
 │                                query belongs to (see below)
 → evidence retrieval             retrieval.retrieve(): jurisdiction hard filter,
 │                                IDF+keyword scoring, Hindi keyword aliases
 → evidence sufficiency           safety.assess_sufficiency(): below threshold →
 │                                abstain, not guess
 → grounded answer                generation: hosted LLM (OpenAI-compatible) or
 │                                deterministic extractive; answers must carry [E#] tags
 → citation mapping               safety.map_citations(): only [E#]-tagged stored
 │                                evidence becomes a citation
 → citation validation            safety.validate_citations(): fields must equal
 │                                stored metadata; URLs must be authoritative https
 → confidence                     safety.confidence_from(): HIGH/MEDIUM/LOW + score
 → abstention when needed         always HTTP 200 with reason + safe fallback + disclaimer
 → final response                 QueryResponse after assert_response_safe guards
```

## Routing decision (swappable step)

`routing.route(request)` classifies which specialised domain the query belongs
to, transparently:

1. **ABS/TK (M4's domain)** wins when the query contains any ABS/TK signal —
   "benefit sharing", "biodiversity", "biological resource", "nagoya", "tkdl",
   "traditional knowledge" (plus Hindi equivalents).
2. **Classification (M2's domain)** when it contains classification-flow
   signals ("classify", "which category", "is my product", "food or cosmetic", …).
3. Otherwise the **explicit jurisdiction toggle** decides: `International` →
   INTERNATIONAL_IP, `India` → INDIA_IP. The toggle is authoritative — the two
   answer-sets are never conflated.

The decision is recorded (`AssistantResult.routing`: domain + rationale) and is
**context-aware**: a short follow-up ("what approvals do I need?") routes on
the conversation-resolved subject.

**How M6 rewires this at integration** — no code rewrite, one seam:

```python
from m1.routing import register_specialist, Domain
register_specialist(Domain.INDIA_IP, "m3 india guidance")
register_specialist(Domain.ABS_TK, "m4 abs/tk guidance")
register_specialist(Domain.INTERNATIONAL_IP, "m5 international guidance")
register_specialist(Domain.CLASSIFICATION, "m2 classifier")
# and start the service with SPECIALISTS_WIRED=1
```

With the switch on, the corpus-safety rule takes effect: a query routed to a
specialist domain with **no registered specialist abstains** — M1's standalone
corpus never silently substitutes for a missing specialist. M6 replaces the
standalone retrieval call in `assistant.handle_query` (step 4) with the
registered specialist's guidance output; M1's corpus then remains the
fallback/demo path only.

## Follow-up handling

Queries with ≤5 content tokens are treated as presumptive follow-ups when
`history` is present: the most recent user turn's content tokens are prepended
for retrieval and routing (capped at 40 tokens). Longer queries are treated as
self-contained. The real question plus history always go to the generator
prompt; grounding, sufficiency and citation rules are unchanged.

## Hosted LLM vs extractive mode

Per `Plan.md` §4.5 the answer generator targets a **hosted LLM API** (any
OpenAI-compatible `/chat/completions` endpoint — no self-hosting):

```bash
export LLM_API_KEY=...            # required for LLM mode
export LLM_BASE_URL=https://api.openai.com/v1   # or any compatible provider
export LLM_MODEL=gpt-4o-mini
```

Without `LLM_API_KEY` the assistant uses a deterministic **extractive**
generator that composes answers only from retrieved evidence text (grounded by
construction), so the pipeline stays runnable and testable offline.

## Trust & safety behaviour (Phase 2)

- **Evidence sufficiency**: two gates — a retrieval floor
  (`MIN_EVIDENCE_SCORE`, no relevant evidence at all) and a sufficiency
  threshold (`SUFFICIENCY_THRESHOLD`, top evidence too weak → abstain, not
  guess). The LLM's own `INSUFFICIENT_EVIDENCE` judgment also abstains.
- **Citation mapping**: answers earn citations only through `[E#]` tags that
  resolve to stored evidence; citation fields are copied verbatim from stored
  corpus metadata and can never be invented.
- **Citation validation**: every served citation is re-checked field-by-field
  against the stored corpus entry; URLs must be https on the authoritative
  domain allow-list. Any failure withholds the response.
- **Confidence**: `HIGH/MEDIUM/LOW` + numeric score that rises with evidence
  strength and corroboration; `LOW(0.0)` is reserved for abstentions.
- **Abstention**: always HTTP 200 with `abstention: true`, a specific
  `abstention_reason`, no citations, a safe fallback text (en/hi) and the
  standing disclaimer (en/hi).
- **Malformed LLM output**: transport errors, malformed envelopes, blank
  content, ungrounded answers (no valid `[E#]` tags) and out-of-range tags all
  abstain instead of fabricating — no silent fallback, no crash.
- **Hindi**: supported MVP scenarios (s.3(p)/TK patentability, AYUSH patent
  processing, TKDL pointer, PCT route) have Hindi corpus renderings (`text_hi`),
  so Hindi queries get genuinely Hindi answers with the Hindi disclaimer.
- **Edge cases**: empty/whitespace query, unsupported language, bad
  jurisdiction or oversized history → HTTP 400 `VALIDATION_ERROR`; a *missing*
  jurisdiction falls back to the safe domestic default (India).

## Integration interface (verified against MEMBER_1.md §4 / Plan.md §7)

`python scripts/verify_contract.py` checks the actual serialised shapes
field-by-field and passes. Contract surface:

- `POST /api/query` (`QueryRequest` → `QueryResponse`), `GET /api/health`;
- `QueryRequest`: id, query, language(en|hi), jurisdiction(India|International),
  formulation_class(null | Classical|Proprietary|Phytopharmaceutical|
  Ayurveda-Aahar|Cosmetic|New Drug|Uncertain), history(Message[]);
- `QueryResponse`: id, answer, citations[], confidence, confidence_score(0–1),
  abstention, abstention_reason, escalation_available, disclaimer;
- `Citation`: id, source_name, source_type, section, excerpt, url, effective_date;
- valid abstention is HTTP 200, never an error.

**Deviations/notes for M6** (also printed by the verifier):

1. `escalation_available` is always `False` in the standalone build — the human
   IP-facilitator path is not part of M1's three phases.
2. `jurisdiction` defaults to `"India"` when the toggle is omitted; any other
   value is rejected with `VALIDATION_ERROR`.
3. The internal RAG `status` field (ok/abstained, Plan.md §7) is carried on the
   `AssistantResult` wrapper, not on `QueryResponse` — the HTTP body matches
   the `QueryResponse` contract exactly.
4. `history` is capped at 20 messages and `Message.role` is restricted to
   `user|assistant` (system messages rejected).
5. Corpus excerpt texts are curated paraphrases from the team research dossier
   (Research.md) against real authoritative sources (URLs verified live,
   September 2026); `text_hi` entries are Hindi renderings whose authoritative
   text remains the English original at the cited source.
