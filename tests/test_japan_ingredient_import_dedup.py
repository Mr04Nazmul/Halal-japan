import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from japan_ingredient_import_dedup import filter_existing_jan_conflicts, filter_existing_source_conflicts


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



class SourceUrlCollisionTests(unittest.TestCase):
    def test_jan13_new_identity_skips_existing_url_identity(self):
        rows = [{"identity_key": "jan:4902705133099", "jan_code": "4902705133099",
                 "source_url": "https://www.meiji.co.jp/products/yogurt/4902705133099.html"}]
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            self.assertIn("select=identity_key,source_url", req.full_url)
            self.assertNotIn("identity_key=in.", req.full_url)
            return io.BytesIO(b'[{"identity_key":"url:existing-meiji","source_url":"https://www.meiji.co.jp/products/yogurt/4902705133099.html"}]')
        safe, conflicts = filter_existing_source_conflicts(rows, "https://example", "test", opener)
        self.assertEqual(safe, [])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(len(calls), 1)

    def test_existing_identity_is_idempotent(self):
        row = {"identity_key": "jan:123", "source_url": "https://example.org/a"}
        def opener(req, timeout):
            return io.BytesIO(b'[{"identity_key":"jan:123","source_url":"https://example.org/a"}]')
        self.assertEqual(filter_existing_source_conflicts([row], "https://example", "test", opener),
                         ([row], []))

    def test_same_batch_duplicate_url_is_skipped(self):
        rows = [
            {"identity_key": "url:a", "source_url": "https://example.org/product"},
            {"identity_key": "jan:123", "source_url": "https://example.org/product"},
        ]
        def opener(req, timeout):
            return io.BytesIO(b"[]")
        safe, conflicts = filter_existing_source_conflicts(rows, "https://example", "test", opener)
        self.assertEqual(len(safe), 1)
        self.assertEqual(len(conflicts), 1)

    def test_failed_lookup_blocks_import(self):
        def opener(req, timeout):
            raise urllib.error.URLError("unavailable")
        with self.assertRaisesRegex(RuntimeError, "refusing unsafe import"):
            filter_existing_source_conflicts(
                [{"identity_key": "jan:123", "source_url": "https://example.org/product"}],
                "https://example", "test", opener)

    def test_paged_index_detects_conflict_on_second_page(self):
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            if "offset=0" in req.full_url:
                return io.BytesIO(json.dumps([
                    {"identity_key": f"old:{i:04d}", "source_url": f"https://example.org/{i}"}
                    for i in range(1000)]).encode())
            self.assertIn("offset=1000", req.full_url)
            return io.BytesIO(b'[{"identity_key":"old:last","source_url":"https://example.org/collision"}]')
        rows = [{"identity_key": "jan:new", "source_url": "https://example.org/collision"}]
        safe, conflicts = filter_existing_source_conflicts(rows, "https://example", "test", opener)
        self.assertEqual(safe, [])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(len(calls), 2)

    def test_malformed_index_fails_closed(self):
        def opener(req, timeout):
            return io.BytesIO(b'[{"source_url":"https://example.org/a"}]')
        with self.assertRaisesRegex(RuntimeError, "malformed row"):
            filter_existing_source_conflicts(
                [{"identity_key": "jan:new", "source_url": "https://example.org/a"}],
                "https://example", "test", opener)


if __name__ == "__main__":
    unittest.main()
