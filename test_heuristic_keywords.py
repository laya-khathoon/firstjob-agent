"""Offline tests for the keyword choice in heuristic_analysis."""
import unittest

from resume_parser import heuristic_analysis


class HeuristicKeywordTests(unittest.TestCase):
    def test_role_area_keywords_come_first(self):
        result = heuristic_analysis("knows python and sql", ["cybersecurity"])
        self.assertEqual(result["search_keywords"], ["cyber security", "ethical hacking"])

    def test_keywords_are_not_repeated_across_areas(self):
        result = heuristic_analysis("x", ["AI/ML", "data"])
        self.assertEqual(len(result["search_keywords"]), len(set(result["search_keywords"])))

    def test_at_most_three_keywords(self):
        result = heuristic_analysis("x", ["AI/ML", "web development", "data"])
        self.assertLessEqual(len(result["search_keywords"]), 3)

    def test_no_area_falls_back_to_found_skills(self):
        result = heuristic_analysis("I use python and docker", [])
        self.assertIn("python", result["search_keywords"])

    def test_unknown_area_is_ignored(self):
        result = heuristic_analysis("I use python", ["underwater basket weaving"])
        self.assertIn("python", result["search_keywords"])


if __name__ == "__main__":
    unittest.main()
