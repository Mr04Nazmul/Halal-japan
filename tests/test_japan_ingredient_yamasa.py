import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from crawl_japanese_ingredients import extract, product_url, allowed_link

class YamasaOfficialSourceTests(unittest.TestCase):
 def test_product_and_catalogue_routes(self):
  self.assertTrue(product_url('https://www.yamasa.com/products/home/tsuyu/sukiyaki-senka-west/'))
  self.assertTrue(product_url('https://www.yamasa.com/products/business/shoyu/sample/'))
  self.assertFalse(product_url('https://www.yamasa.com/products/home/'))
  self.assertTrue(allowed_link('https://www.yamasa.com/products/home/'))

 def test_exact_labeled_ingredient_field_without_invented_jan(self):
  url='https://www.yamasa.com/products/home/tsuyu/sukiyaki-senka-west/'
  html='''<html><head><title>ヤマサすき焼専科（西） 〖ヤマサ醤油株式会社〗</title></head><body>
  <h1>家庭用商品ヤマサすき焼専科（西）</h1><table>
  <tr><th>原材料名</th><td>しょうゆ（小麦・大豆を含む）、砂糖、食塩、日本酒／調味料（アミノ酸等）</td></tr>
  <tr><th>アレルギー成分</th><td>小麦、大豆</td></tr></table></body></html>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'ヤマサすき焼専科（西）')
  self.assertEqual(record['ingredients_ja'],'しょうゆ（小麦・大豆を含む）、砂糖、食塩、日本酒／調味料（アミノ酸等）')
  self.assertIsNone(record['jan'])
  self.assertFalse(record.get('halal_certified',False))

 def test_allergen_only_is_not_ingredient_evidence(self):
  url='https://www.yamasa.com/products/home/tsuyu/sukiyaki-senka-west/'
  html='<html><title>ヤマサすき焼専科（西）</title><table><tr><th>アレルギー成分</th><td>小麦、大豆</td></tr></table></html>'
  record,error=extract(html,url)
  self.assertIsNone(record)
  self.assertEqual(error,'missing_or_ambiguous_ingredients')

if __name__=='__main__':unittest.main()
