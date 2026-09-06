# MEMBER 6 — Integration Foundation + Final QA

**Project:** IP-SAKTI Sahayak (SIH-26045) — CyberSapien
**Reference:** This file implements Section 6 ("Member 6") of `Plan.md`. Read `Plan.md` in full before starting; if anything here conflicts with `Plan.md`, `Plan.md` wins.
**Deployment:** NOT required for this round.

---

## 1. Role

You own the **only workstream whose main purpose is to combine the five completed, independent workstreams** (M1–M5) into one working application, then verify and demo it.

```text
M2 → classification knowledge
M3 → Indian knowledge
M4 → ABS/TK knowledge
M5 → International knowledge
        ↓
M1 → asks / routes / assembles / shows
        ↓
M6 → connects and validates everything
```

You do **not** build the domain functionality of M1–M5 from scratch. You inspect what they built, connect it, fix small mismatches, and test.

## 2. What you start on Day 1 (before M1–M5 finish)

You do not wait for anyone. Phase 1 is entirely preparable in advance from `Plan.md` alone.

## 3. Interface contracts you will reconcile (from `Plan.md` §7 — targets, not code you need up front)

```text
Public API:
  POST /api/query
  POST /api/classify
  GET  /api/health

QueryRequest:
  id, query, language: "en"|"hi", jurisdiction: "India"|"International",
  formulation_class: FormulationClass | null, history: Message[]

QueryResponse:
  id, answer, citations: Citation[], confidence: "HIGH"|"MEDIUM"|"LOW",
  confidence_score: 0.0-1.0, abstention: boolean, abstention_reason: string|null,
  escalation_available: boolean, disclaimer: string

Citation:
  id, source_name, source_type, section, excerpt, url, effective_date

ClassificationResult:
  formulation_class, description, relevant_regimes, tkdl_pointer,
  confidence, needs_clarification, clarification_prompt

Internal RAG Result (from M1/M3/M4/M5, target shape each independently produces):
  answer, citations, confidence, confidence_score, abstention,
  abstention_reason, status: "ok"|"abstained"|"processing_error"

ErrorResponse:
  VALIDATION_ERROR -> 400, PROCESSING_ERROR -> 502, SERVICE_UNAVAILABLE -> 503
  (valid abstention is HTTP 200, not an error)
```

Expect small mismatches between what each member actually built and this target shape — that's expected and is exactly your job to reconcile, not a sign anything went wrong.

## 4. Common Safety Rules (verify, don't re-implement)

1. Never invent legal authority. 2. Never invent citations. 3. Never invent URLs. 4. Never claim the system is a lawyer. 5. Never present uncertain information as certain. 6. Keep India and International rules separate. 7. Prefer primary/authoritative sources. 8. Preserve source traceability. 9. Abstain when evidence is insufficient. 10. Clearly state output is information, not legal advice.

You do not write new citation/confidence/abstention logic — you verify each of M1/M3/M4/M5's own implementation is consistent with these rules and with each other, and flag/fix small inconsistencies.

---

## 5. Conflict-Resolution Rule

When two workstreams disagree (field names, data types, behavior, legal wording, routing, source metadata, assumptions), do not arbitrarily pick one. Resolve in this priority order:

```text
1. Official SIH Problem Statement (PS.md)
        ↓
2. Authoritative source material (real statutes/treaties/registries cited by M3/M4/M5)
        ↓
3. Plan.md
        ↓
4. Final shared integration contract (Section 3 above)
        ↓
5. Member-specific implementation
```

**Exception:** for a legal/factual disagreement, an authoritative source always wins over any member's implementation, even if that contradicts what a member built. For an implementation/interface disagreement (naming, shape, format), `Plan.md` + the integration contract define the intended result.

When resolving a conflict: identify it, name which source of truth applies, make the smallest safe change, preserve working logic where possible, and record the decision briefly in your phase completion report (what conflicted, which source won, what you changed). Do not write a separate document for this.

---

## Phase 1 — Integration Foundation

**Objective:** Define the integration contracts, golden scenarios and test harness so combining M1–M5 on Day 2 is mechanical, not exploratory.

**Tasks:**
- Set up the integration structure/repo layout that M1–M5's outputs will be dropped into.
- Write integration tests against the target contracts in Section 3, using stub/mock responses (since M1–M5 aren't done yet).
- Contract verification checklist per member (what shape each one's output needs to match).
- Write out the five golden scenarios (Section 6 below) as executable test cases against stubs.
- Fallback/error-path structure (`ErrorResponse` codes, abstention-as-200 behavior).
- Common startup instructions (how to run the combined app once wired).
- Compatibility checks (language, id formats, enum values) to run once real member output lands.

**Tests:** the integration test harness runs successfully against stub/mock responses for all five golden scenarios.

**Acceptance criteria:**
- [ ] Integration structure exists and runs against stubs.
- [ ] Contracts are clearly written down per member.
- [ ] All five golden scenarios are defined as test cases.
- [ ] Tests can be prepared/run once real modules land.

You may begin Phase 2 progressively as individual workstreams become ready enough to integrate — you do not need to wait for all of M1–M5 to report `READY` at once (see Phase 2's Progressive Integration Model).

---

## Phase 2 — Combine Workstreams

**Objective:** Wire the five independent workstreams together into one working application via M1's routing step, integrating each one as soon as it is ready enough — not waiting for all five at once.

**Progressive Integration Model:**

```text
M1 ready enough → M6 can integrate M1
M2 ready enough → M6 can integrate M2
M3 ready enough → M6 can integrate M3
M4 ready enough → M6 can integrate M4
M5 ready enough → M6 can integrate M5
                    ↓
           progressively connect
                    ↓
              final integration
                    ↓
                 final QA
```

- Integrate a workstream as soon as it is stable enough to test — this does not require it to be formally `READY`, only stable enough that integrating it is useful for catching compatibility problems early.
- This does **not** create a dependency for Members 1–5: they keep working independently regardless of what M6 has or hasn't integrated yet.
- You may integrate M1–M5 in any order, as each becomes available, and re-integrate a workstream again after it changes.
- Do not force any member to stop, pause, or change their own pace to suit your integration schedule.
- Do not unnecessarily rewrite a workstream just because it isn't integrated yet — preserve working code and make only the fixes genuinely needed for compatibility.
- Final MVP completion still requires all five workstreams integrated — partial/early integration is for de-risking, not a substitute for full integration.

**Tasks:**
- Inspect each completed (or completed-enough) workstream and identify its actual interface (which will differ slightly from the Section 3 target — that's expected).
- Connect M2's classification output into M1's routing step.
- Connect M3's India guidance into M1's routing step.
- Connect M4's ABS/TK guidance into M1's routing step.
- Connect M5's international guidance into M1's routing step.
- Update M1's central conversational experience so its routing decision actually calls M2–M5 instead of relying solely on M1's own standalone corpus (M1's own corpus becomes the fallback/demo path, per `Plan.md` §6 Member 1 and `MEMBER_1.md`'s corpus-safety rule).
- Resolve naming/format/runtime conflicts (field names, enum casing, language codes, id formats) using the Conflict-Resolution Rule in Section 5 above.
- Preserve each member's working feature logic — make only the fixes necessary for compatibility, not rewrites.

**Tests:** re-run the integration harness from Phase 1 against each real workstream as it's connected, plus one end-to-end pass through M1's routing to whichever of M2–M5 are integrated so far.

**Acceptance criteria:**
- [ ] Each available workstream has been integrated as it became ready.
- [ ] All five workstreams are present and reachable through the combined app once all are complete.
- [ ] Major user flows work end-to-end (question → routing → domain result → assembled answer).
- [ ] Modules communicate correctly (real calls, not stubs).
- [ ] No critical integration error remains.
- [ ] No member was blocked or rewritten unnecessarily by the integration process.

Do not start Phase 3 automatically.

---

## Phase 3 — Final QA

**Objective:** Verify the whole MVP behaves safely and correctly end-to-end, and rehearse the final demo.

**Test checklist** (run each for real, paste output):
1. Application startup.
2. `GET /api/health`.
3. Classifier (`POST /api/classify`) across all six categories + `Uncertain`.
4. English query flow.
5. Hindi query flow (supported scenarios).
6. India-jurisdiction query flow.
7. International-jurisdiction query flow.
8. Citations present in responses.
9. Citation validity (every citation traces to a real source record, no invented URLs).
10. Confidence displayed and varies sensibly.
11. Abstention fires on out-of-corpus/insufficient-evidence queries (HTTP 200, not an error).
12. Fallback/safe response text on abstention.
13. ABS/TKDL scenario (via M4) — no fabricated TKDL content.
14. Indian IP scenario (via M3).
15. International IP scenario (via M5) — confirm PCT/Madrid/Hague are not cross-attributed.
16. All five golden demo scenarios (Section 6 below), including their out-of-corpus abstention variants.
17. Invalid/malformed inputs handled without crashing.

**Tasks:**
- Fix integration problems found above (ordinary bugs — fix them yourself; use `BLOCKED` only for a genuinely unresolved external/project-level issue).
- Re-run the Final Safety Checklist from `Plan.md` §14 (no invented statute/section/regulation/treaty requirement/URL/citation/TKDL text; India/International distinct; abstention/confidence/uncertain-classification work; disclaimer visible; source traceability preserved).
- Rehearse the final internal demo end-to-end at least once, timed.

**Tests:** the 17-point Test checklist above, run for real, plus all five golden demo scenarios and their out-of-corpus abstention variants (Section 6), with pasted output.

**Acceptance criteria:**
- [ ] Complete MVP works.
- [ ] Major flows pass.
- [ ] Safety behavior passes (Section 4 rules hold across all five domains).
- [ ] Citations are valid throughout.
- [ ] No critical runtime error remains.
- [ ] Internal demo is repeatable.

---

## 6. Golden Demo Scenarios (from `Plan.md` §13 — verify against the real, integrated app)

1. "Can I patent a classical Ayurvedic formulation from an authoritative text?" → Section 3(p) + TKDL pointer, India jurisdiction (via M3/M4).
2. "I want to commercialise a formulation using a plant collected in India — what approvals do I need?" → Biological Diversity Act/NBA, not patents (via M4).
3. A herbal product with a specific health claim, run through the classifier (M2) → shows a different regime for "food" (Ayurveda-Aahar) vs "classical/proprietary medicine."
4. "How do I register a GI tag for an Ayurvedic product tied to a region?" → GI Registry pathway (via M3).
5. "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?" → PCT/international patent pathway; must **not** invoke Madrid (trademarks, not patents) (via M5), kept visibly separate from any India answer.

Each scenario must also be tried once with a question outside the curated corpus, to confirm abstention fires instead of a fabricated answer.

---

## Phase Completion Report (paste real output, every phase)

```text
PHASE STATUS

Member: 6
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

1. Read this file. 2. Read the relevant `Plan.md` sections. 3. Inspect the existing repository before changing anything. 4. Execute ONLY the phase you were asked to run. 5. Complete the tasks in that phase. 6. Test it. 7. Fix ordinary bugs yourself (`BLOCKED` is only for genuinely unresolved external issues). 8. Verify acceptance criteria. 9. Stop. 10. Do NOT automatically start the next phase.

Also: do not rebuild M1–M5's domain functionality from scratch — only fix what's genuinely necessary for compatibility. Do not create a handoff system — you are the integration point, not a relay. Checkpoint/commit at the end of each phase. Never mark `READY`/`INTEGRATED` without actually running the acceptance checks and all five golden scenarios, and pasting real output.
