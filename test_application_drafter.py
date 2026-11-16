"""Check application prompt inputs without spending API quota."""
import unittest
from unittest.mock import patch

from application_drafter import draft_application


class ApplicationDrafterTests(unittest.TestCase):
    def test_passes_student_and_internship_facts_to_drafter(self):
        analysis = {"skills": ["python", "sql"], "projects": ["PDF search"],
                    "education": "BTech Computer Science"}
        match = {"title": "Data intern", "company": "Example Ltd"}
        with patch("application_drafter.ask_gemini", return_value="Draft") as ask:
            self.assertEqual(draft_application(analysis, match), "Draft")
        prompt = ask.call_args.args[0]
        for fact in ("python, sql", "PDF search", "BTech Computer Science",
                     "Data intern", "Example Ltd", "Never invent or exaggerate"):
            self.assertIn(fact, prompt)
        self.assertEqual(ask.call_args.kwargs["max_output_tokens"], 400)

    def test_missing_optional_values_do_not_crash(self):
        with patch("application_drafter.ask_gemini", return_value=None) as ask:
            self.assertIsNone(draft_application({}, {}))
        self.assertIn("not stated", ask.call_args.args[0])
        self.assertIn("this internship", ask.call_args.args[0])
        self.assertIn("your organisation", ask.call_args.args[0])

    def test_input_dictionaries_are_not_modified(self):
        analysis = {"skills": ["python"]}
        match = {"title": "Intern"}
        with patch("application_drafter.ask_gemini", return_value="Draft"):
            draft_application(analysis, match)
        self.assertEqual(analysis, {"skills": ["python"]})
        self.assertEqual(match, {"title": "Intern"})


if __name__ == "__main__":
    unittest.main()
