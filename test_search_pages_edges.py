"""Edge cases for build_search_pages (no network)."""
import unittest

from internship_searcher import build_search_pages


class SearchPagesEdgeTests(unittest.TestCase):
    def test_no_keywords_gives_no_pages(self):
        self.assertEqual(build_search_pages([]), [])
        self.assertEqual(build_search_pages(None), [])

    def test_blank_keywords_are_ignored(self):
        self.assertEqual(build_search_pages(["", "   ", None]), [])

    def test_only_the_first_three_keywords_are_used(self):
        pages = build_search_pages(["a", "b", "c", "d"])
        self.assertEqual({p["keyword"] for p in pages}, {"a", "b", "c"})

    def test_spaces_become_dashes_in_the_internshala_slug(self):
        pages = build_search_pages(["Machine Learning"])
        internshala = [p for p in pages if p["site"] == "Internshala"][0]
        self.assertTrue(internshala["url"].endswith("keywords-machine-learning/"))

    def test_the_national_portal_is_added_once(self):
        pages = build_search_pages(["python", "sql"])
        self.assertEqual(sum(p["site"].startswith("AICTE") for p in pages), 1)


if __name__ == "__main__":
    unittest.main()
