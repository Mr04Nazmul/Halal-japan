import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from japan_ingredient_source_terms import (
    RESTRICTED_SOURCE_POLICIES,
    is_terms_restricted_url,
    source_terms_restriction,
)
from crawl_japanese_ingredients import allowed_link


class SourceTermsPolicyTests(unittest.TestCase):
    def test_explicitly_restricted_publishers_are_withheld(self):
        examples = {
            "https://agf.ajinomoto.co.jp/product/detail/14113": "agf.ajinomoto.co.jp",
            "https://www.ajinomoto.co.jp/products/": "ajinomoto.co.jp",
            "https://www.asahi-gf.co.jp/products/food/": "asahi-gf.co.jp",
            "https://www.asahiinryo.co.jp/products/": "asahiinryo.co.jp",
            "https://www.fujiya-peko.co.jp/sweets/item/26844.html": "fujiya-peko.co.jp",
            "https://www.maruchan.co.jp/products/search/310686.html": "maruchan.co.jp",
            "https://www.meiji.co.jp/products/drink/4902705133150.html": "meiji.co.jp",
            "https://www.meito-abc.co.jp/products/lineup/new": "meito-abc.co.jp",
            "https://www.morinaga.co.jp/products/detail.php?id=PRD1234-56-7890": "morinaga.co.jp",
            "https://muso.co.jp/item/75025.html": "muso.co.jp",
            "https://www.nipponham.co.jp/products/processed_foods/bread_pizza/24216/": "nipponham.co.jp",
            "https://www.tohato.jp/products/caramelcorn/": "tohato.jp",
            "https://www.topvalu.net/items/detail/4902123456789/": "topvalu.net",
            "https://7premium.jp/product/search/detail?id=10791": "7premium.jp",
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

    def test_unreviewed_sources_are_not_mislabeled_as_explicitly_restricted(self):
        self.assertFalse(is_terms_restricted_url("https://montoile.co.jp/products/example/"))
        self.assertFalse(is_terms_restricted_url("https://www.fujicco.co.jp/products/detail/123/"))

    def test_main_crawler_does_not_enqueue_restricted_current_source_pages(self):
        blocked = [
            "https://agf.ajinomoto.co.jp/product/detail/14113",
            "https://www.asahiinryo.co.jp/products/carbonated/wilkinson_tansan_fruity_muscat/2T532.html",
            "https://www.maruchan.co.jp/products/search/310686.html",
            "https://www.meiji.co.jp/products/drink/4902705133150.html",
            "https://www.morinaga.co.jp/products/detail.php?id=PRD1234-56-7890",
            "https://muso.co.jp/item/75025.html",
            "https://www.nipponham.co.jp/products/processed_foods/bread_pizza/24216/",
            "https://www.topvalu.net/items/detail/4902123456789/",
            "https://7premium.jp/product/search/detail?id=10791",
        ]
        for url in blocked:
            with self.subTest(url=url):
                self.assertFalse(allowed_link(url))

    def test_policy_contains_only_reviewed_explicit_restrictions(self):
        self.assertEqual(
            set(RESTRICTED_SOURCE_POLICIES),
            {
                "agf.ajinomoto.co.jp",
                "ajinomoto.co.jp",
                "asahi-gf.co.jp",
                "asahiinryo.co.jp",
                "fujiya-peko.co.jp",
                "maruchan.co.jp",
                "meiji.co.jp",
                "meito-abc.co.jp",
                "morinaga.co.jp",
                "muso.co.jp",
                "nipponham.co.jp",
                "tohato.jp",
                "topvalu.net",
                "7premium.jp",
            },
        )


if __name__ == "__main__":
    unittest.main()
