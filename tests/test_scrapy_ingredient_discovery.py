import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scrapy_ingredient_discovery import (
    is_ingredient_product_candidate,
    is_product_detail_url,
    is_allowed_source_url,
)


class IngredientDiscoveryTests(unittest.TestCase):
    def test_meiji_detail_with_labelled_table_is_candidate(self):
        html = """
        <html><h1>テストヨーグルト</h1>
        <table><tr><th>原材料名</th><td>生乳、乳製品、砂糖</td></tr></table>
        </html>
        """
        url = "https://www.meiji.co.jp/products/yogurt/4902705133099.html"
        self.assertTrue(is_ingredient_product_candidate(url, html))

    def test_kewpie_detail_with_dt_dd_is_candidate(self):
        html = """
        <html><h1>ドレッシング</h1>
        <dl><dt>原材料名</dt><dd>食用植物油脂、醸造酢、砂糖</dd></dl>
        </html>
        """
        url = "https://www.kewpie.co.jp/products/detail/4901577094040/"
        self.assertTrue(is_ingredient_product_candidate(url, html))

    def test_inline_labeled_declaration_is_candidate(self):
        html = "<html><h1>商品</h1><p>原材料名：小麦粉、砂糖、植物油脂</p></html>"
        url = "https://www.morinaga.co.jp/products/detail.php?id=PRD2010-07-0029"
        self.assertTrue(is_ingredient_product_candidate(url, html))

    def test_7premium_disclaimer_is_not_ingredient_evidence(self):
        html = """
        <html><h1>バターステイツクッキー 3個</h1>
        <p>原材料、アレルゲン、価格等が予告なく変更になる場合があります。</p>
        </html>
        """
        url = "https://7premium.jp/product/search/detail?id=10605"
        self.assertFalse(is_ingredient_product_candidate(url, html))

    def test_category_page_is_not_product_detail(self):
        html = """
        <html><h1>お茶の商品一覧</h1>
        <table><tr><th>原材料名</th><td>茶葉</td></tr></table>
        </html>
        """
        url = "https://www.dydo.co.jp/products/category/tea/"
        self.assertFalse(is_ingredient_product_candidate(url, html))

    def test_category_url_rejected_even_if_it_mentions_ingredients(self):
        self.assertFalse(
            is_product_detail_url("https://www.itoen.jp/products/category/drink/")
        )

    def test_known_product_detail_url_shapes(self):
        urls = [
            "https://www.natori.co.jp/products_search/sausage/item_539",
            "https://www.sanko-seika.co.jp/product/item/9783/",
            "https://www.yamaki.co.jp/catalog/products/index.php?id=86",
            "https://7premium.jp/product/search/detail?id=13340",
            "https://www.dydo.co.jp/products/detail/1249/",
            "https://www.itoen.jp/products/51078/",
            "https://muso.co.jp/item/10022.html",
            "https://housefoods.jp/products/catalog/cd_1,082683.html",
            "https://img.asahiinryo.co.jp/products/carbonated/wilkinson/2T532.html",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(is_product_detail_url(url))

    def test_nagatanien_product_detail_with_labelled_ingredients_is_candidate(self):
        html = """
        <html><h1>抹茶スープ白味噌仕立て</h1>
        <dl><dt>原材料名</dt><dd>調味粉、米みそ、砂糖、抹茶、食塩</dd></dl>
        </html>
        """
        url = "https://www.nagatanien.co.jp/product/detail/1220/"
        self.assertTrue(is_allowed_source_url(url))
        self.assertTrue(is_product_detail_url(url))
        self.assertTrue(is_ingredient_product_candidate(url, html))

    def test_restricted_source_is_skipped_even_with_complete_ingredients(self):
        html = "<html><h1>黄金の味</h1><p>原材料名：りんご、醤油、砂糖、食塩</p></html>"
        url = "https://www.ebarafoods.com/products/detail/123"
        self.assertFalse(is_allowed_source_url(url))
        self.assertFalse(is_ingredient_product_candidate(url, html))

    def test_restricted_domains_and_subdomains_are_not_allowed(self):
        for url in (
            "https://www.calbee.co.jp/products/detail/?p=20261106232447",
            "https://gyoumuyou.ebarafoods.com/products/detail/TCT16A.html",
            "https://www.imuraya.co.jp/goods/zenzai/c-zenzai/noukouz/",
            "https://www.kikkoman.co.jp/products/K05/detail/K053515.html",
            "https://www.morinagamilk.co.jp/products/milk/morinagamilk/1254.html",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_allowed_source_url(url))

    def test_generic_catalogue_page_rejected(self):
        self.assertFalse(is_product_detail_url("https://www.family.co.jp/goods.html"))


if __name__ == "__main__":
    unittest.main()
