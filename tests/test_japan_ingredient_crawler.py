import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from crawl_japanese_ingredients import Collector,extract,product_url

HTML='''<h1>Product</h1><table><tr><th>商品名</th><td>テスト米菓</td></tr><tr><th>JANCODE</th><td>4973728910141</td></tr><tr><th>原材料</th><td>米、食塩</td></tr></table>'''
URL='https://muso.co.jp/item/32882.html'
class Extraction(unittest.TestCase):
 def test_exact_ingredient_field_and_explicit_jan(self):
  r,e=extract(HTML,URL)
  self.assertIsNone(e);self.assertEqual(r['ingredients_ja'],'米、食塩');self.assertEqual(r['jan'],'4973728910141')
  self.assertEqual(r['rule_result'],'HALAL');self.assertFalse(r['halal_certified'])
 def test_missing_and_ambiguous_never_count(self):
  self.assertIsNone(extract('<h1>米菓</h1><p>アレルゲン：小麦</p>',URL)[0])
  self.assertIsNone(extract(HTML+'<dl><dt>原材料</dt><dd>豚肉</dd></dl>',URL)[0])
  r,_=extract(HTML.replace('<tr><th>JANCODE</th><td>4973728910141</td></tr>',''),URL)
  self.assertIsNone(r['jan'])
 def test_no_host_spoofing(self):
  self.assertFalse(product_url('https://muso.co.jp.evil.example/item/32882.html'))
 def test_resume_and_conflict_withholding(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   c.request=lambda u:'User-agent: *\nAllow: /' if u.endswith('/robots.txt') else HTML
   c.run([URL],1,1)
   self.assertEqual(c.count(),1)
   c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.count(),1)
   c.request=lambda u:'User-agent: *\nAllow: /' if u.endswith('/robots.txt') else HTML.replace('米、食塩','米、ゼラチン')
   c.run(['https://muso.co.jp/item/10762.html'],1,1)
   self.assertEqual(c.count(),0)
   self.assertEqual(json.loads((Path(folder)/'summary.json').read_text())['formula_conflicts_withheld'],1)

if __name__=='__main__':unittest.main()
