"""Offline tests for the level guess in heuristic_analysis."""
import unittest
from unittest.mock import patch

import resume_parser
from resume_parser import heuristic_analysis


class HeuristicLevelTests(unittest.TestCase):
    def _level(self, count):
        skills = [f"skill{i}" for i in range(count)]
        with patch.object(resume_parser, "KNOWN_SKILLS", skills):
            return heuristic_analysis(" ".join(skills), [])["level"]

    def test_six_skills_is_beginner(self):
        self.assertEqual(self._level(6), "beginner")

    def test_seven_skills_is_intermediate(self):
        self.assertEqual(self._level(7), "intermediate")

    def test_twelve_skills_is_still_intermediate(self):
        self.assertEqual(self._level(12), "intermediate")

    def test_thirteen_skills_is_advanced(self):
        self.assertEqual(self._level(13), "advanced")

    def test_result_is_marked_as_fallback(self):
        self.assertEqual(heuristic_analysis("python", [])["source"], "fallback")


if __name__ == "__main__":
    unittest.main()
