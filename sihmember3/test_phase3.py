"""Phase 3 tests for Member 3 — Standalone Completion.

Covers (MEMBER_3.md Phase 3):

  - the Section 7 golden scenarios run through the real pipeline (offline,
    deterministic generation mode) with contract + citation assertions;
  - the required edge cases: ambiguous IP type, multiple regimes implicated
    at once (a product that is both a GI candidate and a classical-medicine
    patent question), the food/drug regulatory boundary, the BD-Act x patent
    intersection, cure-claim advertising questions, thin/unsupported
    evidence;
  - the offline half of the citation audit (field-exact mapping of every
    citation to a stored Phase 1 record; the live half — URL resolution and
    PDF excerpt re-verification — is member3/audit_citations.py, run for
    real and pasted in the phase report);
  - the hosted-LLM client interface, verified without network (request
    shape, response parsing, error mapping) using the stand-in mechanism;
  - Hindi edge behavior; TKDL pointer-only sweeps; determinism.

Run with:  python -m unittest member3.test_phase3 -v   (or run all tests)
"""

import io
import json
import re
import unittest
import urllib.error
from unittest import mock

from member3 import (
    CITATION_FIELDS,
    all_sources,
    answer_india_question,
    get_llm_client,
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
)
from member3.llm import HostedLLM, LLMError
from member3.retrieval import retrieve_evidence

# ---------------------------------------------------------------------------
# Scenario set (golden + edge) used by several test classes below.
# ---------------------------------------------------------------------------

GOLDEN_1 = (
    "Can I patent a classical Ayurvedic formulation from an authoritative "
    "text?"
)
GOLDEN_2 = (
    "How do I register a GI tag for an Ayurvedic product tied to a region?"
)
EDGE_MULTI_REGIME = (
    "I have a classical Ayurvedic formulation and want to protect it - can I "
    "patent it, and can the region where we grow the herbs get a GI tag?"
)
EDGE_AMBIGUOUS = "How do I protect my Ayurvedic product in India?"
EDGE_FOOD_DRUG = "Is my bhasma-containing product a food or a drug in India?"
EDGE_BD_PATENT = (
    "Does the Biological Diversity Act affect my patent application for a "
    "herbal formulation?"
)
EDGE_CURE_CLAIM = (
    "Can I claim my tonic cures diabetes and also improve sexual pleasure?"
)
EDGE_CURE_NON_IP = "How do I cure my fever with ayurveda?"
EDGE_PPV_THIN = "How do I register a new medicinal plant variety in India?"
EDGE_UNSUPPORTED = "What is the procedure to appeal before the IPAB?"
EDGE_OUT_OF_CORPUS = (
    "What is the fee for renewing a trademark in Japan under the Madrid "
    "Protocol?"
)

GOLDEN_1_HI = (
    "क्या मैं किसी प्रामाणिक ग्रंथ से लिए गए शास्त्रीय आयुर्वेदिक "
    "फॉर्मूलेशन का पेटेंट कर सकता हूँ?"
)
GOLDEN_2_HI = "मैं अपने आयुर्वेदिक उत्पाद के लिए जीआई टैग कैसे पंजीकृत करूँ?"
EDGE_MULTI_REGIME_HI = (
    "क्या मैं शास्त्रीय आयुर्वेदिक फॉर्मूलेशन का पेटेंट कर सकता हूँ और "
    "जीआई टैग भी पंजीकृत कर सकता हूँ?"
)

SCENARIOS = (
    ("golden_1", GOLDEN_1),
    ("golden_2", GOLDEN_2),
    ("golden_1_hindi", GOLDEN_1_HI),
    ("golden_2_hindi", GOLDEN_2_HI),
    ("edge_multi_regime", EDGE_MULTI_REGIME),
    ("edge_food_drug", EDGE_FOOD_DRUG),
    ("edge_bd_patent", EDGE_BD_PATENT),
    ("edge_cure_claim", EDGE_CURE_CLAIM),
    ("edge_ppv_thin", EDGE_PPV_THIN),
)


def run_scenario(query):
    return answer_india_question(query, llm="template")


def corpus_record(record_id):
    return next(r for r in all_sources() if r["id"] == record_id)


# ---------------------------------------------------------------------------
# Golden scenarios through the pipeline
# ---------------------------------------------------------------------------


class TestGoldenScenariosPhase3(unittest.TestCase):
    def test_golden_1_full_contract_and_citations(self):
        result = run_scenario(GOLDEN_1)
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        self.assertIn(result["confidence"], ("HIGH", "MEDIUM"))
        self.assertGreaterEqual(result["confidence_score"], 0.75)
        self.assertIn(DISCLAIMER_EN, result["answer"])
        cited = {c["id"] for c in result["citations"]}
        self.assertIn("patents_act_1970_s3p", cited)
        self.assertIn("Section 3(p)", result["answer"])
        self.assertIn("traditional knowledge", result["answer"])

    def test_golden_2_full_contract_and_citations(self):
        result = run_scenario(GOLDEN_2)
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        cited = {c["id"] for c in result["citations"]}
        self.assertEqual(cited, {"gi_act_1999_s11_1", "gi_act_1999_s2_1e"})
        self.assertIn("Section 11(1)", result["answer"])
        self.assertIn("Registrar", result["answer"])

    def test_golden_scenarios_deterministic(self):
        for query in (GOLDEN_1, GOLDEN_2, GOLDEN_1_HI, GOLDEN_2_HI):
            first = run_scenario(query)
            for _ in range(3):
                self.assertEqual(run_scenario(query), first)


# ---------------------------------------------------------------------------
# Required edge cases
# ---------------------------------------------------------------------------


class TestEdgeMultiRegimeGIAndPatent(unittest.TestCase):
    """The MEMBER_3.md Phase 3 example: a product that is both a GI
    candidate and a classical-medicine patent question."""

    def test_routing_detects_both_regimes(self):
        decision = route_query(EDGE_MULTI_REGIME)
        self.assertEqual(decision["route"], "india_ip")
        self.assertIn("patents", decision["matched_areas"])
        self.assertIn("geographical_indications", decision["matched_areas"])

    def test_retrieval_keeps_evidence_from_both_regimes(self):
        decision = route_query(EDGE_MULTI_REGIME)
        hits, sufficiency = retrieve_evidence(EDGE_MULTI_REGIME, decision)
        self.assertTrue(sufficiency["sufficient"], sufficiency)
        areas = {h["record"]["scope_area"] for h in hits}
        self.assertIn("patents", areas)
        self.assertIn("geographical_indications", areas)
        ids = {h["record"]["id"] for h in hits}
        self.assertIn("patents_act_1970_s3p", ids)
        self.assertIn("gi_act_1999_s11_1", ids)

    def test_pipeline_answers_with_both_regimes_cited(self):
        result = run_scenario(EDGE_MULTI_REGIME)
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        cited = {c["id"] for c in result["citations"]}
        self.assertIn("patents_act_1970_s3p", cited)
        self.assertTrue(
            {"gi_act_1999_s11_1", "gi_act_1999_s2_1e"} & cited,
            "GI side of the question must be cited",
        )
        # both provisions appear in the answer text
        self.assertIn("Section 3(p)", result["answer"])
        self.assertIn("Section 11(1)", result["answer"])
        self.assertGreaterEqual(result["confidence_score"], 0.75)

    def test_multi_regime_llm_mode_gets_multi_regime_note(self):
        seen = {}

        class EvidenceAwareLLM:
            """Cites the evidence blocks whose sections it references — the
            same constrained behaviour the real hosted LLM is prompted for."""

            def complete(self, system, user):
                seen["user"] = user
                labels = {}
                for label, section in re.findall(
                    r"\[(E\d+)\] source: .*\nsection: ([^\n]+)", user
                ):
                    labels[section] = label
                used = [labels["Section 3(p)"], labels["Section 11(1)"]]
                reply = (
                    "Patent position: Section 3(p) of the Patents Act, 1970 "
                    "bars an invention which, in effect, is traditional "
                    "knowledge, so a classical formulation is not patentable. "
                    "GI position: Section 11(1) lets an association of "
                    "producers apply in writing to the Registrar in the "
                    "prescribed form and fees. [%s] [%s]" % tuple(used)
                )
                return json.dumps({"answer": reply, "evidence_used": used})

        result = answer_india_question(EDGE_MULTI_REGIME, llm=EvidenceAwareLLM())
        self.assertEqual(result["status"], STATUS_OK, result["abstention_reason"])
        self.assertEqual(validate_rag_result(result), [])
        self.assertIn("Multi-regime note", seen["user"])
        self.assertEqual(result["confidence"], "HIGH")

    def test_hindi_multi_regime_matches_english_citations(self):
        en = run_scenario(EDGE_MULTI_REGIME)
        hi = run_scenario(EDGE_MULTI_REGIME_HI)
        self.assertEqual(hi["status"], STATUS_OK)
        self.assertEqual(validate_rag_result(hi), [])
        self.assertIn(DISCLAIMER_HI, hi["answer"])
        self.assertEqual(
            {c["id"] for c in hi["citations"]}, {c["id"] for c in en["citations"]}
        )


class TestEdgeAmbiguousIPType(unittest.TestCase):
    def test_ambiguous_question_abstains_safely(self):
        result = run_scenario(EDGE_AMBIGUOUS)
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention"])
        self.assertTrue(result["abstention_reason"].startswith("out_of_scope"))
        self.assertEqual(result["citations"], [])
        self.assertEqual(result["confidence"], "LOW")
        self.assertIn(DISCLAIMER_EN, result["answer"])

    def test_ambiguous_abstention_is_deterministic(self):
        first = run_scenario(EDGE_AMBIGUOUS)
        for _ in range(3):
            self.assertEqual(run_scenario(EDGE_AMBIGUOUS), first)


class TestEdgeFoodDrugBoundary(unittest.TestCase):
    """A product that could be a food (FSSAI Ayurveda Aahara) or a drug
    (D&C Act) — the corpus's Regulation 2(b) exclusion clause answers."""

    def test_routing_sees_both_sides_of_the_boundary(self):
        decision = route_query(EDGE_FOOD_DRUG)
        self.assertEqual(decision["route"], "india_ip")
        self.assertIn("fssai_ayurveda_aahara", decision["matched_areas"])
        self.assertIn("drugs_cosmetics", decision["matched_areas"])

    def test_boundary_answer_cites_the_exclusion_clause(self):
        result = run_scenario(EDGE_FOOD_DRUG)
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        cited = [c["id"] for c in result["citations"]]
        self.assertIn("fss_aahara_regs_2022_reg2b", cited)
        # the quoted definition contains the actual exclusions
        self.assertIn("bhasma", result["answer"])
        self.assertLessEqual(result["confidence_score"], 0.9)


class TestEdgeBiodiversityPatentIntersection(unittest.TestCase):
    def test_intersection_answer_cites_amended_section_6(self):
        result = run_scenario(EDGE_BD_PATENT)
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        cited = {c["id"] for c in result["citations"]}
        self.assertIn("bda_2002_s6", cited)
        self.assertTrue(
            {"patents_act_1970_s3p", "patents_act_1970_s2j"} & cited
        )
        # the quoted text is the post-2023-amendment regime
        self.assertIn("before grant", result["answer"])
        bda = corpus_record("bda_2002_s6")
        self.assertNotIn("before making such application", bda["excerpt"])


class TestEdgeCureClaims(unittest.TestCase):
    def test_cure_claim_question_without_advertise_word_is_routed(self):
        result = run_scenario(EDGE_CURE_CLAIM)
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        cited = {c["id"] for c in result["citations"]}
        self.assertIn("dmr_act_1954_s3", cited)

    def test_non_ip_cure_question_does_not_get_a_forced_answer(self):
        result = run_scenario(EDGE_CURE_NON_IP)
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(result["abstention_reason"].startswith("insufficient_evidence"))


class TestEdgeThinAndUnsupportedEvidence(unittest.TestCase):
    def test_ppv_registration_question_is_honest_not_inflated(self):
        """The corpus holds only the Section 39 farmers'-rights provision for
        PPV&FRA — no registration procedure. The answer must cite the real
        provision without inventing a procedure, and confidence must not be
        HIGH (Phase 3 removed the misleading 'variety registration' tag)."""
        result = run_scenario(EDGE_PPV_THIN)
        self.assertEqual(validate_rag_result(result), [])
        self.assertEqual(result["status"], STATUS_OK)
        self.assertEqual(
            [c["id"] for c in result["citations"]], ["ppvfr_act_2001_s39_1iv"]
        )
        self.assertLess(result["confidence_score"], 0.75)
        record = corpus_record("ppvfr_act_2001_s39_1iv")
        self.assertNotIn("variety registration", record["tags"])
        # no invented procedure in the answer: no fee, no form number
        self.assertNotIn("₹", result["answer"])
        self.assertNotIn("Form PPV", result["answer"])

    def test_out_of_scope_procedure_question_abstains(self):
        result = run_scenario(EDGE_UNSUPPORTED)
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertEqual(result["citations"], [])

    def test_out_of_corpus_international_abstains(self):
        result = run_scenario(EDGE_OUT_OF_CORPUS)
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(
            result["abstention_reason"].startswith("out_of_scope_international")
        )

    def test_weak_evidence_abstains(self):
        result = run_scenario("Can I copyright my yoga video series?")
        self.assertEqual(result["status"], STATUS_ABSTAINED)
        self.assertTrue(
            result["abstention_reason"].startswith("insufficient_evidence")
        )


# ---------------------------------------------------------------------------
# Citation audit (offline half)
# ---------------------------------------------------------------------------


class TestPhase3CitationAudit(unittest.TestCase):
    """Every citation produced by every Phase 3 scenario must map field-exact
    to a stored Phase 1 record. The live half of the audit (URL resolution +
    PDF excerpt re-verification) is run by member3/audit_citations.py."""

    def test_every_scenario_citation_traces_to_stored_record(self):
        audited = 0
        for _name, query in SCENARIOS:
            result = run_scenario(query)
            self.assertEqual(
                validate_citations(result["citations"]), [], query
            )
            stored = {r["id"]: r for r in all_sources()}
            for citation in result["citations"]:
                record = stored[citation["id"]]
                for field in CITATION_FIELDS:
                    self.assertEqual(
                        citation[field], record[field],
                        (query, citation["id"], field),
                    )
                self.assertEqual(citation["source_type"], record["source_type"])
                self.assertTrue(record["verification"]["method"])
                audited += 1
        self.assertGreater(audited, 0)
        # keep the audit meaningful as scenarios evolve
        self.assertGreaterEqual(audited, 10)

    def test_cited_sections_match_stored_sections(self):
        for _name, query in SCENARIOS:
            result = run_scenario(query)
            for citation in result["citations"]:
                record = corpus_record(citation["id"])
                self.assertEqual(citation["section"], record["section"])
                self.assertIn(citation["section"], record["source_name"] + record["section"] + record["section_title"])

    def test_abstentions_never_carry_citations(self):
        for query in (EDGE_AMBIGUOUS, EDGE_UNSUPPORTED, EDGE_OUT_OF_CORPUS,
                      EDGE_CURE_NON_IP):
            result = run_scenario(query)
            self.assertEqual(result["status"], STATUS_ABSTAINED, query)
            self.assertEqual(result["citations"], [], query)


# ---------------------------------------------------------------------------
# Contract validation (M6 interface)
# ---------------------------------------------------------------------------


class TestPhase3Contract(unittest.TestCase):
    def test_every_scenario_matches_rag_result_contract(self):
        for _name, query in SCENARIOS:
            result = run_scenario(query)
            self.assertEqual(
                sorted(result.keys()),
                sorted([
                    "answer", "citations", "confidence", "confidence_score",
                    "abstention", "abstention_reason", "status",
                ]),
                query,
            )
            self.assertEqual(validate_rag_result(result), [], query)
            self.assertIn(result["status"], ("ok", "abstained", "processing_error"))

    def test_citation_structure_exact(self):
        result = run_scenario(GOLDEN_1)
        self.assertTrue(result["citations"])
        for citation in result["citations"]:
            self.assertEqual(sorted(citation.keys()), sorted(CITATION_FIELDS))
            self.assertEqual(validate_citation(citation), [])

    def test_invalid_mapping_is_rejected_not_silent(self):
        citation = {field: corpus_record("gi_act_1999_s2_1e")[field]
                    for field in CITATION_FIELDS}
        citation["excerpt"] = citation["excerpt"][:50] + " fabricated tail"
        self.assertTrue(validate_citation(citation))
        citation2 = {field: corpus_record("gi_act_1999_s2_1e")[field]
                     for field in CITATION_FIELDS}
        citation2["id"] = "bogus_record"
        self.assertTrue(validate_citation(citation2))


# ---------------------------------------------------------------------------
# Hosted-LLM client interface (offline, no network, no fabricated live run)
# ---------------------------------------------------------------------------


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestHostedLLMClient(unittest.TestCase):
    def test_no_credentials_means_no_client(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(get_llm_client())

    def test_env_configuration_builds_client(self):
        env = {
            "M3_LLM_BASE_URL": "https://api.example.test/v1",
            "M3_LLM_API_KEY": "test-key-123",
            "M3_LLM_MODEL": "test-model",
        }
        with mock.patch.dict("os.environ", env, clear=True):
            client = get_llm_client()
        self.assertIsInstance(client, HostedLLM)
        self.assertEqual(client.base_url, "https://api.example.test/v1")
        self.assertEqual(client.model, "test-model")

    def test_complete_builds_openai_compatible_request(self):
        client = HostedLLM("https://api.example.test/v1", "key", "model-x")
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps(
                {"choices": [{"message": {"content": "structured reply"}}]}
            ).encode("utf-8")
            return _FakeResponse(body)

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            text = client.complete("system prompt", "user prompt")
        self.assertEqual(text, "structured reply")
        self.assertEqual(captured["url"], "https://api.example.test/v1/chat/completions")
        self.assertTrue(
            any(v == "Bearer key" for v in captured["headers"].values())
        )
        self.assertEqual(captured["payload"]["model"], "model-x")
        self.assertEqual(captured["payload"]["temperature"], 0.0)
        self.assertEqual(
            [m["role"] for m in captured["payload"]["messages"]],
            ["system", "user"],
        )

    def test_http_error_maps_to_llmerror(self):
        client = HostedLLM("https://api.example.test/v1", "key", "model-x")

        def fake_urlopen(request, timeout=None):
            raise urllib.error.HTTPError(
                request.full_url, 503, "service unavailable", None, io.BytesIO(b"")
            )

        with mock.patch("urllib.request.urlopen", fake_urlopen):
            with self.assertRaises(LLMError):
                client.complete("s", "u")

    def test_pipeline_maps_llm_failure_to_processing_error(self):
        class FailingLLM:
            def complete(self, system, user):
                raise LLMError("HTTP 503 from hosted LLM")

        result = answer_india_question(GOLDEN_2, llm=FailingLLM())
        self.assertEqual(result["status"], STATUS_PROCESSING_ERROR)
        self.assertFalse(result["abstention"])
        self.assertEqual(result["citations"], [])
        self.assertEqual(validate_rag_result(result), [])


# ---------------------------------------------------------------------------
# TKDL pointer-only sweep (no fabricated TKDL content anywhere)
# ---------------------------------------------------------------------------


class TestTKDLPointerOnly(unittest.TestCase):
    def test_patent_scenario_tkdl_is_pointer_only(self):
        result = run_scenario(GOLDEN_1)
        self.assertIn("TKDL", result["answer"])
        self.assertIn("https://tkdl.res.in", result["answer"])
        self.assertIn("patent offices", result["answer"])
        # no TKDL content claims: no counts, no formulation lists, no access detail
        for forbidden in ("400,000", "370", "formulations in TKDL", "subscribe"):
            self.assertNotIn(forbidden, result["answer"])
        self.assertNotIn("tkdl", {c["id"] for c in result["citations"]})

    def test_non_tk_scenario_does_not_mention_tkdl(self):
        result = run_scenario(GOLDEN_2)
        self.assertNotIn("TKDL", result["answer"])

    def test_corpus_has_no_tkdl_record_or_mandate_claim(self):
        ids = {r["id"] for r in all_sources()}
        self.assertNotIn("tkdl", ids)
        self.assertNotIn("patents_rules_2024", ids)
        for record in all_sources():
            blob = (record["excerpt"] + record["section_title"]).lower()
            self.assertNotIn("tkdl", blob, record["id"])


# ---------------------------------------------------------------------------
# Determinism of the Phase 3 scenario set
# ---------------------------------------------------------------------------


class TestPhase3Determinism(unittest.TestCase):
    def test_all_scenarios_deterministic(self):
        for _name, query in SCENARIOS:
            first = run_scenario(query)
            self.assertEqual(run_scenario(query), first, query)


if __name__ == "__main__":
    unittest.main()
