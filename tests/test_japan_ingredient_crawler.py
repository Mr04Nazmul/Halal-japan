import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from crawl_japanese_ingredients import Collector,extract,product_url,canonical

HTML='''<h1>Product</h1><table><tr><th>商品名</th><td>テスト米菓</td></tr><tr><th>JANCODE</th><td>4973728910141</td></tr><tr><th>原材料</th><td>米、食塩</td></tr></table>'''
URL='https://muso.co.jp/item/32882.html'
class Extraction(unittest.TestCase):
 def test_exact_ingredient_field_and_explicit_jan(self):
  r,e=extract(HTML,URL)
  self.assertIsNone(e);self.assertEqual(r['ingredients_ja'],'米、食塩');self.assertEqual(r['jan'],'4973728910141')
  self.assertEqual(r['rule_result'],'HALAL');self.assertFalse(r['halal_certified'])
  bourbon=HTML.replace('原材料','原材料名／添加物名').replace('米、食塩','小麦粉／乳化剤（大豆由来）、香料')
  r,e=extract(bourbon,'https://www.bourbon.co.jp/product/detail/35359-03.html')
  self.assertIsNone(e);self.assertEqual(r['rule_result'],'HARAM')
 def test_additives_only_field_is_not_a_complete_ingredient_list(self):
  html=HTML.replace('米、食塩','添加物：酸化防止剤(亜硫酸塩)')
  r,e=extract(html,URL)
  self.assertIsNone(r)
  self.assertEqual(e,'additives_only_incomplete_ingredients')
 def test_missing_and_ambiguous_never_count(self):
  self.assertIsNone(extract('<h1>米菓</h1><p>アレルゲン：小麦</p>',URL)[0])
  self.assertIsNone(extract(HTML+'<dl><dt>原材料</dt><dd>豚肉</dd></dl>',URL)[0])
  r,_=extract(HTML.replace('<tr><th>JANCODE</th><td>4973728910141</td></tr>',''),URL)
  self.assertIsNone(r['jan'])
 def test_unicode_path_is_percent_encoded_before_request(self):
  self.assertEqual(canonical('https://muso.co.jp/item/tag/新商品'),
   'https://muso.co.jp/item/tag/%E6%96%B0%E5%95%86%E5%93%81')
 def test_unicode_encode_failures_are_requeued_on_extractor_upgrade(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   c.db.execute("INSERT INTO queue(url,status,attempts,error) VALUES(?,?,?,?)",
    ('https://muso.co.jp/item/tag/新商品','done',5,"UnicodeEncodeError:'ascii' codec can't encode characters"))
   c.db.execute("DELETE FROM metadata WHERE key='extractor_version'");c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.db.execute('SELECT status,attempts,error FROM queue').fetchone(),('pending',0,None))
   c.db.close()
 def test_official_itoen_and_ucc_product_patterns(self):
  from crawl_japanese_ingredients import allowed_link
  self.assertTrue(product_url('https://www.itoen.jp/products/43679/'))
  self.assertTrue(product_url('https://www.ucc.co.jp/product/instant/class-one/class-one-bin-170g.html'))
  self.assertTrue(product_url('https://www.ucc.co.jp/product/drink/coffee/cold-brew/cold-brew-latte.html'))
  self.assertFalse(product_url('https://www.itoen.jp/products/'))
  self.assertFalse(product_url('https://www.ucc.co.jp/product/'))
  self.assertFalse(product_url('https://www.ucc.co.jp/product/instant/'))
  self.assertFalse(product_url('https://www.itoen.jp.evil.example/products/43679/'))
  self.assertTrue(allowed_link('https://www.itoen.jp/products/'))
  self.assertTrue(allowed_link('https://www.ucc.co.jp/product/'))
 def test_pokka_sapporo_official_product_and_catalog(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://www.pokkasapporo-fb.jp/products/water/water/WW50.html'
  self.assertTrue(product_url(url))
  self.assertTrue(allowed_link(url))
  self.assertTrue(allowed_link('https://www.pokkasapporo-fb.jp/products/new.html'))
  self.assertFalse(product_url('https://www.pokkasapporo-fb.jp/products/new.html'))
  self.assertFalse(product_url('https://www.pokkasapporo-fb.jp.evil.example/products/water/water/WW50.html'))
  html='<h1>Green Pack Water（195g）</h1><table><tr><th>JANコード</th><td>4902471103814</td></tr><tr><th>原材料</th><td>水（純水）</td></tr></table>'
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['jan'],'4902471103814')
  self.assertEqual(record['ingredients_ja'],'水（純水）')
  self.assertFalse(record['halal_certified'])
 def test_asahi_official_product_and_hyphenated_jan(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://www.asahiinryo.co.jp/products/milkybeverage/gungun_yogurun/2E2AA.html'
  self.assertTrue(product_url(url))
  self.assertTrue(product_url('https://www.asahiinryo.co.jp/products/others/koku_uma/'))
  self.assertFalse(product_url('https://www.asahiinryo.co.jp/products/'))
  self.assertFalse(product_url('https://www.asahiinryo.co.jp.evil.example/products/milkybeverage/gungun_yogurun/2E2AA.html'))
  self.assertTrue(allowed_link('https://www.asahiinryo.co.jp/products/'))
  html='''<h1>ぐんぐんヨグルン PET500ml</h1><table>
  <tr><th>原材料名</th><td>果糖ぶどう糖液糖（国内製造）、脱脂粉乳、乳酸菌飲料、食塩／酸味料、香料</td></tr>
  <tr><th>JANコード</th><td>49-01340-09964-7</td></tr></table>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['jan'],'4901340099647')
  self.assertEqual(record['name_ja'],'ぐんぐんヨグルン PET500ml')
  self.assertFalse(record['halal_certified'])
  self.assertEqual(record['source_publisher'],'asahiinryo.co.jp')
  bad=html.replace('49-01340-09964-7','49-01340-09964-0')
  record,error=extract(bad,url)
  self.assertIsNone(error)
  self.assertIsNone(record['jan'])

 def test_no_host_spoofing(self):
  self.assertFalse(product_url('https://muso.co.jp.evil.example/item/32882.html'))
 def test_wrapped_heading_and_trailing_slash_label(self):
  html='''<title>公式たれ | メーカー</title><h1>公式たれ</h1>
  <section><div><h3>原材料名／</h3></div><p>果実、食塩</p></section>'''
  r,e=extract(html,'https://www.ebarafoods.com/products/detail/TEST.html')
  self.assertIsNone(e);self.assertEqual(r['ingredients_ja'],'果実、食塩')
  combined='''<title>公式たれ | メーカー</title><h1>公式たれ</h1>
  <p>原材料名／<br>果実、食塩</p>'''
  r,e=extract(combined,'https://www.ebarafoods.com/products/detail/TEST2.html')
  self.assertIsNone(e);self.assertEqual(r['ingredients_ja'],'果実、食塩')
 def test_generic_h1_uses_unambiguous_official_title(self):
  html='''<title>牛めし | 米飯 | メーカー</title><h1>商品情報</h1>
  <dl><dt>原材料名</dt><dd>米、牛肉</dd></dl>'''
  r,e=extract(html,'https://www.tablemark.co.jp/products/frozen/rice/detail/1.html')
  self.assertIsNone(e);self.assertEqual(r['name_ja'],'牛めし')
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
 def test_new_official_seed_is_processed_before_older_discovery_backlog(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   old='https://muso.co.jp/item/10022.html'
   c.db.execute("INSERT INTO queue(url) VALUES(?)",(old,));c.db.commit()
   visited=[]
   c.request=lambda u: 'User-agent: *\nAllow: /' if u.endswith('/robots.txt') else (visited.append(u) or HTML)
   c.run([URL],1,1)
   self.assertEqual(visited[0],URL)
   self.assertEqual(c.db.execute("SELECT status FROM queue WHERE url=?",(old,)).fetchone()[0],'pending')
   c.db.close()
 def test_pending_product_url_outranks_old_navigation_backlog(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   navigation='https://muso.co.jp/item/tag/older-list'
   product='https://www.meiji.co.jp/products/yogurt/4902705127654.html'
   self.assertTrue(product_url(product))
   c.db.executemany("INSERT INTO queue(url) VALUES(?)",[(navigation,),(product,)])
   c.db.commit()
   visited=[]
   c.permitted=lambda u:True
   c.request=lambda u:(visited.append(u) or HTML)
   c.run([],1,1)
   self.assertEqual(visited,[product])
   self.assertEqual(c.db.execute("SELECT status FROM queue WHERE url=?",(navigation,)).fetchone()[0],'pending')
   c.db.close()
 def test_official_sitemap_outranks_navigation_and_replenishes_product_queue(self):
  from crawl_japanese_ingredients import allowed_link,sitemap_url
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   navigation='https://muso.co.jp/item/tag/old-list'
   sitemap='https://muso.co.jp/sitemap-products.xml'
   product='https://muso.co.jp/item/32882.html'
   self.assertTrue(sitemap_url(sitemap))
   self.assertTrue(allowed_link(sitemap))
   self.assertFalse(sitemap_url('https://muso.co.jp.evil.example/sitemap.xml'))
   c.db.executemany("INSERT INTO queue(url) VALUES(?)",[(navigation,),(sitemap,)])
   c.db.commit()
   visited=[]
   c.permitted=lambda u:True
   def page(url):
    visited.append(url)
    if url==sitemap:return '<urlset><url><loc>'+product+'</loc></url></urlset>'
    return HTML
   c.request=page
   c.run([],2,1)
   self.assertEqual(visited,[sitemap,product])
   self.assertEqual(c.db.execute("SELECT status FROM queue WHERE url=?",(navigation,)).fetchone()[0],'pending')
   c.db.close()

 def test_discovered_product_is_prioritized_on_next_page(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   navigation='https://muso.co.jp/item/tag/first-list'
   backlog='https://muso.co.jp/item/tag/older-list'
   product='https://www.meiji.co.jp/products/yogurt/4902705127654.html'
   c.db.executemany("INSERT INTO queue(url) VALUES(?)",[(navigation,),(backlog,)])
   c.db.commit()
   visited=[]
   c.permitted=lambda u:True
   def page(url):
    visited.append(url)
    if url==navigation:return '<a href="'+product+'">新商品</a>'
    return HTML
   c.request=page
   c.run([],2,1)
   self.assertEqual(visited,[navigation,product])
   c.db.close()
 def test_extractor_upgrade_requeues_only_field_rejections_once(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   c.db.execute("INSERT INTO queue(url,status,attempts,error) VALUES(?,?,?,?)",(URL,'done',1,'missing_or_ambiguous_ingredients'))
   c.db.execute("DELETE FROM metadata WHERE key='extractor_version'");c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.db.execute('SELECT status,attempts,error FROM queue').fetchone(),('pending',0,None))
   c.db.execute("UPDATE queue SET status='done',attempts=1,error='missing_or_ambiguous_ingredients'");c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.db.execute('SELECT status FROM queue').fetchone()[0],'done')

 def test_kyoritsu_shop_official_single_product_ingredients_and_jan(self):
  url='https://shop.kyoritsu-foods.co.jp/item-detail/1946407'
  self.assertTrue(product_url(url))
  html='''<title>素焼きピスタチオ | 共立食品ショップ</title>
  <h1>【1個】素焼きピスタチオ 500G</h1>
  <div>JANコード</div><div>4901325404770</div>
  <p>●原材料名…ピスタチオ（アメリカ）</p>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['jan'],'4901325404770')
  self.assertEqual(record['ingredients_ja'],'ピスタチオ(アメリカ)')
  self.assertFalse(record['halal_certified'])
  self.assertFalse(product_url('https://shop.kyoritsu-foods.co.jp.evil.example/item-detail/1946407'))
  bad=html.replace('4901325404770','4901325404771')
  record,error=extract(bad,url)
  self.assertIsNone(error)
  self.assertIsNone(record['jan'])

 def test_kyoritsu_official_product_code_and_pork_gelatin(self):
  url='https://www.kyoritsu-foods.co.jp/product/275/'
  html='''<h1>ゼラチンリーフ</h1><table>
  <tr><th>商品名</th><td>ゼラチンリーフ</td></tr>
  <tr><th>コード</th><td>4901325124364</td></tr>
  <tr><th>原材料名</th><td>ゼラチン（豚由来）</td></tr></table>'''
  self.assertTrue(product_url(url))
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['jan'],'4901325124364')
  self.assertEqual(record['ingredients_ja'],'ゼラチン（豚由来）')
  self.assertEqual(record['rule_result'],'HARAM')
  self.assertFalse(record['halal_certified'])


 def test_kagome_official_foodservice_products_and_ingredients(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://www.kagome.co.jp/foodservice/frozen/5615/'
  self.assertTrue(product_url(url))
  self.assertTrue(product_url('https://www.kagome.co.jp/foodservice/dry/3526/'))
  self.assertTrue(allowed_link('https://www.kagome.co.jp/foodservice/'))
  self.assertFalse(product_url('https://www.kagome.co.jp.evil.example/foodservice/frozen/5615/'))
  self.assertFalse(product_url('https://www.kagome.co.jp/foodservice/frozen/'))
  html='''<h1>赤・黄ピーマングリルのミックス</h1><dl>
  <dt>商品名</dt><dd>赤・黄ピーマングリルのミックス</dd>
  <dt>JANコード</dt><dd>4901306056158</dd>
  <dt>原材料</dt><dd>グリル野菜（赤ピーマン、黄ピーマン）</dd>
  </dl>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['jan'],'4901306056158')
  self.assertEqual(record['ingredients_ja'],'グリル野菜（赤ピーマン、黄ピーマン）')
  self.assertEqual(record['source_publisher'],'kagome.co.jp')
  self.assertFalse(record['halal_certified'])

 def test_agf_official_product_name_ingredients_and_jan(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://agf.ajinomoto.co.jp/product/detail/74230'
  self.assertTrue(product_url(url))
  self.assertTrue(allowed_link('https://agf.ajinomoto.co.jp/product/'))
  self.assertFalse(product_url('https://agf.ajinomoto.co.jp/product/'))
  self.assertFalse(product_url('https://agf.ajinomoto.co.jp.evil.example/product/detail/74230'))
  html='''<h1>「森彦の時間®」 まろやか</h1>
  <h2>「森彦の時間®」 まろやか１２０ｇ</h2>
  <p>原材料名</p><p>コーヒー豆</p>
  <p>JANコード</p><p>4901111554733</p>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'「森彦の時間®」 まろやか１２０ｇ')
  self.assertEqual(record['jan'],'4901111554733')
  self.assertEqual(record['ingredients_ja'],'コーヒー豆')
  self.assertFalse(record['halal_certified'])

if __name__=='__main__':unittest.main()