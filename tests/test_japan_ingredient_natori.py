import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from crawl_japanese_ingredients import Collector, allowed_link, canonical, extract, product_url, source


class NatoriOfficialCatalogueTests(unittest.TestCase):
    PRODUCT = "https://www.natori.co.jp/products_search/squid/item_546"
    SEARCH = ("https://www.natori.co.jp/products_search/search?"
              "formid=shared-area6.formgrid1col1-form&"
              "ible-categoryselectbox1=%E6%B0%B4%E7%94%A3&"
              "ible-categoryselectbox2=&ible-keyword1=&page=2")

    def test_only_supported_natori_product_urls_are_products(self):
        self.assertEqual(source(self.PRODUCT), "natori.co.jp")
        self.assertTrue(product_url(self.PRODUCT))
        self.assertTrue(allowed_link(self.PRODUCT))
        self.assertTrue(allowed_link("https://www.natori.co.jp/products.html"))
        self.assertTrue(allowed_link(self.SEARCH))
        self.assertFalse(product_url(self.SEARCH))
        self.assertFalse(allowed_link("https://www.natori.co.jp/company/"))

    def test_official_category_filters_survive_canonicalization(self):
        url = canonical(self.SEARCH + "&tracking_id=untrusted")
        params = parse_qs(urlsplit(url).query)
        self.assertEqual(params["ible-categoryselectbox1"], ["水産"])
        self.assertEqual(params["page"], ["2"])
        self.assertEqual(params["formid"], ["shared-area6.formgrid1col1-form"])
        self.assertNotIn("tracking_id", params)

    def test_labelled_ingredients_without_jan_remain_uncertified(self):
        html = ('<html><head><title>ソフトいか燻製│株式会社なとり</title></head>'
                '<body><h1>ソフトいか燻製</h1><h3>内容量</h3><p>60g</p>'
                '<h3>原材料名</h3><p>いか（ペルー）、砂糖、発酵調味料、食塩</p>'
                '<h3>栄養成分表</h3><p>145kcal</p></body></html>')
        record, reason = extract(html, self.PRODUCT)
        self.assertIsNone(reason)
        self.assertEqual(record["name_ja"], "ソフトいか燻製")
        self.assertEqual(record["ingredients_ja"], "いか（ペルー）、砂糖、発酵調味料、食塩")
        self.assertIsNone(record["jan"])
        self.assertEqual(record["source_publisher"], "natori.co.jp")
        self.assertEqual(record["ingredient_field_status"], "complete_displayed_field")
        self.assertFalse(record["live_database_updated"])

    def test_missing_declaration_does_not_create_a_record(self):
        record, reason = extract(
            "<html><h1>ソフトいか燻製</h1><p>いか風味のおやつ</p></html>", self.PRODUCT)
        self.assertIsNone(record)
        self.assertEqual(reason, "missing_or_ambiguous_ingredients")

    def test_new_natori_product_seed_precedes_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            collector.permitted = lambda url: True
            collector.request = lambda url: (
                "<html><h1>ソフトいか燻製</h1>"
                "<h3>原材料名</h3><p>いか、食塩</p></html>"
            )
            collector.run(["https://www.natori.co.jp/products.html", self.PRODUCT],
                          max_pages=1, minutes=1)
            observed = collector.db.execute(
                "SELECT url,reason FROM observations ORDER BY rowid LIMIT 1"
            ).fetchone()
            self.assertEqual(observed, (self.PRODUCT, "accepted_new_product"))


    def test_live_natori_nested_div_label_extracts_exact_declaration(self):
        # Real Natori product-page structure observed on 2026-11-02:
        # label and value are sibling ible-part divs within the same block.
        html = ('<html><title>ソフトいか燻製│株式会社なとり</title>'
                '<h1>ソフトいか燻製</h1>'
                '<div class="ible-block">'
                '<div class="ible-part__html"><div class="ible-part__core">'
                '<h3 class="db_subtitle03">原材料名</h3></div></div>'
                '<div class="ible-part__html white_bg"><div class="ible-part__core">'
                'いか（ペルー）、砂糖、発酵調味料、食塩、醸造酢／ソルビトール'
                '</div></div></div>'
                '<table><tr><th>エネルギー</th><td>145kcal</td></tr></table>'
                '</html>')
        record, reason = extract(html, self.PRODUCT)
        self.assertIsNone(reason)
        self.assertEqual(record["ingredients_ja"],
                         "いか（ペルー）、砂糖、発酵調味料、食塩、醸造酢／ソルビトール")
        self.assertIsNone(record["jan"])
        self.assertFalse(record["live_database_updated"])

    def test_nested_div_without_label_never_guesses_ingredients(self):
        html = ('<html><h1>ソフトいか燻製</h1><div class="ible-block">'
                '<div class="ible-part__html"><div class="ible-part__core">'
                '<h3>栄養成分表</h3></div></div>'
                '<div class="ible-part__html"><div class="ible-part__core">'
                'いか、食塩</div></div></div></html>')
        record, reason = extract(html, self.PRODUCT)
        self.assertIsNone(record)
        self.assertEqual(reason, "missing_or_ambiguous_ingredients")

    def test_old_natori_field_failures_requeued_once_without_touching_404(self):
        with tempfile.TemporaryDirectory() as directory:
            collector = Collector(directory, 100)
            collector.db.execute(
                "INSERT INTO queue(url,status,error) VALUES(?,?,?)",
                (self.PRODUCT, "done", "missing_or_ambiguous_ingredients"))
            missing = "https://www.natori.co.jp/products_search/cod/item_545"
            collector.db.execute(
                "INSERT INTO queue(url,status,error) VALUES(?,?,?)",
                (missing, "done", "HTTPError:404"))
            collector.db.execute(
                "UPDATE metadata SET value=? WHERE key='extractor_version'",
                ("official-fields-2026-11-01-v9-asahi-maintenance",))
            collector.db.commit()
            collector.db.close()
            upgraded = Collector(directory, 100)
            self.assertEqual(upgraded.db.execute(
                "SELECT status,error FROM queue WHERE url=?", (self.PRODUCT,)
            ).fetchone(), ("pending", None))
            self.assertEqual(upgraded.db.execute(
                "SELECT status,error FROM queue WHERE url=?", (missing,)
            ).fetchone(), ("done", "HTTPError:404"))
            upgraded.db.close()


if __name__ == "__main__":
    unittest.main()
