"""Model discovery filters and caching, using a fake Gemini client."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from resume_parser import _discover_models


def model(name, actions=("generateContent",)):
    return SimpleNamespace(name="models/" + name, supported_actions=actions)


class ModelDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.cache = patch("resume_parser._DISCOVERED", None)
        self.cache.start()
        self.addCleanup(self.cache.stop)
        self.client = Mock()

    def test_filters_non_text_models_and_sorts_flash_first(self):
        self.client.models.list.return_value = [
            model("gemini-pro"), model("gemini-flash-lite"),
            model("gemini-flash"), model("gemini-embedding"),
            model("gemini-tts"), model("other", ("embedContent",)),
        ]
        self.assertEqual(_discover_models(self.client),
                         ["gemini-flash", "gemini-flash-lite", "gemini-pro"])

    def test_successful_discovery_is_cached(self):
        self.client.models.list.return_value = [model("gemini-flash")]
        self.assertEqual(_discover_models(self.client), ["gemini-flash"])
        self.assertEqual(_discover_models(self.client), ["gemini-flash"])
        self.client.models.list.assert_called_once()

    def test_failures_and_empty_results_allow_fallback(self):
        self.client.models.list.side_effect = RuntimeError("offline")
        self.assertIsNone(_discover_models(self.client))
        self.client.models.list.side_effect = None
        self.client.models.list.return_value = []
        self.assertIsNone(_discover_models(self.client))


if __name__ == "__main__":
    unittest.main()
