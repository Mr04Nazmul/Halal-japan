import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from crawl_japanese_ingredients import allowed_link, extract, extract_many, product_url

RELEASE_URL = "https://sokensha.co.jp/news/2026/13262/"
SALT_INGREDIENTS = "水飴（国内製造（馬鈴薯澱粉、甘藷澱粉、大麦麦芽））、砂糖（てんさい（国産））、小麦粉（岐阜）、昆布（北海道）、米粉（国産）、レモン果汁パウダー、食塩（伊豆大島近海）、澱粉／香料"
STRAWBERRY_INGREDIENTS = "水飴（国内製造（馬鈴薯澱粉、甘藷澱粉、大麦麦芽））、砂糖（てんさい（国産））、小麦粉（岐阜）、昆布（北海道）、米粉（国産）、いちご果汁パウダー、澱粉／香料"

RELEASE_HTML = f"""
<h1>『海のめぐみのもっちりキャンディー 塩レモン味・いちご味』11月16日新発売</h1>
<p>2026.11.11</p>
<table>
<tr><th>項目</th><td>塩レモン味</td><td>いちご味</td></tr>
<tr><th>商品名</th><td>海のめぐみのもっちりキャンディー 塩レモン味</td><td>海のめぐみのもっちりキャンディー いちご味</td></tr>
<tr><th>内容量</th><td>45g（個包装込み）</td><td>45g（個包装込み）</td></tr>
<tr><th>JANコード</th><td>4901735026081</td><td>4901735026173</td></tr>
<tr><th>原材料名</th><td>{SALT_INGREDIENTS}</td><td>{STRAWBERRY_INGREDIENTS}</td></tr>
</table>
"""

LEM_URL = "https://sokensha.co.jp/products/product_detail/161784"
LEM_INGREDIENTS = "砂糖（てんさい（北海道））、水飴、マヌカはちみつ、はちみつ、レモン果汁パウダー、シイタケ菌糸体培養培地抽出物"
LEM_HTML = f"""
<title>創健社 おまもりのど飴 LEMキャンディ はちみつレモン味 | 株式会社創健社</title>
<h1>創健社 おまもりのど飴 ＬＥＭ（Ｒ）キャンディ はちみつレモン味 ５０g（個包装込み）</h1>
<table><tr><th>POSコード</th><td>4901735026180</td></tr></table>
<h3>原材料(一括表示ラベル)</h3><div>{LEM_INGREDIENTS}</div>
"""


class SokenshaReleaseExtraction(unittest.TestCase):
    def test_release_is_allowed_and_extracts_two_separate_products(self):
        self.assertTrue(product_url(RELEASE_URL))
        # Offline extraction fixtures remain useful, but live collection is paused until reuse permission is established.
        self.assertFalse(allowed_link(RELEASE_URL))

        records, error = extract_many(RELEASE_HTML, RELEASE_URL)

        self.assertIsNone(error)
        self.assertEqual(len(records), 2)
        self.assertEqual(
            [record["jan"] for record in records],
            ["4901735026081", "4901735026173"],
        )
        self.assertEqual(
            [record["name_ja"] for record in records],
            [
                "海のめぐみのもっちりキャンディー 塩レモン味",
                "海のめぐみのもっちりキャンディー いちご味",
            ],
        )
        self.assertEqual(
            [record["ingredients_ja"] for record in records],
            [SALT_INGREDIENTS, STRAWBERRY_INGREDIENTS],
        )
        for record in records:
            self.assertEqual(record["source_url"], RELEASE_URL)
            self.assertEqual(record["source_type"], "official_manufacturer_news_release_page")
            self.assertEqual(record["source_published_at"], "2026-11-11")
            self.assertEqual(record["verification_status"], "official_ingredient_field_captured_pending_human_review")
            self.assertEqual(record["reuse_permission"], "not_established")
            self.assertTrue(record["research_only"])
            self.assertFalse(record["packaging_verified"])
            self.assertFalse(record["halal_certified"])

    def test_release_with_missing_ingredient_row_is_not_counted(self):
        broken = RELEASE_HTML.replace("<th>原材料名</th>", "<th>原材料</th>")
        records, error = extract_many(broken, RELEASE_URL)
        self.assertEqual(records, [])
        self.assertEqual(error, "missing_or_ambiguous_ingredients")

    def test_release_with_invalid_jan_is_not_counted(self):
        broken = RELEASE_HTML.replace("4901735026173", "4901735026174")
        records, error = extract_many(broken, RELEASE_URL)
        self.assertEqual(records, [])
        self.assertEqual(error, "invalid_or_duplicate_jan")

    def test_sokensha_product_detail_accepts_explicit_pos_code_and_label(self):
        self.assertTrue(product_url(LEM_URL))
        self.assertFalse(allowed_link(LEM_URL))
        record, error = extract(LEM_HTML, LEM_URL)
        self.assertIsNone(error)
        self.assertEqual(record["jan"], "4901735026180")
        self.assertEqual(record["ingredients_ja"], LEM_INGREDIENTS)
        self.assertEqual(record["ingredient_field_status"], "complete_displayed_field")
        self.assertFalse(record["halal_certified"])


if __name__ == "__main__":
    unittest.main()
