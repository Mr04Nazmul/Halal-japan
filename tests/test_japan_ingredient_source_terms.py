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
    def test_meiji_content_is_withheld_until_permission_is_established(self):
        url = "https://www.meiji.co.jp/products/drink/4902705133150.html"
        self.assertTrue(is_terms_restricted_url(url))
        self.assertEqual(source_terms_restriction(url)["domain"], "meiji.co.jp")
        self.assertIn("regulation", source_terms_restriction(url)["policy_url"])

    def test_fujiya_content_is_withheld_until_permission_is_established(self):
        url = "https://www.fujiya-peko.co.jp/sweets/item/26844.html"
        self.assertTrue(is_terms_restricted_url(url))
        self.assertEqual(source_terms_restriction(url)["domain"], "fujiya-peko.co.jp")
        self.assertIn("copyright", source_terms_restriction(url)["policy_url"])

    def test_restrictions_apply_to_subdomains_and_non_https_urls(self):
        self.assertTrue(is_terms_restricted_url("https://shop.meiji.co.jp/product/1"))
        self.assertTrue(is_terms_restricted_url("http://www.fujiya-peko.co.jp/item/1"))

    def test_other_public_sources_are_not_blocked_by_this_policy(self):
        self.assertFalse(is_terms_restricted_url("https://muso.co.jp/item/75025.html"))
        self.assertFalse(is_terms_restricted_url("https://www.nipponham.co.jp/products/processed_foods/bread_pizza/24216/"))

    def test_main_crawler_does_not_enqueue_restricted_product_pages(self):
        self.assertFalse(allowed_link("https://www.meiji.co.jp/products/drink/4902705133150.html"))
        self.assertFalse(allowed_link("https://www.fujiya-peko.co.jp/sweets/item/26844.html"))
        self.assertTrue(allowed_link("https://www.nipponham.co.jp/products/processed_foods/bread_pizza/24216/"))

    def test_policy_contains_only_reviewed_explicit_restrictions(self):
        self.assertEqual(set(RESTRICTED_SOURCE_POLICIES), {"meiji.co.jp", "fujiya-peko.co.jp"})


if __name__ == "__main__":
    unittest.main()
