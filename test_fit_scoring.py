"""Fit score boundaries and offline fallback, without Gemini requests."""
import unittest
from unittest.mock import patch

from resume_parser import score_fit


class FitScoringTests(unittest.TestCase):
    def test_empty_results_skip_api(self):
        with patch("resume_parser.ask_gemini_json") as ask:
            self.assertEqual(score_fit({"skills": ["python"]}, []), [])
            ask.assert_not_called()

    def test_model_scores_are_clamped_to_percentage(self):
        items = [{"title": "Python intern"}, {"title": "SQL intern"}]
        with patch("resume_parser.ask_gemini_json", return_value=[
                {"score": 150, "reason": "match"}, {"score": -20}]):
            result = score_fit({"skills": ["python"]}, items)
        self.assertIs(result, items)
        self.assertEqual([i["fit_score"] for i in result], [100, 0])
        self.assertEqual(result[0]["fit_reason"], "match")

    def test_incomplete_model_scores_fall_back_per_item(self):
        with patch("resume_parser.ask_gemini_json", return_value=[{"score": 80}]):
            result = score_fit({"skills": ["python"]}, [
                {"title": "Python intern"}, {"title": "Python trainee"}])
        self.assertEqual(result[0]["fit_score"], 80)
        self.assertGreater(result[1]["fit_score"], 25)
        self.assertTrue(result[1]["fit_reason"])

    def test_local_mode_never_calls_gemini(self):
        with patch("resume_parser.ask_gemini_json") as ask:
            result = score_fit({"skills": []}, [{}], use_gemini=False)
        ask.assert_not_called()
        self.assertEqual(result[0]["fit_score"], 25)
        self.assertTrue(result[0]["fit_reason"])


if __name__ == "__main__":
    unittest.main()
