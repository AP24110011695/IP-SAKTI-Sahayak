# MEMBER 3 — Indian IP & Regulatory Guidance

**Project:** IP-SAKTI Sahayak (SIH-26045) — CyberSapien
**Reference:** This file implements Section 6 ("Member 3") of `Plan.md`. Read `Plan.md` in full before starting; if anything here conflicts with `Plan.md`, `Plan.md` wins.
**Deployment:** NOT required for this round.

---

## 1. Role

You own the **complete India-focused IP/regulatory guidance domain** — a standalone specialist capability:

```text
India question → India evidence → India guidance → result
```

Priority scope:
- Patents (incl. the 2024 Patent Rules and the Section 3(p) TK bar)
- GI (Geographical Indications)
- Trade Marks
- Copyright
- Designs
- Plant Variety Protection & Farmers' Rights (PPV&FRA)
- Drugs & Cosmetics Act
- Drugs and Magic Remedies (Objectionable Advertisements) Act
- FSSAI Ayurveda-Aahar regulations
- Indian Biological Diversity Act requirements, where they intersect with India-specific guidance (deep ABS/Nagoya work is M4's job, not yours — cite the BD Act only where an India-IP question needs it)

You own: your own authoritative sources, source metadata, evidence, India-specific retrieval/guidance, citations, confidence/abstention for your workstream, and your own tests.

## 2. Boundaries

You do not own ABS/TKDL/traditional-knowledge (M4's domain), international IP (M5's domain), formulation classification (M2's domain), or the central conversational assistant (M1). You must be able to answer a standalone India IP question and produce a result on your own — you don't need M1's, M4's, or M5's code to build or test.

You must not wait for any other member. Do not create `HANDOFF.md`.

## 3. Real-source rule

**Never invent** a statute, section, rule, URL, form, fee, or citation. Cap: roughly **10–15 short curated excerpts/sections total** across the priority scope above (not full acts) — enough to answer the golden scenarios below with real citations, not a comprehensive database. Depth of correct sourcing beats breadth.

Good starting points (see `PS.md`): India Code (indiacode.nic.in), IP India public databases (patents/InPASS, trade marks, designs, GI Registry — ipindia.gov.in), TKDL (tkdl.res.in) for the pointer only, National Biodiversity Authority (nbaindia.or*).

## 4. Interface contract (target shape — implement independently)

Produce something matching the `RAG Result` shape used across the project:

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

1. Never invent legal authority. 2. Never invent citations. 3. Never invent URLs. 4. Never claim the system is a lawyer. 5. Never present uncertain information as certain. 6. Keep India and International rules separate (you only ever answer as India). 7. Prefer primary/authoritative sources. 8. Preserve source traceability. 9. Abstain when evidence is insufficient. 10. Clearly state output is information, not legal advice.

## 6. Implementation Simplicity Rule

This is a 2-day internal MVP. Use the simplest reliable implementation that satisfies the phase acceptance criteria. Do not build: complex retrieval frameworks; unnecessary multi-stage RAG pipelines; unnecessary vector databases; unnecessary rerankers; elaborate agentic workflows; production-scale infrastructure.

Prioritize, in order: 1) correct real evidence; 2) correct domain routing; 3) correct citations; 4) confidence; 5) safe abstention; 6) reliable standalone behavior. A small, correct domain feature is better than a complex one that's hard to integrate.

## 7. Golden scenarios you must be able to demo standalone

1. "Can I patent a classical Ayurvedic formulation from an authoritative text?" — should invoke Section 3(p) of the Patents Act and point to TKDL as the defensive-disclosure mechanism (you point to TKDL's role; you don't need to reproduce TKDL's restricted content — that nuance is M4's, but a India-patent answer should still correctly name TKDL as the relevant tool).
2. "How do I register a GI tag for an Ayurvedic product tied to a region?" — should invoke the GI Registry/GI Act pathway.
3. Try at least one question outside your curated corpus to confirm abstention fires instead of a fabricated answer.

---

## Phase 1 — India Source Foundation

**Objective:** Assemble a small, real, traceable set of Indian statutory/regulatory sources covering the priority scope.

**Tasks:**
- Select roughly 10–15 real excerpts/sections across the priority scope, prioritizing what's needed for the golden scenarios.
- Record source metadata for each: source name, source type (statute/rule/registry/pharmacopoeia), section/rule number where available, a short excerpt, a real URL, and an effective date if known.
- Make the India jurisdiction explicit on every record (this is never ambiguous with International).
- Basic tests: metadata is complete and well-formed for every record.

**Tests:** spot-check every record's URL resolves and every section/rule number is correctly named.

**Acceptance criteria:**
- [ ] Sources are real (traceable to an actual statute/rule/registry, not invented).
- [ ] India jurisdiction is explicit on every record.
- [ ] Metadata is traceable (URL/section present where available).
- [ ] Sections/rules are recorded where available.

Do not start Phase 2 automatically.

---

## Phase 2 — India Guidance

**Objective:** Turn the India source foundation into a working guidance feature with citations, confidence and abstention.

Implement citation validation, confidence, and abstention **independently** for this workstream — follow the Common Safety Rules above, but do not depend on M1's, M4's, or M5's implementation of the same rules.

**Tasks:**
- India query routing (map a free-text question to the relevant slice of your corpus).
- Evidence selection/retrieval.
- Grounded guidance generation via a hosted LLM API (see `Plan.md` §4.5) constrained to your retrieved evidence.
- Citations (mapped only to real stored evidence).
- Confidence scoring.
- Abstention when evidence is insufficient.
- Hindi support where practical for this workstream's scenarios.

**Tests:** each golden scenario in Section 7 returns a grounded, cited answer; an out-of-corpus question abstains cleanly.

**Acceptance criteria:**
- [ ] Relevant evidence is retrieved for in-scope questions.
- [ ] Citations are traceable to real stored evidence.
- [ ] Unsupported/out-of-scope queries abstain rather than guess.
- [ ] India answers are never confused with or blended into an International answer.

Do not start Phase 3 automatically.

---

## Phase 3 — Standalone Completion

**Objective:** Bring M3 to a fully self-contained, demo-ready state validated against the golden India scenarios.

**Tasks:**
- Run the golden India scenarios in Section 7, with pasted real output.
- Edge cases (ambiguous IP type, multiple regimes implicated at once, e.g. a product that's both a GI candidate and a classical-medicine patent question).
- Citation audit: verify every citation in your test outputs actually traces to a record from Phase 1.
- URL validation: verify every URL you cite actually resolves to a real, relevant page.
- Final tests.
- Short documentation: how to run standalone, and the exact result shape M6 will need to call.

**Tests:** all Section 7 golden scenarios, the out-of-corpus abstention check, and the edge cases above, run for real with pasted output.

**Acceptance criteria:**
- [ ] Golden scenarios pass with real, checked output.
- [ ] No unsupported claims remain.
- [ ] Feature is `READY`.

---

## Phase Completion Report (paste real output, every phase)

```text
PHASE STATUS

Member: 3
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

Also: keep the implementation simple (Section 6). Do not redesign unrelated work. Do not invent statutes/sections/rules/URLs/fees/citations. Do not become the central assistant, the international specialist, the ABS/TK specialist, or the classifier — stay India-only. Do not create a handoff system. Checkpoint/commit at the end of each phase. Never mark `READY` without actually running the acceptance checks and golden scenarios, and pasting real output.
