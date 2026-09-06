from __future__ import annotations

import os
import re
import unittest
import urllib.error
import urllib.request
import unicodedata
from datetime import date
from html.parser import HTMLParser

from member5.corpus import SYSTEM_RIGHTS, load_sources, retrieve_sources


REQUIRED_FIELDS = {
    "id",
    "source_name",
    "source_type",
    "authoritative_body",
    "section",
    "excerpt",
    "url",
    "effective_date",
    "jurisdiction",
    "region",
    "ip_right",
    "system",
    "topics",
    "keywords",
    "verification",
}


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def _normalized_visible_text(page: bytes, charset: str | None) -> str:
    parser = _VisibleTextParser()
    parser.feed(page.decode(charset or "utf-8", errors="replace"))
    text = " ".join(parser.parts)
    return _normalize_for_match(text)


def _normalize_for_match(text: str) -> str:
    normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().casefold()
    normalized = re.sub(r"\(\s+", "(", normalized)
    return re.sub(r"\s+\)", ")", normalized)


class Phase1CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = load_sources()

    def test_corpus_is_deliberately_small_and_deterministic(self) -> None:
        self.assertGreaterEqual(len(self.sources), 8)
        self.assertLessEqual(len(self.sources), 12)
        self.assertEqual(self.sources, load_sources())
        ids = [source["id"] for source in self.sources]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_record_has_complete_metadata(self) -> None:
        for source in self.sources:
            with self.subTest(source=source["id"]):
                self.assertEqual(REQUIRED_FIELDS, set(source))
                for field in REQUIRED_FIELDS - {"effective_date"}:
                    self.assertNotIn(source[field], (None, "", [], {}))
                if source["effective_date"] is not None:
                    date.fromisoformat(source["effective_date"])
                self.assertTrue(source["url"].startswith("https://"))
                self.assertEqual(source["verification"]["status"], "verified")

    def test_all_records_are_explicitly_international(self) -> None:
        for source in self.sources:
            with self.subTest(source=source["id"]):
                self.assertEqual("International", source["jurisdiction"])
                self.assertTrue(source["region"])

    def test_route_systems_have_exact_right_mapping(self) -> None:
        observed = {system: 0 for system in SYSTEM_RIGHTS}
        for source in self.sources:
            if source["system"] in SYSTEM_RIGHTS:
                system = source["system"]
                observed[system] += 1
                self.assertEqual(SYSTEM_RIGHTS[system], source["ip_right"])
        self.assertTrue(all(count >= 1 for count in observed.values()))

    def test_known_article_designations(self) -> None:
        sections = {source["id"]: source["section"] for source in self.sources}
        self.assertEqual("Article 27.3(b)", sections["trips-art-27-3-b"])
        self.assertEqual("Article 3.1", sections["gratk-art-3-1"])
        self.assertEqual("Article 3.2", sections["gratk-art-3-2"])
        self.assertEqual("Article 17", sections["gratk-art-17"])
        self.assertEqual("Article 15.1", sections["cbd-art-15-1"])
        self.assertEqual("Article 15.5", sections["cbd-art-15-5"])
        self.assertEqual("Article 5.1", sections["nagoya-art-5-1"])
        self.assertEqual("Article 6.1", sections["nagoya-art-6-1"])

    def test_excerpts_are_short_nonempty_and_traceable(self) -> None:
        for source in self.sources:
            with self.subTest(source=source["id"]):
                self.assertGreaterEqual(len(source["excerpt"].split()), 6)
                self.assertLessEqual(len(source["excerpt"].split()), 30)
                self.assertIn("Official", source["verification"]["method"])

    def test_patent_golden_scenario_retrieves_pct_not_other_routes(self) -> None:
        results = retrieve_sources(
            "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?"
        )
        systems = [result["system"] for result in results]
        self.assertIn("PCT", systems)
        self.assertNotIn("Madrid", systems)
        self.assertNotIn("Hague", systems)
        self.assertEqual("PCT", systems[0])

    def test_trademark_scenario_retrieves_madrid_not_other_routes(self) -> None:
        results = retrieve_sources(
            "I want to register my Ayurvedic brand name internationally."
        )
        systems = [result["system"] for result in results]
        self.assertIn("Madrid", systems)
        self.assertNotIn("PCT", systems)
        self.assertNotIn("Hague", systems)
        self.assertEqual("Madrid", systems[0])

    def test_design_scenario_retrieves_hague_only_among_routes(self) -> None:
        results = retrieve_sources(
            "How can I register an industrial design for packaging internationally?"
        )
        route_systems = {
            result["system"] for result in results if result["system"] in SYSTEM_RIGHTS
        }
        self.assertEqual({"Hague"}, route_systems)

    def test_intentionally_out_of_corpus_topic_has_no_match(self) -> None:
        self.assertEqual(
            [], retrieve_sources("How is spacecraft lease depreciation taxed?"),
        )

    def test_retrieval_is_deterministic(self) -> None:
        query = "international patent filing outside my country"
        self.assertEqual(retrieve_sources(query), retrieve_sources(query))


@unittest.skipUnless(
    os.environ.get("RUN_NETWORK_TESTS") == "1",
    "Set RUN_NETWORK_TESTS=1 to verify live official URLs.",
)
class Phase1LiveUrlTests(unittest.TestCase):
    def test_every_official_url_resolves_and_contains_its_excerpt(self) -> None:
        sources = load_sources()
        pages: dict[str, str] = {}
        for url in sorted({source["url"] for source in sources}):
            with self.subTest(url=url):
                request = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 IP-SAKTI-Phase1-URL-Check/1.0",
                        "Accept": "text/html,application/xhtml+xml",
                    },
                )
                try:
                    with urllib.request.urlopen(request, timeout=20) as response:
                        self.assertLess(response.status, 400)
                        self.assertTrue(response.geturl().startswith("https://"))
                        pages[url] = _normalized_visible_text(
                            response.read(), response.headers.get_content_charset()
                        )
                except urllib.error.HTTPError as error:
                    self.fail(f"{url} returned HTTP {error.code}")

        for source in sources:
            with self.subTest(source=source["id"]):
                excerpt = _normalize_for_match(source["excerpt"])
                self.assertIn(excerpt, pages[source["url"]])


if __name__ == "__main__":
    unittest.main()
