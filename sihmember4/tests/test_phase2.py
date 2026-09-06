"""Member 4 — Phase 2 test suite.

Run together with Phase 1 tests:

    python -m unittest discover -s m4_abs/tests -t m4_abs -v

Covers: ABS relevance determination, out-of-scope protection, grounded
golden scenario, TKDL pointer + fabrication-safety, citation integrity,
deterministic confidence, safe abstention, Hindi support, the exact result
contract, and the hosted-LLM path (prompt constraints + failure mapping;
no live API call is made or faked anywhere in this suite).
"""

import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import corpus  # noqa: E402
import guidance  # noqa: E402
import hindi  # noqa: E402
import llm_client  # noqa: E402
import retrieval  # noqa: E402

GOLDEN_EN = (
    "I want to commercialise a formulation using a plant collected in India "
    "- what approvals do I need?"
)
GOLDEN_HI = (
    "मैं भारत में एकत्रित पौधों से बने फॉर्मूलेशन का व्यावसायिक उपयोग करना "
    "चाहता हूँ - मुझे क्या अनुमोदन चाहिए?"
)
TRADEMARK_EN = "How do I register a trademark for my Ayurvedic brand?"
TRADEMARK_HI = "मेरे आयुर्वेदिक ब्रांड के लिए ट्रेडमार्क कैसे रजिस्टर करें?"
OUT_OF_CORPUS_EN = (
    "How do I export herbal medicinal products to the EU - what EU "
    "registration do I need?"
)
OUT_OF_CORPUS_FEE = "How much is the NBA processing fee for a Form 2 application?"
TK_PATENT_QUERY = "Can I patent a classical Ayurvedic formulation from an authoritative text?"
INTERNATIONAL_ONLY = "How do I register a trademark internationally under the Madrid Protocol?"
NAGOYA_QUERY = "Nagoya Protocol prior informed consent for genetic resources"


def ok(result):
    return result["status"] == "ok"


class RelevanceTests(unittest.TestCase):
    def test_golden_english_is_abs_relevant(self):
        relevance = guidance.classify_query(GOLDEN_EN)
        self.assertEqual(relevance.domain, guidance.DOMAIN_ABS)
        self.assertTrue(relevance.signals)
        self.assertEqual(relevance.language, "en")

    def test_golden_hindi_is_abs_relevant(self):
        relevance = guidance.classify_query(GOLDEN_HI)
        self.assertEqual(relevance.domain, guidance.DOMAIN_ABS)
        self.assertEqual(relevance.language, "hi")

    def test_trademark_english_is_other_ip(self):
        relevance = guidance.classify_query(TRADEMARK_EN)
        self.assertEqual(relevance.domain, guidance.DOMAIN_OTHER_IP)
        self.assertIn("trademark", " ".join(relevance.signals).lower())

    def test_trademark_hindi_is_other_ip(self):
        relevance = guidance.classify_query(TRADEMARK_HI)
        self.assertEqual(relevance.domain, guidance.DOMAIN_OTHER_IP)
        self.assertEqual(relevance.language, "hi")

    def test_international_only_trademark_is_other_ip(self):
        self.assertEqual(guidance.classify_query(INTERNATIONAL_ONLY).domain,
                         guidance.DOMAIN_OTHER_IP)

    def test_pure_patent_application_is_other_ip(self):
        self.assertEqual(
            guidance.classify_query("How do I file a patent application in India?").domain,
            guidance.DOMAIN_OTHER_IP,
        )

    def test_tk_patentability_query_is_tk(self):
        relevance = guidance.classify_query(TK_PATENT_QUERY)
        self.assertEqual(relevance.domain, guidance.DOMAIN_TK)

    def test_nagoya_query_is_abs(self):
        self.assertEqual(guidance.classify_query(NAGOYA_QUERY).domain,
                         guidance.DOMAIN_ABS)

    def test_bio_resource_query_is_abs(self):
        self.assertEqual(
            guidance.classify_query("Do I need NBA approval to access a biological resource?").domain,
            guidance.DOMAIN_ABS,
        )

    def test_gibberish_is_unclear(self):
        self.assertEqual(guidance.classify_query("xyzzy plugh zorkmid").domain,
                         guidance.DOMAIN_UNCLEAR)

    def test_classification_is_deterministic_and_explainable(self):
        first = guidance.classify_query(GOLDEN_EN)
        second = guidance.classify_query(GOLDEN_EN)
        self.assertEqual(first.domain, second.domain)
        self.assertEqual(first.signals, second.signals)
        self.assertTrue(first.rationale)


class GoldenScenarioTests(unittest.TestCase):
    """The ABS golden scenario, end-to-end, offline stand-in mode."""

    @classmethod
    def setUpClass(cls):
        cls.result = guidance.answer(GOLDEN_EN)

    def test_recognized_and_answered_not_patents(self):
        self.assertTrue(ok(self.result), self.result["abstention_reason"])
        self.assertFalse(self.result["abstention"])

    def test_citations_valid_and_abs(self):
        self.assertTrue(self.result["citations"])
        ids = [c["id"] for c in self.result["citations"]]
        self.assertIn("M4-SRC-003", ids)  # substituted s.7 (SBB prior intimation)
        for citation in self.result["citations"]:
            is_ok, reason = guidance.validate_citation(citation)
            self.assertTrue(is_ok, reason)
            self.assertNotEqual(citation["source_type"], "treaty")
        self.assertNotIn("M4-SRC-010", ids)

    def test_answer_is_grounded(self):
        answer_text = self.result["answer"]
        self.assertIn("State Biodiversity Board", answer_text)
        self.assertIn("Form 2", answer_text)
        self.assertIn("not legal advice", answer_text)
        # every section/article/rule claim must be backed by a citation
        ok_flag, reason = guidance.validate_generated(
            answer_text, self.result["citations"]
        )
        self.assertTrue(ok_flag, reason)
        # no invented amounts
        self.assertNotIn("₹", answer_text)

    def test_confidence_appropriate(self):
        self.assertIn(self.result["confidence"], ("HIGH", "MEDIUM"))
        self.assertGreaterEqual(self.result["confidence_score"], 0.5)
        self.assertLessEqual(self.result["confidence_score"], 0.95)

    def test_no_tkdl_pointer_for_pure_abs(self):
        self.assertIsNone(self.result["tkdl_pointer"])

    def test_disclaimer_appears_exactly_once(self):
        self.assertEqual(self.result["answer"].count("not legal advice"), 1)
        hi = guidance.answer(GOLDEN_HI)
        self.assertEqual(hi["answer"].count("कानूनी सलाह नहीं"), 1)

    def test_deterministic(self):
        again = guidance.answer(GOLDEN_EN)
        self.assertEqual(again, self.result)


class OutOfScopeTests(unittest.TestCase):
    def test_trademark_not_flagged_abs(self):
        result = guidance.answer(TRADEMARK_EN)
        self.assertEqual(result["status"], "abstained")
        self.assertTrue(result["abstention"])
        self.assertEqual(result["citations"], [])
        self.assertIsNone(result["tkdl_pointer"])
        self.assertIn("not legal advice", result["answer"])
        self.assertIn("ABS", result["abstention_reason"])

    def test_trademark_hindi_safe_result(self):
        result = guidance.answer(TRADEMARK_HI)
        self.assertEqual(result["status"], "abstained")
        self.assertIn("कानूनी सलाह नहीं", result["answer"])

    def test_international_only_question_abstains(self):
        result = guidance.answer(INTERNATIONAL_ONLY)
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])

    def test_out_of_corpus_abs_abstains(self):
        result = guidance.answer(OUT_OF_CORPUS_EN)
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])
        self.assertIn("sufficient", result["abstention_reason"].lower())

    def test_unsupported_fee_question_abstains_without_inventing(self):
        result = guidance.answer(OUT_OF_CORPUS_FEE)
        self.assertEqual(result["status"], "abstained")
        self.assertNotIn("₹", result["answer"])
        self.assertNotRegex(result["answer"], r"\d+\s*(rupees|dollars)")

    def test_gibberish_abstains(self):
        result = guidance.answer("xyzzy plugh zorkmid")
        self.assertEqual(result["status"], "abstained")

    def test_abstention_text_has_disclaimer(self):
        for query in (TRADEMARK_EN, OUT_OF_CORPUS_EN, "xyzzy"):
            result = guidance.answer(query)
            self.assertIn("not legal advice", result["answer"])


class TraditionalKnowledgeTests(unittest.TestCase):
    def test_tk_patentability_query_gets_safe_pointer_and_abstains(self):
        result = guidance.answer(TK_PATENT_QUERY)
        self.assertIsNotNone(result["tkdl_pointer"])
        self.assertIn("https://tkdl.res.in", result["tkdl_pointer"])
        self.assertIn("patent", result["tkdl_pointer"].lower())
        # no fabricated TKDL specifics
        self.assertNotIn("TKDL says", result["tkdl_pointer"])
        self.assertNotRegex(result["tkdl_pointer"], r"\d{3,}")

    def test_tk_prior_art_query_answered_with_pointer(self):
        result = guidance.answer("is my ayurvedic traditional knowledge prior art")
        self.assertTrue(ok(result), result["abstention_reason"])
        self.assertIsNotNone(result["tkdl_pointer"])
        self.assertTrue(result["citations"])
        self.assertNotIn("TKDL says", result["answer"])

    def test_pointer_only_from_public_level(self):
        pointer = guidance.build_tkdl_pointer("en")
        for supported in ("CSIR", "Ministry of Ayush", "TKDL Access Agreement"):
            self.assertIn(supported, pointer)
        self.assertNotRegex(pointer, r"\d[\d,]*\s+(formulations|records)")
        pointer_hi = guidance.build_tkdl_pointer("hi")
        self.assertIn("tkdl.res.in", pointer_hi)


class TkdlFabricationSafetyTests(unittest.TestCase):
    """Attempts to generate invented TKDL details must be rejected/abstained."""

    def _mock(self, answer_text):
        class Mock:
            def complete(self, system, user):
                return json.dumps({
                    "answer": answer_text,
                    "citation_ids": ["M4-SRC-010"],
                })
        return Mock()

    def test_tkdl_count_fabrication_rejected(self):
        result = guidance.answer(
            "is my ayurvedic traditional knowledge prior art",
            llm=self._mock("TKDL has 400,000 formulations in its database."),
        )
        self.assertEqual(result["status"], "abstained")
        self.assertIn("count", result["abstention_reason"].lower())

    def test_tkdl_says_claim_rejected(self):
        result = guidance.answer(
            "is my ayurvedic traditional knowledge prior art",
            llm=self._mock("TKDL says this formulation is not prior art."),
        )
        self.assertEqual(result["status"], "abstained")

    def test_tkdl_record_fabrication_rejected(self):
        result = guidance.answer(
            "is my ayurvedic traditional knowledge prior art",
            llm=self._mock("The TKDL database entry 12345 covers turmeric."),
        )
        self.assertEqual(result["status"], "abstained")

    def test_tkdl_outcome_fabrication_rejected(self):
        result = guidance.answer(
            "is my ayurvedic traditional knowledge prior art",
            llm=self._mock("TKDL documents show the patent was revoked."),
        )
        self.assertEqual(result["status"], "abstained")

    def test_validator_directly_rejects_fabrication_patterns(self):
        pointer = guidance.build_tkdl_pointer("en")
        citations = guidance.citations_from_ids(["M4-SRC-010"])
        for bad in (
            "TKDL contains 500,000 records.",
            "TKDL says the formulation lacks novelty.",
            "The TKDL record for neem covers fungicides.",
        ):
            ok_flag, reason = guidance.validate_generated(bad + "\n" + pointer, citations)
            self.assertFalse(ok_flag, bad)
        # the legitimate pointer itself passes with its own citation
        ok_flag, reason = guidance.validate_generated(pointer, citations)
        self.assertTrue(ok_flag, reason)


class CitationIntegrityTests(unittest.TestCase):
    def _valid_citation(self):
        return corpus.to_citation(corpus.get_record("M4-SRC-003"))

    def test_valid_citation_passes(self):
        ok_flag, reason = guidance.validate_citation(self._valid_citation())
        self.assertTrue(ok_flag, reason)

    def test_unknown_id_rejected(self):
        citation = self._valid_citation()
        citation["id"] = "M4-SRC-999"
        ok_flag, reason = guidance.validate_citation(citation)
        self.assertFalse(ok_flag)
        self.assertIn("unknown", reason)

    def test_fabricated_url_rejected(self):
        citation = self._valid_citation()
        citation["url"] = "https://fake-registry.example.gov/bda.pdf"
        ok_flag, reason = guidance.validate_citation(citation)
        self.assertFalse(ok_flag)
        self.assertIn("url", reason)

    def test_altered_section_rejected(self):
        citation = self._valid_citation()
        citation["section"] = "Section 8"
        ok_flag, reason = guidance.validate_citation(citation)
        self.assertFalse(ok_flag)
        self.assertIn("section", reason)

    def test_altered_excerpt_rejected(self):
        citation = self._valid_citation()
        citation["excerpt"] = citation["excerpt"] + " (altered)"
        ok_flag, reason = guidance.validate_citation(citation)
        self.assertFalse(ok_flag)
        self.assertIn("excerpt", reason)

    def test_missing_field_rejected(self):
        citation = self._valid_citation()
        del citation["effective_date"]
        ok_flag, reason = guidance.validate_citation(citation)
        self.assertFalse(ok_flag)
        self.assertIn("missing", reason)

    def test_pipeline_rejects_fabricated_citation(self):
        bad = self._valid_citation()
        bad["url"] = "https://fabricated.example/invented-act.pdf"

        class Mock:
            def complete(self, system, user):
                return json.dumps({
                    "answer": "Guidance with a fabricated source.",
                    "citations": [bad],
                })

        result = guidance.answer(GOLDEN_EN, llm=Mock())
        self.assertEqual(result["status"], "abstained")
        self.assertIn("citation validation failed", result["abstention_reason"])


class ConfidenceTests(unittest.TestCase):
    def test_strong_evidence_high(self):
        label, score = guidance.compute_confidence(
            guidance.get_evidence(guidance.classify_query(GOLDEN_EN).shadow),
            guidance.classify_query(GOLDEN_EN),
        )
        self.assertEqual(label, "HIGH")
        self.assertGreaterEqual(score, 0.75)

    def test_treaty_evidence_high(self):
        relevance = guidance.classify_query(NAGOYA_QUERY)
        label, score = guidance.compute_confidence(
            guidance.get_evidence(relevance.shadow), relevance
        )
        self.assertEqual(label, "HIGH")
        self.assertGreaterEqual(score, 0.75)

    def test_weak_evidence_low(self):
        relevance = guidance.classify_query("I grow medicinal plants on my farm - what rules apply?")
        label, score = guidance.compute_confidence(
            guidance.get_evidence(relevance.shadow), relevance
        )
        self.assertEqual(label, "LOW")
        self.assertLess(score, 0.5)

    def test_benefit_sharing_query_answers_medium_with_citations(self):
        result = guidance.answer("how is benefit sharing determined for approvals")
        self.assertTrue(ok(result), result["abstention_reason"])
        self.assertIn(result["confidence"], ("MEDIUM", "HIGH"))
        ids = [c["id"] for c in result["citations"]]
        self.assertIn("M4-SRC-004", ids)  # section 21(1) benefit sharing
        for citation in result["citations"]:
            is_ok, reason = guidance.validate_citation(citation)
            self.assertTrue(is_ok, reason)

    def test_insufficient_evidence_zero(self):
        label, score = guidance.compute_confidence([], guidance.classify_query("anything"))
        self.assertEqual(label, "LOW")
        self.assertEqual(score, 0.0)

    def test_deterministic(self):
        relevance = guidance.classify_query(GOLDEN_EN)
        evidence = guidance.get_evidence(relevance.shadow)
        self.assertEqual(
            guidance.compute_confidence(evidence, relevance),
            guidance.compute_confidence(evidence, relevance),
        )

    def test_score_in_range(self):
        for query in (GOLDEN_EN, NAGOYA_QUERY, "benefit sharing approvals", "xyzzy"):
            relevance = guidance.classify_query(query)
            _, score = guidance.compute_confidence(
                guidance.get_evidence(relevance.shadow), relevance
            )
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 0.95)


class AbstentionTests(unittest.TestCase):
    def test_no_evidence(self):
        result = guidance.answer("How do I export neem cake to Norway under their rules?")
        self.assertEqual(result["status"], "abstained")
        self.assertTrue(result["abstention"])
        self.assertEqual(result["citations"], [])
        self.assertTrue(result["abstention_reason"])

    def test_weak_evidence_abstains(self):
        result = guidance.answer("I grow medicinal plants on my farm - what rules apply?")
        self.assertEqual(result["status"], "abstained")
        self.assertIn("insufficient", result["abstention_reason"].lower())

    def test_trademark_abstains(self):
        self.assertEqual(guidance.answer(TRADEMARK_EN)["status"], "abstained")

    def test_international_only_abstains(self):
        self.assertEqual(guidance.answer(INTERNATIONAL_ONLY)["status"], "abstained")

    def test_unsupported_abs_question_abstains(self):
        self.assertEqual(guidance.answer(OUT_OF_CORPUS_FEE)["status"], "abstained")

    def test_malformed_model_output_abstains(self):
        class Mock:
            def complete(self, system, user):
                return "this is not json at all"

        result = guidance.answer(GOLDEN_EN, llm=Mock())
        self.assertEqual(result["status"], "abstained")
        self.assertIn("malformed", result["abstention_reason"].lower())

    def test_unsupported_generated_amount_abstains(self):
        class Mock:
            def complete(self, system, user):
                return json.dumps({
                    "answer": "You must pay a benefit-sharing fee of ₹50,000 under section 7.",
                    "citation_ids": ["M4-SRC-003"],
                })

        result = guidance.answer(GOLDEN_EN, llm=Mock())
        self.assertEqual(result["status"], "abstained")
        self.assertIn("amount", result["abstention_reason"].lower())

    def test_unsupported_legal_claim_abstains(self):
        class Mock:
            def complete(self, system, user):
                return json.dumps({
                    "answer": "Under section 44 you must file within 30 days.",
                    "citation_ids": ["M4-SRC-003"],
                })

        result = guidance.answer(GOLDEN_EN, llm=Mock())
        self.assertEqual(result["status"], "abstained")
        self.assertIn("not supported", result["abstention_reason"].lower())

    def test_abstention_never_fabricates_partial_answer(self):
        for query in (TRADEMARK_EN, OUT_OF_CORPUS_EN, OUT_OF_CORPUS_FEE, "xyzzy"):
            result = guidance.answer(query)
            self.assertEqual(result["citations"], [])
            self.assertNotRegex(result["answer"], guidance._AMOUNT_RE)
            self.assertFalse(guidance._URL_RE.search(result["answer"]))

    def test_processing_error_mapped(self):
        class Mock:
            def complete(self, system, user):
                raise RuntimeError("network down")

        result = guidance.answer(GOLDEN_EN, llm=Mock())
        self.assertEqual(result["status"], "processing_error")
        self.assertTrue(result["abstention"])
        self.assertIn("processing error", result["abstention_reason"].lower())


class HindiTests(unittest.TestCase):
    def test_language_detection(self):
        self.assertEqual(hindi.detect_language(GOLDEN_HI), "hi")
        self.assertEqual(hindi.detect_language(GOLDEN_EN), "en")

    def test_shadow_maps_to_english_domain_terms(self):
        shadow = hindi.shadow_query(GOLDEN_HI)
        for term in ("plant", "formulation", "commercialise", "approvals", "collected"):
            self.assertIn(term, shadow)

    def test_hindi_and_english_map_to_same_evidence(self):
        en_ids = retrieval.retrieved_ids(guidance.get_evidence(guidance.classify_query(GOLDEN_EN).shadow))
        hi_ids = retrieval.retrieved_ids(guidance.get_evidence(guidance.classify_query(GOLDEN_HI).shadow))
        self.assertEqual(set(en_ids), set(hi_ids))
        self.assertIn("M4-SRC-003", set(hi_ids))

    def test_hindi_golden_end_to_end(self):
        result = guidance.answer(GOLDEN_HI)
        self.assertTrue(ok(result), result["abstention_reason"])
        self.assertEqual(result["confidence"], "HIGH")
        self.assertTrue(result["citations"])
        for citation in result["citations"]:
            is_ok, reason = guidance.validate_citation(citation)
            self.assertTrue(is_ok, reason)
        self.assertIn("कानूनी सलाह नहीं", result["answer"])
        self.assertIn("राज्य जैव विविधता बोर्ड", result["answer"])
        self.assertIsNone(result["tkdl_pointer"])

    def test_hindi_tkdl_pointer(self):
        result = guidance.answer("क्या मेरा पारंपरिक ज्ञान पूर्व तकनीक है?")
        self.assertIsNotNone(result["tkdl_pointer"])
        self.assertIn("tkdl.res.in", result["tkdl_pointer"])

    def test_hindi_abstention(self):
        result = guidance.answer("NBA फॉर्म 2 की फीस कितनी है?")
        self.assertEqual(result["status"], "abstained")
        self.assertIn("पर्याप्त", result["answer"])
        self.assertNotRegex(result["answer"], r"\d+\s*(rupees|dollars)")

    def test_hindi_legal_claims_validated(self):
        result = guidance.answer(GOLDEN_HI)
        ok_flag, reason = guidance.validate_generated(result["answer"], result["citations"])
        self.assertTrue(ok_flag, reason)


class ResultContractTests(unittest.TestCase):
    def test_exact_fields_on_all_paths(self):
        results = [
            guidance.answer(GOLDEN_EN),
            guidance.answer(GOLDEN_HI),
            guidance.answer(TRADEMARK_EN),
            guidance.answer(OUT_OF_CORPUS_EN),
            guidance.answer(TK_PATENT_QUERY),
            guidance.answer("is my ayurvedic traditional knowledge prior art"),
            guidance.answer("xyzzy"),
        ]
        for result in results:
            self.assertEqual(set(result.keys()), set(guidance.RESULT_FIELDS))
            self.assertIsInstance(result["answer"], str)
            self.assertIsInstance(result["citations"], list)
            self.assertIn(result["confidence"], ("HIGH", "MEDIUM", "LOW"))
            self.assertIsInstance(result["confidence_score"], float)
            self.assertGreaterEqual(result["confidence_score"], 0.0)
            self.assertLessEqual(result["confidence_score"], 1.0)
            self.assertIsInstance(result["abstention"], bool)
            self.assertIn(result["status"], ("ok", "abstained", "processing_error"))
            self.assertTrue(result["tkdl_pointer"] is None or isinstance(result["tkdl_pointer"], str))
            if result["status"] == "abstained":
                self.assertTrue(result["abstention"])
                self.assertTrue(result["abstention_reason"])
            if result["status"] == "ok":
                self.assertFalse(result["abstention"])
                self.assertIsNone(result["abstention_reason"])
                self.assertTrue(result["citations"])

    def test_citation_fields_match_plan_contract(self):
        result = guidance.answer(GOLDEN_EN)
        for citation in result["citations"]:
            self.assertEqual(
                set(citation.keys()),
                {"id", "source_name", "source_type", "section", "excerpt", "url", "effective_date"},
            )

    def test_tkdl_pointer_behavior(self):
        self.assertIsNone(guidance.answer(GOLDEN_EN)["tkdl_pointer"])
        self.assertIsInstance(guidance.answer(TK_PATENT_QUERY)["tkdl_pointer"], str)


class HostedLlmPathTests(unittest.TestCase):
    """The hosted path is implemented and its constraints are tested
    offline. No live API call is made or faked in this suite."""

    def test_no_credentials_means_stand_in(self):
        mode, client = llm_client.get_llm_client(env={})
        self.assertEqual(mode, "stand-in")
        self.assertFalse(getattr(client, "is_llm", True))

    def test_credentials_select_hosted_client(self):
        mode, client = llm_client.get_llm_client(env={llm_client.API_KEY_ENV: "secret"})
        self.assertEqual(mode, "hosted")
        self.assertEqual(client.api_key, "secret")

    def test_prompt_constraints(self):
        evidence = guidance.get_evidence(guidance.classify_query(GOLDEN_EN).shadow)
        system, user = guidance.build_prompt(GOLDEN_EN, "en", evidence)
        for banned in ("MUST NOT invent", "TKDL", "citation_ids"):
            self.assertIn(banned, system)
        self.assertIn("ONLY permitted knowledge source", user)
        for item in evidence:
            self.assertIn(item["record"]["id"], user)
            self.assertIn(item["record"]["excerpt"], user)

    def test_payload_shape_no_network(self):
        client = llm_client.HostedLLM("test-key", model="test-model", base_url="https://example.invalid/v1")
        payload = client.build_payload("system-prompt", "user-prompt")
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["temperature"], 0.0)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["content"], "user-prompt")
        self.assertNotIn("test-key", json.dumps(payload))  # key only in headers

    def test_fenced_json_accepted(self):
        data = guidance.parse_llm_output('```json\n{"answer": "ok", "citation_ids": []}\n```')
        self.assertEqual(data["answer"], "ok")


class SourceFreshnessTests(unittest.TestCase):
    """Phase 2 must not silently rely on stale Phase 1 wording."""

    def test_report_is_current(self):
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "verification_report.json",
        )
        with open(report_path, encoding="utf-8") as fh:
            report = json.load(fh)
        self.assertEqual(report["corpus_version"], corpus.CORPUS_VERSION)
        self.assertTrue(all(r["ok"] for r in report["results"]))

    def test_guidance_avoids_stale_rule_effective_day(self):
        # Phase 1 provenance flags the BDR 2024 exact in-force day as
        # computed/unverified; guidance text must not assert it.
        result = guidance.answer(GOLDEN_EN)
        self.assertNotIn("2024-12-21", result["answer"])
        self.assertNotIn("22 December 2024", result["answer"])

    def test_records_unchanged_from_phase1(self):
        # Corpus content guard: the Phase 2 modules must not mutate records.
        snapshot = copy.deepcopy(corpus.SOURCE_RECORDS)
        guidance.answer(GOLDEN_EN)
        guidance.answer(GOLDEN_HI)
        self.assertEqual(corpus.SOURCE_RECORDS, snapshot)


if __name__ == "__main__":
    unittest.main(verbosity=2)
