"""Offline tests for draft_application: Gemini is replaced by a stub."""
import unittest
from unittest.mock import patch

import application_drafter


class DraftApplicationPromptTests(unittest.TestCase):
    def _run(self, analysis, match):
        with patch.object(application_drafter, "ask_gemini", return_value="ok") as stub:
            result = application_drafter.draft_application(analysis, match)
        return result, stub

    def test_prompt_contains_real_skills_projects_and_job(self):
        analysis = {"skills": ["Python", "SQL"], "projects": ["PageSage"], "education": "BTech CSE"}
        result, stub = self._run(analysis, {"title": "Data Intern", "company": "Acme"})
        prompt = stub.call_args[0][0]
        self.assertEqual(result, "ok")
        for text in ("Python, SQL", "PageSage", "BTech CSE", "Data Intern at Acme"):
            self.assertIn(text, prompt)

    def test_prompt_asks_never_to_invent(self):
        _, stub = self._run({}, {})
        self.assertIn("Never invent", stub.call_args[0][0])

    def test_token_limit_is_passed(self):
        _, stub = self._run({}, {})
        self.assertEqual(stub.call_args[1]["max_output_tokens"], 400)


if __name__ == "__main__":
    unittest.main()
