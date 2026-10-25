import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from japan_ingredient_import_dedup import filter_existing_jan_conflicts


class Jan13StagingCollisionTests(unittest.TestCase):
    def test_different_identity_skipped_without_overwriting(self):
        rows = [
            {"jan_code": "4901325301994", "identity_key": "jan:4901325301994"},
            {"jan_code": "4901002189549", "identity_key": "jan:4901002189549"},
            {"jan_code": None, "identity_key": "url:example"},
        ]
        def opener(req, timeout):
            self.assertIn("jan_code=in.(", req.full_url)
            return io.BytesIO(json.dumps([
                {"jan_code": "4901325301994", "identity_key": "gelatin-origin-20261024:existing"}
            ]).encode())
        safe, skipped = filter_existing_jan_conflicts(rows, "https://example.supabase.co", "test", opener)
        self.assertEqual([r["identity_key"] for r in safe], ["jan:4901002189549", "url:example"])
        self.assertEqual(skipped, ["4901325301994"])

    def test_same_identity_left_for_idempotent_insert(self):
        row = {"jan_code": "4901325301994", "identity_key": "jan:4901325301994"}
        def opener(req, timeout):
            return io.BytesIO(b'[{"jan_code":"4901325301994","identity_key":"jan:4901325301994"}]')
        self.assertEqual(filter_existing_jan_conflicts([row], "https://example", "test", opener), ([row], []))

    def test_failed_lookup_blocks_import(self):
        def opener(req, timeout):
            raise urllib.error.URLError("unavailable")
        with self.assertRaisesRegex(RuntimeError, "refusing unsafe import"):
            filter_existing_jan_conflicts(
                [{"jan_code": "4901325301994", "identity_key": "jan:4901325301994"}],
                "https://example", "test", opener
            )

    def test_no_jan_needs_no_request(self):
        def opener(req, timeout):
            raise AssertionError("should not fetch")
        row = {"jan_code": None, "identity_key": "url:example"}
        self.assertEqual(filter_existing_jan_conflicts([row], "https://example", "test", opener), ([row], []))

    def test_201_candidates_batched(self):
        rows = [{"jan_code": str(4900000000000 + i), "identity_key": "id:" + str(i)} for i in range(201)]
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            return io.BytesIO(b"[]")
        safe, skipped = filter_existing_jan_conflicts(rows, "https://example", "test", opener)
        self.assertEqual(len(calls), 3)
        self.assertEqual(len(safe), 201)
        self.assertFalse(skipped)


if __name__ == "__main__":
    unittest.main()
