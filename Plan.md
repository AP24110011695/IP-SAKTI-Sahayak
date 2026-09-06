# IP-SAKTI Sahayak — Master Execution Plan

**Project:** IP-SAKTI Sahayak  
**SIH Problem:** SIH-26045  
**Team:** CyberSapien  
**Target:** Functional SIH Internal-Round MVP  
**Development window:** ~2 days  
**Deployment:** NOT REQUIRED for the internal round

---

## 1. Purpose

This is the **master plan** for the coding AI agents working on IP-SAKTI Sahayak.

This file is created first. It defines the complete project scope, architecture, six-member workstream division, phases, rules, testing, and final integration process.

Later, this `Plan.md` will be used to create separate execution files:

```text
team/
├── MEMBER_1.md
├── MEMBER_2.md
├── MEMBER_3.md
├── MEMBER_4.md
├── MEMBER_5.md
└── MEMBER_6.md
```

**Do not create those member files while creating this master plan.**

`Plan.md` is the master source of truth for execution.

---

# 2. Project Objective

Build a small, reliable, source-grounded assistant for Ayurveda Intellectual Property and regulatory guidance.

The internal MVP must demonstrate:

1. Formulation classification.
2. India vs International awareness.
3. Relevant legal/regulatory guidance.
4. Retrieval from authoritative sources.
5. Grounded answers.
6. Real citations with source/section/URL where available.
7. Confidence.
8. Safe abstention when evidence is insufficient.
9. English + Hindi MVP support.
10. "Information, not legal advice" disclaimer.
11. ABS guidance.
12. TKDL pointer/reference where appropriate.
13. A working end-to-end demonstration.

The project is intentionally an MVP. Production-scale features are outside the internal-round scope.

Note: the pitch deck's architecture diagram references 22-language support and a self-hosted Indic LLM — these are the production roadmap (Phase 2/3 in the deck), not this build. Coding agents should build and demo only English + Hindi, using a hosted LLM API (see Section 4.5). Do not attempt 22-language coverage or LLM self-hosting in this 2-day window.

---

# 3. Most Important Development Rule

## Complete Workstream, Not Equal Workload

Do **not** divide the project merely into technical layers such as:

```text
Frontend
Backend
RAG
Corpus
Classifier
```

Instead:

> **If several things are strongly connected, keep them under one member.**

> **If a feature can be completed and tested independently, give it to another member.**

Equal workload is NOT required.

A member may have more work if that produces a more self-contained and reliable workstream.

---

# 4. Independence Rule

Members 1–5 must be able to develop their work independently.

A member must NOT wait for another member's unfinished work.

Development should look like:

```text
M1 → complete workstream
M2 → complete workstream
M3 → complete workstream
M4 → complete workstream
M5 → complete workstream
```

Then:

```text
M1 ──┐
M2 ──┤
M3 ──┼──→ M6 → integrate → test → fix → final MVP
M4 ──┤
M5 ──┘
```

The final application will obviously contain connections. Those connections are handled during final integration.

Do NOT create artificial development dependencies.

Do NOT create `HANDOFF.md`.

Do NOT make Members 1–5 continuously exchange unfinished work.

---

# 4.5. Shared Specification (Not a Blocking Phase)

This is a **contract**, not a setup step. No member waits for anyone to build or hand over code before starting Phase 1 — every member reads the same specification below and targets it independently in their own workstream.

A shared specification is fine. A shared implementation dependency is not.

- **Interface shape** — every workstream's final output must match the `QueryRequest`, `QueryResponse`, `Citation`, `ClassificationResult` and `RAG Result` shapes defined in Section 7. Each member implements this shape themselves, in their own code, in whatever way is fastest for their workstream. Nobody needs to import a file another member wrote to do this — matching the spec is enough, and Member 6 reconciles any small mismatches at integration.
- **LLM strategy (recommendation, not a mandate)** — for a 2-day internal round, each member is strongly encouraged to call a hosted LLM API rather than self-hosting or fine-tuning a model. The "open-source Indic LLM" in the pitch deck is a production-roadmap item, not an MVP task, and self-hosting is the most likely way to burn a full day with nothing to show. Each member picks and calls a hosted API independently for their own workstream; if members end up on different providers, Member 6 normalizes this at integration — it is not worth blocking Day 1 on picking one provider together.
- **Corpus caps** — see the size guidance in each member's Phase 1 below. These are per-workstream guidance, not a shared resource anyone waits on.
- **Safety rules** (confidence, citation validation, abstention) — the *rules* in Section 9 are shared and every workstream follows them. The *code* that implements them is not shared: each of M1, M3, M4 and M5 implements its own citation validation, confidence scoring and abstention logic for its own workstream, so that no member is blocked waiting on another's implementation. Member 6 checks all five for consistent behavior during final integration and normalizes small differences rather than forcing a shared library.

---

# 4.6. Knowledge vs Orchestration (Explicit)

This distinction removes the overlap between M1 and M3/M4/M5:

```text
Domain ownership (M2, M3, M4, M5)
  → M2 owns classification knowledge
  → M3 owns Indian-domain knowledge
  → M4 owns ABS/TK-domain knowledge
  → M5 owns international-domain knowledge

Central assistant ownership (M1)
  → owns the conversational experience: asks, routes, assembles, shows

Integration ownership (M6)
  → connects the domain outputs to the central assistant
```

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

## RAG Boundary

There is exactly one RAG responsibility per workstream — no member "owns the project's main RAG":

- **M1** owns the central assistant's own evidence-aware answer flow (its standalone corpus + retrieval, used to build/test/demo M1 independently, and later to assemble whichever domain result routing selects).
- **M3** owns India-specific evidence/retrieval capability.
- **M4** owns ABS/TK-specific evidence/retrieval capability.
- **M5** owns international evidence/retrieval capability.
- **M6** connects these capabilities; it does not own a corpus of its own.

Where retrieval implementation is reused conceptually (e.g. "embed + rank + cite"), the *pattern* may be shared knowledge across members, but the *code and corpus* are never a shared dependency.

---

# 5. Final Six-Member Division

| Member | Workstream | Goal |
|---|---|---|
| **M1** | Main Legal AI Assistant | Complete legal Q&A assistant with retrieval, grounding, citations, confidence and abstention |
| **M2** | Formulation Classifier | Complete formulation classification and classification context |
| **M3** | Indian IP & Regulatory Guidance | Complete India-focused IP/regulatory guidance feature |
| **M4** | ABS + TKDL + Traditional Knowledge | Complete ABS, TKDL and traditional-knowledge feature |
| **M5** | International IP Guidance | Complete international IP/regulatory guidance feature |
| **M6** | Integration Foundation + Final QA | Prepare integration, combine all work, test, fix and finalize |

---

# 6. Workstream Ownership

## Member 1 — Main Legal AI Assistant

Own the complete central conversational assistant experience — the orchestration layer, not a competing domain knowledge base:

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

This member owns the tightly connected assistant/RAG/evidence/answering logic needed to run and test this feature **on its own**, plus the routing decision (which domain a query belongs to) and final answer assembly.

**Member 1 must NOT duplicate:**
- India IP/regulatory legal knowledge (owned by M3);
- ABS/TKDL/traditional-knowledge legal knowledge (owned by M4);
- international IP legal knowledge (owned by M5);
- formulation-classification rules (owned by M2).

The assistant must not depend on another member's unfinished implementation.

A small controlled set of real authoritative sources may be used during development — as a cap, aim for roughly 8–15 short curated excerpts/sections in this workstream, not full statutes. Depth of correct sourcing beats breadth of coverage in a 2-day build. **This corpus exists so M1 can be built, run and tested standalone before integration** — it is not meant to replace or overlap M3/M4/M5's domain corpora. At integration (M6), M1's routing step is wired to call M2/M3/M4/M5's actual outputs; M1's own small corpus then becomes the fallback/demo path rather than the production knowledge source for India/ABS/International queries.

### Phase 1 — Assistant Foundation

**Objective:** Stand up a working end-to-end query→answer pipeline for the central assistant, using its own standalone corpus, runnable and testable without M2–M5.

Build:
- query handling;
- language/jurisdiction context;
- controlled real-source loading;
- retrieval;
- evidence ranking;
- grounded prompt;
- basic answer generation;
- basic response structure;
- tests.

Acceptance:
- query works;
- evidence can be retrieved;
- answer uses retrieved evidence;
- India/International state is respected;
- tests pass.

### Phase 2 — Trust and Safety

**Objective:** Make the assistant's answers trustworthy — every claim traceable, confidence meaningful, and unsupported queries safely declined.

Build:
- evidence threshold;
- citation mapping;
- citation validation;
- confidence;
- abstention;
- safe fallback;
- disclaimer;
- Hindi handling;
- malformed-output handling.

This citation-validation/confidence/abstention logic is built for the main assistant's own use. It follows the same safety rules (Section 9) that M3, M4 and M5 independently implement for their own workstreams — it is not a shared library they import.

Acceptance:
- citations map to real evidence;
- URLs come from stored metadata;
- insufficient evidence abstains;
- confidence works;
- Hindi works for supported scenarios;
- safety tests pass.

### Phase 3 — Standalone Completion

**Objective:** Bring M1 to a fully self-contained, demo-ready state with its routing decision, golden queries and integration interface documented.

Build:
- complete assistant flow;
- follow-ups;
- golden queries;
- edge cases;
- final tests;
- workstream documentation;
- integration interface.

Acceptance:
- works without other members;
- golden queries pass;
- citations are valid;
- abstention works;
- feature is `READY`.

---

## Member 2 — Formulation Classifier

Own the complete formulation-classification feature.

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

Own:
- guided questions;
- decision logic;
- classification;
- confidence;
- clarification;
- relevant-regime mapping;
- suggested questions;
- English/Hindi labels where needed;
- tests.

### Phase 1 — Classification Engine

**Objective:** Build the deterministic classification engine that sorts a formulation into one of the six categories (or Uncertain) from guided answers alone.

Build:
- guided questions;
- deterministic rules;
- six categories;
- `Uncertain`;
- confidence;
- validation;
- tests.

Acceptance:
- known cases classify correctly;
- incomplete input is safe;
- uncertain cases remain uncertain;
- result structure is valid.

### Phase 2 — Context and Routing

**Objective:** Layer regime mapping, clarification and jurisdiction-aware context onto the classification engine without weakening its determinism.

Build:
- relevant-regime mapping;
- suggested questions;
- one clarification round;
- jurisdiction-aware context;
- multilingual labels;
- edge cases.

Acceptance:
- mappings are deterministic;
- clarification is useful;
- no unsupported legal conclusion is generated.

### Phase 3 — Standalone Completion

**Objective:** Bring M2 to a fully self-contained, demo-ready state with bilingual labels, full test coverage and a clear integration interface.

Build:
- final flow;
- 10+ test cases;
- Hindi labels;
- result formatting;
- integration interface;
- documentation.

Acceptance:
- all categories work;
- confidence works;
- routing works;
- tests pass;
- feature is `READY`.

---

## Member 3 — Indian IP & Regulatory Guidance

Own the complete India-focused feature.

Priority scope:
- Patents;
- GI;
- Trademarks;
- Copyright;
- Designs;
- PPV&FRA;
- Drugs & Cosmetics;
- Drugs & Magic Remedies;
- FSSAI Ayurveda-Aahara;
- Indian Biological Diversity requirements where relevant.

Own:
- authoritative sources;
- source metadata;
- evidence;
- India-specific retrieval/guidance;
- citations;
- confidence/abstention where applicable;
- tests.

### Phase 1 — India Source Foundation

**Objective:** Assemble a small, real, traceable set of Indian statutory/regulatory sources covering the priority scope.

Build the real-source foundation for the priority scope. Cap: roughly 10–15 short curated excerpts/sections total across the priority scope (not full acts) — enough to answer the golden scenarios in Section 13 with real citations, not a comprehensive database.

Acceptance:
- sources are real;
- India jurisdiction is explicit;
- metadata is traceable;
- sections/rules are recorded where available.

### Phase 2 — India Guidance

**Objective:** Turn the India source foundation into a working guidance feature with citations, confidence and abstention.

Own citation validation, confidence and abstention for this workstream independently — follow the same safety rules as every other workstream (Section 9), but implement them here rather than depending on another member's code.

Build:
- India query routing;
- evidence selection;
- grounded guidance;
- citations;
- confidence;
- abstention;
- Hindi support where practical.

Acceptance:
- relevant evidence is retrieved;
- citations are traceable;
- unsupported queries abstain;
- India is not confused with International.

### Phase 3 — Standalone Completion

**Objective:** Bring M3 to a fully self-contained, demo-ready state validated against the golden India scenarios.

Build:
- golden India scenarios;
- edge cases;
- citation audit;
- URL validation;
- final tests;
- documentation.

Acceptance:
- feature works independently;
- golden scenarios pass;
- no unsupported claims remain;
- feature is `READY`.

---

## Member 4 — ABS + TKDL + Traditional Knowledge

Own the complete traditional-knowledge workstream.

Scope:
- Access and Benefit Sharing;
- Biological Diversity requirements relevant to ABS;
- Nagoya Protocol;
- Traditional Knowledge;
- TKDL pointer/reference;
- prior-art/traditional-knowledge guidance where supported.

Own:
- authoritative sources;
- evidence;
- metadata;
- guidance logic;
- citations;
- confidence;
- abstention;
- tests.

### Phase 1 — Source Foundation

**Objective:** Assemble a small, real, traceable set of ABS/Nagoya/Biodiversity-Act sources and a legitimate (non-fabricated) TKDL pointer.

Build real-source coverage for the scope above. Cap: roughly 6–10 short curated excerpts (ABS/Nagoya/BD Act provisions, public TKDL descriptions) — enough for the golden ABS scenario, not a full ABS handbook. Since TKDL's own full text is restricted to patent offices under NDA, this workstream must point to TKDL and describe what it covers rather than quote or fabricate its contents.

Acceptance:
- real sources;
- correct ABS representation;
- legitimate TKDL handling;
- no fabricated TKDL text.

### Phase 2 — Guidance Feature

**Objective:** Turn the ABS/TK source foundation into a working guidance feature that correctly recognizes ABS-relevant queries.

Own citation validation, confidence and abstention for this workstream independently — follow the same safety rules as every other workstream (Section 9), but implement them here rather than depending on another member's code.

Build:
- ABS relevance determination;
- guidance;
- TKDL pointer;
- citations;
- confidence;
- abstention;
- Hindi support where practical.

Acceptance:
- ABS cases are recognized;
- unrelated cases are not falsely flagged;
- citations are traceable;
- uncertain cases are safe.

### Phase 3 — Standalone Completion

**Objective:** Bring M4 to a fully self-contained, demo-ready state validated against the golden ABS scenario, with zero fabricated TKDL content.

Build:
- golden ABS scenarios;
- traditional-knowledge scenarios;
- edge cases;
- source/citation audit;
- tests;
- documentation.

Acceptance:
- standalone feature works;
- golden scenarios pass;
- no fabricated legal/TKDL information;
- feature is `READY`.

---

## Member 5 — International IP Guidance

Own the complete international workstream.

Priority scope:
- TRIPS;
- WIPO;
- PCT;
- Madrid;
- Hague;
- relevant CBD/Nagoya material;
- justified export-market material.

Own:
- authoritative international sources;
- jurisdiction/region handling;
- evidence;
- guidance;
- citations;
- confidence;
- abstention;
- tests.

### Phase 1 — International Source Foundation

**Objective:** Assemble a small, real, traceable set of international treaty/route sources (TRIPS, WIPO, PCT, Madrid, Hague, CBD/Nagoya).

Build real-source coverage for the priority scope. Cap: roughly 8–12 short curated excerpts (TRIPS Art. 27.3(b), CBD/Nagoya basics, PCT/Madrid/Hague summaries) — enough for the golden international/export scenario, not full treaty texts.

Acceptance:
- sources are authoritative;
- jurisdiction/region is explicit;
- evidence is traceable.

### Phase 2 — International Guidance

**Objective:** Turn the international source foundation into a working guidance feature with jurisdiction/region-aware routing.

Own citation validation, confidence and abstention for this workstream independently — follow the same safety rules as every other workstream (Section 9), but implement them here rather than depending on another member's code.

Build:
- jurisdiction selection;
- region-aware routing;
- evidence selection;
- grounded guidance;
- citations;
- confidence;
- abstention.

Acceptance:
- international queries retrieve relevant evidence;
- jurisdictions are not conflated;
- citations are valid;
- insufficient evidence abstains.

### Phase 3 — Standalone Completion

**Objective:** Bring M5 to a fully self-contained, demo-ready state validated against the golden international/export scenario.

Build:
- golden international questions;
- export scenarios;
- edge cases;
- citation audit;
- tests;
- documentation.

Acceptance:
- feature works independently;
- golden scenarios pass;
- jurisdiction handling works;
- feature is `READY`.

---

## Member 6 — Integration Foundation + Final QA

Member 6 owns the only workstream whose main purpose is to combine the completed independent workstreams.

Deployment is NOT part of this role for the internal round.

### Phase 1 — Integration Foundation

**Objective:** Define the integration contracts, golden scenarios and test harness so combining M1–M5 on Day 2 is mechanical, not exploratory.

Start immediately.

Build:
- integration structure;
- integration tests;
- contract verification;
- golden scenarios;
- fallback structure;
- common startup instructions;
- compatibility checks.

Acceptance:
- integration structure exists;
- contracts are clear;
- golden scenarios are defined;
- tests can be prepared.

### Phase 2 — Combine Workstreams

**Objective:** Wire the five completed, independent workstreams together into one working application via M1's routing step.

When Members 1–5 have completed their work:

- inspect each completed workstream and identify its interface;
- connect M2's classification output into M1's routing step;
- connect M3's India guidance into M1's routing step;
- connect M4's ABS/TK guidance into M1's routing step;
- connect M5's international guidance into M1's routing step;
- connect M1's central conversational experience so it calls M2–M5 instead of relying solely on its own standalone corpus;
- resolve naming/format/runtime conflicts;
- preserve working feature logic;
- make only necessary fixes, not rewrites.

Acceptance:
- all five workstreams are present;
- major user flows work;
- modules communicate correctly;
- no critical integration error remains.

### Phase 3 — Final QA

**Objective:** Verify the whole MVP behaves safely and correctly end-to-end, and rehearse the final demo.

Test:

1. startup;
2. health;
3. classifier;
4. English;
5. Hindi;
6. India;
7. International;
8. citations;
9. citation validity;
10. confidence;
11. abstention;
12. fallback;
13. ABS/TKDL;
14. Indian IP;
15. international IP;
16. five golden scenarios;
17. invalid inputs.

Fix integration problems.

Acceptance:
- complete MVP works;
- major flows pass;
- safety behavior passes;
- citations are valid;
- no critical runtime error remains;
- internal demo is repeatable.

---

# 7. Shared Integration Rules

These rules exist only so the finished workstreams can be connected safely. They are **not development dependencies**.

## Public API

```text
POST /api/query
POST /api/classify
GET  /api/health
```

## QueryRequest

```text
id: string
query: string
language: "en" | "hi"
jurisdiction: "India" | "International"
formulation_class: FormulationClass | null
history: Message[]
```

## QueryResponse

```text
id: string
answer: string
citations: Citation[]
confidence: "HIGH" | "MEDIUM" | "LOW"
confidence_score: number 0.0–1.0
abstention: boolean
abstention_reason: string | null
escalation_available: boolean
disclaimer: string
```

## Citation

```text
id
source_name
source_type
section
excerpt
url
effective_date
```

The LLM must NOT invent citation metadata.

## ClassificationResult

```text
formulation_class
description
relevant_regimes
tkdl_pointer
confidence
needs_clarification
clarification_prompt
```

## Internal RAG Result

```text
answer
citations
confidence
confidence_score
abstention
abstention_reason
status
```

`status`:

```text
ok
abstained
processing_error
```

## ErrorResponse

```text
VALIDATION_ERROR      → 400
PROCESSING_ERROR      → 502
SERVICE_UNAVAILABLE   → 503
```

Valid abstention is HTTP 200, not an error.

---

# 8. Product-Level Flow

```text
Open application
 ↓
Choose English/Hindi
 ↓
Choose India/International
 ↓
Classify Product (optional)
 ↓
Classification result
 ↓
Relevant context
 ↓
Ask legal/IP question
 ↓
Retrieve evidence
 ↓
Evidence sufficiency check
 ↓
 ┌───────────────────┐
 │                   │
Insufficient       Sufficient
 │                   │
 ↓                   ↓
Abstain          Generate answer
 │                   ↓
Safe fallback     Validate citations
                     ↓
                  Confidence
                     ↓
              Answer + citations
```

---

# 9. Common Safety Rules

Every workstream must:

1. Never invent legal authority.
2. Never invent citations.
3. Never invent URLs.
4. Never claim the system is a lawyer.
5. Never present uncertain information as certain.
6. Keep India and International rules separate.
7. Prefer primary/authoritative sources.
8. Preserve source traceability.
9. Abstain when evidence is insufficient.
10. Clearly state that output is information, not legal advice.

---

# 10. AI Coding Agent Execution Rules

Every member's coding AI must follow this exact pattern:

1. Read its complete member instruction file.
2. Read the relevant parts of `Plan.md`.
3. Inspect the repository before changing anything.
4. Inspect existing code before creating new code.
5. Work only on the assigned workstream.
6. Execute only the currently requested phase.
7. Complete all tasks in that phase.
8. Run tests.
9. Fix ordinary bugs itself.
10. Verify acceptance criteria.
11. Do not automatically start the next phase.
12. Do not redesign unrelated work.
13. Do not invent requirements.
14. Do not invent legal information.
15. Do not create a handoff system.
16. Do not modify another member's work unnecessarily.
17. Keep implementation simple and MVP-focused.
18. Commit/checkpoint at the end of each phase, before starting the next one — a working checkpoint means a bad change can be rolled back without losing everything else.
19. Never mark a phase `READY` from memory or intent alone — actually run the acceptance-criteria checks and the golden query/test for this workstream, and paste the real output in the phase completion report. If a test wasn't actually run, its result is `NOT_STARTED`, not "assumed passing."

---

# 11. Phase Status

Use only:

```text
NOT_STARTED
IN_PROGRESS
READY
BLOCKED
INTEGRATED
```

Do not use `PARTIAL` as an execution state.

For data coverage only, `PARTIAL_COVERAGE` may be used if necessary.

---

# 12. Two-Day Execution

## Day 1 — Parallel Development

All six start independently:

```text
M1 → Main Legal AI Assistant — Phase 1
M2 → Formulation Classifier — Phase 1
M3 → Indian IP — Phase 1
M4 → ABS + TKDL — Phase 1
M5 → International IP — Phase 1
M6 → Integration Foundation — Phase 1
```

Then members continue into their next requested phases according to the team's execution instructions.

**Nobody waits for another member.**

## Day 2 — Completion and Integration

Members 1–5 complete their standalone work.

```text
M1 → READY
M2 → READY
M3 → READY
M4 → READY
M5 → READY
```

M6 progressively integrates completed workstreams and performs final QA.

The integration step is a final connection step, not a development dependency for Members 1–5.

---

# 12.5. Phase Granularity in This Master Plan

Each phase above states its **Objective**, **Tasks** (`Build:`) and **Acceptance criteria** — enough for Members 1–6 to start independently today. Concrete **file/module paths** and **named test cases** are intentionally left for the six per-member execution files (`MEMBER_1.md`…`MEMBER_6.md`), which are the next planning step and are not created in this pass. Restating file trees and exact test names here, before those files exist, would duplicate content that would immediately drift out of sync with them.

---

# 13. Golden Demo Scenarios

The final application must verify at least:

1. Traditional knowledge + patentability — e.g. "Can I patent a classical Ayurvedic formulation from an authoritative text?" (should invoke Section 3(p) and TKDL, India jurisdiction).
2. ABS / biological-resource question — e.g. "I want to commercialise a formulation using a plant collected in India — what approvals do I need?" (should invoke the Biological Diversity Act/NBA, not patents).
3. Ayurveda-Aahar vs medicine classification — e.g. a herbal product with a specific health claim, run through the formulation classifier, showing a different regime for "food" vs "classical/proprietary medicine."
4. Indian IP question — e.g. "How do I register a GI tag for an Ayurvedic product tied to a region?"
5. International/export question — e.g. "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?" (should invoke the PCT/international patent pathway; must NOT invoke Madrid, since Madrid is the trademark registration system, not a patent route — kept visibly separate from the India answer-set).

Each scenario should also be tried once with **insufficient evidence** (a question outside the curated corpus) to confirm abstention fires instead of a fabricated answer. All scenarios must be checked against real evidence before the final demo.

---

# 14. Final Safety Checklist

- [ ] No invented statute.
- [ ] No invented section.
- [ ] No invented regulation.
- [ ] No invented treaty requirement.
- [ ] No invented URL.
- [ ] No fake citation.
- [ ] No fabricated TKDL text.
- [ ] India and International are distinct.
- [ ] Uncertain classification works.
- [ ] Confidence works.
- [ ] Abstention works.
- [ ] Disclaimer is visible.
- [ ] Source traceability is preserved.
- [ ] Real authoritative sources are used.

---

# 15. Definition of Done

## Each Member

A member is `READY` only when:

- all three phases are complete;
- assigned feature works independently;
- real required data/evidence is present;
- tests pass;
- edge cases are handled;
- safety requirements are satisfied;
- integration interface is clear;
- documentation is present;
- no critical blocker remains.

## Whole MVP

The project is complete only when:

- [ ] application starts;
- [ ] main legal assistant works;
- [ ] formulation classifier works;
- [ ] Indian IP feature works;
- [ ] ABS/TKDL feature works;
- [ ] International feature works;
- [ ] `/api/query` works where applicable;
- [ ] `/api/classify` works;
- [ ] `/api/health` works;
- [ ] citations are valid;
- [ ] source URLs are real;
- [ ] confidence is displayed;
- [ ] abstention works;
- [ ] English works;
- [ ] Hindi works for supported MVP flows;
- [ ] India/International handling works;
- [ ] five golden scenarios pass;
- [ ] fallback works;
- [ ] no critical runtime errors remain;
- [ ] final internal demo is rehearsed.

**Deployment is not required.**

---

# 16. Phase Completion Report

Every AI agent must end a phase with:

```text
PHASE STATUS

Member:
Phase:
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

---

# 17. Normal Problem Recovery

For an ordinary implementation problem:

```text
Problem
 ↓
Inspect code
 ↓
Inspect documentation
 ↓
Diagnose
 ↓
Fix
 ↓
Run tests
 ↓
Continue current phase
```

Do not mark `BLOCKED` for an ordinary bug the agent can reasonably fix.

Use `BLOCKED` only for a genuinely unresolved external/project-level issue.

---

# 18. Documentation Hierarchy

The documentation hierarchy is:

```text
Plan.md
   ↓
Member-specific execution files
   ↓
Implementation
```

Do not create competing master plans.

Do not create a handoff-file workflow.

Supporting Markdown files may be created later only when they have a clear purpose.

---

# 19. Final Principle

The six members are **not being given equal amounts of code**.

They are being given **complete areas of responsibility**.

The rule is:

> **Keep connected work together. Keep independent work separate. Let each member finish their own workstream. Then let Member 6 combine, test, and fix the finished work.**

This is the execution model for the IP-SAKTI Sahayak SIH internal-round MVP.
