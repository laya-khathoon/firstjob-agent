"""Offline tests for internship_searcher.build_search_pages (no network)."""
import unittest

from internship_searcher import AICTE_URL, build_search_pages


class BuildSearchPagesTests(unittest.TestCase):
    def test_each_keyword_gets_internshala_and_unstop(self):
        pages = build_search_pages(["python", "data science"])
        by_keyword = {}
        for page in pages:
            by_keyword.setdefault(page["keyword"], []).append(page["site"])
        self.assertEqual(by_keyword["python"][:2], ["Internshala", "Unstop"])
        self.assertEqual(by_keyword["data science"], ["Internshala", "Unstop"])

    def test_multi_word_keyword_becomes_a_slug(self):
        pages = build_search_pages(["Data Science"])
        internshala = [p for p in pages if p["site"] == "Internshala"][0]
        self.assertIn("keywords-data-science", internshala["url"])

    def test_only_the_first_three_keywords_are_used(self):
        pages = build_search_pages(["a", "b", "c", "d", "e"])
        keywords = {p["keyword"] for p in pages}
        self.assertEqual(keywords, {"a", "b", "c"})

    def test_aicte_page_uses_first_keyword_once(self):
        pages = build_search_pages(["python", "sql"])
        aicte = [p for p in pages if p["site"].startswith("AICTE")]
        self.assertEqual(len(aicte), 1)
        self.assertEqual(aicte[0]["keyword"], "python")
        self.assertEqual(aicte[0]["url"], AICTE_URL)

    def test_blank_input_gives_no_pages(self):
        self.assertEqual(build_search_pages([]), [])
        self.assertEqual(build_search_pages(["", "  "]), [])
        self.assertEqual(build_search_pages(None), [])


if __name__ == "__main__":
    unittest.main()
