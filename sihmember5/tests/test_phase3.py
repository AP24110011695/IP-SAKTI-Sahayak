from __future__ import annotations

import json
import subprocess
import sys
import unittest

from member5.corpus import SYSTEM_RIGHTS, load_sources
from member5.guidance import CITATION_FIELD_SET, guide, route_query, validate_citations
from member5.llm import DeterministicEvidenceClient


class Phase3StandaloneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = DeterministicEvidenceClient()

    def test_patent_and_trademark_edge_case_abstains_without_mixing(self) -> None:
        result = guide(
            "How do I protect both the patent and trademark for my Ayurvedic product internationally?",
            client=self.client,
        )
        self.assertTrue(result["abstention"])
        self.assertEqual([], result["citations"])
        self.assertIn("multiple IP rights", result["abstention_reason"])

    def test_patent_trademark_and_design_edge_case_abstains(self) -> None:
        result = guide(
            "I need patent, trademark, and industrial design protection internationally.",
            client=self.client,
        )
        self.assertTrue(result["abstention"])
        self.assertEqual("abstained", result["status"])
        self.assertEqual("", result["answer"])

    def test_ambiguous_international_ip_wording_abstains(self) -> None:
        result = guide(
            "How can I protect my Ayurvedic product internationally?",
            client=self.client,
        )
        self.assertTrue(result["abstention"])
        self.assertIn("No sufficiently relevant evidence", result["abstention_reason"])

    def test_unsupported_country_law_abstains(self) -> None:
        result = guide(
            "What does Brazilian patent law require?",
            client=self.client,
        )
        self.assertTrue(result["abstention"])
        self.assertIn("Domestic Brazil law", result["abstention_reason"])

    def test_export_market_access_is_documented_as_unsupported(self) -> None:
        result = guide(
            "What approvals and labels do I need to export an Ayurvedic supplement to Japan?",
            client=self.client,
        )
        self.assertTrue(result["abstention"])
        self.assertIn("market-access", result["abstention_reason"])
        self.assertEqual([], result["citations"])

    def test_mixed_india_and_international_query_abstains(self) -> None:
        result = guide(
            "Compare the patent filing procedure in India with the international route.",
            client=self.client,
        )
        self.assertTrue(result["abstention"])
        self.assertIn("India-specific", result["abstention_reason"])

    def test_all_success_scenario_citations_pass_complete_audit(self) -> None:
        queries = (
            "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?",
            "I want to register my Ayurvedic brand name internationally.",
            "How can I protect my packaging as an industrial design internationally?",
            "What does TRIPS Article 27.3(b) say about plant patentability?",
            "What does the Nagoya Protocol say about benefit-sharing?",
        )
        source_index = {source["id"]: source for source in load_sources()}
        for query in queries:
            with self.subTest(query=query):
                result = guide(query, client=self.client)
                self.assertEqual("ok", result["status"])
                self.assertTrue(validate_citations(result["citations"]))
                for citation in result["citations"]:
                    self.assertEqual(CITATION_FIELD_SET, set(citation))
                    source = source_index[citation["id"]]
                    for field in CITATION_FIELD_SET:
                        self.assertEqual(source[field], citation[field])

    def test_final_route_outputs_obey_system_right_mapping(self) -> None:
        cases = (
            ("How do I file a patent internationally?", "patent", "PCT"),
            ("How do I protect a trademark internationally?", "trademark", "Madrid"),
            ("How do I protect an industrial design internationally?", "industrial_design", "Hague"),
        )
        source_index = {source["id"]: source for source in load_sources()}
        for query, expected_right, expected_system in cases:
            with self.subTest(query=query):
                decision = route_query(query)
                result = guide(query, client=self.client)
                self.assertEqual(expected_right, decision.ip_right)
                self.assertEqual(expected_system, decision.system)
                self.assertEqual("ok", result["status"])
                route_systems = {
                    source_index[item["id"]]["system"]
                    for item in result["citations"]
                    if source_index[item["id"]]["system"] in SYSTEM_RIGHTS
                }
                self.assertEqual({expected_system}, route_systems)

    def test_every_result_obeys_exact_m6_types_and_status_values(self) -> None:
        results = (
            guide("How do I file a patent internationally?", client=self.client),
            guide("How is spacecraft lease depreciation taxed?", client=self.client),
        )
        allowed_statuses = {"ok", "abstained", "processing_error"}
        for result in results:
            self.assertEqual(
                {"answer", "citations", "confidence", "confidence_score", "abstention", "abstention_reason", "status"},
                set(result),
            )
            self.assertIsInstance(result["answer"], str)
            self.assertIsInstance(result["citations"], list)
            self.assertIn(result["confidence"], {"HIGH", "MEDIUM", "LOW"})
            self.assertIsInstance(result["confidence_score"], float)
            self.assertGreaterEqual(result["confidence_score"], 0.0)
            self.assertLessEqual(result["confidence_score"], 1.0)
            self.assertIsInstance(result["abstention"], bool)
            self.assertIn(result["status"], allowed_statuses)

    def test_cli_runs_standalone_and_returns_contract(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "member5", "How do I register my trademark internationally?"],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual("ok", result["status"])
        self.assertEqual("madrid-system-overview", result["citations"][0]["id"])


if __name__ == "__main__":
    unittest.main()

