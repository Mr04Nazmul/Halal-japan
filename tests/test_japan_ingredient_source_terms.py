import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from japan_ingredient_source_terms import (
    RESTRICTED_SOURCE_POLICIES,
    is_terms_restricted_url,
    source_terms_restriction,
)
from crawl_japanese_ingredients import (allowed_link, product_url, SOURCE_TERMS_QUARANTINE_KEY, quarantine_restricted_pending_sources)


class SourceTermsPolicyTests(unittest.TestCase):
    def test_reviewed_reuse_blocks_are_withheld(self):
        examples = {
            "https://agf.ajinomoto.co.jp/product/detail/14113": "agf.ajinomoto.co.jp",
            "https://www.ajinomoto.co.jp/products/": "ajinomoto.co.jp",
            "https://www.asahi-gf.co.jp/products/food/": "asahi-gf.co.jp",
            "https://www.asahiinryo.co.jp/products/": "asahiinryo.co.jp",
            "https://www.askul.co.jp/p/U217658/": "askul.co.jp",
            "https://www.fujiya-peko.co.jp/sweets/item/26844.html": "fujiya-peko.co.jp",
            "https://www.fujicco.co.jp/products/detail/123": "fujicco.co.jp",
            "https://www.kamedaseika.co.jp/product/2068/": "kamedaseika.co.jp",
            "https://www.sanko-seika.co.jp/product/item/123/": "sanko-seika.co.jp",
            "https://www.bourbon.co.jp/products/detail/123": "bourbon.co.jp",
            "https://www.dydo.co.jp/products/detail/123": "dydo.co.jp",
            "https://www.myojofoods.co.jp/products/items/13987": "myojofoods.co.jp",
            "https://www.natori.co.jp/products_search/item_123": "natori.co.jp",
            "https://www.nissin.com/jp/product/items/13426/": "nissin.com",
            "https://www.sbfoods.co.jp/products/detail/123.html": "sbfoods.co.jp",
            "https://sokensha.co.jp/news/2026/13262/": "sokensha.co.jp",
            "https://www.maruchan.co.jp/products/search/310686.html": "maruchan.co.jp",
            "https://www.meiji.co.jp/products/drink/4902705133150.html": "meiji.co.jp",
            "https://www.meito-abc.co.jp/products/lineup/new": "meito-abc.co.jp",
            "https://www.morinaga.co.jp/products/detail.php?id=PRD1234-56-7890": "morinaga.co.jp",
            "https://www.nagatanien.co.jp/product/detail/1223/": "nagatanien.co.jp",
            "https://muso.co.jp/item/75025.html": "muso.co.jp",
            "https://www.nipponham.co.jp/products/processed_foods/bread_pizza/24216/": "nipponham.co.jp",
            "https://www.tohato.jp/products/caramelcorn/": "tohato.jp",
            "https://www.topvalu.net/items/detail/4902123456789/": "topvalu.net",
            "https://7premium.jp/product/search/detail?id=10791": "7premium.jp",
            "https://www.hikarimiso.co.jp/products/kodawari01/": "hikarimiso.co.jp",
            "https://www.hanamaruki.co.jp/products/instant_soup/sokuseki_wakame/": "hanamaruki.co.jp",
            "https://www.calbee.co.jp/products/detail/?p=20261106232447": "calbee.co.jp",
            "https://www.ebarafoods.com/products/detail/123": "ebarafoods.com",
            "https://www.imuraya.co.jp/goods/zenzai/c-zenzai/noukouz/": "imuraya.co.jp",
            "https://www.kikkoman.co.jp/products/K05/detail/K053515.html": "kikkoman.co.jp",
            "https://www.morinagamilk.co.jp/products/milk/morinagamilk/1254.html": "morinagamilk.co.jp",
            "https://housefoods.jp/products/catalog/cd_1,082683.html": "housefoods.jp",
            "https://www.tablemark.co.jp/products/frozen/rice/detail/7117493.html": "tablemark.co.jp",
            "https://www.lotte.co.jp/products/catalogue/biscuit/01/detail01.html": "lotte.co.jp",
            "https://www.marusanai.co.jp/lineup/detail-64095/": "marusanai.co.jp",
            "https://www.itoen.jp/products/41922/": "itoen.jp",
            "https://www.kewpie.co.jp/products/detail/4901577004865/": "kewpie.co.jp",
            "https://www.meg-snow.com/products/": "meg-snow.com",
            "https://www.yotsuba.co.jp/products/": "yotsuba.co.jp",
            "https://www.tajimaya-cc.net/products/2118": "tajimaya-cc.net",
            "https://www.yamamori.co.jp/products/matsusaka_sukiyaki/": "yamamori.co.jp",
        }
        for url, domain in examples.items():
            with self.subTest(url=url):
                self.assertTrue(is_terms_restricted_url(url))
                self.assertEqual(source_terms_restriction(url)["domain"], domain)
                self.assertIn("https://", source_terms_restriction(url)["policy_url"])

    def test_restrictions_apply_to_subdomains_and_non_https_urls(self):
        self.assertTrue(is_terms_restricted_url("https://shop.meiji.co.jp/product/1"))
        self.assertTrue(is_terms_restricted_url("http://www.fujiya-peko.co.jp/item/1"))
        self.assertTrue(is_terms_restricted_url("https://shop.muso.co.jp/item/1"))
        self.assertTrue(is_terms_restricted_url("https://food.askul.co.jp/p/U217658/"))
        self.assertTrue(is_terms_restricted_url("https://shop.yamamori.co.jp/products/matsusaka_sukiyaki/"))
        self.assertTrue(is_terms_restricted_url("https://shop.sokensha.co.jp/products/example/"))

    def test_kyoritsu_pagination_pages_are_bounded_navigation_not_products(self):
        for page in range(2, 14):
            url = f"https://www.kyoritsu-foods.co.jp/product/page/{page}/"
            with self.subTest(url=url):
                self.assertTrue(allowed_link(url))
                self.assertFalse(product_url(url))
                self.assertFalse(is_terms_restricted_url(url))

    def test_unreviewed_sources_are_not_mislabeled_as_blocked(self):
        # Not yet reviewed for reuse terms; this is not an assertion of permission.
        self.assertFalse(is_terms_restricted_url("https://montoile.co.jp/products/example/"))
        self.assertFalse(is_terms_restricted_url("https://www.kyoritsu-foods.co.jp/product/page/7/"))

    def test_main_crawler_does_not_enqueue_restricted_current_source_pages(self):
        blocked = [
            "https://agf.ajinomoto.co.jp/product/detail/14113",
            "https://www.asahiinryo.co.jp/products/carbonated/wilkinson_tansan_fruity_muscat/2T532.html",
            "https://www.fujicco.co.jp/products/detail/123",
            "https://www.kamedaseika.co.jp/product/2068/",
            "https://www.sanko-seika.co.jp/product/item/123/",
            "https://www.bourbon.co.jp/products/detail/123",
            "https://www.dydo.co.jp/products/detail/123",
            "https://www.myojofoods.co.jp/products/items/13987",
            "https://www.natori.co.jp/products_search/squid/item_546",
            "https://www.nissin.com/jp/product/items/11309/",
            "https://www.sbfoods.co.jp/products/detail/123.html",
            "https://sokensha.co.jp/products/product_detail/161784",
            "https://www.maruchan.co.jp/products/search/310686.html",
            "https://www.meiji.co.jp/products/drink/4902705133150.html",
            "https://www.morinaga.co.jp/products/detail.php?id=PRD1234-56-7890",
            "https://muso.co.jp/item/75025.html",
            "https://www.nipponham.co.jp/products/processed_foods/bread_pizza/24216/",
            "https://www.askul.co.jp/p/U217658/",
            "https://www.hikarimiso.co.jp/products/kodawari01/",
            "https://www.hanamaruki.co.jp/products/instant_soup/sokuseki_wakame/",
            "https://www.calbee.co.jp/products/detail/?p=20261106232447",
            "https://www.ebarafoods.com/products/detail/123",
            "https://www.imuraya.co.jp/goods/zenzai/c-zenzai/noukouz/",
            "https://www.kikkoman.co.jp/products/K05/detail/K053515.html",
            "https://www.morinagamilk.co.jp/products/milk/morinagamilk/1254.html",
            "https://housefoods.jp/products/catalog/cd_1,082683.html",
            "https://www.tablemark.co.jp/products/frozen/rice/detail/7117493.html",
            "https://www.lotte.co.jp/products/catalogue/biscuit/01/detail01.html",
            "https://www.marusanai.co.jp/lineup/detail-64095/",
            "https://www.itoen.jp/products/41922/",
            "https://www.kewpie.co.jp/products/detail/4901577004865/",
            "https://www.meg-snow.com/products/",
            "https://www.yotsuba.co.jp/products/",
            "https://www.tajimaya-cc.net/products/2118",
            "https://www.nagatanien.co.jp/product/detail/1223/",
            "https://www.topvalu.net/items/detail/4902123456789/",
            "https://7premium.jp/product/search/detail?id=10791",
            "https://www.yamamori.co.jp/products/matsusaka_sukiyaki/",
            "https://www.yamamori.co.jp/business/",
        ]
        for url in blocked:
            with self.subTest(url=url):
                self.assertFalse(allowed_link(url))

    def test_policy_contains_only_reviewed_reuse_blocks(self):
        self.assertEqual(
            set(RESTRICTED_SOURCE_POLICIES),
            {
                "agf.ajinomoto.co.jp",
                "askul.co.jp",
                "ajinomoto.co.jp",
                "asahi-gf.co.jp",
                "asahiinryo.co.jp",
                "fujiya-peko.co.jp",
                "fujicco.co.jp",
                "kamedaseika.co.jp",
                "sanko-seika.co.jp",
                "bourbon.co.jp",
                "dydo.co.jp",
                "maruchan.co.jp",
                "myojofoods.co.jp",
                "natori.co.jp",
                "nissin.com",
                "sbfoods.co.jp",
                "meiji.co.jp",
                "meito-abc.co.jp",
                "morinaga.co.jp",
                "nagatanien.co.jp",
                "muso.co.jp",
                "nipponham.co.jp",
                "tohato.jp",
                "topvalu.net",
                "7premium.jp",
                "hikarimiso.co.jp",
                "hanamaruki.co.jp",
                "calbee.co.jp",
                "ebarafoods.com",
                "imuraya.co.jp",
                "kikkoman.co.jp",
                "morinagamilk.co.jp",
                "housefoods.jp",
                "tablemark.co.jp",
                "lotte.co.jp",
                "marusanai.co.jp",
                "itoen.jp",
                "kewpie.co.jp",
                "meg-snow.com",
                "yotsuba.co.jp",
                "tajimaya-cc.net",
                "yamamori.co.jp",
                "sokensha.co.jp",
            },
        )


    def test_blocked_pending_queue_is_quarantined_once_without_deleting_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            db = sqlite3.connect(Path(directory) / "test.sqlite3")
            db.executescript("""
                CREATE TABLE queue(
                    url TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'pending',
                    attempts INTEGER DEFAULT 0,
                    next_try REAL DEFAULT 0,
                    error TEXT
                );
                CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT);
            """)
            blocked = "https://www.nagatanien.co.jp/product/detail/1223/"
            blocked_yamamori = "https://www.yamamori.co.jp/products/matsusaka_sukiyaki/"
            blocked_sokensha = "https://sokensha.co.jp/news/2026/13262/"
            allowed = "https://montoile.co.jp/products/ashitamo-okura-norishio/"
            db.executemany("INSERT INTO queue(url) VALUES(?)",
                           [(blocked,), (blocked_yamamori,), (blocked_sokensha,), (allowed,)])
            db.commit()
            changed = quarantine_restricted_pending_sources(db)
            self.assertEqual(changed, 3)
            rows = dict(db.execute("SELECT url,status FROM queue"))
            self.assertEqual(rows[blocked], "done")
            self.assertEqual(rows[blocked_yamamori], "done")
            self.assertEqual(rows[blocked_sokensha], "done")
            self.assertEqual(rows[allowed], "pending")
            self.assertEqual(db.execute("SELECT count(*) FROM queue").fetchone()[0], 4)
            self.assertEqual(quarantine_restricted_pending_sources(db), 0)
            db.close()


if __name__ == "__main__":
    unittest.main()
