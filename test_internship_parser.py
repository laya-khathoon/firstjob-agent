"""Saved HTML fixtures exercise parsing without contacting job boards."""
import unittest

from internship_searcher import _parse_internshala, build_search_pages


CARD = '''<div class="individual_internship" data-href="/internship/detail/python-1">
<a class="job-title-href" href="/internship/detail/python-1">Python Intern</a>
<p class="company-name">Example Ltd</p>
<div class="row-1-item locations">Remote</div><span class="stipend">5000/month</span>
<div class="job_skill">Python</div><div class="job_skill">SQL</div></div>'''


class InternshipParserTests(unittest.TestCase):
    def test_extracts_posting_and_removes_duplicate_cards(self):
        result = _parse_internshala(CARD + CARD, "python")
        self.assertEqual(len(result), 1)
        posting = result[0]
        self.assertEqual(posting["title"], "Python Intern")
        self.assertEqual(posting["company"], "Example Ltd")
        self.assertEqual(posting["skills"], ["Python", "SQL"])
        self.assertEqual(posting["url"],
                         "https://internshala.com/internship/detail/python-1")
        self.assertEqual(posting["keyword"], "python")

    def test_missing_optional_card_details_are_safe(self):
        result = _parse_internshala(
            '<div class="individual_internship" data-href="/internship/1"></div>',
            "data analyst")
        self.assertEqual(result[0]["title"], "data analyst")
        self.assertEqual(result[0]["skills"], [])
        self.assertEqual(result[0]["company"], "")
        self.assertEqual(_parse_internshala("<html></html>", "python"), [])

    def test_search_pages_ignore_blanks_and_cap_keywords(self):
        self.assertEqual(build_search_pages([None, " "]), [])
        pages = build_search_pages([" python ", "data science", "sql", "java"])
        self.assertEqual(len(pages), 7)
        self.assertEqual(pages[0]["keyword"], "python")
        self.assertIn("data-science", pages[2]["url"])
        self.assertNotIn("java", [p["keyword"] for p in pages])


if __name__ == "__main__":
    unittest.main()
