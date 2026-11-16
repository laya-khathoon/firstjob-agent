"""Resume fallback must remain useful when Gemini is unavailable."""
import unittest
from unittest.mock import patch

from resume_parser import analyze_resume, heuristic_analysis


class ResumeFallbackTests(unittest.TestCase):
    def test_blank_resume_does_not_call_api(self):
        with patch("resume_parser.ask_gemini_json") as ask:
            for text in (None, "", "  \n"):
                result = analyze_resume(text, [], "Both", False)
                self.assertEqual(result["skills"], [])
                self.assertEqual(result["source"], "none")
            ask.assert_not_called()

    def test_role_keywords_are_unique_and_limited(self):
        result = heuristic_analysis("Python SQL React", ["AI/ML", "AI/ML", "data"])
        self.assertEqual(len(result["search_keywords"]), 3)
        self.assertEqual(len(set(result["search_keywords"])), 3)
        self.assertIn("python", result["skills"])
        self.assertEqual(result["source"], "fallback")

    def test_invalid_ai_response_uses_resume_keywords(self):
        for response in (None, [], {"skills": ["invented"]}):
            with self.subTest(response=response):
                with patch("resume_parser.ask_gemini_json", return_value=response):
                    result = analyze_resume("Python SQL", [], "Both", False)
                self.assertEqual(result["source"], "fallback")
                self.assertIn("python", result["search_keywords"])
                self.assertNotIn("invented", result["skills"])

    def test_valid_ai_response_is_marked(self):
        with patch("resume_parser.ask_gemini_json", return_value={
                "skills": ["python"], "search_keywords": ["python"]}):
            result = analyze_resume("Python", ["data"], "Remote", True)
        self.assertEqual(result["source"], "gemini")


if __name__ == "__main__":
    unittest.main()
