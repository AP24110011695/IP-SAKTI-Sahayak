"""Phase 2 tests for Member 3 — India Guidance.

Covers (MEMBER_3.md Phase 2 + the Phase 2 testing requirements):

  1.  golden India patent scenario (Section 3(p) evidence, grounded answer,
      valid citations, confidence, TKDL as pointer only);
  2.  golden India GI scenario (GI Registry/GI Act pathway);
  3.  out-of-corpus queries abstain cleanly;
  4.  India-only routing (international-only questions are never answered as
      India guidance; ABS/TK-specialist questions route to abstention, while
      the India-IP intersection is kept);
  5.  citation integrity (every citation maps to a real stored record;
      fabricated metadata is rejected);
  6.  confidence (varies sensibly with evidence strength; deterministic);
  7.  Hindi support (golden scenarios in Hindi; same evidence and citations);
  8.  abstention matrix (no evidence / weak evidence / unsupported topic /
      malformed or unsupported LLM output);
  9.  contract validation (exact RAG Result shape, citation fields, status
      values);
  10. determinism (repeated identical inputs give identical results), plus
      the Phase 2 source caveats: the re-verified BDA Section 6 amended text
      and the honest FSSAI Ayurveda-Aahara hosting provenance.

All tests are offline and deterministic: the hosted LLM is represented by a
FakeLLM implementing the same .complete(system, user) interface, and the
deterministic template mode is exercised directly.

Run with:  python -m unittest member3.test_phase2 -v   (or run all tests)
"""

import json
import unittest

from member3 import (
    CITATION_FIELDS,
    all_sources,
    answer_india_question,
    compute_confidence,
    route_query,
    validate_citation,
    validate_citations,
    validate_rag_result,
)
from member3.guidance import (
    DISCLAIMER_EN,
    DISCLAIMER_HI,
    STATUS_ABSTAINED,
    STATUS_OK,
    STATUS_PROCESSING_ERROR,
    check_supported_content,
)
from member3.retrieval import extract_keywords, retrieve_evidence


def corpus_record(record_id):
    return next(r for r in all_sources() if r["id"] == record_id)


class FakeLLM:
    """Deterministic stand-in for the hosted LLM. The reply may be a fixed
    string or a callable receiving (system, user) for content-aware fakes."""

    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        if callable(self.reply):
            return self.reply(system, user)
        return self.reply


class BoomLLM:
    """Simulates a hosted-API failure (network/HTTP)."""

    def complete(self, system, user):
        raise RuntimeError("connection refused")


def llm_json(answer, used):
    return json.dumps({"answer": answer, "evidence_used": used})


# ---------------------------------------------------------------------------
# 1. Golden India patent scenario
# ---------------------------------------------------------------------------


class TestGoldenScenario1Patent(unittest.TestCase):
    QUESTION = (
        "Can I patent a classical Ayurvedic formulation from an "
        "authoritative text?"
    )

    def test_routing_targets_patents(self):
        decision = route_query(self.QUESTION)
        self.assertEqual(decision["route"], "india_ip")
        self.assertEqual(decision["scope_area"], "patents")

    def test_retrieval_finds_section_3p_evidence(self):
        hits, sufficiency = retrieve_evidence(self.QUESTION)
        self.assertTrue(sufficiency["sufficient"], sufficiency)
        ids = [hit["record"]["id"] for hit in hits]
        self.assertIn("patents_act_1970_s3p", ids)
        # the best hit carries the Section 3(p) TK bar
        self.assertEqual(hits[0]["record"]["section"], "Section 3(p)")

    def test_template_mode_produces_grounded_cited_answer(self):
        result = answer_india_question(self.QUESTION, llm="template")
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        self.assertFalse(result["abstention"])
        self.assertIn(result["confidence"], ("HIGH", "MEDIUM"))
        self.assertGreaterEqual(result["confidence_score"], 0.75)
        cited = {c["id"] for c in result["citations"]}
        self.assertIn("patents_act_1970_s3p", cited)
        # the answer quotes the actual statutory bar, not a paraphrase cloud
        self.assertIn("traditional knowledge", result["answer"])
        self.assertIn("Section 3(p)", result["answer"])

    def test_tkdl_appears_as_pointer_only(self):
        """The answer names TKDL as the defensive-disclosure pointer with the
        public portal URL, without reproducing or inventing TKDL contents."""
        result = answer_india_question(self.QUESTION, llm="template")
        self.assertEqual(result["status"], STATUS_OK)
        self.assertIn("TKDL", result["answer"])
        self.assertIn("https://tkdl.res.in", result["answer"])
        self.assertIn("patent offices", result["answer"])
        # TKDL is a pointer in the answer text, never a citation record
        self.assertNotIn("tkdl", {c["id"] for c in result["citations"]})
        # no TKDL content claims beyond the role + restricted access
        self.assertNotIn("400,000", result["answer"])
        self.assertNotIn("formulations in TKDL", result["answer"])

    def test_llm_mode_with_constrained_output(self):
        reply = llm_json(
            "Under Section 3(p) of the Patents Act, 1970, an invention which, "
            "in effect, is traditional knowledge or an aggregation of known "
            "properties of traditionally known components is not an "
            "invention. A classical Ayurvedic formulation from an "
            "authoritative text falls in effect within this bar. The "
            "Traditional Knowledge Digital Library (TKDL, https://tkdl.res.in) "
            "is the defensive-disclosure tool for such knowledge. [E1] [E2]",
            ["E1", "E2"],
        )
        result = answer_india_question(self.QUESTION, llm=FakeLLM(reply))
        self.assertEqual(validate_rag_result(result), [], result)
        self.assertEqual(result["status"], STATUS_OK)
        self.assertIn("patents_act_1970_s3p", {c["id"] for c in result["citations"]})
        # every citation maps to a real stored record
        for citation in result["citations"]:
            self.assertEqual(validate_citation(citation), [])


# ---------------------------------------------------------------------------
# 2. Golden India GI scenario
# ---------------------------------------------------------------------------


class TestGoldenScenario2GI(unittest.TestCase):
    QUESTION = (
        "How do I register a GI tag for an Ayurvedic product tied to a region?"
    )

    def test_routing_targets_gi(self):
        decision = route_query(self.QUESTION)
        self.assertEqual(decision["route"], "india_ip")
        self.assertEqual(decision["scope_area"], "geographical_indications")

    def test_retrieval_finds_gi_application_evidence(self):
        hits, sufficiency = retrieve_evidence(self.QUESTION)
        self.assertTrue(sufficiency["sufficient"], sufficiency)
        ids = [hit["record"]["id"] for hit in hits]
        self.assertIn("gi_act_1999_s11_1", ids)
        self.assertIn("gi_act_1999_s2_1e", ids)

    def test_template_mode_produces_grounded_cited_answer(self):
        result = answer_india_question(self.QUESTION, llm="template")
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        cited = {c["id"] for c in result["citations"]}
        self.assertIn("gi_act_1999_s11_1", cited)
        self.assertIn("gi_act_1999_s2_1e", cited)
        # who may apply, per Section 11(1), appears through the quoted text
        self.assertIn("association of persons or producers", result["answer"])
        # the miscitation trap stays out: the definition cited is 2(1)(e)
        self.assertIn("Section 2(1)(e)", result["answer"])
        self.assertNotIn("2(1)(f)", result["answer"])

    def test_llm_mode_cites_gi_records(self):
        reply = llm_json(
            "Under Section 11(1) of the Geographical Indications of Goods "
            "(Registration and Protection) Act, 1999, any association of "
            "persons or producers or organisation representing the producers "
            "of the goods applies in writing to the Registrar in the "
            "prescribed form with the prescribed fees. A geographical "
            "indication is defined in Section 2(1)(e). [E1] [E2]",
            ["E1", "E2"],
        )
        result = answer_india_question(self.QUESTION, llm=FakeLLM(reply))
        self.assertEqual(validate_rag_result(result), [], result)
        self.assertEqual(result["status"], STATUS_OK)
        self.assertEqual(
            {c["id"] for c in result["citations"]},
            {"gi_act_1999_s11_1", "gi_act_1999_s2_1e"},
        )


# ---------------------------------------------------------------------------
# 3. Out-of-corpus abstention
# ---------------------------------------------------------------------------


class TestOutOfCorpusAbstention(unittest.TestCase):
    def test_court_procedure_question_abstains(self):
        result = answer_india_question(
            "How do I file an appeal against a patent refusal in the "
            "Delhi High Court and what are the court fees?"
        )
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention"])
        self.assertIsNone(_error_status(result))
        self.assertEqual(result["citations"], [])
        self.assertTrue(result["abstention_reason"])

    def test_nonsense_query_abstains(self):
        result = answer_india_question("zzz qxj vbn flurble")
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention_reason"].startswith("out_of_scope"))

    def test_abstention_is_not_a_processing_error(self):
        """Valid abstention must be a successful result, not an error."""
        result = answer_india_question(
            "What is the renewal fee for a trademark in Japan?"
        )
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertEqual(validate_rag_result(result), [])


def _error_status(result):
    return result["status"] if result["status"] == STATUS_PROCESSING_ERROR else None


# ---------------------------------------------------------------------------
# 4. India-only routing
# ---------------------------------------------------------------------------


class TestIndiaOnlyRouting(unittest.TestCase):
    INTERNATIONAL_QUERIES = (
        "How do I file a PCT application reaching the national phase?",
        "Can I register my ayurvedic brand internationally via the Madrid "
        "Protocol?",
        "I want to export my herbal products to the USA — what FDA rules "
        "apply?",
        "What does the TRIPS agreement say about plant variety protection?",
    )

    ABS_TK_QUERIES = (
        "What is the Nagoya Protocol benefit sharing requirement?",
        "How do I get NBA approval to access a biological resource for "
        "commercialisation?",
        "How do companies sign mutually agreed terms with communities under "
        "the ABS framework?",
    )

    def test_international_queries_route_away_from_india(self):
        for query in self.INTERNATIONAL_QUERIES:
            decision = route_query(query)
            self.assertEqual(decision["route"], "international_only", query)
            self.assertIsNone(decision["scope_area"], query)

    def test_international_queries_never_answered_as_india(self):
        for query in self.INTERNATIONAL_QUERIES:
            result = answer_india_question(query)
            self.assertEqual(result["status"], STATUS_ABSTAINED, query)
            self.assertEqual(result["citations"], [], query)
            self.assertTrue(
                result["abstention_reason"].startswith("out_of_scope_international"),
                query,
            )

    def test_abs_tk_specialist_queries_route_to_abstention(self):
        for query in self.ABS_TK_QUERIES:
            decision = route_query(query)
            self.assertEqual(decision["route"], "abs_tk_specialist", query)
            result = answer_india_question(query)
            self.assertEqual(result["status"], STATUS_ABSTAINED, query)
            self.assertTrue(
                result["abstention_reason"].startswith("out_of_scope_abs_tk"), query
            )

    def test_biodiversity_act_and_patent_intersection_stays_india(self):
        """The India-IP intersection (BD Act vs a patent application) is
        M3's to answer; only deep ABS mechanics are routed away."""
        decision = route_query(
            "Does the Biological Diversity Act affect my patent application?"
        )
        self.assertEqual(decision["route"], "india_ip")
        self.assertEqual(decision["scope_area"], "patents")

    def test_tkdl_mention_in_patent_question_stays_india(self):
        decision = route_query(
            "Can I patent a classical formulation, and should I check TKDL?"
        )
        self.assertEqual(decision["route"], "india_ip")
        self.assertEqual(decision["scope_area"], "patents")

    def test_every_scope_area_reachable(self):
        queries = {
            "patents": "Is my herbal extraction process patentable in India?",
            "geographical_indications": "How do I register a GI tag?",
            "trademarks": "How do I register a trademark for my brand?",
            "copyright": "What is the copyright term for a literary work?",
            "designs": "Can I register my bottle shape as a design?",
            "ppv_fr": "What are farmers rights over protected seed varieties?",
            "drugs_cosmetics": "What licence does an ayurvedic drug need?",
            "drugs_magic_remedies": "Can I advertise a cure for diabetes?",
            "fssai_ayurveda_aahara": "Is my product an Ayurveda Aahara under FSSAI?",
            "biological_diversity": "What does the biodiversity act say about IPR?",
        }
        for area, query in queries.items():
            decision = route_query(query)
            self.assertEqual(decision["route"], "india_ip", query)
            self.assertEqual(decision["scope_area"], area, query)

    def test_explicit_foreign_jurisdiction_request_abstains(self):
        result = answer_india_question(
            "How do I register a trademark?", jurisdiction="International"
        )
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention_reason"].startswith("out_of_scope"))


# ---------------------------------------------------------------------------
# 5. Citation integrity
# ---------------------------------------------------------------------------


class TestCitationIntegrity(unittest.TestCase):
    def test_golden_citations_map_to_stored_records(self):
        for question in (
            "Can I patent a classical Ayurvedic formulation from an "
            "authoritative text?",
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?",
        ):
            result = answer_india_question(question, llm="template")
            self.assertTrue(result["citations"])
            self.assertEqual(validate_citations(result["citations"]), [])
            stored = {r["id"]: r for r in all_sources()}
            for citation in result["citations"]:
                record = stored[citation["id"]]
                for field in CITATION_FIELDS:
                    self.assertEqual(citation[field], record[field], citation["id"])

    def test_unknown_citation_id_rejected(self):
        problems = validate_citation(
            dict.fromkeys(CITATION_FIELDS, "x") | {"id": "made_up_section_999"}
        )
        self.assertTrue(
            any("does not map to any stored source record" in p for p in problems)
        )

    def test_fabricated_url_rejected(self):
        record = corpus_record("patents_act_1970_s3p")
        citation = {field: record[field] for field in CITATION_FIELDS}
        citation["url"] = "https://fabricated.example.gov.in/patents.pdf"
        problems = validate_citation(citation)
        self.assertTrue(any("url" in p for p in problems))

    def test_wrong_section_number_rejected(self):
        record = corpus_record("gi_act_1999_s2_1e")
        citation = {field: record[field] for field in CITATION_FIELDS}
        citation["section"] = "Section 2(1)(f)"  # the classic miscitation
        problems = validate_citation(citation)
        self.assertTrue(any("section" in p for p in problems))

    def test_missing_field_rejected(self):
        record = corpus_record("gi_act_1999_s11_1")
        citation = {field: record[field] for field in CITATION_FIELDS}
        del citation["effective_date"]
        problems = validate_citation(citation)
        self.assertTrue(any("effective_date" in p for p in problems))

    def test_duplicate_citations_rejected(self):
        record = corpus_record("gi_act_1999_s11_1")
        citation = {field: record[field] for field in CITATION_FIELDS}
        problems = validate_citations([citation, dict(citation)])
        self.assertTrue(any("duplicate" in p for p in problems))

    def test_llm_citing_unprovided_evidence_aborts(self):
        reply = llm_json(
            "A long enough answer that would otherwise pass all the "
            "structural checks in the pipeline validation layer. [E7]",
            ["E7"],
        )
        result = answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?",
            llm=FakeLLM(reply),
        )
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention_reason"].startswith("llm_output_invalid"))


# ---------------------------------------------------------------------------
# 6. Confidence
# ---------------------------------------------------------------------------


class TestConfidence(unittest.TestCase):
    def test_strong_evidence_outranks_weak(self):
        strong_record = corpus_record("patents_act_1970_s3p")
        strong_label, strong_score, _ = compute_confidence(
            [strong_record, corpus_record("patents_act_1970_s2j")],
            routed_scope_area="patents",
            best_score=10,
        )
        weak_label, weak_score, _ = compute_confidence(
            [strong_record], routed_scope_area="patents", best_score=3
        )
        self.assertGreater(strong_score, weak_score)
        self.assertEqual(strong_label, "HIGH")
        self.assertIn(weak_label, ("LOW", "MEDIUM"))

    def test_scope_mismatch_lowers_confidence(self):
        record = corpus_record("patents_act_1970_s3p")
        _, aligned_score, _ = compute_confidence(
            [record], routed_scope_area="patents", best_score=8
        )
        _, misaligned_score, _ = compute_confidence(
            [record], routed_scope_area="geographical_indications", best_score=8
        )
        self.assertGreater(aligned_score, misaligned_score)

    def test_mirror_verified_evidence_scores_below_official_download(self):
        official = corpus_record("patents_act_1970_s3p")  # downloaded+extracted
        mirror = corpus_record("dmr_act_1954_s3")  # mirror-verified
        _, official_score, _ = compute_confidence(
            [official], routed_scope_area="patents", best_score=8
        )
        _, mirror_score, _ = compute_confidence(
            [mirror], routed_scope_area="drugs_magic_remedies", best_score=8
        )
        self.assertGreater(official_score, mirror_score)

    def test_confidence_is_deterministic(self):
        records = [
            corpus_record("patents_act_1970_s3p"),
            corpus_record("patents_act_1970_s2j"),
        ]
        first = compute_confidence(records, "patents", best_score=9)
        for _ in range(5):
            self.assertEqual(compute_confidence(records, "patents", best_score=9), first)

    def test_pipeline_confidence_stable_across_runs(self):
        question = (
            "Can I patent a classical Ayurvedic formulation from an "
            "authoritative text?"
        )
        runs = [
            answer_india_question(question, llm="template") for _ in range(3)
        ]
        for run in runs[1:]:
            self.assertEqual(run["confidence"], runs[0]["confidence"])
            self.assertEqual(run["confidence_score"], runs[0]["confidence_score"])
            self.assertEqual(run["citations"], runs[0]["citations"])

    def test_confidence_label_thresholds(self):
        self.assertEqual(compute_confidence(
            [corpus_record("patents_act_1970_s3p")], "patents", best_score=8
        )[0], "HIGH")
        self.assertEqual(compute_confidence([], "patents", best_score=0), ("LOW", 0.0, "no cited evidence"))


# ---------------------------------------------------------------------------
# 7. Hindi support
# ---------------------------------------------------------------------------

GOLDEN1_HI = (
    "क्या मैं किसी प्रामाणिक ग्रंथ से लिए गए शास्त्रीय आयुर्वेदिक "
    "फॉर्मूलेशन का पेटेंट कर सकता हूँ?"
)
GOLDEN2_HI = "मैं अपने आयुर्वेदिक उत्पाद के लिए जीआई टैग कैसे पंजीकृत करूँ?"


class TestHindiSupport(unittest.TestCase):
    def test_language_detection(self):
        from member3 import detect_language

        self.assertEqual(detect_language("patent my formulation?"), "en")
        self.assertEqual(detect_language(GOLDEN1_HI), "hi")

    def test_hindi_and_english_retrieve_the_same_evidence(self):
        en_hits, en_suff = retrieve_evidence(
            "Can I patent a classical Ayurvedic formulation from an "
            "authoritative text?"
        )
        hi_hits, hi_suff = retrieve_evidence(GOLDEN1_HI)
        self.assertTrue(en_suff["sufficient"] and hi_suff["sufficient"])
        self.assertEqual(
            [h["record"]["id"] for h in en_hits], [h["record"]["id"] for h in hi_hits]
        )

    def test_hindi_golden1_returns_hindi_answer_same_citations(self):
        en_result = answer_india_question(
            "Can I patent a classical Ayurvedic formulation from an "
            "authoritative text?", llm="template",
        )
        hi_result = answer_india_question(GOLDEN1_HI, llm="template")
        self.assertEqual(hi_result["status"], STATUS_OK)
        self.assertEqual(validate_rag_result(hi_result), [])
        self.assertIn(DISCLAIMER_HI, hi_result["answer"])
        self.assertNotIn(DISCLAIMER_EN, hi_result["answer"])
        # same evidence, same citations, same confidence as English
        self.assertEqual(
            [c["id"] for c in hi_result["citations"]],
            [c["id"] for c in en_result["citations"]],
        )
        self.assertEqual(hi_result["confidence_score"], en_result["confidence_score"])
        # statutory excerpts stay verbatim in English (official text)
        self.assertIn("traditional knowledge", hi_result["answer"])
        self.assertIn("Section 3(p)", hi_result["answer"])

    def test_hindi_golden2_same_evidence_as_english(self):
        en_result = answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?", llm="template",
        )
        hi_result = answer_india_question(GOLDEN2_HI, llm="template")
        self.assertEqual(hi_result["status"], STATUS_OK)
        self.assertEqual(validate_rag_result(hi_result), [])
        self.assertIn(DISCLAIMER_HI, hi_result["answer"])
        self.assertEqual(
            {c["id"] for c in hi_result["citations"]},
            {c["id"] for c in en_result["citations"]},
        )

    def test_hindi_llm_mode_demands_hindi_and_keeps_english_statute_names(self):
        seen = {}

        def reply(system, user):
            seen["system"] = system
            return llm_json(
                "Patents Act, 1970 की धारा 3(p) के अनुसार, पारंपरिक ज्ञान है "
                "ऐसा आविष्कार पेटेंट योग्य नहीं है। शास्त्रीय आयुर्वेदिक "
                "फॉर्मूलेशन इस बार में आता है। [E1]",
                ["E1"],
            )

        result = answer_india_question(GOLDEN1_HI, llm=FakeLLM(reply))
        self.assertEqual(result["status"], STATUS_OK)
        self.assertIn("HINDI", seen["system"])
        self.assertEqual(
            [c["id"] for c in result["citations"]], ["patents_act_1970_s3p"]
        )
        self.assertIn(DISCLAIMER_HI, result["answer"])

    def test_hindi_out_of_scope_abstains_in_hindi(self):
        result = answer_india_question("मैं अपने उत्पाद अमेरिका निर्यात कैसे करूँ?")
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertIn(DISCLAIMER_HI, result["answer"])


# ---------------------------------------------------------------------------
# 8. Abstention matrix
# ---------------------------------------------------------------------------


class TestAbstentionMatrix(unittest.TestCase):
    QUESTION = (
        "How do I register a GI tag for an Ayurvedic product tied to a region?"
    )

    def test_no_evidence(self):
        result = answer_india_question("zzz qxj vbn flurble")
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention_reason"].startswith("out_of_scope"))

    def test_weak_evidence(self):
        """One weakly-matching record is not enough — abstain, don't guess."""
        result = answer_india_question("Can I copyright my yoga video series?")
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention_reason"].startswith("insufficient_evidence"))

    def test_unsupported_topic_international(self):
        result = answer_india_question("How do I use the Hague system for designs?")
        self.assertTrue(result["abstention_reason"].startswith("out_of_scope_international"))

    def test_unsupported_topic_abs_tk(self):
        result = answer_india_question(
            "How does benefit sharing work under the Nagoya Protocol?"
        )
        self.assertTrue(result["abstention_reason"].startswith("out_of_scope_abs_tk"))

    def test_malformed_llm_output_abstains_not_errors(self):
        result = answer_india_question(self.QUESTION, llm=FakeLLM("this is not JSON"))
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention_reason"].startswith("llm_output_invalid"))
        self.assertTrue(result["abstention"])

    def test_llm_ignoring_evidence_format_abstains(self):
        result = answer_india_question(
            self.QUESTION, llm=FakeLLM("A plain answer without any JSON structure at all.")
        )
        self.assertTrue(result["abstention_reason"].startswith("llm_output_invalid"))

    def test_llm_with_empty_evidence_list_abstains(self):
        result = answer_india_question(
            self.QUESTION,
            llm=FakeLLM(llm_json("An answer that is long enough for the gate.", [])),
        )
        self.assertTrue(result["abstention_reason"].startswith("llm_output_invalid"))

    def test_llm_invented_section_reference_abstains(self):
        reply = llm_json(
            "Registration follows Section 2(1)(f) of the GI Act and Section "
            "11(1); apply to the Registrar with the prescribed fees. This is "
            "long enough for the gate. [E1]",
            ["E1"],
        )
        result = answer_india_question(self.QUESTION, llm=FakeLLM(reply))
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention_reason"].startswith("unsupported_content"))
        self.assertIn("2(1)(f)", result["abstention_reason"])

    def test_llm_invented_fee_amount_abstains(self):
        reply = llm_json(
            "The application fee is Rs. 5,000 per class under Section 11(1); "
            "any association of producers applies to the Registrar in the "
            "prescribed form. [E1]",
            ["E1"],
        )
        result = answer_india_question(self.QUESTION, llm=FakeLLM(reply))
        self.assertTrue(result["abstention_reason"].startswith("unsupported_content"))
        self.assertIn("Rs. 5,000", result["abstention_reason"])

    def test_llm_invented_url_abstains(self):
        reply = llm_json(
            "Apply via https://gi-portal.example.in/apply as per Section "
            "11(1) of the GI Act with the prescribed fees. This filler makes "
            "the answer long enough for the minimum length check. [E1]",
            ["E1"],
        )
        result = answer_india_question(self.QUESTION, llm=FakeLLM(reply))
        self.assertTrue(result["abstention_reason"].startswith("unsupported_content"))
        self.assertIn("URL", result["abstention_reason"])

    def test_llm_invented_duration_abstains(self):
        reply = llm_json(
            "Registration is valid for 10 years under the GI framework per "
            "Section 11(1); associations of producers may apply to the "
            "Registrar with the prescribed fees. [E1]",
            ["E1"],
        )
        result = answer_india_question(self.QUESTION, llm=FakeLLM(reply))
        self.assertTrue(result["abstention_reason"].startswith("unsupported_content"))
        self.assertIn("10 years", result["abstention_reason"])

    def test_llm_hallucinating_invented_provision_abstains_even_when_otherwise_valid(self):
        """The evidence supports Section 11(1) but NOT a fabricated
        sub-section — the guard must catch the fabricated part."""
        reply = llm_json(
            "Under Section 11(2) any person may apply to the Registrar to "
            "register a geographical indication with the prescribed fees and "
            "form as the Act provides. [E1]",
            ["E1"],
        )
        result = answer_india_question(self.QUESTION, llm=FakeLLM(reply))
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertIn("Section 11(2)", result["abstention_reason"])

    def test_llm_api_failure_is_processing_error_not_abstention(self):
        result = answer_india_question(self.QUESTION, llm=BoomLLM())
        self.assertEqual(result["status"], STATUS_PROCESSING_ERROR)
        self.assertFalse(result["abstention"])
        self.assertIsNone(result["abstention_reason"])
        self.assertEqual(result["citations"], [])


# ---------------------------------------------------------------------------
# 9. Contract validation
# ---------------------------------------------------------------------------


class TestOutputContract(unittest.TestCase):
    def test_ok_result_has_exact_shape(self):
        result = answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?", llm="template",
        )
        self.assertEqual(
            sorted(result.keys()),
            sorted([
                "answer", "citations", "confidence", "confidence_score",
                "abstention", "abstention_reason", "status",
            ]),
        )
        self.assertEqual(result["status"], "ok")
        self.assertIsInstance(result["citations"], list)
        self.assertIsInstance(result["confidence_score"], float)
        self.assertLessEqual(result["confidence_score"], 1.0)

    def test_citation_fields_exact(self):
        result = answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?", llm="template",
        )
        for citation in result["citations"]:
            self.assertEqual(
                sorted(citation.keys()),
                sorted(CITATION_FIELDS),
            )

    def test_status_values(self):
        ok = answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?", llm="template",
        )
        abstained = answer_india_question("zzz qxj vbn")
        error = answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?", llm=BoomLLM(),
        )
        self.assertEqual(ok["status"], "ok")
        self.assertEqual(abstained["status"], "abstained")
        self.assertEqual(error["status"], "processing_error")
        for result in (ok, abstained, error):
            self.assertIn(result["status"], ("ok", "abstained", "processing_error"))

    def test_validate_rag_result_detects_tampering(self):
        result = answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?", llm="template",
        )
        self.assertEqual(validate_rag_result(result), [])
        tampered = dict(result)
        tampered["citations"] = [dict(result["citations"][0])]
        tampered["citations"][0]["url"] = "https://tampered.example.in/x.pdf"
        self.assertTrue(validate_rag_result(tampered))

        wrong_keys = dict(result)
        wrong_keys["extra_field"] = True
        self.assertTrue(validate_rag_result(wrong_keys))

        no_disclaimer = dict(result)
        no_disclaimer["answer"] = "answer without any disclaimer text"
        self.assertTrue(validate_rag_result(no_disclaimer))

    def test_every_ok_answer_carries_disclaimer(self):
        results = [
            answer_india_question(q, llm="template")
            for q in (
                "Can I patent a classical Ayurvedic formulation from an "
                "authoritative text?",
                "How do I register a GI tag for an Ayurvedic product tied to "
                "a region?",
                "Is my product an Ayurveda Aahara under FSSAI?",
                "Can I advertise that my chyawanprash cures diabetes?",
            )
        ]
        for result in results:
            self.assertEqual(result["status"], "ok", result["abstention_reason"])
            self.assertIn(
                DISCLAIMER_EN, result["answer"]
            )

    def test_abstention_and_error_results_carry_no_citations(self):
        abstained = answer_india_question("zzz qxj vbn")
        error = answer_india_question(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region?", llm=BoomLLM(),
        )
        self.assertEqual(abstained["citations"], [])
        self.assertEqual(error["citations"], [])


# ---------------------------------------------------------------------------
# 10. Determinism + Phase 2 source caveats
# ---------------------------------------------------------------------------


class TestDeterminism(unittest.TestCase):
    def test_routing_deterministic(self):
        question = GOLDEN1_HI
        first = route_query(question)
        for _ in range(5):
            self.assertEqual(route_query(question), first)

    def test_retrieval_deterministic(self):
        question = "How do I register a GI tag for an Ayurvedic product?"
        first_ids, first_scores = _retrieval_signature(question)
        for _ in range(5):
            self.assertEqual(_retrieval_signature(question), (first_ids, first_scores))

    def test_full_pipeline_deterministic_in_template_mode(self):
        question = "Is my product an Ayurveda Aahara under FSSAI?"
        first = answer_india_question(question, llm="template")
        for _ in range(3):
            again = answer_india_question(question, llm="template")
            self.assertEqual(again, first)

    def test_keyword_extraction_normalises_variants(self):
        """Singular/plural and synonym variants must retrieve the same
        evidence (extraction keeps the raw token AND its normalised variant,
        so matching, not the raw list, is the contract)."""
        kw1 = extract_keywords("How do I register a GI tag?")
        kw2 = extract_keywords("How do I register a GI tags?")
        self.assertIn("tag", kw1)
        self.assertIn("tag", kw2)
        self.assertEqual(
            _retrieval_signature("How do I register a GI tag?"),
            _retrieval_signature("How do I register a GI tags?"),
        )
        self.assertIn("ayurveda", extract_keywords("ayurvedic medicine"))


def _retrieval_signature(question):
    hits, _ = retrieve_evidence(question)
    return (
        [h["record"]["id"] for h in hits],
        [h["score"] for h in hits],
    )


class TestPhase2SourceCaveats(unittest.TestCase):
    """The two Phase 1 source caveats that Phase 2 had to resolve before
    using the records in guidance."""

    def test_bda_section6_uses_amended_text(self):
        """Phase 1 mirror was pre-2023-amendment. Phase 2 re-verified against
        the Official Gazette of the Amendment Act before using the record:
        approval/registration timing is now BEFORE GRANT, and the superseded
        pre-application wording must be gone."""
        record = corpus_record("bda_2002_s6")
        self.assertIn("before grant of", record["excerpt"])
        self.assertIn("shall register", record["excerpt"])
        self.assertIn("6(1A)", record["section"])
        self.assertNotIn("before making such application", record["excerpt"])
        self.assertNotIn("acceptance of the patent", record["excerpt"])
        self.assertIn("egazette.gov.in", record["url"])
        self.assertEqual(record["verification"]["method"], "downloaded+extracted")
        self.assertIn("RE-VERIFIED", record["verification"]["notes"])
        self.assertIn("1 April 2024", record["effective_date"])

    def test_fssai_gazette_record_is_honest_about_hosting(self):
        """The 2022 Ayurveda Aahara Gazette is hosted on a verified copy, not
        on fssai.gov.in — the record must say so, never claim an official
        FSSAI URL, and prefer the strongest authoritative source."""
        record = corpus_record("fss_aahara_regs_2022_reg2b")
        notes = record["verification"]["notes"]
        self.assertIn("HOSTING NOTE", notes)
        self.assertIn("verified copy of the official Gazette scan", notes)
        self.assertNotIn("fssai.gov.in", record["url"])
        self.assertIn("foodsafetystandard.in", record["url"])
        # the corroborating official FSSAI order (live on fssai.gov.in) exists
        order = corpus_record("fssai_order_2025_cat_a")
        self.assertTrue(order["url"].startswith("https://fssai.gov.in/"))
        self.assertEqual(order["verification"]["method"], "downloaded+extracted")

    def test_no_2024_patent_rules_tkdl_mandate_invented(self):
        """The corpus must not claim a '2024 Patent Rules TKDL mandate' or
        any rule text that was not verified — TKDL appears only as the
        curated pointer in guidance, never as a quoted source."""
        ids = {r["id"] for r in all_sources()}
        self.assertNotIn("patents_rules_2024", ids)
        for record in all_sources():
            blob = (record["excerpt"] + record["section_title"]).lower()
            self.assertNotIn("tkdl", blob, record["id"])
            self.assertNotIn("mandates a tkdl", blob, record["id"])


if __name__ == "__main__":
    unittest.main()
