import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from japan_ingredient_food_filter import is_nonfood_name

class FoodFilter(unittest.TestCase):
    def test_reject_obvious_nonfoods(self):
        for name in ("浴用石けん","ハンドソープ","犬用おやつ","犬のおやつ やわらか鶏ささみバー 12g×4本","猫のおやつ まぐろ","犬のごはん","猫のごはん","ペットのおやつ","ペットフード","ドッグフード","シャンプー","歯磨き粉","化粧水","洗顔フォーム"):
            with self.subTest(name=name):
                self.assertTrue(is_nonfood_name(name))
    def test_keep_real_foods(self):
        for name in ("野生種なめ茸","純米富士酢","ビットクランチ","しょうがパウダー","米こうじ","600ml ペットボトル","アメリカンドッグ","ホットドッグ用マスタード"):
            with self.subTest(name=name):
                self.assertFalse(is_nonfood_name(name))
    def test_empty_values(self):
        self.assertFalse(is_nonfood_name(None))
        self.assertFalse(is_nonfood_name(""))
if __name__=="__main__":
    unittest.main()
