# MEMBER 1 — Main Legal AI Assistant

**Project:** IP-SAKTI Sahayak (SIH-26045) — CyberSapien
**Reference:** This file implements Section 6 ("Member 1") of `Plan.md`. Read `Plan.md` in full before starting; if anything here conflicts with `Plan.md`, `Plan.md` wins.
**Deployment:** NOT required for this round.

---

## 1. Role

You own the **central conversational assistant experience** — the orchestration layer that a user actually talks to. You are not a fourth domain knowledge base; M3 (India), M4 (ABS/TK) and M5 (International) already own their domains.

```text
Question
 ↓
Intent/context handling
 ↓
Decide which specialized domain is relevant (Classification / India / ABS-TK / International)
 ↓
Evidence retrieval (own standalone corpus, for independent dev/demo)
 ↓
Evidence sufficiency
 ↓
Grounded answer
 ↓
Citation validation
 ↓
Confidence
 ↓
Abstention when needed
 ↓
Final response
```

You own: query handling, conversation context/history, query understanding, the routing decision (which domain a query needs), evidence-aware answer assembly, final citation presentation, final confidence presentation, final abstention/fallback presentation, the disclaimer, conversational follow-up behavior, and your own tests.

## 2. Boundaries — Do NOT duplicate

- India IP/regulatory legal knowledge — owned by **M3**.
- ABS/TKDL/traditional-knowledge legal knowledge — owned by **M4**.
- International IP legal knowledge — owned by **M5**.
- Formulation-classification rules — owned by **M2**.

You must not wait for M2–M5's unfinished work, and they must not wait for you. Do not create `HANDOFF.md` or any cross-member exchange file.

## 3. Your standalone corpus (temporary, for independent dev)

To build and test yourself without waiting on M2–M5, use a small controlled set of real authoritative sources — cap: **roughly 8–15 short curated excerpts/sections**, not full statutes. Depth beats breadth.

This corpus is **not** meant to replace or overlap M3/M4/M5's domain corpora. At integration (owned by M6), your routing step gets wired to call M2's classification output and M3/M4/M5's actual guidance outputs; your own small corpus then becomes the fallback/demo path, not the production knowledge source for India/ABS/International queries. Build with that end-state in mind: keep your routing decision as a clean, swappable step, not hardwired only to your own corpus.

**Corpus-safety rule (do not weaken this):**

```text
M1's standalone corpus is ONLY for:
- independent development;
- testing;
- controlled demo fallback.

It must NOT silently answer a query that belongs to the
India, ABS/TK, or International specialist domain when the
corresponding specialist capability is unavailable.

If the router identifies a specialist domain and that
specialist capability is unavailable, return a safe
unavailable/abstention response — never silently substitute
unrelated M1 corpus evidence for a missing specialist.
```

The integrated system must always prefer correct specialist evidence over any fallback evidence. If M3/M4/M5 aren't wired in yet during your own standalone Phase 1–3 development, your routing step may answer from your own corpus for demo purposes — but the moment routing exists at integration, a specialist-domain query with no specialist available must abstain, not answer from your general corpus.

## 4. Interface contract (target shape — implement independently, no imports from other members)

```text
QueryRequest:
  id: string
  query: string
  language: "en" | "hi"
  jurisdiction: "India" | "International"
  formulation_class: FormulationClass | null
  history: Message[]

QueryResponse:
  id: string
  answer: string
  citations: Citation[]
  confidence: "HIGH" | "MEDIUM" | "LOW"
  confidence_score: number 0.0–1.0
  abstention: boolean
  abstention_reason: string | null
  escalation_available: boolean
  disclaimer: string

Citation:
  id, source_name, source_type, section, excerpt, url, effective_date
```

The LLM must NOT invent citation metadata. Valid abstention is HTTP 200 (`status: "abstained"`), not an error.

Public API you expose: `POST /api/query`, `GET /api/health`.

This is a target shape, not a shared dependency — build it yourself; Member 6 reconciles small mismatches at final integration.

## 5. Common Safety Rules (implement independently)

1. Never invent legal authority. 2. Never invent citations. 3. Never invent URLs. 4. Never claim the system is a lawyer. 5. Never present uncertain information as certain. 6. Keep India and International rules separate. 7. Prefer primary/authoritative sources. 8. Preserve source traceability. 9. Abstain when evidence is insufficient. 10. Clearly state output is information, not legal advice.

## 6. Golden scenarios you must be able to demo standalone

Try each against your own corpus, plus once each with a question outside your corpus to confirm abstention fires:

1. "Can I patent a classical Ayurvedic formulation from an authoritative text?" — should reflect Section 3(p) and a TKDL pointer, India jurisdiction. (You may need only a placeholder/aware-of-domain answer here since full depth is M3/M4's job — the point is your routing + abstention logic works.)
2. "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?" — should point toward the PCT/international patent pathway, and must **not** say Madrid (Madrid is trademarks, not patents). Kept visibly separate from any India answer.

---

## Phase 1 — Assistant Foundation

**Objective:** Stand up a working end-to-end query→answer pipeline for the central assistant, using its own standalone corpus, runnable and testable without M2–M5.

**Tasks:**
- Query handling (accept `QueryRequest`, validate input).
- Language/jurisdiction context handling (en/hi, India/International).
- Controlled real-source loading (your 8–15 excerpts, with real metadata).
- Retrieval over that corpus.
- Evidence ranking.
- Grounded prompt construction.
- Basic answer generation via a hosted LLM API (do not self-host/fine-tune — see `Plan.md` §4.5).
- Basic `QueryResponse` structure.
- Unit tests for the above.

**Files/modules:** left to your judgment; keep query handling, retrieval, and answer generation in separably-testable modules so Phase 2's safety layer can wrap them without a rewrite.

**Tests:** at minimum — a query returns a non-empty answer; retrieval returns evidence from your corpus; India vs International context changes retrieval/answer.

**Acceptance criteria:**
- [ ] Query works end-to-end.
- [ ] Evidence can be retrieved from your own corpus.
- [ ] Answer is grounded in retrieved evidence (not free-form).
- [ ] India/International state is respected.
- [ ] Tests pass.

Do not proceed to Phase 2 until this is checked off. Do not start Phase 2 automatically — wait to be asked.

---

## Phase 2 — Trust and Safety

**Objective:** Make the assistant's answers trustworthy — every claim traceable, confidence meaningful, and unsupported queries safely declined.

**Tasks:**
- Evidence-sufficiency threshold (below it → abstain, not guess).
- Citation mapping (answer claims → real stored evidence, never invented).
- Citation validation (URLs/sections come from stored metadata only).
- Confidence scoring (`HIGH`/`MEDIUM`/`LOW` + numeric score).
- Abstention path (`abstention: true`, `abstention_reason` set, HTTP 200).
- Safe fallback response text.
- Standing "information, not legal advice" disclaimer on every response.
- Hindi handling for at least the supported MVP scenarios.
- Malformed-LLM-output handling (don't crash, don't fabricate — abstain instead).

This citation-validation/confidence/abstention logic is for **your own** use — it is not a shared library other members import, but it must follow the Common Safety Rules above (same rules M3/M4/M5 independently implement for themselves).

**Tests:** a query with strong evidence returns HIGH/MEDIUM confidence and valid citations; a query with no matching evidence abstains cleanly (HTTP 200, `abstention: true`); a Hindi query for a supported scenario returns a Hindi answer.

**Acceptance criteria:**
- [ ] Citations map to real evidence.
- [ ] URLs come from stored metadata, never invented.
- [ ] Insufficient evidence triggers abstention, not a guess.
- [ ] Confidence works and varies sensibly with evidence strength.
- [ ] Hindi works for supported scenarios.
- [ ] Safety tests pass.

Do not start Phase 3 automatically.

---

## Phase 3 — Standalone Completion

**Objective:** Bring M1 to a fully self-contained, demo-ready state with its routing decision, golden queries and integration interface documented.

**Tasks:**
- Complete assistant flow, including the domain-routing decision step (Section 1 diagram) even though it currently only points at your own corpus.
- Conversational follow-up handling (using `history`).
- Run the two golden scenarios in Section 6 above, plus one out-of-corpus query per scenario to confirm abstention.
- Edge cases (empty query, unsupported language, missing jurisdiction).
- Final tests.
- Short workstream documentation: what you built, how to run it, what the routing step currently does and how it's meant to be rewired at integration.
- Confirm your actual output shape against Section 4's contract and note any deviations for M6.

**Tests:** the golden scenarios in Section 6, run for real, with pasted output.

**Acceptance criteria:**
- [ ] Works completely without M2–M5 present.
- [ ] Golden queries pass.
- [ ] Citations are valid, no fabricated authority/URLs/TKDL text.
- [ ] Abstention works.
- [ ] Feature is `READY`.

---

## Phase Completion Report (paste real output, every phase)

```text
PHASE STATUS

Member: 1
Phase: <1/2/3>
Status: NOT_STARTED / IN_PROGRESS / READY / BLOCKED / INTEGRATED

Completed:
- ...

Not completed:
- ...

Tests run:
- ...

Tests passed:
- ...

Files created/changed:
- ...

Known issues:
- ...

Blockers:
- ...

Acceptance criteria:
- Passed:
- Failed:

Ready for next phase: YES / NO
```

## Execution Rules (recap)

1. Read this file. 2. Read the relevant `Plan.md` sections. 3. Inspect the existing repository before changing anything. 4. Execute ONLY the phase you were asked to run. 5. Complete the tasks in that phase. 6. Test it. 7. Fix ordinary bugs yourself. 8. Verify acceptance criteria. 9. Stop. 10. Do NOT automatically start the next phase.

Also: do not redesign unrelated work. Do not invent legal information. Do not create a handoff system. Do not let your fallback corpus silently answer a specialist-domain query (Section 3). Checkpoint/commit at the end of each phase. Never mark `READY` without actually running the acceptance checks and golden query, and pasting real output.
