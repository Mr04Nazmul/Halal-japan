"""Offline tests for the scheduled Open Food Facts collector's circuit breaker."""
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import urllib.error

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "collect_japan_ingredients.py"
spec = importlib.util.spec_from_file_location("collect_japan_ingredients", SCRIPT)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CollectJapanIngredientsTests(unittest.TestCase):
    def http_error(self, code, headers=None):
        return urllib.error.HTTPError(
            "https://world.openfoodfacts.org/api/v2/search",
            code,
            "upstream error",
            headers or {},
            None,
        )

    def test_401_is_not_retried(self):
        calls = []
        sleeps = []

        def opener(request, timeout):
            calls.append(request.full_url)
            raise self.http_error(401)

        with self.assertRaises(urllib.error.HTTPError):
            collector.fetch_page(25, opener=opener, sleeper=sleeps.append)

        self.assertEqual(len(calls), 1)
        self.assertEqual(sleeps, [])

    def test_403_and_429_stop_the_batch(self):
        for code in (401, 403, 429):
            self.assertTrue(collector.should_stop_batch(self.http_error(code)))

    def test_503_retries_once_then_succeeds(self):
        calls = []
        sleeps = []

        def opener(request, timeout):
            calls.append(request.full_url)
            if len(calls) == 1:
                raise self.http_error(503)
            return io.BytesIO(json.dumps({"products": []}).encode())

        payload = collector.fetch_page(25, opener=opener, sleeper=sleeps.append)
        self.assertEqual(payload["products"], [])
        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [7])

    def test_persistent_503_stops_after_bounded_retry(self):
        calls = []
        sleeps = []

        def opener(request, timeout):
            calls.append(request.full_url)
            raise self.http_error(503)

        with self.assertRaises(urllib.error.HTTPError):
            collector.fetch_page(25, opener=opener, sleeper=sleeps.append)

        self.assertEqual(len(calls), 2)
        self.assertEqual(sleeps, [7])
        self.assertTrue(collector.should_stop_batch(self.http_error(503)))

    def test_long_retry_after_is_not_ignored_or_retried(self):
        calls = []
        sleeps = []

        def opener(request, timeout):
            calls.append(request.full_url)
            raise self.http_error(503, {"Retry-After": "600"})

        with self.assertRaises(urllib.error.HTTPError):
            collector.fetch_page(25, opener=opener, sleeper=sleeps.append)

        self.assertEqual(len(calls), 1)
        self.assertEqual(sleeps, [])

    def test_collector_stops_after_first_access_denial(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "candidates.csv"
            state = pathlib.Path(directory) / "state.json"

            def fetcher(page):
                calls.append(page)
                raise self.http_error(401)

            result = collector.collect(
                start_page=25,
                max_pages=20,
                output=output,
                state=state,
                fetcher=fetcher,
                sleeper=lambda _: None,
            )

            self.assertEqual(calls, [25])
            self.assertEqual(result["pages_attempted"], 1)
            self.assertEqual(result["pages_this_run"], 0)
            self.assertEqual(result["new_ingredient_products"], 0)
            self.assertEqual(result["status"], "source_unavailable")
            self.assertEqual(result["stop_reason"], "upstream_access_or_server_failure")
            self.assertEqual(json.loads(state.read_text())["errors"][0]["page"], 25)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
