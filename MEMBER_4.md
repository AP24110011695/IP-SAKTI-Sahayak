# MEMBER 4 — ABS + TKDL + Traditional Knowledge

**Project:** IP-SAKTI Sahayak (SIH-26045) — CyberSapien
**Reference:** This file implements Section 6 ("Member 4") of `Plan.md`. Read `Plan.md` in full before starting; if anything here conflicts with `Plan.md`, `Plan.md` wins.
**Deployment:** NOT required for this round.

---

## 1. Role

You own the **complete Access-and-Benefit-Sharing / Traditional-Knowledge guidance domain** — a standalone specialist capability:

```text
ABS/TK question → ABS/TK evidence → guidance → result
```

Scope:
- Access and Benefit Sharing (ABS) obligations.
- Biological Diversity Act requirements relevant to ABS (2023 amendment, 2024 Rules).
- Nagoya Protocol.
- Traditional Knowledge (TK) concepts.
- TKDL pointer/reference behavior.
- Prior-art / traditional-knowledge guidance where the evidence actually supports it.

You own: your own authoritative sources, evidence, metadata, guidance logic, citations, confidence, abstention, and your own tests.

## 2. Boundaries

You do not own India-general IP (patents/GI/trademarks beyond where they intersect ABS — that's M3's domain), international IP (M5's domain), formulation classification (M2's domain), or the central conversational assistant (M1). You must be able to answer a standalone ABS/TK question on your own — you don't need M1's, M3's, or M5's code to build or test.

You must not wait for any other member. Do not create `HANDOFF.md`.

## 3. Real-source rule — and the TKDL-specific constraint

**Never invent** an ABS/BD Act/Nagoya provision, URL, or citation. Cap: roughly **6–10 short curated excerpts** (ABS/Nagoya/BD Act provisions, public TKDL descriptions) — enough for the golden ABS scenario, not a full ABS handbook.

**Critical constraint on TKDL:** TKDL's own database content is restricted to patent offices under NDA — it is not publicly reproducible. This workstream must **point to** TKDL and accurately describe what it covers (a defensive-publication database of codified traditional-medicine knowledge used to defeat spurious patents, referenced via `tkdl.res.in`) rather than quote, paraphrase in detail, or fabricate its internal contents. A `tkdl_pointer` in your output should say "this is TK that TKDL likely covers, consult TKDL/a patent examiner" — never "TKDL says X."

## 4. Interface contract (target shape — implement independently)

```text
answer
citations: Citation[]   # id, source_name, source_type, section, excerpt, url, effective_date
confidence: "HIGH" | "MEDIUM" | "LOW"
confidence_score: 0.0–1.0
abstention: boolean
abstention_reason: string | null
status: "ok" | "abstained" | "processing_error"
tkdl_pointer: string | null   # a pointer/description, never fabricated TKDL text
```

This is a target shape for M6 to wire into M1's routing at integration — build it yourself; don't wait for M1's code.

## 5. Common Safety Rules (implement independently)

1. Never invent legal authority. 2. Never invent citations. 3. Never invent URLs. 4. Never claim the system is a lawyer. 5. Never present uncertain information as certain. 6. Keep India and International rules separate. 7. Prefer primary/authoritative sources. 8. Preserve source traceability. 9. Abstain when evidence is insufficient. 10. Clearly state output is information, not legal advice. **11 (this domain specifically): never fabricate TKDL content — point to it, don't quote it.**

## 6. Implementation Simplicity Rule

This is a 2-day internal MVP. Use the simplest reliable implementation that satisfies the phase acceptance criteria. Do not build: complex retrieval frameworks; unnecessary multi-stage RAG pipelines; unnecessary vector databases; unnecessary rerankers; elaborate agentic workflows; production-scale infrastructure.

Prioritize, in order: 1) correct real evidence; 2) correct domain routing; 3) correct citations; 4) confidence; 5) safe abstention; 6) reliable standalone behavior. A small, correct domain feature is better than a complex one that's hard to integrate.

## 7. Golden scenario you must be able to demo standalone

- "I want to commercialise a formulation using a plant collected in India — what approvals do I need?" — should invoke the Biological Diversity Act / National Biodiversity Authority (ABS approval), and should explicitly **not** be answered as a patents question.
- Try at least one question outside your curated corpus to confirm abstention fires instead of a fabricated answer.
- Try at least one clearly unrelated question (e.g. a pure trademark question) to confirm you don't falsely flag it as ABS-relevant.

---

## Phase 1 — Source Foundation

**Objective:** Assemble a small, real, traceable set of ABS/Nagoya/Biodiversity-Act sources and a legitimate (non-fabricated) TKDL pointer.

**Tasks:**
- Select roughly 6–10 real excerpts: relevant Biological Diversity Act (as amended 2023) provisions and 2024 Rules, relevant Nagoya Protocol articles, and a short, accurate, public description of what TKDL is and does (not its internal content).
- Record source metadata for each: source name, type, section/article, excerpt, real URL, effective date if known.
- Confirm your TKDL description is a pointer/description only — no fabricated database entries.

**Tests:** spot-check every record's URL resolves; verify the TKDL description contains no invented specifics.

**Acceptance criteria:**
- [ ] Sources are real.
- [ ] ABS representation is correct (matches the actual BD Act/Nagoya framework, not an invented one).
- [ ] TKDL is handled legitimately (pointer/description, not fabricated content).
- [ ] No fabricated TKDL text anywhere.

Do not start Phase 2 automatically.

---

## Phase 2 — Guidance Feature

**Objective:** Turn the ABS/TK source foundation into a working guidance feature that correctly recognizes ABS-relevant queries.

Implement citation validation, confidence, and abstention **independently** for this workstream — follow the Common Safety Rules above, but do not depend on M1's, M3's, or M5's implementation.

**Tasks:**
- ABS-relevance determination (does this query actually need ABS/TK guidance, or is it a different IP question misfiled here?).
- Guidance generation via a hosted LLM API, grounded in your Phase 1 evidence.
- TKDL pointer generation (never fabricated content).
- Citations, confidence, abstention.
- Hindi support where practical.

**Tests:** the ABS golden scenario returns correct, grounded guidance; a clearly unrelated question (e.g. trademark-only) is correctly NOT flagged as ABS-relevant; an out-of-corpus ABS question abstains cleanly.

**Acceptance criteria:**
- [ ] ABS cases are correctly recognized.
- [ ] Unrelated cases are not falsely flagged as ABS.
- [ ] Citations are traceable to real stored evidence.
- [ ] Uncertain cases are handled safely (abstain, don't guess).

Do not start Phase 3 automatically.

---

## Phase 3 — Standalone Completion

**Objective:** Bring M4 to a fully self-contained, demo-ready state validated against the golden ABS scenario, with zero fabricated TKDL content.

**Tasks:**
- Run the golden ABS scenario and the traditional-knowledge-adjacent scenarios in Section 7, with pasted real output.
- Edge cases (a question that's part-ABS, part-patent; a question that names a specific plant/species).
- Source/citation audit: verify every citation traces to a real Phase 1 record.
- Explicit TKDL-content audit: re-check every TKDL-related output line for fabricated specifics.
- Final tests.
- Short documentation: how to run standalone, and the exact result shape M6 will need to call.

**Tests:** all Section 7 golden scenarios, the out-of-corpus abstention check, the unrelated-question false-positive check, and the edge cases above, run for real with pasted output.

**Acceptance criteria:**
- [ ] Feature works completely independently.
- [ ] Golden scenarios pass with real, checked output.
- [ ] No fabricated legal or TKDL information anywhere in outputs.
- [ ] Feature is `READY`.

---

## Phase Completion Report (paste real output, every phase)

```text
PHASE STATUS

Member: 4
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

Also: keep the implementation simple (Section 6). Do not redesign unrelated work. Do not invent ABS/BD Act/Nagoya provisions, URLs, or citations. **Never fabricate or reproduce restricted TKDL content.** Do not become general India IP, international IP, the classifier, or the central assistant — stay ABS/TK-only. Do not create a handoff system. Checkpoint/commit at the end of each phase. Never mark `READY` without actually running the acceptance checks and golden scenario, and pasting real output.
