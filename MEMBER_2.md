# MEMBER 2 — Formulation Classifier

**Project:** IP-SAKTI Sahayak (SIH-26045) — CyberSapien
**Reference:** This file implements Section 6 ("Member 2") of `Plan.md`. Read `Plan.md` in full before starting; if anything here conflicts with `Plan.md`, `Plan.md` wins.
**Deployment:** NOT required for this round.

---

## 1. Role

You own the **complete formulation-classification feature**: given guided answers about a product, deterministically sort it into one of six categories (or `Uncertain`), and map it to the regimes it implicates.

Required categories:

```text
Classical
Proprietary
Phytopharmaceutical
Ayurveda-Aahar
Cosmetic
New Drug
Uncertain
```

You own: the guided questions, decision logic, classification, confidence, one round of clarification, relevant-regime mapping, suggested questions, English/Hindi labels, and your own tests.

## 2. Boundaries

You do not own India/ABS/International legal knowledge (M3/M4/M5) or the central conversational assistant (M1). You produce a `ClassificationResult` that M1 will later route on — you do not need M1's code to build or test yourself; a CLI, notebook, or minimal test harness that calls your classifier directly is enough.

You must not wait for M1 or any other member. Do not create `HANDOFF.md`.

## 3. Interface contract (target shape — implement independently)

```text
ClassificationResult:
  formulation_class
  description
  relevant_regimes
  tkdl_pointer
  confidence
  needs_clarification
  clarification_prompt
```

This is a target shape for M6 to wire into M1 later — build it yourself; don't wait for anyone else's code to match against.

## 4. Basis for classification (from the problem statement)

Use the distinctions in `PS.md`/`Research.md` as your source of truth for what separates the categories, e.g.: a classical/generic medicine has its formulation and method drawn from a First-Schedule authoritative text (largely traditional knowledge, faces the Section 3(p) patent bar, defended via TKDL); a new/non-classical drug requires proof of safety and effectiveness and has genuine patent potential; phytopharmaceuticals, Ayurveda-Aahar/nutraceuticals and cosmetics are distinct regulatory tracks again. Do not invent classification criteria beyond what these documents support — if uncertain, that's what the `Uncertain` category and clarification round are for.

## 5. Golden scenario you must be able to demo standalone

- A herbal product with a specific health claim, run through your classifier, showing it lands in a **different** category (e.g. Ayurveda-Aahar/food vs classical/proprietary medicine) depending on the answers given — demonstrating the classifier actually discriminates, not just returns a default.

---

## Phase 1 — Classification Engine

**Objective:** Build the deterministic classification engine that sorts a formulation into one of the six categories (or `Uncertain`) from guided answers alone.

**Tasks:**
- Guided questions (the minimum set needed to discriminate the six categories).
- Deterministic decision rules (not a black-box LLM guess — the classification itself should be rule-based/explainable; an LLM may help phrase questions/output, but the category decision must be traceable).
- All six categories + `Uncertain` fallback.
- Confidence for the classification.
- Input validation.
- Unit tests.

**Tests:** at least one clear-cut worked example per category (6 cases) plus at least one genuinely ambiguous case that should return `Uncertain`.

**Acceptance criteria:**
- [ ] Known/worked cases classify correctly.
- [ ] Incomplete input is handled safely (doesn't crash, doesn't guess wildly).
- [ ] Genuinely ambiguous cases remain `Uncertain` rather than forcing a category.
- [ ] Result structure is valid.

Do not start Phase 2 automatically.

---

## Phase 2 — Context and Routing

**Objective:** Layer regime mapping, clarification and jurisdiction-aware context onto the classification engine without weakening its determinism.

**Tasks:**
- Relevant-regime mapping per category (e.g. classical → TKDL/Section 3(p) exposure; new drug → patent potential + clinical evidence requirement).
- Suggested follow-up questions per category.
- One round of clarification for borderline/incomplete answers.
- Jurisdiction-aware context (India vs International) — the classification itself doesn't change by jurisdiction, but the regime mapping you attach might reference which regime set is relevant.
- Multilingual (English/Hindi) labels for categories and questions.
- Edge cases (contradictory answers, partial answers).

**Tests:** verify regime mappings are the same every time for the same input (deterministic); verify clarification triggers only when genuinely needed, not on every query.

**Acceptance criteria:**
- [ ] Regime mappings are deterministic.
- [ ] Clarification round is useful (narrows genuinely ambiguous cases) not noisy.
- [ ] No unsupported legal conclusion is generated (you map to regimes, you don't give legal guidance — that's M3/M4/M5's job).

Do not start Phase 3 automatically.

---

## Phase 3 — Standalone Completion

**Objective:** Bring M2 to a fully self-contained, demo-ready state with bilingual labels, full test coverage and a clear integration interface.

**Tasks:**
- Final end-to-end flow (questions → answers → classification → regime mapping → result).
- 10+ test cases covering all six categories, `Uncertain`, and edge cases.
- Hindi labels verified for all categories/questions.
- Result formatting matching the `ClassificationResult` contract.
- Run the golden scenario in Section 5 above, with pasted output.
- Short documentation: how to run your classifier standalone, and the exact shape M6 will need to call.

**Tests:** the 10+ case suite (all six categories + `Uncertain` + edge cases) plus the golden scenario from Section 5, run for real with pasted output.

**Acceptance criteria:**
- [ ] All six categories work, plus `Uncertain`.
- [ ] Confidence works.
- [ ] Regime-mapping/routing works.
- [ ] Tests pass (10+ cases).
- [ ] Feature is `READY`.

---

## Phase Completion Report (paste real output, every phase)

```text
PHASE STATUS

Member: 2
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

Also: do not redesign unrelated work. Do not invent classification criteria beyond what `PS.md`/`Research.md` support. Do not give India/ABS/International legal guidance — map to regimes only, leave the guidance itself to M3/M4/M5. Do not create a handoff system. Checkpoint/commit at the end of each phase. Never mark `READY` without actually running the acceptance checks and golden scenario, and pasting real output.
