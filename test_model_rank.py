"""Offline tests for the Gemini model ordering helper."""
import unittest

from resume_parser import _model_rank


class ModelRankTests(unittest.TestCase):
    def test_flash_comes_before_flash_lite(self):
        self.assertLess(_model_rank("gemini-2.0-flash"), _model_rank("gemini-2.0-flash-lite"))

    def test_flash_lite_comes_before_other_gemini(self):
        self.assertLess(_model_rank("gemini-flash-lite"), _model_rank("gemini-pro"))

    def test_gemini_comes_before_unrelated_models(self):
        self.assertLess(_model_rank("gemini-pro"), _model_rank("gemma-3"))

    def test_latest_alias_beats_dated_version_in_the_same_group(self):
        self.assertLess(_model_rank("gemini-flash-latest"), _model_rank("gemini-2.0-flash"))

    def test_sorting_a_mixed_list(self):
        names = ["gemma-3", "gemini-pro", "gemini-flash-lite", "gemini-flash"]
        self.assertEqual(sorted(names, key=_model_rank),
                         ["gemini-flash", "gemini-flash-lite", "gemini-pro", "gemma-3"])


if __name__ == "__main__":
    unittest.main()
