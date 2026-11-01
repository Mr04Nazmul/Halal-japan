"""Marukome official Japanese ingredient source; fail closed on missing fields."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from crawl_japanese_ingredients import allowed_link, extract, product_url, source

DETAIL = "https://www.marukome.co.jp/product/detail/miso_001/"
CATALOGUE = "https://www.marukome.co.jp/product/"
HTML = """<html><head><title>料亭の味（だし入り）｜マルコメ</title></head>
<body><h1>商品情報</h1><dl>
<dt>内容量</dt><dd>750g / 375g</dd>
<dt>原材料</dt><dd>大豆（アメリカ又はカナダ又はその他）、米、食塩、かつおエキス、かつお節粉末、昆布エキス／調味料（アミノ酸等）、酒精、（一部に大豆を含む）</dd>
<dt>アレルギー</dt><dd>大豆</dd>
</dl></body></html>"""


class MarukomeOfficialSourceTests(unittest.TestCase):
    def test_catalogue_and_detail_scope(self):
        self.assertEqual(source(DETAIL), "marukome.co.jp")
        self.assertTrue(product_url(DETAIL))
        self.assertTrue(allowed_link(CATALOGUE))
        self.assertFalse(product_url(CATALOGUE))
        self.assertFalse(allowed_link("https://www.marukome.co.jp/recipe/"))

    def test_explicit_ingredient_field_no_invented_jan(self):
        record, reason = extract(HTML, DETAIL)
        self.assertIsNone(reason)
        self.assertEqual(record["name_ja"], "料亭の味（だし入り）")
        self.assertEqual(record["ingredients_ja"], "大豆（アメリカ又はカナダ又はその他）、米、食塩、かつおエキス、かつお節粉末、昆布エキス／調味料（アミノ酸等）、酒精、（一部に大豆を含む）")
        self.assertIsNone(record["jan"])
        self.assertEqual(record["source_publisher"], "marukome.co.jp")
        self.assertEqual(record["ingredient_field_status"], "complete_displayed_field")
        self.assertFalse(record.get("halal_certified", False))

    def test_missing_declaration_fails_closed(self):
        html = "<html><title>料亭の味（だし入り）｜マルコメ</title><h1>商品情報</h1><p>大豆アレルギー</p></html>"
        record, reason = extract(html, DETAIL)
        self.assertIsNone(record)
        self.assertEqual(reason, "missing_or_ambiguous_ingredients")


if __name__ == "__main__":
    unittest.main()
