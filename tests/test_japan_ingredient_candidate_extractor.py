import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from extract_crawl_ingredient_candidates import extract_candidate_records


class IngredientCandidateExtractorTests(unittest.TestCase):
    def record(self, url, evidence, barcode_candidates=None):
        return {
            "source_url": url,
            "page_title": "明治北海道十勝ヨーグルト 400g | ヨーグルト | 株式会社 明治",
            "evidence": evidence,
            "barcode_candidates": barcode_candidates or [],
            "verification": "needs_human_review",
            "halal_certified": False,
            "page_sha256": "a" * 64,
        }

    def test_numeric_product_url_and_generic_barcode_candidates_are_not_jan(self):
        record = self.record(
            "https://www.meiji.co.jp/products/yogurt/4902705133099.html",
            ["原材料名 | 乳製品（国内製造、外国製造）、砂糖\n内容量 | 400g"],
            ["4902705133099", "4902705096707"],
        )
        rows = extract_candidate_records([record], exported_at="2026-11-22T00:00:00Z")
        self.assertEqual(1, len(rows))
        self.assertEqual("", rows[0]["jan_code"])
        self.assertEqual("[]", rows[0]["jan_code_candidates"])
        self.assertEqual("明治北海道十勝ヨーグルト 400g", rows[0]["product_name"])
        self.assertEqual("false", rows[0]["halal_certified"])
        self.assertEqual("needs_human_review", rows[0]["verification_status"])

    def test_explicit_label_and_valid_checksum_capture_jan(self):
        record = self.record(
            "https://www.yamaki.co.jp/catalog/products/index.php?id=86",
            ["JANコード | 4903065061206\n原材料名\n食塩（国内製造）、ぶどう糖、風味原料（かつおぶし粉末）"],
        )
        rows = extract_candidate_records([record], exported_at="2026-11-22T00:00:00Z")
        self.assertEqual("4903065061206", rows[0]["jan_code"])
        self.assertEqual('["4903065061206"]', rows[0]["jan_code_candidates"])

    def test_multiple_explicit_jans_are_not_guessed(self):
        record = self.record(
            "https://example.co.jp/products/item.html",
            [
                "JANコード 4903065061206\nJANコード 4903065061077\n"
                "原材料名 食塩（国内製造）、ぶどう糖、かつおぶし粉末"
            ],
        )
        rows = extract_candidate_records([record], exported_at="2026-11-22T00:00:00Z")
        self.assertEqual("", rows[0]["jan_code"])
        self.assertEqual(
            ["4903065061206", "4903065061077"],
            json.loads(rows[0]["jan_code_candidates"]),
        )

    def test_allergen_only_text_is_not_an_ingredient_record(self):
        record = self.record(
            "https://example.co.jp/products/item.html",
            ["アレルギー情報 小麦、卵、乳成分"],
        )
        self.assertEqual([], extract_candidate_records([record], exported_at="2026-11-22T00:00:00Z"))


if __name__ == "__main__":
    unittest.main()
