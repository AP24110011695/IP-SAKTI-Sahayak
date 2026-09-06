# MEMBER 5 — International IP Guidance

**Project:** IP-SAKTI Sahayak (SIH-26045) — CyberSapien
**Reference:** This file implements Section 6 ("Member 5") of `Plan.md`. Read `Plan.md` in full before starting; if anything here conflicts with `Plan.md`, `Plan.md` wins.
**Deployment:** NOT required for this round.

---

## 1. Role

You own the **complete international IP/regulatory guidance domain** — a standalone specialist capability:

```text
International question → international evidence → guidance → result
```

Priority scope:
- TRIPS (incl. Article 27.3(b))
- WIPO GRATK Treaty (2024)
- PCT — **the international patent filing pathway**
- Madrid — **the international trademark registration system** (not patents)
- Hague — **the international industrial-design registration system** (not patents)
- Relevant CBD/Nagoya material at the international level
- Justified export-market material (herbal-product market-access basics for key export markets), where you have a real, citable source

You own: your own authoritative international sources, jurisdiction/region handling, evidence, guidance, citations, confidence, abstention, and your own tests.

**Get the treaty/route mapping right — this is a common factual error to avoid:**

```text
PCT    → patents
Madrid → trademarks
Hague  → industrial designs
```

Never describe Madrid or Hague as a patent route, and never describe PCT as a trademark or design route.

## 2. Boundaries

You do not own India-specific IP (M3's domain), ABS/TKDL (M4's domain), formulation classification (M2's domain), or the central conversational assistant (M1). You must be able to answer a standalone international IP question on your own — you don't need M1's, M3's, or M4's code to build or test.

You must not wait for any other member. Do not create `HANDOFF.md`.

## 3. Real-source rule

**Never invent** a treaty article, route, requirement, URL, or citation. Cap: roughly **8–12 short curated excerpts** (e.g. TRIPS Art. 27.3(b), CBD/Nagoya basics at the international level, PCT/Madrid/Hague summaries) — enough for the golden international/export scenario, not full treaty texts.

## 4. Interface contract (target shape — implement independently)

```text
answer
citations: Citation[]   # id, source_name, source_type, section, excerpt, url, effective_date
confidence: "HIGH" | "MEDIUM" | "LOW"
confidence_score: 0.0–1.0
abstention: boolean
abstention_reason: string | null
status: "ok" | "abstained" | "processing_error"
```

This is a target shape for M6 to wire into M1's routing at integration — build it yourself; don't wait for M1's code.

## 5. Common Safety Rules (implement independently)

1. Never invent legal authority. 2. Never invent citations. 3. Never invent URLs. 4. Never claim the system is a lawyer. 5. Never present uncertain information as certain. 6. Keep India and International rules separate (you only ever answer as International, and your answer must not blend in India-specific procedure). 7. Prefer primary/authoritative sources. 8. Preserve source traceability. 9. Abstain when evidence is insufficient. 10. Clearly state output is information, not legal advice.

## 6. Implementation Simplicity Rule

This is a 2-day internal MVP. Use the simplest reliable implementation that satisfies the phase acceptance criteria. Do not build: complex retrieval frameworks; unnecessary multi-stage RAG pipelines; unnecessary vector databases; unnecessary rerankers; elaborate agentic workflows; production-scale infrastructure.

Prioritize, in order: 1) correct real evidence; 2) correct domain routing; 3) correct citations; 4) confidence; 5) safe abstention; 6) reliable standalone behavior. A small, correct domain feature is better than a complex one that's hard to integrate.

## 7. Golden scenario you must be able to demo standalone

- "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?" — must correctly point to the **PCT** international patent pathway. Must **not** mention Madrid as a route for this (Madrid is trademarks). Kept visibly separate from any India-jurisdiction answer.
- Try at least one question outside your curated corpus to confirm abstention fires instead of a fabricated answer.
- Try at least one trademark-flavored international question ("I want to register my Ayurvedic brand name internationally") to confirm you correctly point to Madrid, not PCT — this is your internal check that you haven't swapped the two systems.

---

## Phase 1 — International Source Foundation

**Objective:** Assemble a small, real, traceable set of international treaty/route sources (TRIPS, WIPO, PCT, Madrid, Hague, CBD/Nagoya).

**Tasks:**
- Select roughly 8–12 real excerpts across the priority scope, each tagged with which IP right it governs (patent / trademark / design / other) so PCT/Madrid/Hague are never confused downstream.
- Record source metadata: source name, type, article/section, excerpt, real URL, effective date if known.
- Make the international jurisdiction explicit and the specific right (patent/trademark/design) explicit on every relevant record.

**Tests:** spot-check every record's URL resolves; verify PCT/Madrid/Hague records are each tagged with the correct IP right.

**Acceptance criteria:**
- [ ] Sources are authoritative and real.
- [ ] Jurisdiction/region is explicit, and the specific right (patent/trademark/design) is explicit for PCT/Madrid/Hague records.
- [ ] Evidence is traceable.

Do not start Phase 2 automatically.

---

## Phase 2 — International Guidance

**Objective:** Turn the international source foundation into a working guidance feature with jurisdiction/region-aware routing.

Implement citation validation, confidence, and abstention **independently** for this workstream — follow the Common Safety Rules above, but do not depend on M1's, M3's, or M4's implementation.

**Tasks:**
- Jurisdiction selection / region-aware routing.
- Evidence selection, keyed correctly by IP right (patent question → PCT evidence; trademark question → Madrid evidence; design question → Hague evidence).
- Grounded guidance generation via a hosted LLM API.
- Citations, confidence, abstention.
- A guardrail check: before returning an answer that mentions PCT, Madrid, or Hague, verify the right being discussed (patent/trademark/design) matches the system being cited.

**Tests:** the patent golden scenario returns PCT, not Madrid; the trademark check scenario returns Madrid, not PCT; an out-of-corpus question abstains cleanly.

**Acceptance criteria:**
- [ ] International queries retrieve relevant evidence.
- [ ] Jurisdictions are not conflated with India.
- [ ] PCT/Madrid/Hague are never cross-attributed to the wrong IP right.
- [ ] Citations are valid.
- [ ] Insufficient evidence triggers abstention.

Do not start Phase 3 automatically.

---

## Phase 3 — Standalone Completion

**Objective:** Bring M5 to a fully self-contained, demo-ready state validated against the golden international/export scenario.

**Tasks:**
- Run the golden scenarios in Section 7, with pasted real output.
- Export/market-access scenario if you have a real citable source for it.
- Edge cases (a query that touches both patent and trademark protection for the same product).
- Citation audit: verify every citation traces to a real Phase 1 record, and that PCT/Madrid/Hague attributions are all correct.
- Final tests.
- Short documentation: how to run standalone, and the exact result shape M6 will need to call.

**Tests:** all Section 7 golden scenarios (including the trademark self-check), the out-of-corpus abstention check, and the edge cases above, run for real with pasted output.

**Acceptance criteria:**
- [ ] Feature works completely independently.
- [ ] Golden scenarios pass with real, checked output.
- [ ] Jurisdiction handling works, and no patent/trademark/design system is mis-attributed.
- [ ] Feature is `READY`.

---

## Phase Completion Report (paste real output, every phase)

```text
PHASE STATUS

Member: 5
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

Also: keep the implementation simple (Section 6). Do not redesign unrelated work. Do not invent treaty articles, routes, requirements, URLs, or citations. Never confuse PCT (patents) / Madrid (trademarks) / Hague (designs). Do not create a handoff system. Checkpoint/commit at the end of each phase. Never mark `READY` without actually running the acceptance checks and golden scenarios, and pasting real output.
