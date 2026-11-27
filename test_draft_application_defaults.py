"""Offline tests for draft_application defaults."""
import unittest
from unittest.mock import patch

import application_drafter


class DraftApplicationDefaultsTests(unittest.TestCase):
    def _prompt(self, analysis, match):
        with patch.object(application_drafter, "ask_gemini", return_value=None) as stub:
            result = application_drafter.draft_application(analysis, match)
        self.assertIsNone(result)
        return stub.call_args[0][0]

    def test_missing_skills_and_projects_say_not_stated(self):
        prompt = self._prompt({"skills": [], "projects": None}, {})
        self.assertIn("real skills: not stated", prompt)
        self.assertIn("projects: not stated", prompt)

    def test_missing_title_company_and_education_use_defaults(self):
        prompt = self._prompt({}, {})
        self.assertIn("this internship at your organisation", prompt)
        self.assertIn("final-year BTech student", prompt)

    def test_projects_are_joined_with_semicolons(self):
        prompt = self._prompt({"projects": ["A", "B"]}, {})
        self.assertIn("A; B", prompt)


if __name__ == "__main__":
    unittest.main()
