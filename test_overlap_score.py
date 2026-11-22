"""Offline tests for the keyword-overlap fallback fit score."""
import unittest

from resume_parser import _overlap_score


class OverlapScoreTests(unittest.TestCase):
    def test_no_skill_hits_scores_low(self):
        self.assertEqual(_overlap_score(["python"], "a cook for a hotel"), 25)

    def test_skill_hits_raise_the_score(self):
        score = _overlap_score(["python"], "python developer internship")
        self.assertGreaterEqual(score, 45)

    def test_score_is_capped_at_95(self):
        skills = ["python", "sql", "java", "c++", "react", "node", "aws", "ml"]
        text = "python sql java c++ react node aws ml internship"
        self.assertLessEqual(_overlap_score(skills, text), 95)

    def test_entry_level_posting_helps_a_beginner(self):
        plain = _overlap_score(["python"], "python trainee role", level="")
        beginner = _overlap_score(["python"], "python trainee role",
                                  level="beginner")
        self.assertGreater(beginner, plain)

    def test_senior_posting_hurts_a_beginner(self):
        plain = _overlap_score(["python"], "senior python lead", level="")
        beginner = _overlap_score(["python"], "senior python lead",
                                  level="beginner")
        self.assertLess(beginner, plain)

    def test_empty_text_does_not_crash(self):
        self.assertEqual(_overlap_score(["python"], ""), 25)
        self.assertEqual(_overlap_score(["python"], None), 25)


if __name__ == "__main__":
    unittest.main()
