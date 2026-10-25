import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from japan_ingredient_policy import screen

class Rules(unittest.TestCase):
    def test_all_requested_terms(self):
        for term in ['豚肉','ポークエキス','ラード','ゼラチン','乳化剤','香料','コラーゲン','ショートニング','レシチン','加工油脂','たんぱく加水分解物','発酵調味料','料理酒','みりん']:
            with self.subTest(term=term):self.assertEqual(screen('小麦粉、'+term)['rule_result'],'HARAM')
    def test_plant_exception_is_local(self):
        self.assertEqual(screen('砂糖、植物性乳化剤')['rule_result'],'HALAL')
        self.assertEqual(screen('砂糖、乳化剤(植物由来)')['rule_result'],'HALAL')
        self.assertEqual(screen('植物性乳化剤、ゼラチン')['rule_result'],'HARAM')
        self.assertEqual(screen('植物性乳化剤、乳化剤')['rule_result'],'HARAM')
    def test_additives_and_missing_label(self):
        self.assertEqual(screen('小麦粉、砂糖','香料')['rule_result'],'HARAM')
        for text in ['',None,'不明','豚肉不使用','乳化剤不使用','香料不使用']:
            self.assertEqual(screen(text)['rule_result'],'UNKNOWN')
        self.assertEqual(screen('米',complete=False)['rule_result'],'UNKNOWN')
    def test_alcoholic_product_name_is_not_halal(self):
        for name, ingredients in [
            ('プレミアム生ビール','麦芽、ホップ'),
            ('本格麦焼酎','麦、麦麹'),
            ('オーガニック ワイン','ぶどう、酸化防止剤'),
            ('Eagle Wings ケンタッキーバーボンウィスキー','グレーン、モルト'),
        ]:
            with self.subTest(name=name):
                result=screen(ingredients,product_name=name)
                self.assertEqual(result['rule_result'],'HARAM')
                self.assertFalse(result['halal_certified'])
    def test_wine_ingredient_and_non_alcoholic_exception(self):
        self.assertEqual(screen('牛肉、赤ワイン、食塩')['rule_result'],'HARAM')
        self.assertEqual(screen('米、清酒')['rule_result'],'HARAM')
        self.assertEqual(screen('麦芽、ホップ',product_name='ノンアルコールビール')['rule_result'],'HALAL')
        self.assertEqual(screen('ぶどう酢',product_name='ワインビネガー')['rule_result'],'HALAL')
    def test_official_seven_premium_regressions(self):
        for name, ingredients in [
            ('麦職人 1800ml','麦（オーストラリア産、国産）、麦麹'),
            ('麦職人 900ml','麦、麦麹'),
            ('芋職人 1800ml','さつまいも、米麹'),
            ('芋職人 900ml','さつまいも、米麹'),
        ]:
            with self.subTest(name=name):
                result=screen(ingredients,product_name=name)
                self.assertEqual(result['rule_result'],'HARAM')
                self.assertFalse(result['halal_certified'])
        self.assertEqual(screen('枠外表面下部に記載')['rule_result'],'UNKNOWN')
        self.assertEqual(screen('米、発酵調味液')['rule_result'],'HARAM')

    def test_clear_is_policy_only(self):
        r=screen('米(国産)、食塩')
        self.assertEqual(r['rule_result'],'HALAL')
        self.assertFalse(r['halal_certified'])
        self.assertEqual(screen('小麦粉、乳化剤不使用、ゼラチン')['rule_result'],'HARAM')

if __name__=='__main__':unittest.main()
