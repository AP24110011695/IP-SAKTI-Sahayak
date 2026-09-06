from __future__ import annotations

import copy
import unittest

from member5.corpus import load_sources
from member5.guidance import (
    CITATION_FIELDS,
    confidence_for,
    guide,
    route_query,
    select_evidence,
    validate_citations,
)
from member5.llm import DeterministicEvidenceClient, GenerationError


class StaticClient:
    def __init__(self, output):
        self.output = output

    def generate(self, **kwargs):
        return self.output


class FailingClient:
    def generate(self, **kwargs):
        raise GenerationError("Hosted provider unavailable.")


class Phase2GuidanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = DeterministicEvidenceClient()

    def test_patent_golden_scenario(self) -> None:
        result = guide(
            "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?",
            client=self.client,
        )
        self.assertEqual("ok", result["status"])
        self.assertFalse(result["abstention"])
        self.assertIn("Patent Cooperation Treaty (PCT)", result["answer"])
        self.assertNotIn("Madrid", result["answer"])
        self.assertNotIn("Hague", result["answer"])
        self.assertEqual("HIGH", result["confidence"])
        self.assertTrue(validate_citations(result["citations"]))
        self.assertTrue(all(citation["id"].startswith("pct-") for citation in result["citations"]))
        self.assertNotIn("Indian Patent Office", result["answer"])

    def test_international_trademark_uses_madrid(self) -> None:
        result = guide(
            "I want to register my Ayurvedic brand name internationally.",
            client=self.client,
        )
        self.assertEqual("ok", result["status"])
        self.assertIn("Madrid System", result["answer"])
        self.assertNotIn("Patent Cooperation Treaty", result["answer"])
        self.assertEqual(["madrid-system-overview"], [item["id"] for item in result["citations"]])

    def test_industrial_design_uses_hague(self) -> None:
        result = guide(
            "How can I protect my packaging as an industrial design internationally?",
            client=self.client,
        )
        self.assertEqual("ok", result["status"])
        self.assertIn("Hague System", result["answer"])
        self.assertEqual(["hague-system-overview"], [item["id"] for item in result["citations"]])

    def test_out_of_corpus_abstains_without_fabrication(self) -> None:
        result = guide("How is spacecraft lease depreciation taxed?", client=self.client)
        self.assertEqual("abstained", result["status"])
        self.assertTrue(result["abstention"])
        self.assertEqual("", result["answer"])
        self.assertEqual([], result["citations"])

    def test_india_jurisdiction_is_rejected(self) -> None:
        result = guide("How do I file a patent?", jurisdiction="India", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("International jurisdiction only", result["abstention_reason"])

    def test_explicit_india_only_query_is_not_answered_as_international(self) -> None:
        result = guide("What is the patent filing procedure in India?", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("India-specific", result["abstention_reason"])

    def test_international_query_does_not_become_india_guidance(self) -> None:
        result = guide("How do I file a patent internationally?", client=self.client)
        self.assertEqual("ok", result["status"])
        self.assertNotIn("India-specific", result["answer"])

    def test_requested_region_is_preserved_for_route_guidance(self) -> None:
        decision = route_query("Can I use the PCT for a patent in the United States?")
        self.assertTrue(decision.supported)
        self.assertEqual("United States", decision.region)

    def test_unsupported_country_specific_market_access_abstains(self) -> None:
        result = guide("How do I export an Ayurvedic supplement to the USA?", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("market-access", result["abstention_reason"])

    def test_unsupported_country_specific_law_abstains(self) -> None:
        result = guide("What does United States patent law require?", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("Domestic United States law", result["abstention_reason"])

    def test_citation_integrity_rejects_unknown_id(self) -> None:
        source = load_sources()[0]
        citation = {field: source[field] for field in CITATION_FIELDS}
        citation["id"] = "invented-source"
        self.assertFalse(validate_citations([citation]))

    def test_citation_integrity_rejects_fabricated_url(self) -> None:
        source = load_sources()[0]
        citation = {field: source[field] for field in CITATION_FIELDS}
        citation["url"] = "https://example.invalid/fake"
        self.assertFalse(validate_citations([citation]))

    def test_citation_integrity_rejects_incorrect_section(self) -> None:
        source = load_sources()[0]
        citation = {field: source[field] for field in CITATION_FIELDS}
        citation["section"] = "Article 999"
        self.assertFalse(validate_citations([citation]))

    def test_citation_integrity_rejects_altered_metadata(self) -> None:
        source = load_sources()[0]
        citation = {field: source[field] for field in CITATION_FIELDS}
        citation["source_name"] = "Altered source"
        self.assertFalse(validate_citations([citation]))

    def test_citation_integrity_rejects_missing_field(self) -> None:
        source = load_sources()[0]
        citation = {field: source[field] for field in CITATION_FIELDS}
        citation.pop("effective_date")
        self.assertFalse(validate_citations([citation]))

    def test_citation_integrity_rejects_altered_excerpt(self) -> None:
        source = load_sources()[0]
        citation = {field: source[field] for field in CITATION_FIELDS}
        citation["excerpt"] = "Invented wording that never appeared in the source."
        self.assertFalse(validate_citations([citation]))

    def test_citation_integrity_rejects_altered_effective_date(self) -> None:
        source = next(item for item in load_sources() if item["effective_date"])
        citation = {field: source[field] for field in CITATION_FIELDS}
        citation["effective_date"] = "1900-01-01"
        self.assertFalse(validate_citations([citation]))

    def test_citation_integrity_rejects_mismatched_source_fields(self) -> None:
        first, second = load_sources()[0], load_sources()[1]
        citation = {field: first[field] for field in CITATION_FIELDS}
        citation["url"] = second["url"]
        self.assertFalse(validate_citations([citation]))

    def test_confidence_is_deterministic_and_evidence_based(self) -> None:
        decision = route_query("How do I file a patent internationally?")
        evidence = select_evidence(decision)
        strong = confidence_for(decision, evidence)
        self.assertEqual(strong, confidence_for(decision, evidence))
        weak_decision = route_query("patent")
        weak = confidence_for(weak_decision, [])
        self.assertGreater(strong[1], weak[1])
        self.assertEqual("LOW", weak[0])

    def test_weak_query_abstains(self) -> None:
        result = guide("patent", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("too weak", result["abstention_reason"])

    def test_wrong_ip_right_system_mapping_abstains_before_generation(self) -> None:
        result = guide("Can Madrid be used to file a patent?", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("Unsafe mapping", result["abstention_reason"])

    def test_pct_named_for_a_trademark_abstains(self) -> None:
        result = guide("Can PCT register my brand internationally?", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("Unsafe mapping", result["abstention_reason"])

    def test_hague_named_for_a_trademark_abstains(self) -> None:
        result = guide("Can Hague register a trademark internationally?", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("Unsafe mapping", result["abstention_reason"])

    def test_madrid_named_for_a_design_abstains(self) -> None:
        result = guide("Can Madrid protect my bottle design internationally?", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertIn("Unsafe mapping", result["abstention_reason"])

    def test_travel_trips_wording_abstains_instead_of_trips_route(self) -> None:
        result = guide("How long are business trips abroad?", client=self.client)
        self.assertTrue(result["abstention"])
        self.assertNotIn("TRIPS", result["answer"])

    def test_patent_query_with_travel_trips_word_uses_pct(self) -> None:
        result = guide(
            "Can I patent my fishing trips booking app internationally?",
            client=self.client,
        )
        self.assertEqual("ok", result["status"])
        self.assertTrue(all(citation["id"].startswith("pct-") for citation in result["citations"]))

    def test_lowercase_trips_agreement_still_routes_to_trips(self) -> None:
        result = guide(
            "What does the trips agreement say about excluding plants from patentability?",
            client=self.client,
        )
        self.assertEqual("ok", result["status"])
        self.assertEqual(["trips-art-27-3-b"], [item["id"] for item in result["citations"]])

    def test_trips_scenario_uses_trips_evidence(self) -> None:
        result = guide(
            "What does TRIPS Article 27.3(b) say about plant patentability?",
            client=self.client,
        )
        self.assertEqual("ok", result["status"])
        self.assertEqual(["trips-art-27-3-b"], [item["id"] for item in result["citations"]])
        self.assertIn("Article 27.3(b)", result["answer"])

    def test_genetic_resources_framework_wording_reaches_cbd_route(self) -> None:
        result = guide(
            "What international framework covers access to genetic resources?",
            client=self.client,
        )
        self.assertEqual("ok", result["status"])
        self.assertEqual(
            {"cbd-art-15-1", "cbd-art-15-5", "nagoya-art-6-1"},
            {item["id"] for item in result["citations"]},
        )

    def test_bare_design_wording_routes_to_hague_with_region(self) -> None:
        result = guide("How do I register a design in the European Union?", client=self.client)
        self.assertEqual("ok", result["status"])
        self.assertEqual(["hague-system-overview"], [item["id"] for item in result["citations"]])
        self.assertIn("European Union", result["answer"])

    def test_wrong_system_in_generated_answer_is_rejected(self) -> None:
        client = StaticClient({"answer": "Use the Madrid System for this patent.", "citation_ids": ["pct-system-overview"]})
        result = guide("How do I file a patent internationally?", client=client)
        self.assertTrue(result["abstention"])
        self.assertIn("safety guardrail", result["abstention_reason"])

    def test_malformed_model_output_abstains(self) -> None:
        result = guide(
            "How do I file a patent internationally?",
            client=StaticClient({"unexpected": "shape"}),
        )
        self.assertTrue(result["abstention"])
        self.assertEqual("abstained", result["status"])

    def test_unknown_model_citation_id_abstains(self) -> None:
        result = guide(
            "How do I file a patent internationally?",
            client=StaticClient({"answer": "Use PCT.", "citation_ids": ["fake"]}),
        )
        self.assertTrue(result["abstention"])

    def test_model_invented_deadline_is_rejected(self) -> None:
        result = guide(
            "How do I file a patent internationally?",
            client=StaticClient({"answer": "Use PCT and act within 99 months.", "citation_ids": ["pct-system-overview"]}),
        )
        self.assertTrue(result["abstention"])
        self.assertIn("safety guardrail", result["abstention_reason"])

    def test_model_invented_treaty_article_is_rejected(self) -> None:
        result = guide(
            "How do I file a patent internationally?",
            client=StaticClient(
                {"answer": "Under PCT Article 33 the international search report is prepared.", "citation_ids": ["pct-system-overview"]}
            ),
        )
        self.assertTrue(result["abstention"])
        self.assertIn("safety guardrail", result["abstention_reason"])

    def test_grounded_article_mention_is_accepted(self) -> None:
        result = guide(
            "What does TRIPS say about plant patentability?",
            client=StaticClient(
                {
                    "answer": "TRIPS Article 27.3(b) permits Members to exclude plants and animals other than micro-organisms from patentability.",
                    "citation_ids": ["trips-art-27-3-b"],
                }
            ),
        )
        self.assertEqual("ok", result["status"])

    def test_provider_failure_returns_processing_error(self) -> None:
        result = guide("How do I file a patent internationally?", client=FailingClient())
        self.assertTrue(result["abstention"])
        self.assertEqual("processing_error", result["status"])

    def test_hindi_patent_uses_same_pct_evidence(self) -> None:
        english = guide("How do I file a patent internationally?", client=self.client)
        hindi = guide(
            "मैं अपनी नई आयुर्वेदिक दवा के लिए भारत के बाहर पेटेंट दाखिल करना चाहता हूँ।",
            language="hi",
            client=self.client,
        )
        self.assertEqual("ok", hindi["status"])
        self.assertIn("पेटेंट सहयोग संधि (PCT)", hindi["answer"])
        self.assertIn("कानूनी सलाह नहीं", hindi["answer"])
        self.assertEqual(
            [item["id"] for item in english["citations"]],
            [item["id"] for item in hindi["citations"]],
        )

    def test_hindi_trademark_uses_same_madrid_evidence(self) -> None:
        english = guide("I want to register my brand internationally.", client=self.client)
        hindi = guide(
            "मैं अपना आयुर्वेदिक ब्रांड अंतरराष्ट्रीय रूप से पंजीकृत करना चाहता हूँ।",
            language="hi",
            client=self.client,
        )
        self.assertEqual("ok", hindi["status"])
        self.assertIn("मैड्रिड सिस्टम", hindi["answer"])
        self.assertEqual(
            [item["id"] for item in english["citations"]],
            [item["id"] for item in hindi["citations"]],
        )

    def test_hindi_design_uses_same_hague_evidence(self) -> None:
        english = guide("How can I protect an industrial design internationally?", client=self.client)
        hindi = guide(
            "मैं अपने उत्पाद का डिज़ाइन अंतरराष्ट्रीय स्तर पर पंजीकृत करना चाहता हूँ।",
            language="hi",
            client=self.client,
        )
        self.assertEqual("ok", hindi["status"])
        self.assertIn("हेग सिस्टम", hindi["answer"])
        self.assertIn("कानूनी सलाह नहीं", hindi["answer"])
        self.assertEqual(
            [item["id"] for item in english["citations"]],
            [item["id"] for item in hindi["citations"]],
        )

    def test_repeated_request_is_stable(self) -> None:
        kwargs = {"client": self.client}
        query = "I want to register my brand internationally."
        self.assertEqual(guide(query, **kwargs), guide(query, **kwargs))

    def test_result_matches_exact_rag_contract(self) -> None:
        result = guide("How do I file a patent internationally?", client=self.client)
        self.assertEqual(
            {"answer", "citations", "confidence", "confidence_score", "abstention", "abstention_reason", "status"},
            set(result),
        )


if __name__ == "__main__":
    unittest.main()

