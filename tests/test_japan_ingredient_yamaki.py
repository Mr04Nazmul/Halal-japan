"""Yamaki catalogue: only exact labelled ingredient text and checksum-valid JAN."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from crawl_japanese_ingredients import source, product_url, allowed_link, canonical, extract

URL = "https://www.yamaki.co.jp/catalog/products/?id=42"
URL_INDEX = "https://www.yamaki.co.jp/catalog/products/index.php?id=58"

class YamakiOfficialSourceTests(unittest.TestCase):
    def test_exact_catalogue_product_url_scope(self):
        self.assertEqual(source(URL), "yamaki.co.jp")
        self.assertTrue(product_url(URL))
        self.assertTrue(product_url(URL_INDEX))
        self.assertTrue(allowed_link(URL_INDEX))
        self.assertFalse(product_url("https://www.yamaki.co.jp/catalog/products/"))
        self.assertFalse(product_url("https://www.yamaki.co.jp/catalog/products/?id=bad"))
        self.assertEqual(canonical(URL), URL)

    def test_labelled_ingredients_and_jan(self):
        html = """<html><head><title>煮干 90g | 商品情報 | ヤマキ株式会社</title></head>
        <body><h1>煮干 90g</h1><dl>
        <dt>JANコード</dt><dd>4903065117101</dd>
        <dt>原材料名</dt><dd>かたくちいわし（国内産）、食塩 / 酸化防止剤（ビタミンE）</dd>
        </dl><p>アレルギー情報：えび・かに・豚肉・ゼラチン</p></body></html>"""
        record, error = extract(html, URL)
        self.assertIsNone(error)
        self.assertEqual(record["name_ja"], "煮干 90g")
        self.assertEqual(record["jan"], "4903065117101")
        self.assertEqual(record["ingredients_ja"], "かたくちいわし（国内産）、食塩 / 酸化防止剤（ビタミンE）")
        self.assertEqual(record["source_url"], URL)
        self.assertFalse(record.get("halal_certified", False))

    def test_heading_based_label_and_no_invented_jan(self):
        html = """<html><head><title>かつおパック 4g×8P | ヤマキ</title></head>
        <body><h1>かつおパック 4g×8P</h1>
        <h2>原材料名</h2><p>かつおのふし（国内製造）</p></body></html>"""
        record, error = extract(html, "https://www.yamaki.co.jp/catalog/products/?id=162")
        self.assertIsNone(error)
        self.assertEqual(record["ingredients_ja"], "かつおのふし（国内製造）")
        self.assertIsNone(record["jan"])

    def test_allergens_only_rejected(self):
        html = "<html><h1>煮干 90g</h1><h2>アレルギー情報</h2><p>小麦・乳・豚肉・ゼラチン</p></html>"
        record, error = extract(html, URL)
        self.assertIsNone(record)
        self.assertEqual(error, "missing_or_ambiguous_ingredients")

if __name__ == "__main__":
    unittest.main()
