"""Member 4 — Phase 1 test suite.

Run from the m4_abs directory (or MEMBER_4 root with m4_abs on the path):

    python -m unittest discover -s m4_abs/tests -t m4_abs -v

Covers the Phase 1 requirements: complete metadata on every record, real
URLs restricted to official domains, section/article/rule markers, sane
verbatim excerpts, deterministic records and retrieval, TKDL pointer-only
safety, golden ABS scenario support, trademark false-negative guard, and
out-of-corpus abstention support.
"""

import datetime
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import corpus  # noqa: E402
import retrieval  # noqa: E402

RECORDS = corpus.SOURCE_RECORDS

REQUIRED_FIELDS = (
    "id", "source_name", "source_type", "section", "excerpt", "url",
    "effective_date", "jurisdiction", "scope", "keywords",
    "tkdl_pointer_record", "provenance",
)

VALID_SOURCE_TYPES = {
    "statute", "amendment_act", "subordinate_legislation", "treaty",
    "official_website",
}
LEGAL_SOURCE_TYPES = VALID_SOURCE_TYPES - {"official_website"}
VALID_JURISDICTIONS = {"India", "International"}

# Domains verified during Phase 1; any new URL must be added here together
# with its verification evidence, never silently.
OFFICIAL_URL_DOMAINS = {
    "megbiodiversity.nic.in",   # Meghalaya Biodiversity Board (NIC govt domain)
    "egazette.gov.in",          # Gazette of India (official e-Gazette)
    "www.nbaindia.nic.in",      # National Biodiversity Authority (NIC domain)
    "www.cbd.int",              # CBD Secretariat
    "tkdl.res.in",              # TKDL official site
}

EXPECTED_IDS = [f"M4-SRC-{n:03d}" for n in range(1, 11)]

# Key phrases that must appear in each record's excerpt - catches silent
# corruption of the verified legal text (e.g. wrong section, wrong article).
EXCERPT_MARKERS = {
    "M4-SRC-001": ["National Biodiversity Authority", "biological resource occurring in India"],
    "M4-SRC-002": [
        "register with the National Biodiversity Authority",
        "before grant of such intellectual property rights",
        "at the time of commercialisation",
    ],
    "M4-SRC-003": [
        "prior intimation to the concerned State Biodiversity Board",
        "codified traditional knowledge",
        "registered AYUSH practitioners",
    ],
    "M4-SRC-004": ["benefit sharing", "fair and equitable sharing of benefits"],
    "M4-SRC-005": ["Form 1", "Form 2", "web portal of the Authority"],
    "M4-SRC-006": ["traditional knowledge associated with genetic resources", "mutually agreed terms"],
    "M4-SRC-007": ["prior informed consent"],
    "M4-SRC-008": ["prior and informed consent or approval and involvement"],
    "M4-SRC-009": ["knowledge, innovations and practices of indigenous and local communities"],
    "M4-SRC-010": [
        "Representative Database of Ayurvedic, Unani, Siddha and Sowarigpa",
        "available to Patent Offices only under TKDL Access Agreement",
    ],
}


class CorpusStructureTests(unittest.TestCase):
    def test_corpus_size_within_cap(self):
        # MEMBER_4.md Phase 1 cap: roughly 6-10 short curated excerpts.
        self.assertGreaterEqual(len(RECORDS), 6)
        self.assertLessEqual(len(RECORDS), 10)

    def test_ids_unique_and_order_deterministic(self):
        ids = corpus.record_ids()
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, EXPECTED_IDS)
        self.assertEqual([r["id"] for r in RECORDS], EXPECTED_IDS)

    def test_every_record_has_complete_metadata(self):
        for record in RECORDS:
            for field in REQUIRED_FIELDS:
                self.assertIn(field, record, f"{record.get('id')} missing {field}")
            for field in ("id", "source_name", "source_type", "excerpt", "url",
                          "jurisdiction", "scope"):
                self.assertTrue(str(record[field]).strip(), f"{record['id']}.{field} empty")
            self.assertIsInstance(record["keywords"], list)
            self.assertTrue(record["keywords"], f"{record['id']} has no keywords")
            self.assertIsInstance(record["tkdl_pointer_record"], bool)
            self.assertIsInstance(record["provenance"], dict)

    def test_source_types_and_jurisdictions_valid(self):
        for record in RECORDS:
            self.assertIn(record["source_type"], VALID_SOURCE_TYPES, record["id"])
            self.assertIn(record["jurisdiction"], VALID_JURISDICTIONS, record["id"])

    def test_legal_records_have_section_and_effective_date(self):
        for record in RECORDS:
            if record["source_type"] in LEGAL_SOURCE_TYPES:
                self.assertTrue(
                    record["section"] and record["section"].strip(),
                    f"{record['id']} legal record missing section/article/rule marker",
                )
                self.assertTrue(
                    record["effective_date"],
                    f"{record['id']} legal record missing effective_date",
                )
                try:
                    datetime.date.fromisoformat(record["effective_date"])
                except ValueError:
                    self.fail(f"{record['id']} effective_date not ISO: {record['effective_date']}")

    def test_provenance_present_on_every_record(self):
        for record in RECORDS:
            prov = record["provenance"]
            for key in ("verified_on", "verification_method", "document_identity"):
                self.assertTrue(prov.get(key, "").strip(), f"{record['id']}.provenance.{key} empty")
            self.assertEqual(prov["verified_on"], corpus.VERIFIED_ON)
            # disclosure of jurisdiction/scope boundaries
            self.assertTrue(record["scope"].strip())

    def test_urls_are_https_on_official_domains(self):
        for record in RECORDS:
            url = record["url"]
            self.assertTrue(url.startswith("https://"), f"{record['id']} URL not https")
            domain = url.split("/")[2]
            self.assertIn(domain, OFFICIAL_URL_DOMAINS, f"{record['id']} unexpected domain {domain}")

    def test_excerpts_nonempty_and_sane(self):
        for record in RECORDS:
            excerpt = record["excerpt"]
            self.assertTrue(excerpt.strip(), f"{record['id']} empty excerpt")
            self.assertEqual(excerpt, excerpt.strip(), f"{record['id']} excerpt has stray whitespace")
            self.assertNotIn("\n", excerpt, f"{record['id']} excerpt contains raw newline")
            self.assertGreaterEqual(len(excerpt), 60, f"{record['id']} excerpt too short")
            self.assertLessEqual(len(excerpt), 1200, f"{record['id']} excerpt too long")
            self.assertTrue(re.search(r"[A-Za-z]{3}", excerpt), f"{record['id']} excerpt has no words")

    def test_excerpt_key_phrases_unchanged(self):
        for record in RECORDS:
            for marker in EXCERPT_MARKERS[record["id"]]:
                self.assertIn(marker, record["excerpt"], f"{record['id']} lost marker: {marker}")

    def test_corpus_covers_required_categories(self):
        types = {r["source_type"] for r in RECORDS}
        sections = " ".join(r["section"] or "" for r in RECORDS)
        self.assertIn("statute", types)                      # BD Act
        self.assertIn("amendment_act", types)                # 2023 Amendment
        self.assertIn("subordinate_legislation", types)      # 2024 Rules
        self.assertIn("treaty", types)                       # Nagoya / CBD
        self.assertIn("official_website", types)             # TKDL pointer
        self.assertIn("Section 7", sections)
        self.assertIn("Article 6", sections)
        self.assertIn("Article 8(j)", sections)

    def test_jurisdictions_kept_distinct(self):
        for record in RECORDS:
            if record["source_type"] == "treaty":
                self.assertEqual(record["jurisdiction"], "International", record["id"])
            else:
                self.assertEqual(record["jurisdiction"], "India", record["id"])


class CitationShapeTests(unittest.TestCase):
    def test_to_citation_matches_plan_contract(self):
        # Plan.md section 7 Citation: id, source_name, source_type, section,
        # excerpt, url, effective_date.
        for record in RECORDS:
            citation = corpus.to_citation(record)
            self.assertEqual(
                set(citation.keys()),
                {"id", "source_name", "source_type", "section", "excerpt", "url", "effective_date"},
            )
            self.assertEqual(citation["url"], record["url"])
            self.assertEqual(citation["section"], record["section"])


class TkdlSafetyTests(unittest.TestCase):
    """TKDL constraint: pointer/description only; no fabricated content."""

    def test_exactly_one_tkdl_pointer_record(self):
        flagged = [r for r in RECORDS if r["tkdl_pointer_record"]]
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged[0]["id"], corpus.TKDL_RECORD_ID)

    def test_tkdl_record_is_official_website_pointer(self):
        record = corpus.get_record(corpus.TKDL_RECORD_ID)
        self.assertEqual(record["source_type"], "official_website")
        self.assertEqual(record["url"], "https://tkdl.res.in/")
        self.assertIsNone(record["section"])
        self.assertIn("POINTER ONLY", record["scope"])
        self.assertIn("tkdl.res.in", record["pointer_guidance"])

    def test_tkdl_excerpt_contains_no_numbers_or_counts(self):
        record = corpus.get_record(corpus.TKDL_RECORD_ID)
        digits = re.findall(r"\d", record["excerpt"])
        self.assertEqual(digits, [], f"TKDL excerpt contains digits (counts?): {digits}")
        for banned in ("TKDL says", "TKDL contains", "TKDL has", "records of formulations"):
            self.assertNotIn(banned.lower(), record["excerpt"].lower())

    def test_tkdl_pointer_guidance_forbids_fabrication(self):
        record = corpus.get_record(corpus.TKDL_RECORD_ID)
        guidance = record["pointer_guidance"].lower()
        self.assertIn("never", guidance)
        self.assertIn("tkdl says", guidance)  # explicitly banned there
        self.assertIn("patent", guidance)     # consult patent office/examiner

    def test_no_other_record_claims_tkdl_content(self):
        for record in RECORDS:
            if record["id"] == corpus.TKDL_RECORD_ID:
                continue
            blob = " ".join(
                str(v) for k, v in record.items() if k not in ("provenance", "keywords")
            ).lower()
            self.assertNotIn("tkdl", blob, f"{record['id']} unexpectedly mentions TKDL")
            self.assertNotIn("traditional knowledge digital library", blob, record["id"])


class UrlVerificationReportTests(unittest.TestCase):
    """The shipped verification_report.json must cover every corpus URL."""

    REPORT_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "verification_report.json",
    )

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(cls.REPORT_PATH):
            raise AssertionError(
                "verification_report.json missing - run: python m4_abs/verify_urls.py"
            )
        with open(cls.REPORT_PATH, encoding="utf-8") as fh:
            cls.report = json.load(fh)

    def test_report_covers_every_corpus_url_successfully(self):
        by_url = {r["url"]: r for r in self.report["results"]}
        for record in RECORDS:
            self.assertIn(record["url"], by_url, f"{record['id']} URL not in verification report")
            self.assertTrue(by_url[record["url"]]["ok"], f"{record['id']} URL did not verify")

    def test_report_is_current_with_corpus(self):
        self.assertEqual(self.report["corpus_version"], corpus.CORPUS_VERSION)


class RetrievalTests(unittest.TestCase):
    GOLDEN_QUERY = (
        "I want to commercialise a formulation using a plant collected in "
        "India - what approvals do I need?"
    )
    TRADEMARK_QUERY = "How do I register a trademark for my herbal tea brand in India?"
    OUT_OF_CORPUS_QUERY = (
        "How do I export herbal medicinal products to the EU - what EU "
        "registration do I need?"
    )

    def test_golden_abs_scenario_retrieves_relevant_records(self):
        results = retrieval.retrieve(self.GOLDEN_QUERY)
        ids = retrieval.retrieved_ids(results)
        self.assertTrue(ids, "golden ABS scenario retrieved no evidence")
        self.assertIn("M4-SRC-003", ids, "amended section 7 (SBB prior intimation) not retrieved")
        self.assertGreaterEqual(len(ids), 2, "golden scenario should surface several ABS records")
        self.assertEqual(ids[0], "M4-SRC-003", "section 7 should rank first for commercialisation")

    def test_golden_scenario_records_are_abs_not_patent_records(self):
        results = retrieval.retrieve(self.GOLDEN_QUERY)
        for item in results:
            record = item["record"]
            self.assertEqual(record["jurisdiction"], "India")
            # no record retrieved by the golden query may be the TKDL pointer
            self.assertFalse(record["tkdl_pointer_record"])

    def test_trademark_only_query_returns_no_abs_evidence(self):
        self.assertEqual(retrieval.retrieve(self.TRADEMARK_QUERY), [])

    def test_trademark_query_fails_domain_or_score_gate(self):
        # Document *why* the trademark query is rejected: it may pass the
        # domain gate (herbal) but must stay below the evidence threshold.
        self.assertTrue(retrieval.is_domain_query(self.TRADEMARK_QUERY))
        best = max(
            (retrieval.score_record(retrieval._tokenize(self.TRADEMARK_QUERY), r) for r in RECORDS),
            default=0.0,
        )
        self.assertLess(best, retrieval.MIN_SCORE)

    def test_out_of_corpus_abs_query_returns_no_evidence(self):
        self.assertEqual(retrieval.retrieve(self.OUT_OF_CORPUS_QUERY), [])

    def test_nagoya_and_tk_queries_retrieve_treaty_and_pointer(self):
        nagoya = retrieval.retrieve("Nagoya Protocol prior informed consent for genetic resources")
        self.assertIn("M4-SRC-007", retrieval.retrieved_ids(nagoya))
        tk = retrieval.retrieve(
            "traditional knowledge of indigenous communities and genetic resources"
        )
        self.assertIn("M4-SRC-008", retrieval.retrieved_ids(tk))
        prior_art = retrieval.retrieve("is my ayurvedic traditional knowledge prior art")
        self.assertIn(corpus.TKDL_RECORD_ID, retrieval.retrieved_ids(prior_art))

    def test_benefit_sharing_query_retrieves_section_21(self):
        results = retrieval.retrieve("how is benefit sharing determined for approvals")
        self.assertIn("M4-SRC-004", retrieval.retrieved_ids(results))

    def test_retrieval_is_deterministic(self):
        first = retrieval.retrieve(self.GOLDEN_QUERY)
        second = retrieval.retrieve(self.GOLDEN_QUERY)
        self.assertEqual(retrieval.retrieved_ids(first), retrieval.retrieved_ids(second))
        self.assertEqual([r["score"] for r in first], [r["score"] for r in second])

    def test_retrieval_ordering_and_topk(self):
        results = retrieval.retrieve(
            "NBA approval commercial utilisation formulation intellectual property "
            "benefit sharing form 2 web portal"
        )
        self.assertLessEqual(len(results), 5)
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_gibberish_returns_no_evidence(self):
        self.assertEqual(retrieval.retrieve("xyzzy plugh zorkmid"), [])
        self.assertEqual(retrieval.retrieve(""), [])

    def test_scores_are_deterministic_floats(self):
        tokens = retrieval._tokenize(self.GOLDEN_QUERY)
        for record in RECORDS:
            score = retrieval.score_record(tokens, record)
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
