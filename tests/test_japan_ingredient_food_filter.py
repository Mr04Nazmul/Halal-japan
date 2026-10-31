import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from japan_ingredient_food_filter import is_nonfood_name,is_nonfood_ingredient_text,has_unresolved_html_artifacts

class FoodFilter(unittest.TestCase):
    def test_reject_obvious_nonfoods(self):
        for name in ("浴用石けん","ハンドソープ","犬用おやつ","犬のおやつ やわらか鶏ささみバー 12g×4本","猫のおやつ まぐろ","犬のごはん","猫のごはん","ペットのおやつ","ペットフード","ドッグフード","シャンプー","歯磨き粉","化粧水","洗顔フォーム","ナチュラムーン・ナプキン昼用","オーガニックコットンナプキン","スカルプリッチプロフェッショナル"):
            with self.subTest(name=name):
                self.assertTrue(is_nonfood_name(name))
    def test_keep_real_foods(self):
        for name in ("野生種なめ茸","純米富士酢","ビットクランチ","しょうがパウダー","米こうじ","600ml ペットボトル","アメリカンドッグ","ホットドッグ用マスタード"):
            with self.subTest(name=name):
                self.assertFalse(is_nonfood_name(name))
    def test_invalid_ingredient_placeholders(self):
        for value in ("主な原材料の産地", " 主な 原材料の産地 ", "ポリエチレン"):
            with self.subTest(value=value):
                self.assertTrue(is_nonfood_ingredient_text(value))
        for value in ("コーヒー豆", "米、食塩", "小麦粉（国内製造）、砂糖", None, ""):
            with self.subTest(value=value):
                self.assertFalse(is_nonfood_ingredient_text(value))
    def test_html_artifacts_are_reviewed_not_imported(self):
        for value in ("米<br>食塩", "米&lt;br&gt;食塩", "砂糖&#12354;", "砂糖&#x3042;", "米&amp;塩"):
            with self.subTest(value=value):
                self.assertTrue(has_unresolved_html_artifacts(value))
        for value in ("米、食塩", "米 & 塩", "コーヒー豆", None, ""):
            with self.subTest(value=value):
                self.assertFalse(has_unresolved_html_artifacts(value))
    def test_empty_values(self):
        self.assertFalse(is_nonfood_name(None))
        self.assertFalse(is_nonfood_name(""))
if __name__=="__main__":
    unittest.main()
