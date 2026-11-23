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
    def test_access_and_server_errors_stop_the_page_batch(self):
        for code in (401, 403, 429, 500, 502, 503, 504):
            error = urllib.error.HTTPError("https://world.openfoodfacts.org/test",
                                           code, "blocked", {}, None)
            self.assertTrue(collector.should_stop_batch(error), code)
        not_found = urllib.error.HTTPError("https://world.openfoodfacts.org/test",
                                           404, "not found", {}, None)
        self.assertFalse(collector.should_stop_batch(not_found))

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
        self.assertEqual(sleeps, [7])

    def test_long_retry_after_stops_to_respect_rate_limit(self):
        calls = []

        def opener(request, timeout):
            calls.append(1)
            if len(calls) == 1:
                raise urllib.error.HTTPError(request.full_url, 429, "rate limited",
                                             {"Retry-After": "600"}, None)
            return io.BytesIO(b'{"products":[]}')

        sleeps = []
        with self.assertRaises(urllib.error.HTTPError):
            collector.fetch_products("https://world.openfoodfacts.org/test",
                                     opener=opener, sleeper=sleeps.append)
        self.assertEqual(len(calls), 1)
        self.assertEqual(sleeps, [])

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
        self.assertEqual(sleeps, [7, 14])

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

    def test_fetch_page_calculates_total_pages_from_api_count(self):
        # OFF API v2 page_count is per-page; count is the total match count.
        payload = {"products": [{"code": "4901002018849"}], "count": 1700, "page_count": 100}
        products, total_pages = collector.fetch_page(
            "https://world.openfoodfacts.org/api/v2/search",
            opener=lambda req, timeout: io.BytesIO(json.dumps(payload).encode()),
            sleeper=lambda _: None,
            page_size=100,
        )
        self.assertEqual(len(products), 1)
        self.assertEqual(total_pages, 17)

    def test_zero_total_count_has_no_pages(self):
        payload = {"products": [], "count": 0, "page_count": 0}
        products, total_pages = collector.fetch_page(
            "https://world.openfoodfacts.org/api/v2/search",
            opener=lambda req, timeout: io.BytesIO(json.dumps(payload).encode()),
            sleeper=lambda _: None,
            page_size=100,
        )
        self.assertEqual(products, [])
        self.assertEqual(total_pages, 0)

    def test_search_url_uses_supported_structured_api(self):
        from urllib.parse import parse_qs, urlsplit
        url = collector.build_search_url(12, 100)
        parsed = urlsplit(url)
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/api/v2/search")
        self.assertEqual(params["countries_tags_en"], ["japan"])
        self.assertEqual(params["page"], ["12"])
        self.assertEqual(params["page_size"], ["100"])
        self.assertIn("ingredients_text_ja", params["fields"][0])

    def test_zero_page_count_does_not_probe_nonexistent_pages(self):
        self.assertEqual(collector.page_sequence(4, 5, 0), [])

    def test_page_sequence_wraps_at_page_count(self):
        self.assertEqual(collector.page_sequence(6, 4, 7), [6, 7, 1, 2])
        self.assertEqual(collector.page_sequence(8, 3, 7), [1, 2, 3])

    def test_page_sequence_without_page_count_is_monotonic(self):
        self.assertEqual(collector.page_sequence(6, 3, None), [6, 7, 8])

    def test_page_sequence_never_repeats_within_a_window(self):
        self.assertEqual(collector.page_sequence(2, 20, 7), [2, 3, 4, 5, 6, 7, 1])


if __name__ == "__main__":
    unittest.main()
