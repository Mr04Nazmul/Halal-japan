"""Nichirei official product pages: exact ingredient heading and adjacent JAN only."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from crawl_japanese_ingredients import source, product_url, allowed_link, extract

URL = "https://www.nichireifoods.co.jp/product/detail/sho_id150/"

class NichireiOfficialSourceTests(unittest.TestCase):
    def test_product_scope_and_catalogue(self):
        self.assertEqual(source(URL), "nichireifoods.co.jp")
        self.assertTrue(product_url(URL))
        self.assertTrue(allowed_link(URL))
        self.assertTrue(allowed_link("https://www.nichireifoods.co.jp/product/"))
        self.assertTrue(allowed_link("https://www.nichireifoods.co.jp/product/frozenfood/pc7/"))
        self.assertFalse(product_url("https://www.nichireifoods.co.jp/product/"))
        self.assertFalse(product_url("https://www.nichireifoods.co.jp/media/15531/"))

    def test_official_labelled_ingredients_and_adjacent_jan(self):
        html = """<html><head><title>香り枝豆（塩味付） - 商品情報 - ニチレイフーズ</title></head>
        <body><h1>香り枝豆（塩味付）</h1>
        <li class="p-data-list--info">
          <span class="p-data-list--info__name">JAN<br>コード</span>
          <div id="js-jan-code" class="p-data-list--info__text">4902130359873</div>
        </li>
        <section class="l-content__inner--pb-only">
          <h2 class="c-heading-08">原材料名</h2>
          <p>えだまめ（大豆）、食塩</p>
        </section>
        <section><h2>本商品に含まれるアレルギー物質</h2><p>ゼラチン</p></section>
        </body></html>"""
        record, error = extract(html, URL)
        self.assertIsNone(error)
        self.assertEqual(record["name_ja"], "香り枝豆（塩味付）")
        self.assertEqual(record["jan"], "4902130359873")
        self.assertEqual(record["ingredients_ja"], "えだまめ（大豆）、食塩")
        self.assertFalse(record.get("halal_certified", False))

    def test_allergen_only_is_not_ingredient_evidence(self):
        html = """<html><h1>香り枝豆（塩味付）</h1>
        <section><h2>本商品に含まれるアレルギー物質</h2>
        <p>大豆・ゼラチン</p></section></html>"""
        record, error = extract(html, URL)
        self.assertIsNone(record)
        self.assertEqual(error, "missing_or_ambiguous_ingredients")

    def test_missing_or_invalid_jan_is_not_guessed(self):
        html = """<html><h1>香り枝豆（塩味付）</h1>
        <li class="p-data-list--info">
        <span class="p-data-list--info__name">JAN<br>コード</span>
        <div class="p-data-list--info__text">4902130359874</div></li>
        <section><h2>原材料名</h2><p>えだまめ（大豆）、食塩</p></section></html>"""
        record, error = extract(html, URL)
        self.assertIsNone(error)
        self.assertIsNone(record["jan"])
        self.assertEqual(record["source_url"], URL)

if __name__ == "__main__":
    unittest.main()
