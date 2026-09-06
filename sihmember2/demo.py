"""Standalone demo / minimal CLI for the Member 2 formulation classifier.

Pure stdlib, no UI, no server, no dependencies -- enough to demo and exercise
the whole M2 feature end-to-end without any other member's code:

    python -m member2.demo                     # scripted demo (English)
    python -m member2.demo --lang hi           # scripted demo (Hindi)
    python -m member2.demo --interactive       # guided question flow (terminal)
    python -m member2.demo --interactive --lang hi --jurisdiction international

The interactive flow is driven ENTIRELY by the classifier's public API: it
shows the current question (from ``clarification_question_ids``), records the
answer, and re-classifies -- it contains no decision logic of its own. Each
question is asked at most once, and classification always stays deterministic
and rule-based inside classifier.py.

This module is demo scaffolding (M2 Phase 3); the classifier has no dependency
on it, and M6 does not need it for integration.
"""

import sys

from . import (
    AYURVEDA_AAHAR,
    CLASSICAL,
    COSMETIC,
    NEW_DRUG,
    PROPRIETARY,
    PHYTOPHARMACEUTICAL,
    UNCERTAIN,
    HIGH,
    INDIA,
    INTERNATIONAL,
    apply_clarification,
    classify,
    get_question,
    validate_classification_result,
)

EN = "en"
HI = "hi"

# Demo-level UI strings (not part of the classifier contract).
UNSURE_LABEL = {EN: "u. I don't know / not sure", HI: "u. मुझे नहीं पता / अनिश्चित"}
SKIP_LABEL = {EN: "s. skip (leave unanswered)", HI: "s. छोड़ें (उत्तर न दें)"}
QUIT_LABEL = {EN: "q. stop here", HI: "q. यहीं रोकें"}
CHOOSE_PROMPT = {EN: "Choose 1-{}, u, s or q: ", HI: "1-{}, u, s या q में से चुनें: "}

# ---------------------------------------------------------------------------
# Golden scenario (MEMBER_2.md Section 5): a herbal product with a specific
# health claim must land in DIFFERENT categories depending on the answers.
# ---------------------------------------------------------------------------

GOLDEN_PRODUCT = "Herbal amla-moringa health mix (same product, different presentations)"

GOLDEN_SCENARIOS = [
    (
        "A. positioned as FOOD: wellness/immunity claim only, no treatment claim, "
        "no bhasma, no Schedule E-1 herbs",
        {"primary_purpose": "food_wellness", "food_exclusion": "none",
         "new_indication": "no"},
        AYURVEDA_AAHAR,
    ),
    (
        "B. positioned as MEDICINE: recipe unchanged from Charaka Samhita",
        {"primary_purpose": "therapeutic", "text_source": "yes",
         "standardised_fraction": "no", "ingredients_known": "yes",
         "new_indication": "no"},
        CLASSICAL,
    ),
    (
        "C. positioned as MEDICINE claiming to TREAT type-2 diabetes "
        "(indication not established for these ingredients)",
        {"primary_purpose": "therapeutic", "text_source": "no",
         "standardised_fraction": "no", "ingredients_known": "yes",
         "new_indication": "yes"},
        NEW_DRUG,
    ),
]

# Canonical 10+ case suite (also asserted in test_classifier.py).
CASE_SUITE = [
    ("classical: unchanged authoritative-text recipe", CLASSICAL,
     {"primary_purpose": "therapeutic", "text_source": "yes",
      "standardised_fraction": "no", "ingredients_known": "yes",
      "new_indication": "no"}),
    ("proprietary: new combination of known ingredients", PROPRIETARY,
     {"primary_purpose": "therapeutic", "text_source": "no",
      "standardised_fraction": "no", "ingredients_known": "yes",
      "new_indication": "no"}),
    ("phytopharmaceutical: standardised fraction, defined markers",
     PHYTOPHARMACEUTICAL,
     {"primary_purpose": "therapeutic", "text_source": "no",
      "standardised_fraction": "yes"}),
    ("new drug: novel ingredient", NEW_DRUG,
     {"primary_purpose": "therapeutic", "text_source": "no",
      "standardised_fraction": "no", "ingredients_known": "no"}),
    ("ayurveda-aahar: food, wellness claims only", AYURVEDA_AAHAR,
     {"primary_purpose": "food_wellness", "food_exclusion": "none",
      "new_indication": "no"}),
    ("cosmetic: external cleansing/beautifying use", COSMETIC,
     {"primary_purpose": "external_cosmetic", "new_indication": "no"}),
    ("uncertain: discriminating answers 'unsure'", UNCERTAIN,
     {"primary_purpose": "therapeutic", "text_source": "unsure",
      "standardised_fraction": "unsure"}),
    ("uncertain: nothing answered", UNCERTAIN, {}),
    ("edge: contradictory text-source vs standardisation", UNCERTAIN,
     {"primary_purpose": "therapeutic", "text_source": "yes",
      "standardised_fraction": "yes"}),
    ("edge: food carrying a cure claim moves to the drug track", NEW_DRUG,
     {"primary_purpose": "food_wellness", "food_exclusion": "none",
      "new_indication": "yes", "text_source": "no",
      "standardised_fraction": "no", "ingredients_known": "yes"}),
    ("edge: bhasma 'food' from an authoritative text is a classical drug",
     CLASSICAL,
     {"primary_purpose": "food_wellness", "food_exclusion": "bhasma_or_e1",
      "text_source": "yes", "new_indication": "no"}),
    ("edge: classical recipe with a new therapeutic claim (MEDIUM cap)",
     CLASSICAL,
     {"primary_purpose": "therapeutic", "text_source": "yes",
      "standardised_fraction": "no", "ingredients_known": "yes",
      "new_indication": "yes"}),
]


def collect_scripted_results():
    """Run all scripted scenarios and return (label, result) pairs.

    Test-friendly: no printing. Every result is a real classify() output.
    """
    results = []
    for label, answers, _ in GOLDEN_SCENARIOS:
        results.append(("golden/" + label, classify(answers)))
    for label, _, answers in CASE_SUITE:
        results.append(("suite/" + label, classify(answers)))
    return results


def collect_clarification_round(language=EN):
    """One clarification round: incomplete -> prompt -> narrowed result."""
    first = classify({"primary_purpose": "therapeutic"}, language=language)
    prompt = first["clarification_prompt"]
    final = apply_clarification(
        {"primary_purpose": "therapeutic"}, {"text_source": "yes"},
        language=language,
    )
    return first, prompt, final


def run_scripted(language=EN, jurisdiction=INDIA, output_fn=print):
    """Print the full scripted demo. Returns the collected results for tests."""
    line = "=" * 72
    output_fn(line)
    output_fn("IP-SAKTI Sahayak - Member 2 Formulation Classifier (standalone demo)")
    output_fn("deterministic rule-based classification | no LLM in the decision path")
    output_fn(line)

    output_fn("\n1. GOLDEN SCENARIO (MEMBER_2.md Section 5)")
    output_fn("   Product: %s" % GOLDEN_PRODUCT)
    golden_results = []
    for label, answers, expected in GOLDEN_SCENARIOS:
        result = classify(answers, jurisdiction=jurisdiction, language=language)
        golden_results.append((label, result))
        output_fn("   - %s" % label)
        output_fn("     -> formulation_class: %s | confidence: %s (%s)"
                  % (result["formulation_class"], result["confidence"],
                     result["confidence_score"]))
        output_fn("     -> regimes: %s" % "; ".join(result["relevant_regimes"][:2]))
    categories = {r["formulation_class"] for _, r in golden_results}
    output_fn("   => discriminated into %d different categories: %s"
              % (len(categories), sorted(categories)))

    output_fn("\n2. FULL ClassificationResult for golden scenario B (exact shape M6 consumes)")
    output_fn(json_safe(golden_results[1][1]))

    first, prompt, final = collect_clarification_round(language=language)
    output_fn("\n3. ONE CLARIFICATION ROUND (incomplete -> prompt -> narrowed)")
    output_fn("   answers given: primary_purpose='therapeutic'")
    output_fn("   -> %s | asks: %s" % (first["formulation_class"],
                                       first["clarification_question_ids"]))
    output_fn("   prompt: %s" % prompt)
    output_fn("   after answering text_source='yes' -> %s (confidence %s, "
              "needs_clarification=%s)"
              % (final["formulation_class"], final["confidence"],
                 final["needs_clarification"]))

    output_fn("\n4. ALL %d CASES OF THE CANONICAL SUITE" % len(CASE_SUITE))
    for label, _, answers in CASE_SUITE:
        result = classify(answers, jurisdiction=jurisdiction, language=language)
        problems = validate_classification_result(result)
        output_fn("   [%s] %-58s -> %s (%s)%s"
                  % ("OK" if not problems else "BAD", label[:58],
                     result["formulation_class"], result["confidence"],
                     "" if not problems else " structure problems: %s" % problems))

    output_fn("\n5. HINDI SAMPLE (machine values stable, text localised)")
    hi_result = classify(CASE_SUITE[0][2], language=HI)
    output_fn("   formulation_class (machine): %s" % hi_result["formulation_class"])
    output_fn("   label: %s / %s" % (hi_result["category_labels"]["en"],
                                     hi_result["category_labels"]["hi"]))
    output_fn("   description: %s..." % hi_result["description"][:60])

    output_fn("\n6. STRUCTURE CHECK")
    all_results = golden_results + [(label, classify(a)) for label, _, a in CASE_SUITE]
    problems_total = sum(1 for _, r in all_results if validate_classification_result(r))
    output_fn("   validate_classification_result: %d/%d results valid"
              % (len(all_results) - problems_total, len(all_results)))
    output_fn(line)
    return golden_results


def json_safe(result):
    """Render a ClassificationResult as readable JSON for the console."""
    import json
    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Interactive guided flow
# ---------------------------------------------------------------------------

def _ask_question(question_id, language, input_fn, output_fn):
    """Ask one guided question. Returns the option value, 'unsure', '' (skip)
    or None (quit)."""
    question = get_question(question_id)
    text = question["text_hi"] if language == HI else question["text"]
    options = question["options_hi"] if language == HI else question["options"]
    output_fn("\n" + text)
    keys = list(options)
    for index, key in enumerate(keys, start=1):
        output_fn("  %d. %s" % (index, options[key]))
    output_fn("  %s" % UNSURE_LABEL[language])
    output_fn("  %s" % SKIP_LABEL[language])
    output_fn("  %s" % QUIT_LABEL[language])
    while True:
        raw = input_fn(CHOOSE_PROMPT[language].format(len(keys))).strip().lower()
        if raw == "q":
            return None
        if raw == "u":
            return "unsure"
        if raw == "s":
            return ""
        if raw in options:
            return raw
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            return keys[int(raw) - 1]
        output_fn("  ? try again")


def run_interactive(input_fn=input, output_fn=print, language=EN, jurisdiction=INDIA):
    """Guided question flow: questions -> answers -> classification -> regimes
    -> clarification (as needed) -> final ClassificationResult.

    Driven only by the classifier's public API (clarification_question_ids);
    each question is asked at most once. Returns the final result dict.
    """
    line = "=" * 72
    output_fn(line)
    output_fn("IP-SAKTI Sahayak - Formulation Classifier (guided flow)")
    output_fn(line)

    answers = {}
    asked = set()
    result = classify(answers, jurisdiction=jurisdiction, language=language)
    for _ in range(len(get_question_list()) + 1):
        if not result["needs_clarification"]:
            break
        pending = [qid for qid in result["clarification_question_ids"] if qid not in asked]
        if not pending:
            break
        question_id = pending[0]
        asked.add(question_id)
        value = _ask_question(question_id, language, input_fn, output_fn)
        if value is None:
            break
        if value != "":
            answers[question_id] = value
        result = classify(answers, jurisdiction=jurisdiction, language=language)

    output_fn("\n" + line)
    output_fn("RESULT")
    output_fn(line)
    output_fn(json_safe(result))
    return result


def get_question_list():
    from .questions import QUESTIONS
    return QUESTIONS


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    language = EN
    jurisdiction = INDIA
    interactive = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--interactive":
            interactive = True
        elif arg == "--lang":
            i += 1
            language = argv[i].lower()
        elif arg == "--jurisdiction":
            i += 1
            jurisdiction = argv[i].capitalize()
        else:
            print("unknown argument: %s" % arg)
            print(__doc__)
            return 2
        i += 1

    if language not in (EN, HI):
        print("error: --lang must be 'en' or 'hi', got %r" % language)
        return 2
    if jurisdiction not in (INDIA, INTERNATIONAL):
        print("error: --jurisdiction must be 'India' or 'International', got %r"
              % jurisdiction)
        return 2

    try:
        if interactive:
            run_interactive(language=language, jurisdiction=jurisdiction)
        else:
            run_scripted(language=language, jurisdiction=jurisdiction)
    except ValueError as error:  # defensive: classifier-side validation
        print("error: %s" % error)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
