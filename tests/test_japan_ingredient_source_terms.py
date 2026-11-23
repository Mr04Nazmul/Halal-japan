import json
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
from crawl_japanese_ingredients import (allowed_link, canonical, kyoritsu_shop_category_url, product_url, SOURCE_TERMS_QUARANTINE_KEY, quarantine_restricted_pending_sources)
from agent_reach_public_sources import build_report


class SourceTermsPolicyTests(unittest.TestCase):
    def test_reviewed_reuse_blocks_are_withheld(self):
        examples = {
            "https://agf.ajinomoto.co.jp/product/detail/14113": "agf.ajinomoto.co.jp",
            "https://www.ajinomoto.co.jp/products/": "ajinomoto.co.jp",
            "https://www.asahi-gf.co.jp/products/food/": "asahi-gf.co.jp",
            "https://www.asahiinryo.co.jp/products/": "asahiinryo.co.jp",
            "https://www.askul.co.jp/p/U217658/": "askul.co.jp",
            "https://www.matsukiyococokara-online.com/products/food/": "matsukiyococokara-online.com",
            "https://www.fujiya-peko.co.jp/sweets/item/26844.html": "fujiya-peko.co.jp",
            "https://www.fujicco.co.jp/products/detail/123": "fujicco.co.jp",
            "https://www.glico.com/jp/product/drink/glicomilk/47200/": "glico.com",
            "https://www.kamedaseika.co.jp/product/2068/": "kamedaseika.co.jp",
            "https://www.sanko-seika.co.jp/product/item/123/": "sanko-seika.co.jp",
            "https://www.bourbon.co.jp/products/detail/123": "bourbon.co.jp",
            "https://www.dydo.co.jp/products/detail/123": "dydo.co.jp",
            "https://www.myojofoods.co.jp/products/items/13987": "myojofoods.co.jp",
            "https://www.natori.co.jp/products_search/item_123": "natori.co.jp",
            "https://www.nissin.com/jp/product/items/13426/": "nissin.com",
            "https://www.sbfoods.co.jp/products/detail/123.html": "sbfoods.co.jp",
            "https://sokensha.co.jp/news/2026/13262/": "sokensha.co.jp",
            "https://montoile.co.jp/products/tenohira-gopan-tomato-basil/": "montoile.co.jp",
            "https://new.ohsawa-japan.co.jp/?actmode=ItemDetail&iid=906": "ohsawa-japan.co.jp",
            "https://www.pokkasapporo-fb.jp/products/soup/jikkuri/WZ02.html": "pokkasapporo-fb.jp",
            "https://www.uha-mikakuto.co.jp/catalog/gummy/gu330.html": "uha-mikakuto.co.jp",
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
            "https://products.kirin.co.jp/softdrink/softdrink/detail.html?id=7380": "kirin.co.jp",
            "https://www.morinagamilk.co.jp/products/milk/morinagamilk/1254.html": "morinagamilk.co.jp",
            "https://housefoods.jp/products/catalog/cd_1,082683.html": "housefoods.jp",
            "https://www.tablemark.co.jp/products/frozen/rice/detail/7117493.html": "tablemark.co.jp",
            "https://www.lotte.co.jp/products/catalogue/biscuit/01/detail01.html": "lotte.co.jp",
            "https://www.marusanai.co.jp/lineup/detail-64095/": "marusanai.co.jp",
            "https://www.itoen.jp/products/41922/": "itoen.jp",
            "https://www.kewpie.co.jp/products/detail/4901577004865/": "kewpie.co.jp",
            "https://www.kyoritsu-foods.co.jp/product/28092/": "kyoritsu-foods.co.jp",
            "https://shop.kyoritsu-foods.co.jp/item-detail/1981297": "kyoritsu-foods.co.jp",
            "https://www.meg-snow.com/products/": "meg-snow.com",
            "https://www.yotsuba.co.jp/products/": "yotsuba.co.jp",
            "https://www.tajimaya-cc.net/products/2118": "tajimaya-cc.net",
            "https://www.yamamori.co.jp/products/matsusaka_sukiyaki/": "yamamori.co.jp",
            "https://www.kagome.co.jp/foodservice/frozen/5615/": "kagome.co.jp",
            "https://www.katosangyo.co.jp/product/detail/159/": "katosangyo.co.jp",
            "https://www.ohyamafoods.co.jp/products/junkomesu500ml": "ohyamafoods.co.jp",
            "https://www.kurakon.jp/products/01/shiodai.html": "kurakon.jp",
            "https://sangaria.co.jp/products/oishisa-dantotsu-caramel-and-milk/": "sangaria.co.jp",
            "https://www.lawson.co.jp/recommend/original/detail/123": "lawson.co.jp",
            "https://shop.mizkan.co.jp/products/detail/123": "mizkan.co.jp",
            "https://www.mizkan.co.jp/products/detail/123": "mizkan.co.jp",
            "https://mizkan.asia/jp/terms-of-use": "mizkan.asia",
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
        self.assertTrue(is_terms_restricted_url("https://shop.matsukiyococokara-online.com/products/food/"))
        self.assertTrue(is_terms_restricted_url("https://shop.yamamori.co.jp/products/matsusaka_sukiyaki/"))
        self.assertTrue(is_terms_restricted_url("https://shop.sokensha.co.jp/products/example/"))
        self.assertTrue(is_terms_restricted_url("https://shop.kyoritsu-foods.co.jp/item-detail/1981297"))
        self.assertTrue(is_terms_restricted_url("https://shop.montoile.co.jp/products/example/"))
        self.assertTrue(is_terms_restricted_url("https://new.ohsawa-japan.co.jp/?actmode=ItemDetail&iid=906"))
        self.assertTrue(is_terms_restricted_url("https://shop.pokkasapporo-fb.jp/products/example/"))
        self.assertTrue(is_terms_restricted_url("https://shop.uha-mikakuto.co.jp/catalog/gummy/gu330.html"))
        self.assertTrue(is_terms_restricted_url("https://and.kagome.co.jp/products/feature/"))
        self.assertTrue(is_terms_restricted_url("https://www.glico.com/jp/product/drink/glicomilk/47200/"))
        self.assertTrue(is_terms_restricted_url("https://products.kirin.co.jp/softdrink/softdrink/detail.html?id=7380"))
        self.assertTrue(is_terms_restricted_url("https://shop.katosangyo.co.jp/product/detail/159/"))
        self.assertTrue(is_terms_restricted_url("https://www.ohyamafoods.co.jp/products/junkomesu500ml"))
        self.assertTrue(is_terms_restricted_url("https://www.kurakon.jp/products/01/shiodai.html"))
        self.assertTrue(is_terms_restricted_url("https://shop.sangaria.co.jp/products/oishisa-dantotsu-caramel-and-milk/"))
        self.assertTrue(is_terms_restricted_url("https://www.lawson.co.jp/recommend/original/detail/123"))
        self.assertTrue(is_terms_restricted_url("https://mldata.lawson.co.jp/lab/food/"))
        self.assertTrue(is_terms_restricted_url("https://shop.mizkan.co.jp/products/detail/123"))
        self.assertTrue(is_terms_restricted_url("https://www.mizkan.co.jp/products/detail/123"))
        self.assertTrue(is_terms_restricted_url("https://mizkan.asia/jp/terms-of-use"))

    def test_kyoritsu_manufacturer_and_shop_sources_are_paused_pending_reuse_permission(self):
        urls = (
            "https://www.kyoritsu-foods.co.jp/product/page/7/",
            "https://shop.kyoritsu-foods.co.jp/",
            "https://shop.kyoritsu-foods.co.jp/item-detail/1953381",
            "https://shop.kyoritsu-foods.co.jp/item-list?categoryId=109441",
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(is_terms_restricted_url(url))
                self.assertFalse(allowed_link(url))
                self.assertFalse(product_url(url))
        self.assertTrue(kyoritsu_shop_category_url("https://shop.kyoritsu-foods.co.jp/item-list?categoryId=109441"))
        self.assertFalse(kyoritsu_shop_category_url("https://shop.kyoritsu-foods.co.jp/item-list?categoryId=109441&sort=price"))
        self.assertFalse(allowed_link("https://shop.kyoritsu-foods.co.jp/item-list?foo=1"))
        self.assertFalse(allowed_link("https://shop.kyoritsu-foods.co.jp/item-list?categoryId=abc"))

    def test_unreviewed_sources_are_not_mislabeled_as_blocked(self):
        # Not yet reviewed for reuse terms; this is not an assertion of permission.
        self.assertFalse(is_terms_restricted_url("https://www.family.co.jp/goods.html"))
        self.assertFalse(is_terms_restricted_url("https://www.yamaki.co.jp/catalog/products/index.php?id=86"))

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
            "https://montoile.co.jp/products/tenohira-gopan-tomato-basil/",
            "https://new.ohsawa-japan.co.jp/?actmode=ItemDetail&iid=906",
            "https://www.pokkasapporo-fb.jp/products/soup/jikkuri/WZ02.html",
            "https://www.uha-mikakuto.co.jp/catalog/gummy/gu330.html",
            "https://www.maruchan.co.jp/products/search/310686.html",
            "https://www.meiji.co.jp/products/drink/4902705133150.html",
            "https://www.morinaga.co.jp/products/detail.php?id=PRD1234-56-7890",
            "https://muso.co.jp/item/75025.html",
            "https://www.nipponham.co.jp/products/processed_foods/bread_pizza/24216/",
            "https://www.askul.co.jp/p/U217658/",
            "https://www.matsukiyococokara-online.com/products/food/example",
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
            "https://www.kagome.co.jp/foodservice/frozen/5615/",
            "https://www.katosangyo.co.jp/product/detail/159/",
            "https://www.ohyamafoods.co.jp/products/junkomesu500ml",
            "https://www.kurakon.jp/products/01/shiodai.html",
            "https://sangaria.co.jp/products/oishisa-dantotsu-caramel-and-milk/",
            "https://www.glico.com/jp/product/drink/glicomilk/47200/",
            "https://products.kirin.co.jp/softdrink/softdrink/detail.html?id=7380",
            "https://www.lawson.co.jp/recommend/original/detail/123",
            "https://shop.mizkan.co.jp/item-detail/123",
            "https://www.mizkan.co.jp/products/detail/123",
            "https://www.kyoritsu-foods.co.jp/product/28092/",
            "https://shop.kyoritsu-foods.co.jp/item-detail/1981297",
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
                "matsukiyococokara-online.com",
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
                "kyoritsu-foods.co.jp",
                "kagome.co.jp",
                "glico.com",
                "kirin.co.jp",
                "meg-snow.com",
                "yotsuba.co.jp",
                "tajimaya-cc.net",
                "yamamori.co.jp",
                "sokensha.co.jp",
                "montoile.co.jp",
                "ohsawa-japan.co.jp",
                "pokkasapporo-fb.jp",
                "uha-mikakuto.co.jp",
                "katosangyo.co.jp",
                "ohyamafoods.co.jp",
                "kurakon.jp",
                "sangaria.co.jp",
                "lawson.co.jp",
                "mizkan.co.jp",
                "mizkan.asia",
            },
        )


    def test_agent_reach_discovery_is_paused_without_accessing_third_party_sites(self):
        report = build_report()
        self.assertEqual(report["status"], "paused")
        self.assertEqual(report["reason_code"], "search_provider_not_configured")
        self.assertEqual(report["sources_accessed"], [])
        self.assertEqual(report["candidate_count"], 0)
        self.assertEqual(report["verified_product_records"], 0)
        self.assertEqual(report["supabase_imported"], 0)
        self.assertNotIn("halaljapan.app", json.dumps(report))

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
            blocked_montoile = "https://montoile.co.jp/products/tenohira-gopan-tomato-basil/"
            blocked_ohsawa = "https://new.ohsawa-japan.co.jp/?actmode=ItemDetail&iid=906"
            blocked_pokka = "https://www.pokkasapporo-fb.jp/products/soup/jikkuri/WZ02.html"
            blocked_uha = "https://www.uha-mikakuto.co.jp/catalog/gummy/gu330.html"
            blocked_kagome = "https://www.kagome.co.jp/foodservice/frozen/5615/"
            blocked_glico = "https://www.glico.com/jp/product/drink/glicomilk/47200/"
            blocked_kirin = "https://products.kirin.co.jp/softdrink/softdrink/detail.html?id=7380"
            blocked_kato = "https://www.katosangyo.co.jp/product/detail/159/"
            blocked_ohyama = "https://www.ohyamafoods.co.jp/products/junkomesu500ml"
            blocked_kurakon = "https://www.kurakon.jp/products/01/shiodai.html"
            blocked_sangaria = "https://sangaria.co.jp/products/oishisa-dantotsu-caramel-and-milk/"
            blocked_matsukiyo = "https://www.matsukiyococokara-online.com/products/food/example"
            blocked_lawson = "https://www.lawson.co.jp/recommend/original/detail/123"
            blocked_mizkan = "https://shop.mizkan.co.jp/products/detail/123"
            blocked_mizkan_asia = "https://mizkan.asia/jp/terms-of-use"
            blocked_kyoritsu_main = "https://www.kyoritsu-foods.co.jp/product/28092/"
            blocked_kyoritsu_shop = "https://shop.kyoritsu-foods.co.jp/item-detail/1981297"
            allowed = "https://www.yamaki.co.jp/catalog/products/index.php?id=86"
            db.executemany("INSERT INTO queue(url) VALUES(?)",
                           [(blocked,), (blocked_yamamori,), (blocked_sokensha,), (blocked_montoile,), (blocked_ohsawa,), (blocked_pokka,), (blocked_uha,), (blocked_kagome,), (blocked_glico,), (blocked_kirin,), (blocked_kato,), (blocked_ohyama,), (blocked_kurakon,), (blocked_sangaria,), (blocked_matsukiyo,), (blocked_lawson,), (blocked_mizkan,), (blocked_mizkan_asia,), (blocked_kyoritsu_main,), (blocked_kyoritsu_shop,), (allowed,)])
            db.commit()
            changed = quarantine_restricted_pending_sources(db)
            self.assertEqual(changed, 20)
            rows = dict(db.execute("SELECT url,status FROM queue"))
            self.assertEqual(rows[blocked], "done")
            self.assertEqual(rows[blocked_yamamori], "done")
            self.assertEqual(rows[blocked_sokensha], "done")
            self.assertEqual(rows[blocked_montoile], "done")
            self.assertEqual(rows[blocked_ohsawa], "done")
            self.assertEqual(rows[blocked_pokka], "done")
            self.assertEqual(rows[blocked_uha], "done")
            self.assertEqual(rows[blocked_kagome], "done")
            self.assertEqual(rows[blocked_glico], "done")
            self.assertEqual(rows[blocked_kirin], "done")
            self.assertEqual(rows[blocked_kato], "done")
            self.assertEqual(rows[blocked_ohyama], "done")
            self.assertEqual(rows[blocked_kurakon], "done")
            self.assertEqual(rows[blocked_sangaria], "done")
            self.assertEqual(rows[blocked_matsukiyo], "done")
            self.assertEqual(rows[blocked_lawson], "done")
            self.assertEqual(rows[blocked_mizkan], "done")
            self.assertEqual(rows[blocked_mizkan_asia], "done")
            self.assertEqual(rows[blocked_kyoritsu_main], "done")
            self.assertEqual(rows[blocked_kyoritsu_shop], "done")
            self.assertEqual(rows[allowed], "pending")
            self.assertEqual(db.execute("SELECT count(*) FROM queue").fetchone()[0], 21)
            self.assertEqual(quarantine_restricted_pending_sources(db), 0)
            db.close()


if __name__ == "__main__":
    unittest.main()
