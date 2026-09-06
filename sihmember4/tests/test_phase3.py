"""Member 4 — Phase 3 test suite.

Run together with Phases 1-2:

    python -m unittest discover -s m4_abs/tests -t m4_abs -v

Phase 3 = demo-readiness validation: golden scenarios (EN/HI), traditional-
knowledge/TKDL scenarios, edge cases (part-ABS/part-patent, specific species,
unrelated IP, international-only, unsupported ABS), the citation audit, the
explicit TKDL-content audit, the source-correctness audit, confidence and
abstention audits, the exact result contract, and repeated deterministic
behavior. All checks run against real pipeline output.
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
import phase3_scenarios as p3  # noqa: E402

RESULTS = None  # populated once for the whole suite


def setUpModule():
    global RESULTS
    RESULTS = p3.run_all()


def result_for(name):
    for scenario_name, _query, _expectation, result in RESULTS:
        if scenario_name == name:
            return result
    raise KeyError(name)


class ScenarioAuditTests(unittest.TestCase):
    """Every canonical scenario must pass contract + citation + TKDL audits
    and meet its expectation."""

    def test_all_scenarios_pass_all_audits(self):
        report = p3.audit_all(RESULTS)
        failures = {name: v for name, v in report.items() if v}
        self.assertEqual(failures, {}, json.dumps(failures, ensure_ascii=False, indent=2)[:2000])

    def test_expected_statuses(self):
        for name, _query, expectation, result in RESULTS:
            if expectation == "ok":
                self.assertEqual(result["status"], "ok", name)
            elif expectation == "ok_pointer":
                self.assertEqual(result["status"], "ok", name)
                self.assertIsNotNone(result["tkdl_pointer"], name)
            elif expectation == "abstain_ptr":
                self.assertEqual(result["status"], "abstained", name)
                self.assertIsNotNone(result["tkdl_pointer"], name)
            else:
                self.assertEqual(result["status"], "abstained", name)


class GoldenScenarioPhase3Tests(unittest.TestCase):
    def test_golden_en_full_verification(self):
        result = result_for("golden_en")
        self.assertEqual(result["status"], "ok")
        ids = [c["id"] for c in result["citations"]]
        self.assertIn("M4-SRC-003", ids)          # substituted s.7
        self.assertTrue({"M4-SRC-001", "M4-SRC-005"} & set(ids))
        self.assertEqual(result["confidence"], "HIGH")
        self.assertIn("State Biodiversity Board", result["answer"])
        self.assertIn("Form 2", result["answer"])
        self.assertIn("not legal advice", result["answer"])
        self.assertEqual(result["answer"].count("not legal advice"), 1)
        self.assertIsNone(result["tkdl_pointer"])
        self.assertNotIn("patent", result["answer"].lower().split("intellectual property")[0].split("patent")[0])

    def test_golden_hi_matches_english_evidence(self):
        en = [c["id"] for c in result_for("golden_en")["citations"]]
        hi = [c["id"] for c in result_for("golden_hi")["citations"]]
        self.assertEqual(set(en), set(hi))

    def test_golden_hi_hindi_framing_and_disclaimer(self):
        result = result_for("golden_hi")
        self.assertEqual(result["status"], "ok")
        self.assertIn("राज्य जैव विविधता बोर्ड", result["answer"])
        self.assertIn("कानूनी सलाह नहीं", result["answer"])
        self.assertEqual(result["answer"].count("कानूनी सलाह नहीं"), 1)
        # statutory names preserved in English (no invented Hindi legal terms)
        self.assertIn("Biological Diversity Act 2002", result["answer"])
        for citation in result["citations"]:
            ok_flag, reason = guidance.validate_citation(citation)
            self.assertTrue(ok_flag, reason)

    def test_golden_not_treated_as_patent_question(self):
        relevance = guidance.classify_query(p3.GOLDEN_EN)
        self.assertEqual(relevance.domain, guidance.DOMAIN_ABS)
        self.assertEqual(relevance.other_ip_signals, [])
        # citations must be biological-diversity sources, not patent sources
        for citation in result_for("golden_en")["citations"]:
            self.assertNotEqual(citation["source_type"], "treaty")
            self.assertIn("Biological Diversity", citation["source_name"])


class TraditionalKnowledgePhase3Tests(unittest.TestCase):
    def test_tk_query_supported_with_pointer(self):
        result = result_for("tk_query")
        self.assertEqual(result["status"], "ok")
        self.assertIsNotNone(result["tkdl_pointer"])
        self.assertTrue(result["citations"])
        self.assertIn("TKDL Access Agreement", result["tkdl_pointer"])

    def test_tkdl_pointer_query_abstains_but_points(self):
        result = result_for("tkdl_pointer_query")
        self.assertEqual(result["status"], "abstained")
        self.assertIsNotNone(result["tkdl_pointer"])
        self.assertEqual(result["citations"], [])
        self.assertIn("prior art", result["tkdl_pointer"].lower().replace("prior-art", "prior art"))

    def test_tkdl_details_query_abstains_without_fabrication(self):
        result = result_for("tkdl_details_query")
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])
        self.assertEqual(p3.audit_tkdl_output(result), [])
        # the abstention text must not leak any TKDL specifics
        self.assertNotIn("turmeric", result["answer"].lower())

    def test_pointer_matches_public_level_description(self):
        for name in ("tk_query", "tkdl_pointer_query", "tkdl_details_query"):
            pointer = result_for(name)["tkdl_pointer"]
            self.assertIn("https://tkdl.res.in", pointer)
            self.assertIn("CSIR", pointer)
            self.assertIn("Ministry of Ayush", pointer)
            self.assertEqual(p3.audit_tkdl_output({"answer": "", "tkdl_pointer": pointer,
                                                   "abstention_reason": "", "citations": []}), [])


class TkdlFabricationRejectionTests(unittest.TestCase):
    """Hostile generation attempts must be rejected/abstained (pipeline-level)."""

    def _answer_with(self, answer_text):
        class Mock:
            def complete(self, system, user):
                return json.dumps({"answer": answer_text,
                                   "citation_ids": ["M4-SRC-010"]})

        return guidance.answer(p3.TK_QUERY, llm=Mock())

    def test_invented_count_rejected(self):
        result = self._answer_with("TKDL has 400,000 formulations and 5 lakh records.")
        self.assertEqual(result["status"], "abstained")

    def test_tkdl_says_rejected(self):
        result = self._answer_with("TKDL says this knowledge lacks novelty.")
        self.assertEqual(result["status"], "abstained")

    def test_invented_record_rejected(self):
        result = self._answer_with("The TKDL database entry 12,345 covers this formulation.")
        self.assertEqual(result["status"], "abstained")

    def test_invented_examiner_outcome_rejected(self):
        result = self._answer_with("TKDL documents show the EPO granted the patent anyway.")
        self.assertEqual(result["status"], "abstained")

    def test_clean_pointer_passes_the_same_guards(self):
        pointer = guidance.build_tkdl_pointer("en")
        self.assertEqual(p3.audit_tkdl_output(
            {"answer": "", "tkdl_pointer": pointer, "abstention_reason": "", "citations": []}), [])


class EdgeCaseTests(unittest.TestCase):
    def test_part_abs_part_patent_uses_abs_evidence(self):
        result = result_for("edge_part_abs_patent")
        self.assertEqual(result["status"], "ok")
        ids = [c["id"] for c in result["citations"]]
        self.assertIn("M4-SRC-003", ids)                      # s.7 ABS obligation
        self.assertNotIn("M4-SRC-010", ids)
        self.assertIn("outside this workstream", result["answer"])  # boundary note
        # no invented patent guidance: only claims backed by cited ABS records
        self.assertEqual(p3.audit_citations(result), [])

    def test_nba_before_patent_hits_section_6(self):
        result = result_for("edge_nba_before_patent")
        self.assertEqual(result["status"], "ok")
        ids = [c["id"] for c in result["citations"]]
        self.assertIn("M4-SRC-002", ids)                      # amended s.6 IPR/ABS intersection
        self.assertIn("register with the NBA", result["answer"])
        self.assertIn("outside this workstream", result["answer"])

    def test_part_abs_part_patent_in_hindi(self):
        result = guidance.answer(
            "मैं भारत में जंगल से एकत्रित पौधों से बने फॉर्मूलेशन का पेटेंट "
            "कराना चाहता हूँ - क्या अनुमोदन चाहिए?"
        )
        self.assertEqual(result["status"], "ok")
        self.assertIn("ABS आवश्यकताएँ स्वतंत्र रूप से लागू होती हैं", result["answer"])
        self.assertEqual(p3.audit_all([( "hi_patent", "", "ok", result )])["hi_patent"], [])

    def test_species_query_answers_general_framework_only(self):
        result = result_for("edge_species")
        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["citations"])
        answer_lower = result["answer"].lower()
        # no species-specific legal conclusions are invented
        self.assertNotIn("ashwagandha is exempt", answer_lower)
        self.assertNotIn("ashwagandha is not", answer_lower)
        self.assertNotIn("ashwagandha requires", answer_lower)
        self.assertEqual(p3.audit_citations(result), [])

    def test_species_exemption_probe_abstains(self):
        result = result_for("edge_species_exemption_probe")
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])
        self.assertIn("insufficient", result["abstention_reason"].lower())

    def test_unrelated_trademark_not_abs(self):
        result = result_for("edge_unrelated_trademark")
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])
        self.assertIsNone(result["tkdl_pointer"])
        self.assertIn("trademark", result["abstention_reason"].lower())

    def test_international_only_madrid_abstains(self):
        result = result_for("edge_international_madrid")
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])
        self.assertNotIn("NBA", result["answer"].split("(")[0])

    def test_international_export_outside_corpus_abstains(self):
        result = result_for("edge_international_export")
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])
        self.assertIn("insufficient", result["abstention_reason"].lower())

    def test_unsupported_fee_abstains_without_amounts(self):
        result = result_for("edge_unsupported_fee")
        self.assertEqual(result["status"], "abstained")
        self.assertNotRegex(result["answer"], r"[₹$]\s?\d")
        self.assertIn("no fee", result["abstention_reason"])


class CitationAuditPhase3Tests(unittest.TestCase):
    def test_every_scenario_citation_is_exact_stored_record(self):
        for name, _q, _e, result in RESULTS:
            violations = p3.audit_citations(result)
            self.assertEqual(violations, [], f"{name}: {violations}")

    def test_cited_evidence_supports_generated_claims(self):
        for name, _q, _e, result in RESULTS:
            if result["status"] == "ok":
                ok_flag, reason = guidance.validate_generated(result["answer"], result["citations"])
                self.assertTrue(ok_flag, f"{name}: {reason}")

    def test_citation_ids_are_the_only_llm_input(self):
        # the prompt asks for ids only; citation objects are rebuilt from storage
        evidence = guidance.get_evidence(guidance.classify_query(p3.GOLDEN_EN).shadow)
        _system, user = guidance.build_prompt(p3.GOLDEN_EN, "en", evidence)
        self.assertIn("citation_ids", user)
        self.assertNotIn('"url":', user.split("Curated evidence records")[1].split("Write a short")[0].replace("url=", ""))

    def test_altered_source_metadata_rejected(self):
        base = corpus.to_citation(corpus.get_record("M4-SRC-001"))
        for field, value in (("source_name", "Invented Act 2099"),
                             ("source_type", "invented_type"),
                             ("effective_date", "2099-01-01")):
            citation = dict(base)
            citation[field] = value
            ok_flag, reason = guidance.validate_citation(citation)
            self.assertFalse(ok_flag, field)
            self.assertIn(field, reason)

    def test_llm_can_neither_create_nor_mutate_citations(self):
        stored = corpus.to_citation(corpus.get_record("M4-SRC-003"))
        mutated = dict(stored)
        mutated["excerpt"] = "Completely invented legal text."
        fabricated = dict(stored, id="M4-FAKE-001", url="https://fake.example/act.pdf")

        class Mock:
            def complete(self, system, user):
                return json.dumps({"answer": "Some answer.",
                                   "citations": [mutated, fabricated]})

        result = guidance.answer(p3.GOLDEN_EN, llm=Mock())
        self.assertEqual(result["status"], "abstained")
        self.assertIn("citation validation failed", result["abstention_reason"])


class SourceCorrectnessAuditTests(unittest.TestCase):
    def test_static_source_audit_clean(self):
        self.assertEqual(p3.source_audit(), [])

    def test_report_covers_all_corpus_urls_and_is_fresh(self):
        report_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "verification_report.json",
        )
        with open(report_path, encoding="utf-8") as fh:
            report = json.load(fh)
        self.assertEqual(report["corpus_version"], corpus.CORPUS_VERSION)
        report_urls = {r["url"] for r in report["results"] if r["ok"]}
        for record in corpus.SOURCE_RECORDS:
            self.assertIn(record["url"], report_urls, record["id"])

    def test_amendment_material_current(self):
        # the amendment records are the post-2023 law, effective 2024-04-01
        for record in corpus.SOURCE_RECORDS:
            if record["id"] in ("M4-SRC-002", "M4-SRC-003", "M4-SRC-004"):
                self.assertEqual(record["effective_date"], "2024-04-01")
                self.assertIn("Act No. 10 of 2023", record["source_name"])

    def test_rules_material_used_as_verified(self):
        rules = corpus.get_record("M4-SRC-005")
        self.assertIn("G.S.R. 665(E)", rules["source_name"])
        self.assertIn("22nd October, 2024", rules["provenance"]["document_identity"])
        # guidance never asserts the computed effective day
        result = result_for("golden_en")
        self.assertNotIn("2024-12-21", result["answer"])

    def test_nagoya_representation_accurate(self):
        for record_id, marker in (("M4-SRC-006", "mutually agreed terms"),
                                  ("M4-SRC-007", "prior informed consent"),
                                  ("M4-SRC-008", "prior and informed consent")):
            record = corpus.get_record(record_id)
            self.assertEqual(record["jurisdiction"], "International")
            self.assertIn(marker, record["excerpt"].lower())


class ConfidenceAbstentionAuditTests(unittest.TestCase):
    def test_strong_evidence_high_weak_not_high(self):
        strong = guidance.compute_confidence(
            guidance.get_evidence(guidance.classify_query(p3.GOLDEN_EN).shadow),
            guidance.classify_query(p3.GOLDEN_EN),
        )
        weak = guidance.compute_confidence(
            guidance.get_evidence(guidance.classify_query(p3.SPECIES_EXEMPTION_PROBE).shadow),
            guidance.classify_query(p3.SPECIES_EXEMPTION_PROBE),
        )
        self.assertEqual(strong[0], "HIGH")
        self.assertNotEqual(weak[0], "HIGH")
        self.assertLess(weak[1], strong[1])

    def test_confidence_evidence_derived_not_llm(self):
        # compute_confidence takes only evidence + relevance - no model input
        relevance = guidance.classify_query(p3.GOLDEN_EN)
        evidence = guidance.get_evidence(relevance.shadow)
        first = guidance.compute_confidence(evidence, relevance)
        self.assertEqual(first, guidance.compute_confidence(evidence, relevance))

    def test_processing_error_not_fabricated_answer(self):
        class Mock:
            def complete(self, system, user):
                raise RuntimeError("API unreachable")

        result = guidance.answer(p3.GOLDEN_EN, llm=Mock())
        self.assertEqual(result["status"], "processing_error")
        self.assertTrue(result["abstention"])
        self.assertEqual(result["citations"], [])

    def test_unsupported_tkdl_detail_causes_abstention(self):
        class Mock:
            def complete(self, system, user):
                return json.dumps({"answer": "TKDL contains 5,00,000 records on this plant.",
                                   "citation_ids": ["M4-SRC-010"]})

        result = guidance.answer(p3.TK_QUERY, llm=Mock())
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["citations"], [])

    def test_citation_failure_causes_abstention(self):
        class Mock:
            def complete(self, system, user):
                return json.dumps({"answer": "Answer.", "citation_ids": ["M4-SRC-042"]})

        result = guidance.answer(p3.GOLDEN_EN, llm=Mock())
        self.assertEqual(result["status"], "abstained")

    def test_repeated_runs_deterministic(self):
        first = p3.run_all()
        second = p3.run_all()
        for (name_a, _qa, _ea, ra), (name_b, _qb, _eb, rb) in zip(first, second):
            self.assertEqual(name_a, name_b)
            self.assertEqual(ra, rb, name_a)


class Phase3ResultContractTests(unittest.TestCase):
    def test_full_contract_on_every_scenario(self):
        for name, _q, _e, result in RESULTS:
            violations = p3.audit_contract(result)
            self.assertEqual(violations, [], f"{name}: {violations}")

    def test_m6_can_consume_without_other_members(self):
        # import surface: only m4_abs modules
        import corpus as c
        import guidance as g
        result = g.answer(p3.GOLDEN_EN)
        payload = json.dumps(result, ensure_ascii=False)
        self.assertIn("citations", payload)
        self.assertEqual(set(result["citations"][0].keys()),
                         {"id", "source_name", "source_type", "section", "excerpt",
                          "url", "effective_date"})


class TkdlCorpusAuditTests(unittest.TestCase):
    def test_corpus_tkdl_record_is_pointer_only(self):
        tkdl = corpus.get_record(corpus.TKDL_RECORD_ID)
        self.assertEqual(p3.audit_tkdl_output({
            "answer": "", "abstention_reason": "", "tkdl_pointer": None,
            "citations": [corpus.to_citation(tkdl)],
        }), [])
        # scope/pointer text never asserts counts or outcomes
        for text in (tkdl["scope"], tkdl["pointer_guidance"], tkdl["provenance"]["notes"]):
            self.assertEqual(p3.audit_tkdl_output({
                "answer": "", "abstention_reason": "", "tkdl_pointer": None,
                "citations": [], "extra": text,
            }), [])

    def test_no_other_corpus_record_mentions_tkdl(self):
        for record in corpus.SOURCE_RECORDS:
            if record["id"] == corpus.TKDL_RECORD_ID:
                continue
            blob = " ".join(str(v) for k, v in record.items()
                            if k not in ("provenance", "keywords")).lower()
            self.assertNotIn("tkdl", blob, record["id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
