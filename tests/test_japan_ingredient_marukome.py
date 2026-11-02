"""Marukome official Japanese ingredient source; fail closed on missing fields."""
import sys
import sqlite3
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from crawl_japanese_ingredients import Collector, allowed_link, extract, product_url, source

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

    def test_business_catalogue_and_explicit_product_declaration(self):
        # Business catalogue product identifiers have an official trailing
        # letter (e.g. miso_045b), unlike consumer product IDs.
        catalogue = "https://www.marukome.co.jp/business/product/miso_b/all/"
        detail = "https://www.marukome.co.jp/business/product/detail/miso_045b/"
        self.assertEqual(source(detail), "marukome.co.jp")
        self.assertTrue(allowed_link(catalogue))
        self.assertFalse(product_url(catalogue))
        self.assertTrue(product_url(detail))
        self.assertTrue(allowed_link(detail))
        self.assertFalse(allowed_link("https://www.marukome.co.jp/business/recipe/"))

        # The manufacturer explicitly lists the ingredients for the 10kg/20kg
        # business packs together. Do not fabricate a JAN for either size.
        html = """<html><head><title>プロ用白 10kg / 20kg｜マルコメ</title></head>
        <body><h1>商品情報</h1><dl>
        <dt>内容量</dt><dd>10kg / 20kg</dd>
        <dt>原材料</dt><dd>大豆（アメリカ又はカナダ又はその他）、米、食塩／酒精</dd>
        <dt>アレルゲン</dt><dd>大豆</dd>
        </dl></body></html>"""
        record, reason = extract(html, detail)
        self.assertIsNone(reason)
        self.assertEqual(record["name_ja"], "プロ用白 10kg / 20kg")
        self.assertEqual(record["ingredients_ja"], "大豆（アメリカ又はカナダ又はその他）、米、食塩／酒精")
        self.assertIsNone(record["jan"])
        self.assertFalse(record.get("halal_certified", False))

    def test_legacy_business_navigation_pages_requeued_once(self):
        detail = "https://www.marukome.co.jp/business/product/detail/miso_045b/"
        missing = "https://www.marukome.co.jp/business/product/detail/miso_999b/"
        with tempfile.TemporaryDirectory() as tmp:
            state = sqlite3.connect(str(Path(tmp) / "state.sqlite3"))
            state.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)")
            state.execute("INSERT INTO metadata VALUES(?,?)",
                          ("extractor_version", "official-fields-2026-11-02-v10-natori-core"))
            state.execute("""CREATE TABLE queue(
                url TEXT PRIMARY KEY,status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,next_try REAL DEFAULT 0,error TEXT)""")
            state.execute("INSERT INTO queue VALUES(?,?,?,?,?)",
                          (detail, "done", 1, 0, None))
            state.execute("INSERT INTO queue VALUES(?,?,?,?,?)",
                          (missing, "done", 1, 0, "HTTPError:404"))
            state.commit()
            state.close()
            collector = Collector(tmp, 100)
            self.assertEqual(collector.db.execute(
                "SELECT status FROM queue WHERE url=?", (detail,)).fetchone()[0], "pending")
            self.assertEqual(collector.db.execute(
                "SELECT status FROM queue WHERE url=?", (missing,)).fetchone()[0], "done")
            collector.db.execute("UPDATE queue SET status='done' WHERE url=?", (detail,))
            collector.db.commit()
            collector.db.close()
            reopened = Collector(tmp, 100)
            self.assertEqual(reopened.db.execute(
                "SELECT status FROM queue WHERE url=?", (detail,)).fetchone()[0], "done")
            reopened.db.close()

    def test_missing_declaration_fails_closed(self):
        html = "<html><title>料亭の味（だし入り）｜マルコメ</title><h1>商品情報</h1><p>大豆アレルギー</p></html>"
        record, reason = extract(html, DETAIL)
        self.assertIsNone(record)
        self.assertEqual(reason, "missing_or_ambiguous_ingredients")


if __name__ == "__main__":
    unittest.main()
