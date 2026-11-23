import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

candidate_module = load_module(
    "off_japan_ingredients",
    "scripts/import_off_japan_ingredients.py",
)
catalogue_module = load_module(
    "off_catalogue_to_supabase",
    "scripts/import_off_catalogue_to_supabase.py",
)


class JapaneseIngredientCandidateTests(unittest.TestCase):
    def test_valid_japanese_jan13(self):
        self.assertTrue(candidate_module.is_japanese_ingredient_candidate(
            "4902705126558", "おいしい牛乳 900ml", "生乳100%（国産）"))

    def test_valid_japanese_jan8(self):
        self.assertTrue(candidate_module.is_japanese_ingredient_candidate(
            "49452976", "雪印北海道練乳", "生乳、しょ糖 (44.2%)"))

    def test_foreign_product_not_automatically_japanese(self):
        self.assertFalse(candidate_module.is_japanese_ingredient_candidate(
            "3229820181950", "Fourrés Chocolat au Lait", "Farine de blé, sucre, beurre de cacao"))

    def test_japanese_name_requires_japanese_ingredients(self):
        self.assertFalse(candidate_module.is_japanese_ingredient_candidate(
            "4902705126558", "おいしい牛乳", "whole milk and sugar"))

    def test_invalid_ean_not_accepted(self):
        self.assertFalse(candidate_module.is_japanese_ingredient_candidate(
            "4902705126559", "おいしい牛乳", "生乳100%（国産）"))

    def test_non_ean_identifier_not_accepted(self):
        self.assertFalse(candidate_module.is_japanese_ingredient_candidate(
            "123456789012", "おいしい牛乳", "生乳100%（国産）"))


class OFFSupplementalJapanShardTests(unittest.TestCase):
    def sample(self, **overrides):
        row = {
            "code": "4902705126558",
            "product_name": "おいしい牛乳",
            "brands": "Example Japan",
            "ingredients_text": "生乳100%（国産）",
            "scope": "japan_country_tag",
            "_sourceUrl": "https://world.openfoodfacts.org/product/4902705126558",
        }
        row.update(overrides)
        return row

    def test_checksum_valid_jan13_and_jan8(self):
        self.assertTrue(catalogue_module.valid_jan_code("4902705126558"))
        self.assertTrue(catalogue_module.valid_jan_code("49452976"))
        self.assertFalse(catalogue_module.valid_jan_code("4902705126559"))

    def test_only_japan_country_tag_is_accepted_from_supplemental_shards(self):
        accepted = catalogue_module.build_review_row(
            self.sample(), require_japan_scope=True
        )
        rejected = catalogue_module.build_review_row(
            self.sample(scope="japanese_barcode_prefix_only"),
            require_japan_scope=True,
        )
        self.assertIsNotNone(accepted)
        self.assertIsNone(rejected)

    def test_japanese_name_and_ingredient_text_are_both_required(self):
        self.assertIsNone(catalogue_module.build_review_row(
            self.sample(product_name="Japanese Milk"),
            require_japan_scope=True,
        ))
        self.assertIsNone(catalogue_module.build_review_row(
            self.sample(ingredients_text="whole milk"),
            require_japan_scope=True,
        ))

    def test_unknown_ingredient_text_is_rejected(self):
        self.assertIsNone(catalogue_module.build_review_row(
            self.sample(ingredients_text="unknown"),
            require_japan_scope=True,
        ))

    def test_source_url_is_preserved_and_invalid_url_is_replaced(self):
        expected = "https://world.openfoodfacts.org/product/4902705126558"
        accepted = catalogue_module.build_review_row(
            self.sample(), require_japan_scope=True
        )
        fallback = catalogue_module.build_review_row(
            self.sample(_sourceUrl="https://example.com/product/4902705126558"),
            require_japan_scope=True,
        )
        self.assertEqual(accepted["source_url"], expected)
        self.assertEqual(fallback["source_url"], expected)

    def test_all_supplemental_rows_remain_review_only_not_halal_certified(self):
        row = catalogue_module.build_review_row(
            self.sample(), require_japan_scope=True
        )
        self.assertEqual(row["evidence_level"], "discovery_only")
        self.assertEqual(row["status"], "needs_review")
        self.assertNotIn("halal_certified", row)
        self.assertNotIn("_halalVerified", row)


if __name__ == "__main__":
    unittest.main()
