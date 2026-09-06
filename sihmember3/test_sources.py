"""Phase 1 tests for Member 3 — India Source Foundation.

Verifies (MEMBER_3.md Phase 1):
* every source record has complete, well-formed metadata;
* India jurisdiction is explicit and exclusive on every record;
* sections/rules are recorded and correctly named for the golden scenarios;
* URL status/verification is recorded for every record (live spot-checks were
  performed on 2026-09-06 with member3/verify_urls.py; unit tests stay offline);
* the corpus is real and internally consistent (no placeholder text, unique
  ids, https URLs);
* golden scenario 1 (Section 3(p) patent question) and scenario 2 (GI
  registration question) are supported by real source records;
* at least one deliberately out-of-corpus topic returns no matches, so the
  corpus is intentionally limited and abstention-ready for Phase 2.

Run with:  python -m unittest member3.test_sources -v
"""

import unittest

from member3 import (
    JURISDICTION,
    OUT_OF_CORPUS_TOPICS,
    SCOPE_AREAS,
    all_sources,
    find_sources,
    validate_corpus,
    validate_source_record,
)


class TestCorpusMetadata(unittest.TestCase):
    """Metadata completeness and well-formedness for every record."""

    def test_corpus_size_in_expected_band(self):
        sources = all_sources()
        self.assertGreaterEqual(len(sources), 10, "corpus too small for the scope")
        self.assertLessEqual(len(sources), 15, "corpus exceeds the agreed cap")

    def test_every_record_validates(self):
        problems = validate_corpus()
        self.assertEqual(problems, {}, "records with metadata problems")

    def test_all_priority_scopes_covered(self):
        areas = {record["scope_area"] for record in all_sources()}
        for area in SCOPE_AREAS:
            self.assertIn(area, areas, "scope area missing from corpus: %s" % area)

    def test_india_jurisdiction_explicit_everywhere(self):
        for record in all_sources():
            self.assertEqual(record["jurisdiction"], "India", record["id"])
            self.assertNotEqual(record["jurisdiction"].lower(), "international")

    def test_ids_unique_and_snake_case(self):
        ids = [record["id"] for record in all_sources()]
        self.assertEqual(len(ids), len(set(ids)))
        for record_id in ids:
            self.assertEqual(record_id, record_id.lower())
            self.assertNotIn(" ", record_id)

    def test_urls_are_https_and_unique_enough(self):
        urls = [record["url"] for record in all_sources()]
        for url in urls:
            self.assertTrue(url.startswith("https://"), url)
            self.assertNotIn("example.com", url)
            self.assertNotIn("TODO", url)

    def test_excerpts_are_real_prose_not_placeholders(self):
        forbidden = ("lorem", "todo", "tbd", "xxx", "placeholder", "insert ")
        for record in all_sources():
            excerpt = record["excerpt"].lower()
            for word in forbidden:
                self.assertNotIn(word, excerpt, (record["id"], word))

    def test_excerpts_carry_their_section_marker(self):
        """Each excerpt should visibly contain its provision marker, so the
        quote and the recorded section cannot drift apart."""
        checks = {
            "patents_act_1970_s3p": "(p)",
            "patents_act_1970_s2j": "(j)",
            "patents_act_1970_s10_4d": "(D)",
            "gi_act_1999_s2_1e": "(e)",
            "gi_act_1999_s11_1": "11. (1)",
            "tm_act_1999_s9_1b": "(b)",
            "designs_act_2000_s2d": "(d)",
            "copyright_act_1957_s22": "22.",
            "dc_act_1940_s3a": "(a)",
            "dmr_act_1954_s3": "3.",
            "dmr_act_1954_s2c": "(c)",
            "ppvfr_act_2001_s39_1iv": "(iv)",
            # bda_2002_s6 was re-verified against the amended official text in
            # Phase 2; the excerpt now quotes substituted sub-sections 6(1) and
            # 6(1A) from the Amendment Act Gazette, so the marker is "(1A)".
            "bda_2002_s6": "(1A)",
            "fss_aahara_regs_2022_reg2b": "(b)",
        }
        for record in all_sources():
            if record["id"] in checks:
                self.assertIn(checks[record["id"]], record["excerpt"], record["id"])

    def test_verification_recorded_for_every_url(self):
        for record in all_sources():
            verification = record["verification"]
            self.assertIn(verification["method"],
                          ("downloaded+extracted", "mirror-verified"),
                          record["id"])
            self.assertTrue(verification["checked_on"], record["id"])
            self.assertTrue(verification["url_status"], record["id"])
            self.assertTrue(verification["notes"], record["id"])

    def test_effective_date_recorded_everywhere(self):
        for record in all_sources():
            self.assertTrue(record["effective_date"].strip(), record["id"])

    def test_sources_reference_real_issuers(self):
        """Every issuer string must name a real government/official body —
        a cheap guard against invented authorities."""
        known_official = (
            "Government of India", "FSSAI", "Food Safety and Standards Authority",
        )
        for record in all_sources():
            self.assertTrue(
                any(body in record["issuer"] for body in known_official),
                (record["id"], record["issuer"]),
            )


class TestGoldenScenarioSupport(unittest.TestCase):
    """The two India golden scenarios must be backed by real source records."""

    def test_scenario1_patent_classical_formulation_sources(self):
        """'Can I patent a classical Ayurvedic formulation from an
        authoritative text?' needs the Section 3(p) TK bar and the
        patentability definitions, with traceable citations."""
        sources = {record["id"] for record in all_sources()}
        self.assertIn("patents_act_1970_s3p", sources)
        self.assertIn("patents_act_1970_s2j", sources)
        self.assertIn("patents_act_1970_s10_4d", sources)

        s3p = next(r for r in all_sources() if r["id"] == "patents_act_1970_s3p")
        self.assertEqual(s3p["section"], "Section 3(p)")
        self.assertIn("traditional knowledge", s3p["excerpt"])
        self.assertIn("3(p)", s3p["tags"])

        # retrieval seam finds it for the scenario question
        hits = find_sources(
            "Can I patent a classical Ayurvedic formulation from an "
            "authoritative text? traditional knowledge patent"
        )
        self.assertTrue(hits)
        top_ids = [record["id"] for record, _ in hits[:3]]
        self.assertIn("patents_act_1970_s3p", top_ids)

    def test_scenario2_gi_registration_sources(self):
        """'How do I register a GI tag for an Ayurvedic product tied to a
        region?' needs the GI definition and the application provision."""
        sources = {record["id"] for record in all_sources()}
        self.assertIn("gi_act_1999_s2_1e", sources)
        self.assertIn("gi_act_1999_s11_1", sources)

        s11 = next(r for r in all_sources() if r["id"] == "gi_act_1999_s11_1")
        self.assertEqual(s11["section"], "Section 11(1)")
        self.assertIn("apply in writing to the Registrar", s11["excerpt"])

        hits = find_sources(
            "How do I register a GI tag for an Ayurvedic product tied to a "
            "region? geographical indication registration apply"
        )
        self.assertTrue(hits)
        top_ids = [record["id"] for record, _ in hits[:3]]
        self.assertIn("gi_act_1999_s11_1", top_ids)
        self.assertIn("gi_act_1999_s2_1e", top_ids)

    def test_gi_definition_clause_letter_is_precise(self):
        """The GI definition is Section 2(1)(e) in this Act — a common
        miscitation says 2(1)(f) (which defines 'goods'). Guard it."""
        record = next(r for r in all_sources() if r["id"] == "gi_act_1999_s2_1e")
        self.assertEqual(record["section"], "Section 2(1)(e)")
        self.assertIn("2(1)(f)", record["verification"]["notes"])

    def test_drug_definition_supports_classical_boundary(self):
        record = next(r for r in all_sources() if r["id"] == "dc_act_1940_s3a")
        self.assertEqual(record["section"], "Section 3(a)")
        self.assertIn("First Schedule", record["excerpt"])
        self.assertIn("authoritative books", record["excerpt"])


class TestOutOfCorpusAbstentionReadiness(unittest.TestCase):
    """The corpus is intentionally limited: international IP (M5) and deep
    ABS/Nagoya (M4) topics must yield NO matches, so Phase 2 abstains."""

    def test_out_of_corpus_topics_return_nothing(self):
        for topic in OUT_OF_CORPUS_TOPICS:
            hits = find_sources(topic)
            self.assertEqual(hits, [], "unexpected matches for %r" % topic)

    def test_nonsense_query_returns_nothing(self):
        self.assertEqual(find_sources("zzz qxj vbn"), [])

    def test_in_scope_queries_still_match(self):
        self.assertTrue(find_sources("ayurvedic drug authoritative books first schedule"))
        self.assertTrue(find_sources("advertisement claims magic remedies"))
        self.assertTrue(find_sources("fssai ayurveda aahara food bhasma"))
        self.assertTrue(find_sources("farmers rights seed plant varieties"))
        self.assertTrue(find_sources("design packaging shape bottle"))
        self.assertTrue(find_sources("copyright term sixty years public domain"))
        self.assertTrue(find_sources("trademark descriptive brand registration"))


class TestDeterminism(unittest.TestCase):
    def test_find_sources_deterministic(self):
        query = "patent traditional knowledge ayurveda"
        runs = [find_sources(query) for _ in range(5)]
        for run in runs[1:]:
            self.assertEqual(
                [r["id"] for r, _ in run], [r["id"] for r, _ in runs[0]]
            )

    def test_all_sources_returns_fresh_copies(self):
        first = all_sources()
        first[0]["excerpt"] = "tampered"
        second = all_sources()
        self.assertNotEqual(first[0]["excerpt"], second[0]["excerpt"])


if __name__ == "__main__":
    unittest.main()
