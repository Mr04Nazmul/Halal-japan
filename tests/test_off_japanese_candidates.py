import importlib.util
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "import_off_japan_ingredients.py"
spec = importlib.util.spec_from_file_location("off_japan_ingredients", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class JapaneseIngredientCandidateTests(unittest.TestCase):
    def test_valid_japanese_jan13(self):
        self.assertTrue(module.is_japanese_ingredient_candidate(
            "4902705126558", "おいしい牛乳 900ml", "生乳100%（国産）"))

    def test_valid_japanese_jan8(self):
        self.assertTrue(module.is_japanese_ingredient_candidate(
            "49452976", "雪印北海道練乳", "生乳、しょ糖 (44.2%)"))

    def test_foreign_product_not_automatically_japanese(self):
        self.assertFalse(module.is_japanese_ingredient_candidate(
            "3229820181950", "Fourrés Chocolat au Lait", "Farine de blé, sucre, beurre de cacao"))

    def test_japanese_name_requires_japanese_ingredients(self):
        self.assertFalse(module.is_japanese_ingredient_candidate(
            "4902705126558", "おいしい牛乳", "whole milk and sugar"))

    def test_invalid_ean_not_accepted(self):
        self.assertFalse(module.is_japanese_ingredient_candidate(
            "4902705126559", "おいしい牛乳", "生乳100%（国産）"))

    def test_non_ean_identifier_not_accepted(self):
        self.assertFalse(module.is_japanese_ingredient_candidate(
            "123456789012", "おいしい牛乳", "生乳100%（国産）"))


if __name__ == "__main__":
    unittest.main()
