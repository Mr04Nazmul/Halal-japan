"""Kirin official soft-drink product evidence is discovered without guessing JANs."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from crawl_japanese_ingredients import allowed_link, canonical, extract, product_url, source

DETAIL = "https://products.kirin.co.jp/softdrink/softdrink/detail.html?id=9057"
CATALOGUE = "https://products.kirin.co.jp/softdrink/nutrition/softdrink/"
HTML = """<html><head><title>キリン おいしい免疫ケア｜商品情報</title></head>
<body><main><h1>キリン おいしい免疫ケア 100ml ペットボトル</h1>
<section><h2>原材料名</h2><p>砂糖（国内製造）、脱脂粉乳、乳酸菌末／酸味料、安定剤（増粘多糖類：大豆由来）、香料、シリコーン</p></section>
<table><tr><th>JANコード</th><td>単品：45216671</td></tr>
<tr><th>容量</th><td>100ml</td></tr></table></main></body></html>"""

class KirinOfficialSourceTests(unittest.TestCase):
    def test_official_softdrink_catalogue_and_details_only(self):
        self.assertEqual(source(DETAIL), "kirin.co.jp")
        self.assertTrue(allowed_link(CATALOGUE))
        self.assertTrue(product_url(DETAIL))
        self.assertEqual(canonical(DETAIL), DETAIL)
        self.assertFalse(allowed_link("https://products.kirin.co.jp/alcohol/"))

    def test_labelled_ingredient_and_valid_jan8(self):
        record, reason = extract(HTML, DETAIL)
        self.assertIsNone(reason)
        self.assertEqual(record["jan"], "45216671")
        self.assertEqual(record["name_ja"], "キリン おいしい免疫ケア 100ml ペットボトル")
        self.assertIn("脱脂粉乳", record["ingredients_ja"])
        self.assertEqual(record["source_url"], DETAIL)
        self.assertEqual(record["source_publisher"], "kirin.co.jp")
        self.assertFalse(record.get("halal_certified", False))

    def test_missing_labelled_ingredients_fails_closed(self):
        html = "<h1>キリン テスト飲料</h1><h2>アレルゲン</h2><p>乳、大豆</p>"
        record, reason = extract(html, DETAIL)
        self.assertIsNone(record)
        self.assertEqual(reason, "missing_or_ambiguous_ingredients")

if __name__ == "__main__":
    unittest.main()
