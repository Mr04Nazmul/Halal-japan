"""Offline regression tests for bounded Open Food Facts candidate collection."""
import importlib.util
import io
import json
import pathlib
import unittest
import urllib.error

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "import_off_japan_ingredients.py"
spec = importlib.util.spec_from_file_location("off_candidate_collector", SCRIPT)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class OpenFoodFactsRetryTests(unittest.TestCase):
    def test_503_then_success(self):
        calls = []
        sleeps = []

        def opener(request, timeout):
            calls.append(request.full_url)
            if len(calls) == 1:
                raise urllib.error.HTTPError(request.full_url, 503, "unavailable", {}, None)
            return io.BytesIO(json.dumps({"products": [{"code": "4901002018849"}]}).encode())

        result = collector.fetch_products("https://world.openfoodfacts.org/test",
                                          opener=opener, sleeper=sleeps.append)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [3])

    def test_retry_after_is_capped(self):
        calls = []

        def opener(request, timeout):
            calls.append(1)
            if len(calls) == 1:
                raise urllib.error.HTTPError(request.full_url, 429, "rate limited",
                                             {"Retry-After": "600"}, None)
            return io.BytesIO(b'{"products":[]}')

        sleeps = []
        self.assertEqual(collector.fetch_products("https://world.openfoodfacts.org/test",
                                                  opener=opener, sleeper=sleeps.append), [])
        self.assertEqual(sleeps, [30])

    def test_401_is_not_retried(self):
        calls = []

        def opener(request, timeout):
            calls.append(1)
            raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", {}, None)

        with self.assertRaises(urllib.error.HTTPError):
            collector.fetch_products("https://world.openfoodfacts.org/test",
                                     opener=opener, sleeper=lambda _: None)
        self.assertEqual(len(calls), 1)

    def test_persistent_503_stops_after_three_attempts(self):
        calls = []
        sleeps = []

        def opener(request, timeout):
            calls.append(1)
            raise urllib.error.HTTPError(request.full_url, 503, "unavailable", {}, None)

        with self.assertRaises(urllib.error.HTTPError):
            collector.fetch_products("https://world.openfoodfacts.org/test",
                                     opener=opener, sleeper=sleeps.append)
        self.assertEqual(len(calls), 3)
        self.assertEqual(sleeps, [3, 6])

    def test_malformed_response_rejected(self):
        with self.assertRaises(ValueError):
            collector.fetch_products("https://world.openfoodfacts.org/test",
                                     opener=lambda req, timeout: io.BytesIO(b'{"count":0}'),
                                     sleeper=lambda _: None)

    def test_jan_validation_and_japanese_gate(self):
        self.assertTrue(collector.valid_ean("4901002018849"))
        self.assertFalse(collector.valid_ean("4901002018848"))
        self.assertTrue(collector.is_japanese_ingredient_candidate(
            "4901002018849", "けしの実", "けしの実、植物油脂、食塩"))
        self.assertFalse(collector.is_japanese_ingredient_candidate(
            "4901002018849", "Poppy seeds", "water and salt"))


if __name__ == "__main__":
    unittest.main()
