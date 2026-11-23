"""Safety tests for OFF review-queue staging."""

import importlib.util
import json
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "stage_off_ingredient_batch.py"
spec = importlib.util.spec_from_file_location("off_staging", SCRIPT)
staging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(staging)


class OffStagingTests(unittest.TestCase):
    def test_jan_checksum_is_required(self):
        self.assertTrue(staging.valid_ean("4901002018849"))
        self.assertTrue(staging.valid_ean("49012345"))
        self.assertFalse(staging.valid_ean("4901002018848"))
        self.assertFalse(staging.valid_ean("490100201884"))
        self.assertFalse(staging.valid_ean("4006381333931"))  # valid EAN-13 but not Japanese-prefix gated below

    def test_review_rows_keep_off_license_and_unverified_status(self):
        record = {
            "barcode": "4901002018849",
            "name": "けしの実",
            "brand": "テスト食品",
            "ingredients": "けしの実、植物油脂、食塩",
            "source_url": "https://world.openfoodfacts.org/product/4901002018849",
        }
        rows = staging.build_rows([json.dumps(record, ensure_ascii=False)])
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["jan_code"], "4901002018849")
        self.assertEqual(row["evidence_level"], "discovery_only")
        self.assertEqual(row["status"], "needs_review")
        self.assertIn("ODbL-1.0", row["discovery_source"])
        self.assertIn("DbCL-1.0", row["discovery_source"])

    def test_duplicate_barcode_is_only_staged_once(self):
        record = {
            "barcode": "4901002018849",
            "name": "けしの実",
            "brand": "テスト食品",
            "ingredients": "けしの実、植物油脂、食塩",
            "source_url": "https://world.openfoodfacts.org/product/4901002018849",
        }
        line = json.dumps(record, ensure_ascii=False)
        self.assertEqual(len(staging.build_rows([line, line])), 1)

    def test_rejects_non_off_url_and_invalid_checksum(self):
        bad_url = {
            "barcode": "4901002018849",
            "name": "けしの実",
            "brand": "テスト食品",
            "ingredients": "けしの実、植物油脂、食塩",
            "source_url": "https://example.com/product/4901002018849",
        }
        bad_code = dict(bad_url, barcode="4901002018848",
                        source_url="https://world.openfoodfacts.org/product/4901002018848")
        self.assertEqual(staging.build_rows([
            json.dumps(bad_url, ensure_ascii=False),
            json.dumps(bad_code, ensure_ascii=False),
        ]), [])

    def test_rejects_non_japanese_or_incomplete_candidates(self):
        record = {
            "barcode": "4901002018849",
            "name": "Poppy seeds",
            "brand": "Test",
            "ingredients": "poppy seeds, oil, salt",
            "source_url": "https://world.openfoodfacts.org/product/4901002018849",
        }
        self.assertEqual(staging.build_rows([json.dumps(record)]), [])


if __name__ == "__main__":
    unittest.main()
