import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from crawl_japanese_ingredients import extract,product_url,allowed_link,sitemap_url

class MaruchanOfficialSourceTests(unittest.TestCase):
 def test_only_exact_product_detail_paths_are_product_urls(self):
  self.assertTrue(product_url('https://www.maruchan.co.jp/products/search/500506.html'))
  self.assertTrue(product_url('https://www.maruchan.co.jp/products/search/mendukuri_torigarashoyu.html'))
  self.assertFalse(product_url('https://www.maruchan.co.jp/products/search/new/new/'))
  self.assertTrue(sitemap_url('https://www.maruchan.co.jp/sitemap.xml'))

 def test_maruchan_content_is_withheld_without_reuse_permission(self):
  self.assertFalse(allowed_link('https://www.maruchan.co.jp/products/search/500506.html'))
  self.assertFalse(allowed_link('https://www.maruchan.co.jp/sitemap.xml'))
  self.assertFalse(allowed_link('https://www.maruchan.co.jp/products/search/new/new/new/'))
  self.assertFalse(allowed_link('https://www.maruchan.co.jp/campaign/'))

 def test_exact_official_ingredient_and_jan_fields_are_extracted(self):
  ingredients='麦芽糖(国内製造)、砂糖、粉末かつおぶし、粉末かつおエキス、酵母エキス、粉末しいたけエキス、粉末こんぶ、植物油／加工でん粉'
  html=f'''<div id="header"><h1><a><img alt="東洋水産"></a></h1></div>
  <div id="contents"><h1 class="heading">だしの素鰹あじ 食塩不使用 小袋16袋入 64g</h1>
  <table><tr><th>JANコード</th><td>4901990107389</td></tr></table>
  <p class="heading">原材料名</p><p class="description">{ingredients}</p></div>'''
  record,error=extract(html,'https://www.maruchan.co.jp/products/search/500506.html')
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'だしの素鰹あじ 食塩不使用 小袋16袋入 64g')
  self.assertEqual(record['jan'],'4901990107389')
  self.assertEqual(record['ingredients_ja'],ingredients)
  self.assertFalse(record['halal_certified'])
  self.assertEqual(record['ingredient_field_status'],'complete_displayed_field')

 def test_pork_ingredient_is_captured_but_never_certified(self):
  ingredients='めん(小麦粉(国内製造)、食塩、卵粉、植物油、大豆食物繊維)、添付調味料(しょうゆ、ポークエキス、豚脂、植物油、食塩、チキンエキス、こんぶエキス、香辛料、たん白加水分解物、野菜エキス、砂糖、香味油脂、粉末煮干し)、かやく(チンゲン菜、メンマ、なると、のり、ねぎ)／加工でん粉、調味料(アミノ酸等)、酒精、かんすい、炭酸カルシウム、乳化剤、カラメル色素、増粘多糖類、クチナシ色素、pH調整剤、酸化防止剤(ビタミンE)、ベニコウジ色素、香料、ビタミンB2、ビタミンB1、(一部に小麦・卵・乳成分・大豆・鶏肉・豚肉・ゼラチンを含む)'
  html=f'''<h1>麺づくり 鶏ガラ醤油</h1><table><tr><th>JANコード</th><td>4901990378765</td></tr></table>
  <p class="heading">原材料名</p><p class="description">{ingredients}</p>'''
  record,error=extract(html,'https://www.maruchan.co.jp/products/search/mendukuri_torigarashoyu.html')
  self.assertIsNone(error)
  self.assertEqual(record['jan'],'4901990378765')
  self.assertEqual(record['ingredients_ja'],ingredients)
  self.assertEqual(record['rule_result'],'HARAM')
  self.assertFalse(record['halal_certified'])

if __name__=='__main__':unittest.main()
