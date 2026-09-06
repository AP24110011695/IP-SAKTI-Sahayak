"""Member 2 test suite (Phases 1-3) for the IP-SAKTI Sahayak formulation
classifier.

Coverage:
* Phase 1: one clear-cut worked example per category, Uncertain cases,
  incomplete input, input validation, result structure, determinism,
  golden food-vs-medicine scenario.
* Phase 2: jurisdiction-aware regime mapping (deterministic, classification
  invariant), bilingual labels/questions/prompts, one-round clarification
  behaviour, edge cases.
* Phase 3: canonical 10+ case suite, public-API end-to-end guided flow,
  ClassificationResult contract verification, demo module, full Hindi sweep.

Run with:  python -m unittest member2.test_classifier -v
"""

import unittest

from member2 import (
    AYURVEDA_AAHAR,
    CLASSICAL,
    COSMETIC,
    NEW_DRUG,
    PROPRIETARY,
    PHYTOPHARMACEUTICAL,
    UNCERTAIN,
    HIGH,
    MEDIUM,
    LOW,
    ALL_CATEGORIES,
    INDIA,
    INTERNATIONAL,
    ValidationError,
    apply_clarification,
    classify,
    get_questions,
    validate_classification_result,
)

# Clear-cut answer sets, one per named category.
CLASSICAL_ANSWERS = {
    "primary_purpose": "therapeutic",
    "text_source": "yes",
    "standardised_fraction": "no",
    "ingredients_known": "yes",
    "new_indication": "no",
}
PROPRIETARY_ANSWERS = {
    "primary_purpose": "therapeutic",
    "text_source": "no",
    "standardised_fraction": "no",
    "ingredients_known": "yes",
    "new_indication": "no",
}
PHYTOPHARMACEUTICAL_ANSWERS = {
    "primary_purpose": "therapeutic",
    "text_source": "no",
    "standardised_fraction": "yes",
}
NEW_DRUG_ANSWERS = {
    "primary_purpose": "therapeutic",
    "text_source": "no",
    "standardised_fraction": "no",
    "ingredients_known": "no",
}
AYURVEDA_AAHAR_ANSWERS = {
    "primary_purpose": "food_wellness",
    "food_exclusion": "none",
    "new_indication": "no",
}
COSMETIC_ANSWERS = {
    "primary_purpose": "external_cosmetic",
    "new_indication": "no",
}

CLEAR_CUT_CASES = [
    (CLASSICAL_ANSWERS, CLASSICAL),
    (PROPRIETARY_ANSWERS, PROPRIETARY),
    (PHYTOPHARMACEUTICAL_ANSWERS, PHYTOPHARMACEUTICAL),
    (NEW_DRUG_ANSWERS, NEW_DRUG),
    (AYURVEDA_AAHAR_ANSWERS, AYURVEDA_AAHAR),
    (COSMETIC_ANSWERS, COSMETIC),
]


class TestClearCutCategories(unittest.TestCase):
    """One clear-cut worked example per named category."""

    def test_classical_medicine(self):
        """Triphala churna: recipe and method unchanged from an authoritative text."""
        result = classify(CLASSICAL_ANSWERS)
        self.assertEqual(result["formulation_class"], CLASSICAL)
        self.assertEqual(result["confidence"], HIGH)
        self.assertEqual(result["confidence_score"], 0.95)
        self.assertFalse(result["needs_clarification"])
        self.assertIsNone(result["clarification_prompt"])
        self.assertIn("TKDL", result["tkdl_pointer"])
        self.assertTrue(
            any("Section 3(p)" in regime for regime in result["relevant_regimes"]),
            "Classical result must implicate the Section 3(p) regime",
        )

    def test_proprietary_medicine(self):
        """New syrup combining known Ayurvedic herbs, not from any classical text."""
        result = classify(PROPRIETARY_ANSWERS)
        self.assertEqual(result["formulation_class"], PROPRIETARY)
        self.assertEqual(result["confidence"], HIGH)
        self.assertFalse(result["needs_clarification"])
        self.assertTrue(
            any("proprietary" in regime.lower() for regime in result["relevant_regimes"])
        )

    def test_phytopharmaceutical(self):
        """Standardised Bacopa fraction with defined bacoside markers."""
        result = classify(PHYTOPHARMACEUTICAL_ANSWERS)
        self.assertEqual(result["formulation_class"], PHYTOPHARMACEUTICAL)
        self.assertEqual(result["confidence"], HIGH)
        self.assertFalse(result["needs_clarification"])

    def test_phytopharmaceutical_even_when_text_source_unsure(self):
        """A standardised fraction is a phytopharmaceutical regardless of text source."""
        result = classify({
            "primary_purpose": "therapeutic",
            "text_source": "unsure",
            "standardised_fraction": "yes",
        })
        self.assertEqual(result["formulation_class"], PHYTOPHARMACEUTICAL)

    def test_new_drug_novel_ingredient(self):
        """Formulation containing an ingredient not established in Ayurvedic use."""
        result = classify(NEW_DRUG_ANSWERS)
        self.assertEqual(result["formulation_class"], NEW_DRUG)
        self.assertEqual(result["confidence"], HIGH)
        self.assertFalse(result["needs_clarification"])

    def test_new_drug_new_indication(self):
        """Known ingredients, but a claim to treat an indication not established for them."""
        result = classify({
            "primary_purpose": "therapeutic",
            "text_source": "no",
            "standardised_fraction": "no",
            "ingredients_known": "yes",
            "new_indication": "yes",
        })
        self.assertEqual(result["formulation_class"], NEW_DRUG)
        self.assertEqual(result["confidence"], HIGH)

    def test_ayurveda_aahar(self):
        """Herbal jam per a Schedule A recipe, sold as food with wellness claims only."""
        result = classify(AYURVEDA_AAHAR_ANSWERS)
        self.assertEqual(result["formulation_class"], AYURVEDA_AAHAR)
        self.assertEqual(result["confidence"], HIGH)
        self.assertFalse(result["needs_clarification"])
        self.assertIsNone(result["tkdl_pointer"])
        self.assertTrue(
            any("FSSAI" in regime for regime in result["relevant_regimes"]),
            "Ayurveda-Aahar result must implicate the FSSAI regime",
        )

    def test_cosmetic(self):
        """Neem-turmeric face cream: external use for cleansing/appearance, no claims."""
        result = classify(COSMETIC_ANSWERS)
        self.assertEqual(result["formulation_class"], COSMETIC)
        self.assertEqual(result["confidence"], HIGH)
        self.assertFalse(result["needs_clarification"])
        self.assertIsNone(result["tkdl_pointer"])
        self.assertTrue(
            any("Cosmetic Rules" in regime for regime in result["relevant_regimes"])
        )


class TestUncertainCases(unittest.TestCase):
    """Genuinely ambiguous / contradictory cases must stay Uncertain."""

    def test_ambiguous_text_source_and_standardisation_unsure(self):
        result = classify({
            "primary_purpose": "therapeutic",
            "text_source": "unsure",
            "standardised_fraction": "unsure",
        })
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])
        self.assertEqual(result["confidence"], LOW)
        self.assertIn("text_source", result["clarification_question_ids"])
        self.assertIn("First Schedule", result["clarification_prompt"])

    def test_ambiguous_food_exclusion_unsure(self):
        """Herbal product sold as food; user unsure about bhasma/E-1/cure-claim status."""
        result = classify({
            "primary_purpose": "food_wellness",
            "food_exclusion": "unsure",
        })
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])
        self.assertEqual(result["confidence"], LOW)
        self.assertIn("bhasma", (result["clarification_prompt"] or "").lower())

    def test_contradictory_text_source_vs_standardised_fraction(self):
        result = classify({
            "primary_purpose": "therapeutic",
            "text_source": "yes",
            "standardised_fraction": "yes",
        })
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])
        self.assertEqual(result["confidence"], LOW)
        self.assertIn("conflict", (result["clarification_prompt"] or "").lower())

    def test_other_purpose_is_uncertain(self):
        result = classify({"primary_purpose": "other"})
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])

    def test_unsure_purpose_is_uncertain(self):
        result = classify({"primary_purpose": "unsure"})
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])


class TestIncompleteInput(unittest.TestCase):
    """Incomplete input must be handled safely: no crash, no wild guess."""

    def test_empty_answers(self):
        result = classify({})
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])
        self.assertEqual(result["confidence"], LOW)
        self.assertIn("primary_purpose", result["clarification_question_ids"])
        self.assertIn("primary intended use", result["clarification_prompt"])

    def test_none_answers(self):
        result = classify(None)
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])

    def test_partial_therapeutic_only(self):
        result = classify({"primary_purpose": "therapeutic"})
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])
        # The clarification prompt must ask the concrete blocking question.
        self.assertIn("First Schedule", result["clarification_prompt"])

    def test_incomplete_result_is_still_valid(self):
        for answers in ({}, None, {"primary_purpose": "therapeutic"},
                        {"primary_purpose": "food_wellness"}):
            self.assertEqual(validate_classification_result(classify(answers)), [])


class TestInputValidation(unittest.TestCase):
    """Structurally invalid payloads raise ValidationError, not crashes."""

    def test_non_dict_raises(self):
        for bad in ("chyavanprash", 42, ["primary_purpose"], object()):
            with self.assertRaises(ValidationError):
                classify(bad)

    def test_unknown_question_id_raises(self):
        with self.assertRaises(ValidationError):
            classify({"purpose": "therapeutic"})

    def test_invalid_value_raises(self):
        with self.assertRaises(ValidationError):
            classify({"primary_purpose": "magic"})

    def test_non_string_value_raises(self):
        with self.assertRaises(ValidationError):
            classify({"text_source": 1})
        with self.assertRaises(ValidationError):
            classify({"text_source": ["yes"]})

    def test_case_and_whitespace_are_normalised(self):
        sloppy = {
            "primary_purpose": "  Therapeutic ",
            "text_source": "YES",
            "standardised_fraction": "No",
            "ingredients_known": "Yes",
            "new_indication": "NO",
        }
        self.assertEqual(classify(sloppy), classify(CLASSICAL_ANSWERS))

    def test_question_definitions_are_wellformed(self):
        questions = get_questions()
        self.assertEqual(len(questions), 6)
        for question in questions:
            self.assertIn("id", question)
            self.assertIn("text", question)
            self.assertIn("options", question)
            self.assertTrue(question["options"])


class TestResultStructure(unittest.TestCase):
    """Every result must satisfy the ClassificationResult contract."""

    def test_all_clear_cut_results_are_valid(self):
        for answers, _ in CLEAR_CUT_CASES:
            self.assertEqual(validate_classification_result(classify(answers)), [])

    def test_all_uncertain_results_are_valid(self):
        uncertain_cases = [
            {},
            {"primary_purpose": "therapeutic"},
            {"primary_purpose": "therapeutic", "text_source": "unsure",
             "standardised_fraction": "unsure"},
            {"primary_purpose": "therapeutic", "text_source": "yes",
             "standardised_fraction": "yes"},
        ]
        for answers in uncertain_cases:
            self.assertEqual(validate_classification_result(classify(answers)), [])

    def test_required_fields_present(self):
        result = classify(CLASSICAL_ANSWERS)
        for field in ("formulation_class", "description", "relevant_regimes",
                      "tkdl_pointer", "confidence", "needs_clarification",
                      "clarification_prompt"):
            self.assertIn(field, result)

    def test_description_and_reasoning_for_every_category(self):
        for answers, _ in CLEAR_CUT_CASES:
            result = classify(answers)
            self.assertTrue(result["description"].strip())
            self.assertTrue(result["reasoning"])
            self.assertTrue(
                all(isinstance(entry, str) for entry in result["reasoning"])
            )


class TestDeterminism(unittest.TestCase):
    """The classifier must be fully deterministic."""

    def test_repeated_runs_identical(self):
        all_cases = [answers for answers, _ in CLEAR_CUT_CASES] + [
            {},
            {"primary_purpose": "therapeutic"},
            {"primary_purpose": "food_wellness", "food_exclusion": "unsure"},
            {"primary_purpose": "therapeutic", "text_source": "yes",
             "standardised_fraction": "yes"},
        ]
        for answers in all_cases:
            runs = [classify(answers) for _ in range(5)]
            for run in runs[1:]:
                self.assertEqual(run, runs[0])


class TestConfidenceBehaviour(unittest.TestCase):
    """Confidence must reflect how much discriminating evidence exists."""

    def test_lazy_food_answer_is_medium(self):
        """Aahar without answering the cure-claim cross-check -> MEDIUM."""
        result = classify({
            "primary_purpose": "food_wellness",
            "food_exclusion": "none",
        })
        self.assertEqual(result["formulation_class"], AYURVEDA_AAHAR)
        self.assertEqual(result["confidence"], MEDIUM)
        self.assertEqual(result["confidence_score"], 0.70)
        self.assertTrue(
            any("confidence reduced" in entry for entry in result["reasoning"]),
            "reasoning must explain why confidence was reduced",
        )

    def test_proprietary_with_unsure_standardisation_is_medium(self):
        result = classify({
            "primary_purpose": "therapeutic",
            "text_source": "no",
            "standardised_fraction": "unsure",
            "ingredients_known": "yes",
            "new_indication": "no",
        })
        self.assertEqual(result["formulation_class"], PROPRIETARY)
        self.assertEqual(result["confidence"], MEDIUM)

    def test_uncertain_is_always_low(self):
        result = classify({"primary_purpose": "therapeutic"})
        self.assertEqual(result["confidence"], LOW)
        self.assertEqual(result["confidence_score"], 0.45)

    def test_high_only_for_clear_cut(self):
        for answers, _ in CLEAR_CUT_CASES:
            result = classify(answers)
            self.assertEqual(result["confidence"], HIGH, answers)


class TestGoldenScenario(unittest.TestCase):
    """MEMBER_2.md Section 5: a herbal product must land in a DIFFERENT
    category depending on the answers - food vs classical medicine."""

    def test_herbal_product_food_vs_medicine(self):
        food_result = classify(AYURVEDA_AAHAR_ANSWERS)
        medicine_result = classify(CLASSICAL_ANSWERS)
        self.assertEqual(food_result["formulation_class"], AYURVEDA_AAHAR)
        self.assertEqual(medicine_result["formulation_class"], CLASSICAL)
        self.assertNotEqual(food_result["formulation_class"],
                            medicine_result["formulation_class"])
        # The two regimes must be visibly different tracks.
        self.assertTrue(any("FSSAI" in r for r in food_result["relevant_regimes"]))
        self.assertTrue(any("Drugs and Cosmetics Act" in r
                            for r in medicine_result["relevant_regimes"]))


class TestEdgeCases(unittest.TestCase):
    """Claim- and substance-driven track switches and borderline notes."""

    def test_food_with_cure_claim_moves_to_drug_track(self):
        """Cure claims on a food-positioned product fall under the D&C Act."""
        result = classify({
            "primary_purpose": "food_wellness",
            "food_exclusion": "none",
            "new_indication": "yes",
            "text_source": "no",
            "standardised_fraction": "no",
            "ingredients_known": "yes",
        })
        self.assertEqual(result["formulation_class"], NEW_DRUG)

    def test_food_with_bhasma_excluded_from_aahar(self):
        """Bhasma-containing product sold as 'food' is a D&C Act drug; from a
        classical text it is Classical."""
        result = classify({
            "primary_purpose": "food_wellness",
            "food_exclusion": "bhasma_or_e1",
            "text_source": "yes",
            "new_indication": "no",
        })
        self.assertEqual(result["formulation_class"], CLASSICAL)

    def test_cosmetic_with_therapeutic_claim_moves_to_drug_track(self):
        result = classify({
            "primary_purpose": "external_cosmetic",
            "new_indication": "yes",
            "text_source": "no",
            "standardised_fraction": "no",
            "ingredients_known": "yes",
        })
        self.assertEqual(result["formulation_class"], NEW_DRUG)

    def test_classical_with_new_indication_claim_capped_at_medium(self):
        result = classify({
            "primary_purpose": "therapeutic",
            "text_source": "yes",
            "standardised_fraction": "no",
            "ingredients_known": "yes",
            "new_indication": "yes",
        })
        self.assertEqual(result["formulation_class"], CLASSICAL)
        self.assertEqual(result["confidence"], MEDIUM)
        self.assertFalse(result["needs_clarification"])
        self.assertTrue(any("new therapeutic claim" in entry
                            for entry in result["reasoning"]))

    def test_new_indication_missing_with_known_ingredients_is_uncertain(self):
        result = classify({
            "primary_purpose": "therapeutic",
            "text_source": "no",
            "standardised_fraction": "no",
            "ingredients_known": "yes",
        })
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertIn("new_indication", result["clarification_question_ids"])
        self.assertIn("treatment/cure claim", result["clarification_prompt"])


def _has_devanagari(text):
    """True if the text contains Devanagari script (U+0900-U+097F)."""
    return any("\u0900" <= ch <= "\u097F" for ch in text)


class TestJurisdictionContext(unittest.TestCase):
    """Phase 2: India vs International context. Classification itself must
    NEVER change with jurisdiction -- only the attached regime/context data."""

    def test_default_jurisdiction_is_india(self):
        result = classify(CLASSICAL_ANSWERS)
        self.assertEqual(result["jurisdiction"], INDIA)

    def test_invalid_jurisdiction_raises(self):
        with self.assertRaises(ValidationError):
            classify(CLASSICAL_ANSWERS, jurisdiction="Europe")
        with self.assertRaises(ValidationError):
            classify(CLASSICAL_ANSWERS, jurisdiction=None)

    def test_invalid_language_raises(self):
        with self.assertRaises(ValidationError):
            classify(CLASSICAL_ANSWERS, language="fr")
        with self.assertRaises(ValidationError):
            classify(CLASSICAL_ANSWERS, language=None)

    def test_jurisdiction_does_not_change_classification(self):
        cases = [answers for answers, _ in CLEAR_CUT_CASES] + [
            {"primary_purpose": "therapeutic"},
            {"primary_purpose": "therapeutic", "text_source": "yes",
             "standardised_fraction": "yes"},
            {"primary_purpose": "food_wellness", "food_exclusion": "none"},
        ]
        for answers in cases:
            india = classify(answers, jurisdiction=INDIA)
            intl = classify(answers, jurisdiction=INTERNATIONAL)
            self.assertEqual(india["formulation_class"], intl["formulation_class"], answers)
            self.assertEqual(india["confidence"], intl["confidence"], answers)
            self.assertEqual(india["confidence_score"], intl["confidence_score"], answers)
            self.assertEqual(india["reasoning"], intl["reasoning"], answers)
            self.assertEqual(india["needs_clarification"], intl["needs_clarification"], answers)

    def test_india_regimes_for_classical(self):
        regimes = classify(CLASSICAL_ANSWERS, jurisdiction=INDIA)["relevant_regimes"]
        joined = " | ".join(regimes)
        for expected in ("Section 3(p)", "TKDL", "Drugs and Cosmetics Act",
                         "Biological Diversity Act", "Trade Marks Act"):
            self.assertIn(expected, joined)

    def test_international_regimes_for_classical(self):
        regimes = classify(CLASSICAL_ANSWERS, jurisdiction=INTERNATIONAL)["relevant_regimes"]
        joined = " | ".join(regimes)
        for expected in ("TRIPS", "GRATK", "Nagoya", "TKDL"):
            self.assertIn(expected, joined)

    def test_international_regimes_for_new_drug_include_pct(self):
        regimes = classify(NEW_DRUG_ANSWERS, jurisdiction=INTERNATIONAL)["relevant_regimes"]
        joined = " | ".join(regimes)
        self.assertIn("PCT", joined)
        self.assertIn("TRIPS", joined)

    def test_international_regimes_for_aahar_include_food_export(self):
        regimes = classify(AYURVEDA_AAHAR_ANSWERS, jurisdiction=INTERNATIONAL)["relevant_regimes"]
        joined = " | ".join(regimes)
        for expected in ("Novel Food", "DSHEA", "Madrid"):
            self.assertIn(expected, joined)

    def test_uncertain_has_empty_regimes_in_both_jurisdictions(self):
        for jurisdiction in (INDIA, INTERNATIONAL):
            result = classify({}, jurisdiction=jurisdiction)
            self.assertEqual(result["relevant_regimes"], [])
            self.assertIsNone(result["tkdl_pointer"])

    def test_tkdl_pointer_present_for_classical_in_both_jurisdictions(self):
        for jurisdiction in (INDIA, INTERNATIONAL):
            result = classify(CLASSICAL_ANSWERS, jurisdiction=jurisdiction)
            self.assertIn("TKDL", result["tkdl_pointer"])


class TestRegimeMappingDeterminism(unittest.TestCase):
    """Phase 2 test requirement: regime mappings must be the same every time
    for the same input."""

    def test_regimes_identical_across_runs(self):
        for answers, _ in CLEAR_CUT_CASES:
            for jurisdiction in (INDIA, INTERNATIONAL):
                runs = [classify(answers, jurisdiction=jurisdiction)["relevant_regimes"]
                        for _ in range(5)]
                for run in runs[1:]:
                    self.assertEqual(run, runs[0], (answers, jurisdiction))

    def test_suggested_questions_identical_across_runs(self):
        for answers, _ in CLEAR_CUT_CASES:
            runs = [classify(answers)["suggested_questions"] for _ in range(5)]
            for run in runs[1:]:
                self.assertEqual(run, runs[0])

    def test_regime_lists_are_static_tables(self):
        """Mappings must not be computed at runtime from mutable state."""
        india = classify(CLASSICAL_ANSWERS, jurisdiction=INDIA)["relevant_regimes"]
        # A fresh call after mutating the returned list must give the same mapping.
        india.append("tampered entry")
        fresh = classify(CLASSICAL_ANSWERS, jurisdiction=INDIA)["relevant_regimes"]
        self.assertNotIn("tampered entry", fresh)
        self.assertEqual(len(fresh), len(india) - 1)


class TestSuggestedQuestions(unittest.TestCase):
    """Phase 2: category-specific suggested follow-up questions."""

    def test_every_named_category_has_suggestions(self):
        for answers, category in CLEAR_CUT_CASES:
            suggestions = classify(answers)["suggested_questions"]
            self.assertTrue(suggestions, category)

    def test_uncertain_has_no_suggestions(self):
        self.assertEqual(classify({})["suggested_questions"], [])

    def test_suggestion_structure_bilingual(self):
        for answers, _ in CLEAR_CUT_CASES:
            for sq in classify(answers)["suggested_questions"]:
                self.assertTrue(sq["id"].startswith("sq_"))
                self.assertTrue(sq["en"].strip())
                self.assertTrue(_has_devanagari(sq["hi"]))

    def test_suggestion_ids_unique(self):
        for answers, _ in CLEAR_CUT_CASES:
            ids = [sq["id"] for sq in classify(answers)["suggested_questions"]]
            self.assertEqual(len(ids), len(set(ids)))


class TestClarificationRound(unittest.TestCase):
    """Phase 2: one round of clarification for borderline/incomplete answers,
    triggered only when genuinely needed."""

    def test_clear_cut_never_triggers_clarification(self):
        for answers, _ in CLEAR_CUT_CASES:
            result = classify(answers)
            self.assertFalse(result["needs_clarification"], answers)
            self.assertIsNone(result["clarification_prompt"], answers)
            self.assertEqual(result["clarification_question_ids"], [], answers)

    def test_partial_but_sufficient_does_not_trigger_clarification(self):
        """Phytopharmaceutical needs only purpose/text/standardisation; the
        unconsulted questions must not trigger a clarification round."""
        result = classify(PHYTOPHARMACEUTICAL_ANSWERS)
        self.assertFalse(result["needs_clarification"])
        self.assertIsNone(result["clarification_prompt"])

    def test_borderline_food_triggers_targeted_clarification(self):
        """Lazy Aahar answers classify as Aahar, but the missing cure-claim
        cross-check could flip the category -- exactly one targeted question."""
        result = classify({"primary_purpose": "food_wellness", "food_exclusion": "none"})
        self.assertEqual(result["formulation_class"], AYURVEDA_AAHAR)
        self.assertTrue(result["needs_clarification"])
        self.assertEqual(result["clarification_question_ids"], ["new_indication"])
        self.assertIn("confirm", result["clarification_prompt"].lower())

    def test_borderline_proprietary_asks_about_standardisation(self):
        result = classify({
            "primary_purpose": "therapeutic",
            "text_source": "no",
            "standardised_fraction": "unsure",
            "ingredients_known": "yes",
            "new_indication": "no",
        })
        self.assertEqual(result["formulation_class"], PROPRIETARY)
        self.assertTrue(result["needs_clarification"])
        self.assertEqual(result["clarification_question_ids"], ["standardised_fraction"])

    def test_clarification_round_narrows_borderline_food(self):
        original = {"primary_purpose": "food_wellness", "food_exclusion": "none"}
        confirmed = apply_clarification(original, {"new_indication": "no"})
        self.assertEqual(confirmed["formulation_class"], AYURVEDA_AAHAR)
        self.assertEqual(confirmed["confidence"], HIGH)
        self.assertFalse(confirmed["needs_clarification"])

    def test_clarification_round_narrows_incomplete_uncertain(self):
        original = {"primary_purpose": "therapeutic"}
        first = classify(original)
        self.assertEqual(first["formulation_class"], UNCERTAIN)
        self.assertEqual(first["clarification_question_ids"], ["text_source"])
        confirmed = apply_clarification(original, {"text_source": "yes"})
        self.assertEqual(confirmed["formulation_class"], CLASSICAL)
        self.assertFalse(confirmed["needs_clarification"])

    def test_clarification_round_resolves_contradiction(self):
        original = {
            "primary_purpose": "therapeutic",
            "text_source": "yes",
            "standardised_fraction": "yes",
        }
        first = classify(original)
        self.assertEqual(first["formulation_class"], UNCERTAIN)
        self.assertIn("conflict", first["clarification_prompt"].lower())
        resolved = apply_clarification(original, {"standardised_fraction": "no"})
        self.assertEqual(resolved["formulation_class"], CLASSICAL)
        self.assertFalse(resolved["needs_clarification"])

    def test_unclear_clarification_answer_stays_safe(self):
        """Answering the clarification with 'unsure' must NOT force a category."""
        result = apply_clarification(
            {"primary_purpose": "therapeutic"}, {"text_source": "unsure"}
        )
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])


class TestBilingual(unittest.TestCase):
    """Phase 2: English/Hindi labels, questions and prompts. Machine values
    must stay identical across languages."""

    def test_category_labels_bilingual_for_every_category(self):
        from member2 import CATEGORY_LABELS
        for category in ALL_CATEGORIES:
            labels = CATEGORY_LABELS[category]
            self.assertEqual(labels["en"], category)
            self.assertTrue(_has_devanagari(labels["hi"]), category)

    def test_questions_bilingual(self):
        for question in get_questions():
            self.assertTrue(_has_devanagari(question["text_hi"]), question["id"])
            self.assertEqual(set(question["options"]), set(question["options_hi"]),
                             question["id"])
            for option_text in question["options_hi"].values():
                self.assertTrue(_has_devanagari(option_text), question["id"])

    def test_hindi_result_localises_text_keeps_machine_values(self):
        en = classify(CLASSICAL_ANSWERS, language="en")
        hi = classify(CLASSICAL_ANSWERS, language="hi")
        self.assertEqual(hi["formulation_class"], CLASSICAL)
        self.assertEqual(hi["confidence"], en["confidence"])
        self.assertEqual(hi["relevant_regimes"], en["relevant_regimes"])
        self.assertTrue(_has_devanagari(hi["description"]))
        self.assertTrue(_has_devanagari(hi["category_labels"]["hi"]))
        self.assertEqual(hi["category_labels"]["en"], "Classical")
        for sq in hi["suggested_questions"]:
            self.assertTrue(_has_devanagari(sq["hi"]))

    def test_hindi_clarification_prompts(self):
        empty = classify({}, language="hi")
        self.assertTrue(_has_devanagari(empty["clarification_prompt"]))
        self.assertEqual(empty["clarification_question_ids"], ["primary_purpose"])
        borderline = classify(
            {"primary_purpose": "food_wellness", "food_exclusion": "none"},
            language="hi",
        )
        self.assertTrue(_has_devanagari(borderline["clarification_prompt"]))
        contradiction = classify(
            {"primary_purpose": "therapeutic",
             "text_source": "yes", "standardised_fraction": "yes"},
            language="hi",
        )
        self.assertTrue(_has_devanagari(contradiction["clarification_prompt"]))

    def test_hindi_uncertain_description(self):
        hi = classify({}, language="hi")
        self.assertEqual(hi["formulation_class"], UNCERTAIN)
        self.assertTrue(_has_devanagari(hi["description"]))


class TestStringTablesComplete(unittest.TestCase):
    """Guard against future questions/categories missing bilingual strings."""

    def test_every_question_has_a_blocking_reason(self):
        from member2.classifier import _ALLOWED_VALUES
        from member2.strings import BLOCKING_REASONS
        for question_id in _ALLOWED_VALUES:
            for language in ("en", "hi"):
                self.assertTrue(BLOCKING_REASONS[question_id][language].strip(),
                                (question_id, language))

    def test_every_category_has_bilingual_description(self):
        from member2.strings import DESCRIPTIONS
        for category in ALL_CATEGORIES:
            for language in ("en", "hi"):
                self.assertTrue(DESCRIPTIONS[category][language].strip(),
                                (category, language))


class TestPhase3CaseSuite(unittest.TestCase):
    """Phase 3: the canonical 10+ case suite (mirrors demo.CASE_SUITE)."""

    def test_canonical_suite_classifies_correctly(self):
        from member2.demo import CASE_SUITE
        self.assertGreaterEqual(len(CASE_SUITE), 10)
        for label, expected_class, answers in CASE_SUITE:
            result = classify(answers)
            self.assertEqual(
                result["formulation_class"], expected_class,
                "case %r expected %s, got %s"
                % (label, expected_class, result["formulation_class"]),
            )
            self.assertEqual(validate_classification_result(result), [], label)

    def test_canonical_suite_confidences(self):
        from member2.demo import CASE_SUITE
        for label, expected_class, answers in CASE_SUITE:
            result = classify(answers)
            if expected_class == UNCERTAIN:
                self.assertEqual(result["confidence"], LOW, label)
                self.assertTrue(result["needs_clarification"], label)
            elif label.startswith("edge: classical recipe with a new"):
                self.assertEqual(result["confidence"], MEDIUM, label)
            elif label.startswith("edge: bhasma"):
                self.assertEqual(result["confidence"], HIGH, label)
            else:
                self.assertEqual(result["confidence"], HIGH, label)

    def test_suite_covers_all_seven_categories(self):
        from member2.demo import CASE_SUITE
        covered = {expected for _, expected, _ in CASE_SUITE}
        self.assertEqual(covered, set(ALL_CATEGORIES))


class TestEndToEndFlow(unittest.TestCase):
    """Phase 3: the full guided flow — questions -> answers -> classification
    -> regime mapping -> clarification where required -> final result — driven
    ONLY through the public API (clarification_question_ids), exactly as M1
    would converse. Each question is asked at most once."""

    def drive_flow(self, bank, jurisdiction=INDIA, language="en"):
        answers = {}
        asked = []
        result = classify(answers, jurisdiction=jurisdiction, language=language)
        for _ in range(len(get_questions()) + 1):
            if not result["needs_clarification"]:
                break
            pending = [q for q in result["clarification_question_ids"]
                       if q not in asked]
            if not pending:
                break
            question_id = pending[0]
            asked.append(question_id)
            value = bank.get(question_id)
            if value is not None:
                answers[question_id] = value
            result = classify(answers, jurisdiction=jurisdiction,
                              language=language)
        return result, asked

    def test_food_path(self):
        result, asked = self.drive_flow({
            "primary_purpose": "food_wellness",
            "food_exclusion": "none",
            "new_indication": "no",
        })
        self.assertEqual(asked, ["primary_purpose", "food_exclusion",
                                 "new_indication"])
        self.assertEqual(result["formulation_class"], AYURVEDA_AAHAR)
        self.assertEqual(result["confidence"], HIGH)
        self.assertFalse(result["needs_clarification"])
        self.assertTrue(any("FSSAI" in r for r in result["relevant_regimes"]))

    def test_drug_path_to_proprietary(self):
        result, asked = self.drive_flow({
            "primary_purpose": "therapeutic",
            "text_source": "no",
            "ingredients_known": "yes",
            "new_indication": "no",
            "standardised_fraction": "no",
        })
        self.assertEqual(asked, ["primary_purpose", "text_source",
                                 "ingredients_known", "new_indication",
                                 "standardised_fraction"])
        self.assertEqual(result["formulation_class"], PROPRIETARY)
        self.assertEqual(result["confidence"], HIGH)
        self.assertFalse(result["needs_clarification"])

    def test_drug_path_without_standardisation_answer_is_borderline(self):
        """Leaving standardised_fraction unanswered leaves a real possibility
        (a standardised fraction would be a Phytopharmaceutical), so the flow
        asks about it before settling at MEDIUM confidence."""
        result, asked = self.drive_flow({
            "primary_purpose": "therapeutic",
            "text_source": "no",
            "ingredients_known": "yes",
            "new_indication": "no",
        })
        self.assertEqual(asked, ["primary_purpose", "text_source",
                                 "ingredients_known", "new_indication",
                                 "standardised_fraction"])
        self.assertEqual(result["formulation_class"], PROPRIETARY)
        self.assertEqual(result["confidence"], MEDIUM)
        self.assertTrue(result["needs_clarification"])

    def test_cosmetic_path(self):
        result, asked = self.drive_flow({
            "primary_purpose": "external_cosmetic",
            "new_indication": "no",
        })
        self.assertEqual(asked, ["primary_purpose", "new_indication"])
        self.assertEqual(result["formulation_class"], COSMETIC)
        self.assertFalse(result["needs_clarification"])

    def test_bhasma_food_path_to_classical(self):
        result, asked = self.drive_flow({
            "primary_purpose": "food_wellness",
            "food_exclusion": "bhasma_or_e1",
            "text_source": "yes",
        })
        self.assertEqual(asked, ["primary_purpose", "food_exclusion",
                                 "text_source"])
        self.assertEqual(result["formulation_class"], CLASSICAL)
        self.assertFalse(result["needs_clarification"])

    def test_skipped_question_stays_safe(self):
        result, asked = self.drive_flow({
            "primary_purpose": "therapeutic",
            "text_source": None,  # user skipped; never answered
        })
        self.assertEqual(asked, ["primary_purpose", "text_source"])
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        self.assertTrue(result["needs_clarification"])
        self.assertEqual(validate_classification_result(result), [])

    def test_no_question_asked_twice(self):
        for bank in (
            {"primary_purpose": "therapeutic", "text_source": "no",
             "ingredients_known": "yes", "new_indication": "no"},
            {"primary_purpose": "food_wellness", "food_exclusion": "unsure"},
            {"primary_purpose": "external_cosmetic", "new_indication": "yes",
             "text_source": "yes"},
        ):
            _, asked = self.drive_flow(bank)
            self.assertEqual(len(asked), len(set(asked)), bank)
            self.assertTrue(set(asked) <= {q["id"] for q in get_questions()})


class TestResultContractPhase3(unittest.TestCase):
    """Phase 3: the actual output must match the Plan.md Section 7
    ClassificationResult contract; additive extras stay compatible."""

    REQUIRED = ("formulation_class", "description", "relevant_regimes",
                "tkdl_pointer", "confidence", "needs_clarification",
                "clarification_prompt")

    def test_contract_fields_on_every_category(self):
        from member2.demo import CASE_SUITE
        for label, _, answers in CASE_SUITE:
            result = classify(answers)
            for field in self.REQUIRED:
                self.assertIn(field, result, label)
            self.assertEqual(validate_classification_result(result), [], label)

    def test_contract_fields_types(self):
        for answers, _ in CLEAR_CUT_CASES:
            result = classify(answers)
            self.assertIsInstance(result["formulation_class"], str)
            self.assertIsInstance(result["description"], str)
            self.assertIsInstance(result["relevant_regimes"], list)
            self.assertIsInstance(result["confidence"], str)
            self.assertIsInstance(result["needs_clarification"], bool)
            self.assertTrue(result["clarification_prompt"] is None
                            or isinstance(result["clarification_prompt"], str))
            self.assertTrue(result["tkdl_pointer"] is None
                            or isinstance(result["tkdl_pointer"], str))

    def test_additive_fields_are_compatible(self):
        """A consumer reading only the 7 contract fields loses nothing
        required; the extras ride along harmlessly."""
        result = classify(CLASSICAL_ANSWERS)
        extras = set(result) - set(self.REQUIRED)
        self.assertTrue({"confidence_score", "clarification_question_ids",
                         "jurisdiction", "language", "category_labels",
                         "suggested_questions", "reasoning"} <= extras)
        # The contract-only projection is self-consistent.
        projection = {field: result[field] for field in self.REQUIRED}
        self.assertEqual(validate_classification_result(projection), [])

    def test_validator_rejects_broken_results(self):
        from member2 import validate_classification_result
        self.assertTrue(validate_classification_result("not a dict"))
        self.assertTrue(validate_classification_result({"formulation_class": "Junk"}))
        broken = classify(CLASSICAL_ANSWERS)
        broken["confidence"] = "CERTAIN"
        self.assertTrue(validate_classification_result(broken))


class TestHindiVerificationPhase3(unittest.TestCase):
    """Phase 3: full Hindi verification sweep — labels, questions/options,
    all three prompt types; machine values identical across languages."""

    SWEEP_CASES = CLEAR_CUT_CASES + [
        ({}, "empty"),
        ({"primary_purpose": "food_wellness", "food_exclusion": "none"},
         "borderline"),
        ({"primary_purpose": "therapeutic", "text_source": "yes",
          "standardised_fraction": "yes"}, "contradiction"),
    ]

    def test_machine_values_identical_across_languages(self):
        for answers, label in self.SWEEP_CASES:
            en = classify(answers, language="en")
            hi = classify(answers, language="hi")
            for field in ("formulation_class", "confidence", "confidence_score",
                          "relevant_regimes", "needs_clarification",
                          "clarification_question_ids"):
                self.assertEqual(en[field], hi[field], (label, field))
            self.assertEqual([sq["id"] for sq in en["suggested_questions"]],
                             [sq["id"] for sq in hi["suggested_questions"]],
                             label)

    def test_hindi_text_fields_for_every_sweep_case(self):
        for answers, label in self.SWEEP_CASES:
            hi = classify(answers, language="hi")
            self.assertTrue(_has_devanagari(hi["description"]), label)
            self.assertTrue(_has_devanagari(hi["category_labels"]["hi"]), label)
            if hi["clarification_prompt"] is not None:
                self.assertTrue(_has_devanagari(hi["clarification_prompt"]),
                                label)
            for sq in hi["suggested_questions"]:
                self.assertTrue(_has_devanagari(sq["hi"]), label)

    def test_regime_names_unchanged_by_language(self):
        """Documented approach: regime names are English proper nouns in both
        languages; no invented Hindi legal names."""
        for answers, _ in CLEAR_CUT_CASES:
            en = classify(answers, language="en")
            hi = classify(answers, language="hi")
            self.assertEqual(en["relevant_regimes"], hi["relevant_regimes"])
            self.assertFalse(
                any(_has_devanagari(r) for r in hi["relevant_regimes"]),
                "regime names must stay English",
            )


class TestDemoModule(unittest.TestCase):
    """Phase 3: the standalone demo must run against the real classifier."""

    def test_scripted_results_are_valid_and_discriminating(self):
        from member2.demo import collect_scripted_results
        results = collect_scripted_results()
        self.assertGreaterEqual(len(results), 12)
        for label, result in results:
            self.assertEqual(validate_classification_result(result), [], label)

    def test_golden_scenario_discriminates_three_categories(self):
        from member2.demo import GOLDEN_SCENARIOS
        seen = []
        for label, answers, expected in GOLDEN_SCENARIOS:
            result = classify(answers)
            self.assertEqual(result["formulation_class"], expected, label)
            seen.append(result["formulation_class"])
        self.assertEqual(len(set(seen)), len(GOLDEN_SCENARIOS),
                         "golden scenario must not collapse to one default category")

    def test_interactive_food_path(self):
        from member2.demo import run_interactive
        inputs = iter(["2", "1", "2"])  # purpose=food, exclusion=none, new_ind=no
        captured = []

        def fake_input(prompt):
            captured.append(prompt)
            return next(inputs)

        result = run_interactive(input_fn=fake_input,
                                 output_fn=lambda text: captured.append(text))
        self.assertEqual(result["formulation_class"], AYURVEDA_AAHAR)
        self.assertFalse(result["needs_clarification"])
        rendered = "\n".join(captured)
        self.assertIn("Ayurveda-Aahar", rendered)

    def test_interactive_skip_and_quit_paths(self):
        from member2.demo import run_interactive
        skip_inputs = iter(["2", "s"])
        result = run_interactive(input_fn=lambda prompt: next(skip_inputs),
                                 output_fn=lambda text: None)
        self.assertEqual(result["formulation_class"], UNCERTAIN)
        quit_inputs = iter(["q"])
        result = run_interactive(input_fn=lambda prompt: next(quit_inputs),
                                 output_fn=lambda text: None)
        self.assertEqual(result["formulation_class"], UNCERTAIN)

    def test_invalid_language_flag_returns_error_code(self):
        from member2.demo import main
        self.assertEqual(main(["--lang", "fr"]), 2)

    def test_scripted_demo_runs_in_hindi(self):
        from member2.demo import run_scripted
        captured = []
        golden = run_scripted(language="hi", output_fn=captured.append)
        self.assertEqual(len(golden), 3)
        rendered = "\n".join(captured)
        self.assertTrue(_has_devanagari(rendered))


if __name__ == "__main__":
    unittest.main()
