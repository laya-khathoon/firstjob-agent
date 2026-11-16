"""Offline coverage of Gemini JSON parsing; no API key or network needed."""
import unittest
from unittest.mock import patch

from resume_parser import ask_gemini_json


class ResumeJsonTests(unittest.TestCase):
    def parse(self, response):
        with patch("resume_parser.ask_gemini", return_value=response) as ask:
            result = ask_gemini_json("Read this resume", max_output_tokens=600)
        self.assertIn("JSON only", ask.call_args.args[0])
        self.assertEqual(ask.call_args.kwargs["max_output_tokens"], 600)
        return result

    def test_plain_object(self):
        self.assertEqual(self.parse('{"skills": ["python"]}'),
                         {"skills": ["python"]})

    def test_markdown_fence(self):
        self.assertEqual(self.parse('```json\n{"level": "beginner"}\n```'),
                         {"level": "beginner"})

    def test_array_response_for_fit_scores(self):
        self.assertEqual(self.parse('[{"score": 75}]'), [{"score": 75}])

    def test_missing_malformed_and_non_json_responses(self):
        for response in (None, "", "unavailable", '{"skills": }'):
            with self.subTest(response=response):
                self.assertIsNone(self.parse(response))


if __name__ == "__main__":
    unittest.main()
