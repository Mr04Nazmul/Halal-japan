"""Sanko Seika official product pages: preserve displayed ingredients, never invent JAN."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from crawl_japanese_ingredients import source, product_url, allowed_link, extract

URL="https://www.sanko-seika.co.jp/product/item/5096/"
HTML="""<html><head><title>ミックスかりんとう | 三幸製菓株式会社</title></head><body>
<h1>ミックスかりんとう（114g）</h1><table>
<tr><th>原材料</th><td>小麦粉（国内製造）、植物油脂、黒糖、ゼラチン／香料<br/>◆はちみつを使用していますので、1歳未満の乳児には与えないでください。</td></tr>
<tr><th>アレルゲン</th><td>小麦、ゼラチン</td></tr>
</table></body></html>"""

class SankoSeikaTests(unittest.TestCase):
 def test_scope(self):
  self.assertEqual(source(URL),"sanko-seika.co.jp")
  self.assertTrue(product_url(URL))
  self.assertTrue(allowed_link("https://www.sanko-seika.co.jp/product/"))
  self.assertFalse(product_url("https://www.sanko-seika.co.jp/product/"))
  self.assertFalse(allowed_link("https://www.sanko-seika.co.jp/news/9237/"))

 def test_exact_label_and_no_fake_jan(self):
  record,error=extract(HTML,URL)
  self.assertIsNone(error)
  self.assertEqual(record["name_ja"],"ミックスかりんとう（114g）")
  self.assertEqual(record["ingredients_ja"],"小麦粉（国内製造）、植物油脂、黒糖、ゼラチン／香料")
  self.assertIsNone(record["jan"])
  self.assertEqual(record["source_publisher"],"sanko-seika.co.jp")
  self.assertFalse(record.get("halal_certified",False))

 def test_missing_field_fails_closed(self):
  record,error=extract("<html><h1>ミックスかりんとう</h1><p>アレルゲン：小麦</p></html>",URL)
  self.assertIsNone(record)
  self.assertEqual(error,"missing_or_ambiguous_ingredients")

if __name__=="__main__":unittest.main()
