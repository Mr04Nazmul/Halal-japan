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
    def test_clear_is_policy_only(self):
        r=screen('米(国産)、食塩')
        self.assertEqual(r['rule_result'],'HALAL')
        self.assertFalse(r['halal_certified'])
        self.assertEqual(screen('小麦粉、乳化剤不使用、ゼラチン')['rule_result'],'HARAM')

if __name__=='__main__':unittest.main()
