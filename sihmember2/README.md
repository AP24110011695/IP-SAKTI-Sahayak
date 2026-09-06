# Member 2 — Formulation Classifier (IP-SAKTI Sahayak, SIH-26045)

Self-contained, deterministic, rule-based classification of Ayurveda
formulations into **Classical / Proprietary / Phytopharmaceutical /
Ayurveda-Aahar / Cosmetic / New Drug** (or **Uncertain**), with
jurisdiction-aware regime mapping, English/Hindi text, confidence and
one-round clarification support.

Pure Python 3 stdlib. No LLM, no network, no database, no dependencies on any
other member's code. All category distinctions come from `PS.md` /
`Research.md` only (Research.md §B.3 drug/food/cosmetic framework,
First-Schedule classical definition, FSSAI Ayurveda-Aahara exclusions,
phytopharmaceutical/new-drug definitions).

## Run it standalone

```bash
# full test suite (70+ tests)
python -m unittest member2.test_classifier -v

# scripted demo: golden scenario, clarification round, canonical 12-case suite
python -m member2.demo
python -m member2.demo --lang hi

# interactive guided flow (driven by clarification_question_ids)
python -m member2.demo --interactive
python -m member2.demo --interactive --lang hi --jurisdiction international
```

## Programmatic use (what M6/M1 call)

```python
from member2 import classify, apply_clarification, get_questions

result = classify(
    {
        "primary_purpose": "therapeutic",     # option values are stable ids
        "text_source": "yes",                 # case-insensitive
        "standardised_fraction": "no",
        "ingredients_known": "yes",
        "new_indication": "no",
    },
    jurisdiction="India",   # or "International" — context only (see below)
    language="en",          # or "hi" — rendering only (see below)
)

# one clarification round: merge the user's answers to
# result["clarification_question_ids"] and re-classify
result = apply_clarification(answers, {"text_source": "yes"})
```

Question definitions (ids, option ids, English/Hindi text) come from
`get_questions()` — render the guided UI from that, never from hardcoded text.

## Flow

```
get_questions() -> render guided questions (en/hi)
      |
      v
classify(answers, jurisdiction, language)      # deterministic rules
      |
      +-- definite & clear-cut ------------------> result (needs_clarification=False)
      |
      +-- definite but borderline ----------------> result + targeted follow-up
      |       (one missing answer could change      (clarification_question_ids)
      |        the category; confidence MEDIUM/LOW)      |
      |                                                  v
      |                                    apply_clarification(answers, extra)
      |
      +-- incomplete / unsure / contradictory ----> Uncertain + clarification
                                                   prompt naming the blocking
                                                   question(s)
```

- `needs_clarification` is **True** only when the result is `Uncertain` or
  borderline (a consulted-but-unanswered question could flip the category).
  Clear-cut and partial-but-sufficient inputs never ask anything — one round,
  never noisy. The *one round only* conversational policy belongs to the
  caller (M1); `apply_clarification` makes the merge deterministic.
- Confidence: HIGH (0.95) / MEDIUM (0.70) / LOW (0.45), computed by
  re-running the rules on hypothetical answer variations — deterministic and
  explained in `result["reasoning"]`.

## ClassificationResult shape (Plan.md §7 contract + additive extras)

Required contract fields (always present):

| Field                  | Type / values                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| `formulation_class`    | `"Classical" \| "Proprietary" \| "Phytopharmaceutical" \| "Ayurveda-Aahar" \| "Cosmetic" \| "New Drug" \| "Uncertain"` |
| `description`          | non-empty string (localised via `language`)                                   |
| `relevant_regimes`     | list of regime-name strings for `jurisdiction` (Uncertain → `[]`)             |
| `tkdl_pointer`         | string for Classical, else `None` (TKDL is pointed at, never quoted)          |
| `confidence`           | `"HIGH" \| "MEDIUM" \| "LOW"`                                                 |
| `needs_clarification`  | bool                                                                          |
| `clarification_prompt` | string when `needs_clarification`, else `None`                                |

Additive extras (safe for M6 to ignore; validated by
`validate_classification_result`):

| Field                        | Purpose                                                              |
|------------------------------|----------------------------------------------------------------------|
| `confidence_score`           | float 0.0–1.0                                                        |
| `clarification_question_ids` | machine-usable question ids to collect next (empty when not needed)  |
| `jurisdiction`               | `"India"` \| `"International"` (echoed back)                         |
| `language`                   | `"en"` \| `"hi"` (echoed back)                                       |
| `category_labels`            | `{"en": ..., "hi": ...}` human-readable category label               |
| `suggested_questions`        | category-specific follow-ups: `[{"id","en","hi"}, ...]`              |
| `reasoning`                  | step-by-step English rule trace (explainability / audit)             |

`validate_classification_result(result) -> list[str]` returns contract
violations (empty list = valid); M6 can use it as an integration check.

## Deliberate constraints (integration-relevant)

1. **Determinism**: same answers (+ parameters) → byte-identical result. No
   LLM, randomness, clock or network in the decision path. The decision rules
   read only the answer dict — jurisdiction and language never affect the
   classification, only the attached context/rendering.
2. **Machine values are English and stable**: `formulation_class`, question
   ids, option values and regime names do not change with `language`. Hindi
   text is additive (`text_hi`, `options_hi`, `category_labels["hi"]`).
3. **Regime names stay English** in both languages: they are statute/treaty
   proper nouns used as mapping data; no official Hindi legal names are
   invented. Hindi coverage = category labels, questions/options,
   descriptions and all prompt types.
4. **Mapping, not guidance**: `relevant_regimes` names the regimes a category
   implicates (some conditionally worded, e.g. ABS "where biological resources
   are accessed"). Legal guidance for India/ABS/International belongs to
   M3/M4/M5; M2 attaches no advice, filings, forms or outcomes.
5. **Validation errors are explicit**: `member2.ValidationError` (a
   `ValueError`) is raised for non-dict answers, unknown question ids, values
   outside a question's allowed set, or invalid `jurisdiction`/`language`.
   Incomplete input (missing keys, `None`, `""`, `"unsure"`) is *not* an
   error — it classifies safely as `Uncertain`.
6. **TKDL is a pointer, not content**: full TKDL text is restricted (patent
   offices under NDA); the result carries the public pointer only
   (`tkdl.res.in`, from PS.md's dataset list).
7. `relevant_regimes` lists are returned as fresh copies; mutating a result
   cannot corrupt subsequent classifications.

## File map

```
member2/
├── categories.py    # machine-readable category/confidence constants
├── questions.py     # 6 guided questions, bilingual, stable ids
├── strings.py       # bilingual descriptions, blocking reasons, prompts
├── regimes.py       # per-category, per-jurisdiction regime maps + suggested questions
├── classifier.py    # validation, deterministic rules, confidence, result builder
├── demo.py          # scripted demo + interactive CLI (Phase 3 scaffolding)
└── test_classifier.py
```
