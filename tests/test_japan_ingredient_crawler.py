import json,sys,tempfile,unittest,time,urllib.error,sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from crawl_japanese_ingredients import Collector,extract,product_url,canonical

HTML='''<h1>Product</h1><table><tr><th>商品名</th><td>テスト米菓</td></tr><tr><th>JANCODE</th><td>4973728910141</td></tr><tr><th>原材料</th><td>米、食塩</td></tr></table>'''
URL='https://muso.co.jp/item/32882.html'
class Extraction(unittest.TestCase):
 def test_muso_product_table_extracts_explicit_jan_and_ingredients(self):
  record,error=extract(HTML,URL)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'テスト米菓')
  self.assertEqual(record['jan'],'4973728910141')
  self.assertEqual(record['ingredients_ja'],'米、食塩')
  self.assertFalse(record['halal_certified'])

 def test_muso_label_recovery_requeues_only_seeded_field_rejections(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   rejected='https://muso.co.jp/item/32882.html'
   blocked='https://muso.co.jp/item/32883.html'
   accepted='https://muso.co.jp/item/32884.html'
   c.db.executemany('INSERT INTO queue(url,status,attempts,next_try,error) VALUES(?,?,?,?,?)',[
    (rejected,'done',1,0,'missing_or_ambiguous_ingredients'),
    (blocked,'done',1,0,'robots_disallowed'),
    (accepted,'done',1,0,'missing_or_ambiguous_ingredients')])
   c.db.execute('INSERT INTO products(id,formula,payload) VALUES(?,?,?)',
    ('existing:muso','existing',json.dumps({'source_url':accepted,'jan':None,'rule_result':'UNKNOWN'})))
   c.db.commit()
   c.permitted=lambda u:True
   c.request=lambda u:HTML
   c.run([rejected,blocked,accepted],max_pages=1,minutes=0.1)
   self.assertEqual(c.count(),2)
   self.assertEqual(c.db.execute('SELECT status,error FROM queue WHERE url=?',(rejected,)).fetchone(),('done',None))
   self.assertEqual(c.db.execute('SELECT status,error FROM queue WHERE url=?',(blocked,)).fetchone(),('done','robots_disallowed'))
   self.assertEqual(c.db.execute('SELECT status,error FROM queue WHERE url=?',(accepted,)).fetchone(),('done','missing_or_ambiguous_ingredients'))
   c.db.close()
 def test_housefoods_origin_heading_is_not_an_ingredient_declaration(self):
  url='https://housefoods.jp/products/catalog/cd_1,092996.html'
  ingredients='コーングリッツ（国内製造）、植物油脂、食塩／調味料（アミノ酸等）、（一部に豚肉を含む）'
  html=f'''<title>６２ｇ とんがりコーン | ハウス食品</title>
  <h1>６２ｇ とんがりコーン</h1><div id="materials">
  <h2>原材料名／主な原材料の産地</h2>
  <table><tr><th>原材料名</th><td>{ingredients}</td></tr>
  <tr><th>主な原材料の産地</th><td>コーングリッツ［とうもろこし（アメリカ産）］</td></tr></table></div>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['ingredients_ja'],ingredients)
  self.assertEqual(record['name_ja'],'６２ｇ とんがりコーン')
  self.assertIsNone(record['jan'])
  self.assertFalse(record['halal_certified'])
  # The section heading alone is never enough to create a product record.
  self.assertEqual(extract('<h1>商品</h1><h2>原材料名／主な原材料の産地</h2>',url)[1],
                   'missing_or_ambiguous_ingredients')

 def test_housefoods_failed_field_pages_requeued_once_without_touching_blocks(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   base='https://housefoods.jp/products/catalog/cd_1,'
   rejected=base+'092996.html'
   blocked=base+'092997.html'
   accepted=base+'092998.html'
   c.db.executemany('INSERT INTO queue(url,status,error) VALUES(?,?,?)',[
    (rejected,'done','missing_or_ambiguous_ingredients'),
    (blocked,'done','robots_disallowed'),
    (accepted,'done','missing_or_ambiguous_ingredients')])
   c.db.execute('INSERT INTO products(id,formula,payload) VALUES(?,?,?)',
                ('accepted:test','f',json.dumps({'source_url':accepted})))
   c.db.execute("UPDATE metadata SET value='official-fields-2026-11-02-v11-marukome-business' WHERE key='extractor_version'")
   c.db.execute("DELETE FROM metadata WHERE key='housefoods_origin_heading_recovery_20261103'")
   c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(rejected,)).fetchone()[0],'pending')
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(blocked,)).fetchone()[0],'done')
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(accepted,)).fetchone()[0],'done')
   self.assertEqual(c.count(),1)
   c.db.execute("UPDATE queue SET status='done',error='missing_or_ambiguous_ingredients' WHERE url=?",(rejected,))
   c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(rejected,)).fetchone()[0],'done')
   c.db.close()
 def test_missing_product_404_does_not_block_other_products_on_host(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   first='https://muso.co.jp/item/32882.html'
   second='https://muso.co.jp/item/32883.html'
   c.permitted=lambda u:True
   def request(u):
    if u==first:raise urllib.error.HTTPError(u,404,'Not Found',{},None)
    return HTML
   c.request=request
   c.run([first,second],max_pages=2,minutes=1)
   self.assertEqual(c.count(),1)
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(first,)).fetchone()[0],'done')
   self.assertIsNone(c.db.execute("SELECT reason FROM host_state WHERE host='muso.co.jp'").fetchone())
   c.db.close()

 def test_old_404_host_cooldowns_are_cleared_without_dropping_queue(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   c.db.execute("INSERT INTO host_state VALUES(?,?,?)",('muso.co.jp',time.time()+900,'HTTPError:404'))
   c.db.execute("INSERT INTO queue(url) VALUES(?)",('https://muso.co.jp/item/32882.html',))
   c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertIsNone(c.db.execute("SELECT reason FROM host_state WHERE host='muso.co.jp'").fetchone())
   self.assertEqual(c.db.execute('SELECT count(*) FROM queue').fetchone()[0],1)
   c.db.close()

 def test_asahi_maintenance_page_is_not_an_ingredient_record(self):
  from crawl_japanese_ingredients import is_temporary_maintenance
  url='https://www.asahiinryo.co.jp/products/milkybeverage/calpis_the_rich/2E24T.html'
  maintenance='<html><h1>まことに申し訳ございません。ただいまメンテナンス中です。</h1><p>安全性が確認でき次第、順次再開を予定しています。</p></html>'
  self.assertTrue(is_temporary_maintenance(maintenance,url))
  self.assertFalse(is_temporary_maintenance(maintenance,'https://7premium.jp/product/search/detail?id=10791'))
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   c.permitted=lambda u:True
   c.request=lambda u:maintenance
   c.run([url],max_pages=1,minutes=0.1)
   status,attempts,next_try,error=c.db.execute('SELECT status,attempts,next_try,error FROM queue WHERE url=?',(url,)).fetchone()
   self.assertEqual((status,attempts,error),('pending',1,'temporary_source_maintenance'))
   self.assertGreater(next_try,0)
   self.assertEqual(c.count(),0)
   c.db.close()

 def test_asahi_old_field_rejections_requeued_once_on_upgrade(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   url='https://www.asahiinryo.co.jp/products/milkybeverage/calpis_the_rich/2E24T.html'
   agf='https://agf.ajinomoto.co.jp/product/detail/14113'
   c.db.executemany('INSERT INTO queue(url,status,error) VALUES(?,?,?)',
    [(url,'done','missing_or_ambiguous_ingredients'),(agf,'done','missing_or_ambiguous_ingredients')])
   c.db.execute("UPDATE metadata SET value='official-fields-2026-11-01-v8-agf-div' WHERE key='extractor_version'")
   c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(url,)).fetchone()[0],'pending')
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(agf,)).fetchone()[0],'done')
   c.db.close()

 def test_reject_origin_heading_and_packaging_polymer(self):
  for value in ('主な原材料の産地','ポリエチレン'):
   with self.subTest(value=value):
    r,e=extract(HTML.replace('米、食塩',value),URL)
    self.assertIsNone(r)
    self.assertEqual(e,'non_ingredient_text')
 def test_quarantine_legacy_checkpoint_on_upgrade(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   url='https://housefoods.jp/products/catalog/cd_1,082675,spice2,youfu,all.html'
   c.db.execute("INSERT INTO queue(url,status) VALUES(?,?)",(url,'done'))
   record={'ingredients_ja':'主な原材料の産地','source_url':url}
   c.db.execute("INSERT INTO products(id,formula,payload) VALUES(?,?,?)",('old:placeholder','x',json.dumps(record)))
   c.db.execute("UPDATE metadata SET value='old-extractor' WHERE key='extractor_version'")
   c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.count(),0)
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(url,)).fetchone()[0],'pending')
   c.db.close()
 def test_complete_sake_lees_ingredients_are_captured_for_review(self):
  html=HTML.replace('米、食塩','米、酒かす、食塩')
  record,error=extract(html,URL)
  self.assertIsNone(error)
  self.assertEqual(record['ingredients_ja'],'米、酒かす、食塩')
  self.assertEqual(record['rule_result'],'UNKNOWN')
  self.assertFalse(record['halal_certified'])
  self.assertEqual(record['ingredient_field_status'],'complete_displayed_field')
  self.assertEqual(record['jan'],'4973728910141')
 def test_old_unknown_rejection_requeued_only_after_extractor_upgrade(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   url='https://agf.ajinomoto.co.jp/product/detail/14113'
   blocked='https://agf.ajinomoto.co.jp/product/detail/14114'
   c.db.execute("INSERT INTO queue(url,status,attempts,error) VALUES(?,?,?,?)",
    (url,'done',3,'incomplete_ingredient_declaration'))
   c.db.execute("INSERT INTO queue(url,status,attempts,error) VALUES(?,?,?,?)",
    (blocked,'done',3,'robots_disallowed'))
   c.db.execute("UPDATE metadata SET value='old-extractor' WHERE key='extractor_version'")
   c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.db.execute("SELECT status,attempts,error FROM queue WHERE url=?",(url,)).fetchone(),('pending',0,None))
   self.assertEqual(c.db.execute("SELECT status,error FROM queue WHERE url=?",(blocked,)).fetchone(),('done','robots_disallowed'))
   c.db.close()
 def test_exact_ingredient_field_and_explicit_jan(self):
  r,e=extract(HTML,URL)
  self.assertIsNone(e);self.assertEqual(r['ingredients_ja'],'米、食塩');self.assertEqual(r['jan'],'4973728910141')
  self.assertEqual(r['rule_result'],'HALAL');self.assertFalse(r['halal_certified'])
  bourbon=HTML.replace('原材料','原材料名／添加物名').replace('米、食塩','小麦粉／乳化剤（大豆由来）、香料')
  r,e=extract(bourbon,'https://www.bourbon.co.jp/product/detail/35359-03.html')
  self.assertIsNone(e);self.assertEqual(r['rule_result'],'HARAM')
 def test_escaped_html_is_not_a_verified_ingredient_field(self):
  for artifact in ('米&lt;br&gt;食塩', '米&#60;br&#62;食塩'):
   with self.subTest(artifact=artifact):
    record,error=extract(HTML.replace('米、食塩',artifact),URL)
    self.assertIsNone(record)
    self.assertEqual(error,'unresolved_html_in_ingredient_field')
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
 def test_topvalu_official_category_pagination_keeps_required_query(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://www.topvalu.net/items/list/100575100/?direction=desc&page=2&sort=Products.release_datetime'
  self.assertTrue(allowed_link(url))
  self.assertEqual(canonical(url),url)
  self.assertEqual(canonical('https://www.topvalu.net/items/detail/4549414696004/?sort=Products.release_datetime'),
   'https://www.topvalu.net/items/detail/4549414696004/')
 def test_refreshes_successful_catalogue_seeds_without_retrying_products_or_blocks(self):
  from crawl_japanese_ingredients import allowed_link
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   catalogue='https://www.topvalu.net/items/'
   myojo_catalogue='https://www.myojofoods.co.jp/products/items/'
   nissin_catalogue='https://www.nissin.com/jp/'
   muso_sitemap='https://muso.co.jp/wp-sitemap.xml'
   product='https://www.topvalu.net/items/detail/4549414700565/'
   blocked='https://www.kewpie.co.jp/products/'
   self.assertTrue(allowed_link(myojo_catalogue))
   self.assertTrue(allowed_link(nissin_catalogue))
   self.assertTrue(allowed_link(muso_sitemap))
   seeds=[catalogue,myojo_catalogue,nissin_catalogue,muso_sitemap,product,blocked]
   c.enqueue(seeds)
   c.db.execute("UPDATE queue SET status='done'")
   c.db.execute("UPDATE queue SET error='robots_disallowed' WHERE url=?",(blocked,))
   c.db.commit()
   # A zero-page run exercises seed preparation without making HTTP requests.
   c.run(seeds,max_pages=0,minutes=0)
   states=dict(c.db.execute("SELECT url,status FROM queue"))
   self.assertEqual(states[canonical(catalogue)],'pending')
   self.assertEqual(states[canonical(myojo_catalogue)],'pending')
   self.assertEqual(states[canonical(nissin_catalogue)],'pending')
   self.assertEqual(states[canonical(muso_sitemap)],'pending')
   self.assertEqual(states[canonical(product)],'done')
   self.assertEqual(states[canonical(blocked)],'done')
   c.db.close()
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
 def test_reject_recursive_marketing_navigation_not_product_pages(self):
  from crawl_japanese_ingredients import allowed_link
  recursive='https://housefoods.jp/products/special/currymarche/arrangement/qa/product/qa/product/index.html'
  self.assertFalse(allowed_link(recursive))
  self.assertFalse(allowed_link('https://www.kagome.co.jp/products/brand/ys100/chisan/farmer/10/'))
  self.assertTrue(allowed_link('https://housefoods.jp/products/catalog/cd_1%2C083967%2Cspice%2Cyoufu%2Chouse_s.html'))
  self.assertTrue(allowed_link('https://www.kagome.co.jp/foodservice/frozen/5615/'))

 def test_skip_kagome_marketing_backlog_without_deleting_queue(self):
  from crawl_japanese_ingredients import allowed_link
  marketing=['https://www.kagome.co.jp/products/vegetablejuice/brand/',
             'https://and.kagome.co.jp/products/feature/']
  product='https://www.kagome.co.jp/foodservice/frozen/5615/'
  self.assertTrue(allowed_link(product))
  for url in marketing:self.assertFalse(allowed_link(url))
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   good='https://muso.co.jp/item/tag/new-products'
   c.db.executemany("INSERT INTO queue(url) VALUES(?)",[(url,) for url in marketing+[good]])
   c.db.commit()
   visited=[]
   c.permitted=lambda u:True
   c.request=lambda u:(visited.append(u) or '<h1>Catalog</h1>')
   c.run([],max_pages=1,minutes=1)
   self.assertEqual(visited,[good])
   for url in marketing:
    self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(url,)).fetchone()[0],'pending')
   c.db.close()

 def test_skip_legacy_marketing_backlog_without_deleting_queue(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   bad='https://housefoods.jp/products/special/currymarche/arrangement/qa/product/index.html'
   kagome='https://www.kagome.co.jp/products/brand/ys100/chisan/farmer/10/'
   good='https://muso.co.jp/item/tag/new-products'
   c.db.executemany("INSERT INTO queue(url) VALUES(?)",[(bad,),(kagome,),(good,)])
   c.db.commit()
   visited=[]
   c.permitted=lambda u:True
   c.request=lambda u:(visited.append(u) or '<h1>Catalog</h1>')
   c.run([],max_pages=1,minutes=1)
   self.assertEqual(visited,[good])
   self.assertEqual(c.db.execute("SELECT status FROM queue WHERE url=?",(bad,)).fetchone()[0],'pending')
   self.assertEqual(c.db.execute("SELECT status FROM queue WHERE url=?",(kagome,)).fetchone()[0],'pending')
   c.db.close()

 def test_quarantines_legacy_marketing_backlog_without_deleting_rows(self):
  with tempfile.TemporaryDirectory() as folder:
   db=sqlite3.connect(Path(folder)/'state.sqlite3')
   db.executescript('''CREATE TABLE queue(url TEXT PRIMARY KEY,status TEXT DEFAULT 'pending',attempts INTEGER DEFAULT 0,next_try REAL DEFAULT 0,error TEXT);
   CREATE TABLE products(id TEXT PRIMARY KEY,formula TEXT,payload TEXT,conflict INTEGER DEFAULT 0);
   CREATE TABLE host_state(host TEXT PRIMARY KEY,next_try REAL DEFAULT 0,reason TEXT);
   CREATE TABLE observations(url TEXT,reason TEXT,at TEXT);
   CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);''')
   db.execute("INSERT INTO metadata VALUES('extractor_version',?)",('official-fields-2026-11-22-v14-glico-product-name-jan',))
   urls=[
    'https://housefoods.jp/products/special/currymarche/arrangement/qa/index.html',
    'https://www.kagome.co.jp/products/brand/ys100/chisan/farmer/10/',
    'https://and.kagome.co.jp/products/feature/',
    'https://housefoods.jp/products/catalog/cd_1,092996.html']
   db.executemany("INSERT INTO queue(url,status) VALUES(?,'pending')",[(u,) for u in urls])
   db.commit();db.close()
   c=Collector(folder,100000)
   for url in urls[:3]:
    self.assertEqual(c.db.execute('SELECT status,error FROM queue WHERE url=?',(url,)).fetchone(),
                     ('done','out_of_scope_navigation'))
   self.assertEqual(c.db.execute('SELECT status,error FROM queue WHERE url=?',(urls[3],)).fetchone(),
                    ('pending',None))
   self.assertEqual(c.db.execute('SELECT count(*) FROM queue').fetchone()[0],4)
   self.assertEqual(c.db.execute("SELECT value FROM metadata WHERE key='legacy_marketing_navigation_quarantine_20261122_v1'").fetchone()[0],'done')
   c.db.close()

 def test_montoile_official_product_page_extracts_labelled_jan_and_ingredients(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://montoile.co.jp/products/hannama-assort/'
  self.assertTrue(product_url(url))
  self.assertTrue(product_url('https://www.matsukiyococokara-online.com/store/catalog/product/view/id/4904083473651'))
  self.assertTrue(allowed_link('https://montoile.co.jp/products-sitemap.xml'))
  self.assertFalse(product_url('https://montoile.co.jp/product_category/hannama/'))
  html='''<main><section id="product"><h1>半生アソート</h1>
  <dl><div><dt>内容量</dt><dd>１３４ｇ</dd></div>
  <div><dt>JANコード</dt><dd>4580530497045</dd></div></dl>
  <div class="product_detail"><div class="inner"><h2>原材料名</h2>
  <div>〈粒あんどら焼〉砂糖、小麦粉、液全卵／膨脹剤、香料<br>
  〈栗どら焼〉砂糖、生あん、小麦粉／トレハロース、膨脹剤</div>
  </div></div></section></main>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'半生アソート')
  self.assertEqual(record['jan'],'4580530497045')
  self.assertIn('〈粒あんどら焼〉',record['ingredients_ja'])
  self.assertIn('〈栗どら焼〉',record['ingredients_ja'])
  self.assertEqual(record['source_publisher'],'montoile.co.jp')
  self.assertFalse(record['halal_certified'])

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
  for catalogue in ('https://www.asahiinryo.co.jp/products/list/nutrition/',
                    'https://www.asahiinryo.co.jp/products/list/jan/0002.html'):
   self.assertFalse(product_url(catalogue))
   self.assertTrue(allowed_link(catalogue))
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

 def test_nissin_official_product_with_blank_decorative_h1(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://www.nissin.com/jp/product/items/11309/'
  self.assertTrue(product_url(url))
  self.assertTrue(allowed_link(url))
  self.assertFalse(product_url('https://www.nissin.com.evil.example/jp/product/items/11309/'))
  html='''<title>0秒チキンラーメン | 日清食品グループ</title>
  <h1> </h1><h1>0秒チキンラーメン</h1>
  <table><tr><th>JANコード</th><td>4902105112113</td></tr></table>
  <section><h2>原材料名</h2><p>小麦粉（国内製造）、植物油脂、しょうゆ</p></section>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'0秒チキンラーメン')
  self.assertEqual(record['jan'],'4902105112113')
  self.assertEqual(record['ingredients_ja'],'小麦粉（国内製造）、植物油脂、しょうゆ')
  self.assertFalse(record['halal_certified'])
  record,error=extract(html.replace('4902105112113','invalid'),url)
  self.assertIsNone(error)
  self.assertIsNone(record['jan'])

 def test_full_ingredient_label_outweighs_origin_material_rows(self):
  # Nissin publishes the full declaration and a separate origin-of-materials
  # table. The latter must not be treated as another competing ingredient list.
  url='https://www.nissin.com/jp/product/items/11309/'
  html='''<title>0秒チキンラーメン | 日清食品</title><h1>0秒チキンラーメン</h1>
  <table><tr><th>JANコード</th><td>4902105112113</td></tr></table>
  <section><h2>原材料名</h2><p>小麦粉（国内製造）、植物油脂、しょうゆ</p></section>
  <h2>主な原材料の産地情報</h2>
  <table><tr><th>原材料</th><td>小麦粉（小麦）</td></tr>
  <tr><th>原材料</th><td>植物油脂（パーム）</td></tr></table>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['ingredients_ja'],'小麦粉（国内製造）、植物油脂、しょうゆ')
  self.assertEqual(record['jan'],'4902105112113')
  self.assertFalse(record['halal_certified'])
  # Two different full ingredient declarations remain ambiguous: fail closed.
  ambiguous=html.replace('</section>','<p>原材料名：豚肉、食塩</p></section>')
  record,error=extract(ambiguous,url)
  self.assertIsNone(record)
  self.assertEqual(error,'missing_or_ambiguous_ingredients')

 def test_dydo_official_product_pattern_and_label(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://www.dydo.co.jp/products/detail/1231/'
  self.assertTrue(product_url(url))
  self.assertTrue(allowed_link('https://www.dydo.co.jp/products/'))
  self.assertTrue(allowed_link('https://www.dydo.co.jp/products/list/'))
  listing='https://www.dydo.co.jp/products/list/?rt_bn_product_list_skip=12&rt_bn_product_list_all_skip='
  self.assertTrue(allowed_link(listing))
  self.assertIn('rt_bn_product_list_skip=12',canonical(listing))
  self.assertIn('rt_bn_product_list_all_skip=',canonical(listing))
  self.assertNotIn('tracking=',canonical(listing+'&tracking=ignore'))
  self.assertFalse(product_url('https://www.dydo.co.jp/products/'))
  self.assertFalse(product_url('https://www.dydo.co.jp.evil.example/products/detail/1231/'))
  html='''<title>ミウ スポーツチャージ｜商品情報｜ダイドードリンコ</title>
  <h1>ミウ スポーツチャージ</h1><table>
  <tr><th>原材料</th><td>糖類(砂糖(国内製造)、果糖ぶどう糖液糖)、食塩／酸味料、粗製海水塩化マグネシウム、甘味料（アセスルファムK、スクラロース）、香料、酸化防止剤(ビタミンC)</td></tr>
  </table>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'ミウ スポーツチャージ')
  self.assertIsNone(record['jan'])
  self.assertEqual(record['source_publisher'],'dydo.co.jp')
  self.assertFalse(record['halal_certified'])

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
   agf='https://agf.ajinomoto.co.jp/product/detail/14113'
   c.db.execute("INSERT INTO queue(url,status,attempts,error) VALUES(?,?,?,?)",(agf,'done',1,'missing_or_ambiguous_ingredients'))
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

 def test_agf_real_div_based_ingredient_and_jan_markup(self):
  # Fixture follows the actual labelled div structure of AGF's official
  # /product/detail/14113 page, rather than an invented p/p table.
  url='https://agf.ajinomoto.co.jp/product/detail/14113'
  html='''<h1>「煎」プレミアムドリップ</h1>
  <h2>「煎」プレミアムドリップ 濃厚 深いコク２０袋</h2>
  <div class="agf-cs-product-table-row"><div class="agf-cs-product-table-heading">原材料名</div>
  <div class="agf-cs-product-table-data">コーヒー豆</div></div>
  <div class="agf-cs-product-table-row"><div class="agf-cs-product-table-heading">JANコード</div>
  <div class="agf-cs-product-table-data">4901111960473</div></div>
  <div class="agf-cs-product-table-row"><div class="agf-cs-product-table-heading">主な原料の産地</div>
  <div class="agf-cs-product-table-data">生豆生産国名：タンザニア、コロンビア、他</div></div>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['ingredients_ja'],'コーヒー豆')
  self.assertEqual(record['jan'],'4901111960473')
  self.assertEqual(record['name_ja'],'「煎」プレミアムドリップ 濃厚 深いコク２０袋')
  self.assertFalse(record['halal_certified'])
  missing_jan=html.replace('4901111960473','')
  record,error=extract(missing_jan,url)
  self.assertIsNone(error)
  self.assertIsNone(record['jan'])
  conflicting=html.replace('</div></div>','</div></div><div class="agf-cs-product-table-row"><div class="agf-cs-product-table-heading">原材料名</div><div class="agf-cs-product-table-data">豚肉</div></div>',1)
  record,error=extract(conflicting,url)
  self.assertIsNone(record)
  self.assertEqual(error,'missing_or_ambiguous_ingredients')

 def test_agf_only_requeue_does_not_replay_unrelated_missing_fields(self):
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   agf='https://agf.ajinomoto.co.jp/product/detail/14113'
   house='https://housefoods.jp/products/catalog/cd_1,082675,spice2,youfu,all.html'
   c.db.executemany('INSERT INTO queue(url,status,error) VALUES(?,?,?)',
    [(agf,'done','missing_or_ambiguous_ingredients'),(house,'done','missing_or_ambiguous_ingredients')])
   c.db.execute("UPDATE metadata SET value='official-fields-2026-11-01-v7' WHERE key='extractor_version'")
   c.db.commit();c.db.close()
   c=Collector(folder,100000)
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(agf,)).fetchone()[0],'pending')
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(house,)).fetchone()[0],'done')
   c.db.close()

 def test_suntory_and_morinaga_official_product_discovery(self):
  from crawl_japanese_ingredients import allowed_link
  suntory='https://products.suntory.co.jp/d/4901777452909/'
  morinaga='https://www.morinaga.co.jp/products/detail.php?id=PRD2026-09-0007'
  self.assertTrue(product_url(suntory))
  self.assertTrue(product_url(morinaga))
  self.assertTrue(allowed_link(suntory))
  self.assertTrue(allowed_link(morinaga))
  self.assertTrue(allowed_link('https://www.morinaga.co.jp/products/new.php'))
  self.assertFalse(product_url('https://products.suntory.co.jp.evil.example/d/4901777452909/'))
  self.assertFalse(product_url('https://www.morinaga.co.jp.evil.example/products/detail.php?id=PRD2026-09-0007'))
  self.assertFalse(product_url('https://products.suntory.co.jp/d/not-a-jan/'))
  self.assertFalse(product_url('https://www.morinaga.co.jp/products/'))
  suntory_html='''<title>クラフトボス | サントリー</title><h2>クラフトボス 世界のＴＥＡ アップルティー 500mlペット</h2>
  <dl><dt>JANコード</dt><dd>4901777452909</dd>
  <dt>原材料</dt><dd>紅茶、果汁（りんご）／香料</dd></dl>'''
  record,error=extract(suntory_html,suntory)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'クラフトボス 世界のＴＥＡ アップルティー 500mlペット')
  self.assertEqual(record['jan'],'4901777452909')
  self.assertEqual(record['ingredients_ja'],'紅茶、果汁（りんご）／香料')
  self.assertFalse(record['halal_certified'])
  morinaga_html='''<h1>チョコレート 半熟ダースミルクショコラ</h1>
  <h2>原材料</h2><p>砂糖、小麦粉、洋酒／乳化剤</p>
  <h2>JANコード</h2><p>4902888277306</p>'''
  record,error=extract(morinaga_html,morinaga)
  self.assertIsNone(error)
  self.assertEqual(record['jan'],'4902888277306')
  self.assertEqual(record['rule_result'],'HARAM')
  self.assertFalse(record['halal_certified'])


 def test_pasconet_official_product_page_with_full_ingredients_without_jan(self):
  from crawl_japanese_ingredients import allowed_link
  url='https://www.pasconet.co.jp/products/5259/index.html'
  catalogue='https://www.pasconet.co.jp/products/nutrition/index.html'
  self.assertTrue(product_url(url))
  self.assertTrue(allowed_link(url))
  self.assertTrue(allowed_link(catalogue))
  self.assertFalse(product_url(catalogue))
  self.assertFalse(product_url('https://www.pasconet.co.jp.evil.example/products/5259/index.html'))
  ingredients='小麦粉（小麦（国産））、チーズクリーム、ハム、マーガリン、こしょう入りマヨネーズタイプソース、パン酵母、加工油脂、砂糖、ショートニング、食塩、でんぷん加工品（でんぷん）、乳等を主要原料とする食品、モルトエキス、卵／加工デンプン、増粘剤（加工デンプン、増粘多糖類）、調味料（有機酸等）、ｐＨ調整剤、乳化剤、酢酸Ｎａ、リン酸塩（Ｎａ）、イーストフード、香料、酸化防止剤（ビタミンＣ、ビタミンＥ）、カゼインＮａ、着色料（クチナシ赤色素、カロチノイド）、発色剤（亜硝酸Ｎａ）、ビタミンＣ、香辛料、（一部に卵・小麦・乳成分・大豆・鶏肉・豚肉を含む）'
  html=f'''<h1 class="title">塩パン ハムチーズペッパー</h1>
  <section><h3 class="headStyle02 color1 small">原材料</h3><p>{ingredients}</p>
  <h3 class="headStyle02 color1 small">成分表</h3></section>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'塩パン ハムチーズペッパー')
  self.assertEqual(record['ingredients_ja'],ingredients)
  self.assertIsNone(record['jan'])
  self.assertEqual(record['source_publisher'],'pasconet.co.jp')
  self.assertEqual(record['ingredient_field_status'],'complete_displayed_field')
  self.assertEqual(record['rule_result'],'HARAM')
  self.assertFalse(record['halal_certified'])

 def test_pasconet_catalogue_refreshes_and_prioritizes_new_product_pages(self):
  catalogue='https://www.pasconet.co.jp/products/nutrition/index.html'
  product='https://www.pasconet.co.jp/products/5259/index.html'
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   c.db.execute('INSERT INTO queue(url,status,error) VALUES(?,?,?)',(catalogue,'done',None))
   c.db.commit()
   visited=[]
   c.permitted=lambda u:True
   def request(url):
    visited.append(url)
    if url==catalogue:return f'<h1>栄養成分表</h1><a href="{product}">商品</a>'
    return HTML
   c.request=request
   c.run([catalogue],max_pages=2,minutes=1)
   self.assertEqual(visited,[catalogue,product])
   self.assertEqual(c.count(),1)
   self.assertEqual(c.db.execute('SELECT status FROM queue WHERE url=?',(catalogue,)).fetchone()[0],'done')
   c.db.close()


 def test_mizkan_official_store_products_capture_full_ingredients_without_guessing_jan(self):
  from crawl_japanese_ingredients import allowed_link,source
  urls=[
   'https://shop.mizkan.co.jp/products/vnd00329',
   'https://shop.mizkan.co.jp/products/vnd00328',
   'https://shop.mizkan.co.jp/products/kurozup04',
   'https://shop.mizkan.co.jp/products/pnz00242',
   'https://shop.mizkan.co.jp/products/fruitysup00318',
   'https://shop.mizkan.co.jp/products/pnz00241',
   'https://shop.mizkan.co.jp/products/ponzu01',
   'https://shop.mizkan.co.jp/products/nat00330']
  for url in urls:
   with self.subTest(url=url):
    self.assertEqual(source(url),'mizkan.co.jp')
    self.assertTrue(product_url(url))
    self.assertTrue(allowed_link(url))
  self.assertFalse(product_url('https://shop.mizkan.co.jp/products/'))
  url=urls[3]
  ingredients='しょうゆ（国内製造）、醸造酢、果糖ぶどう糖液糖、かんきつ混合果汁、バター風味エキス（ポークエキス、バター（北海道製造）、食塩）、でん粉、食塩、バターミルクパウダー、砂糖、野菜エキス、ポークチキン香味オイル、焙煎糖、こしょう、クリーム加工品、酵母エキス加工品／調味料（アミノ酸等）、香料、酸味料、増粘多糖類、乳化剤、（一部に小麦・乳成分・大豆・鶏肉・豚肉を含む）'
  html=f'<h1>北海道バタぽんby味ぽん</h1><h3>原材料名</h3><p>{ingredients}</p>'
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'北海道バタぽんby味ぽん')
  self.assertEqual(record['ingredients_ja'],ingredients)
  self.assertIsNone(record['jan'])
  self.assertEqual(record['rule_result'],'HARAM')
  self.assertEqual(record['ingredient_field_status'],'complete_displayed_field')
  self.assertFalse(record['halal_certified'])


 def test_matsukiyo_retailer_pages_capture_only_labelled_ingredients_and_explicit_jan(self):
  from crawl_japanese_ingredients import allowed_link,source
  fixtures=[
   ('https://www.matsukiyococokara-online.com/store/catalog/product/view/id/4904083473651',
    'matsukiyo LAB　糖質９．３ｇソイスナック　チーズ味 ２９ｇ','4904083473651',
    '大豆パフ（調製豆乳粉、でんぷん）（国内製造）、植物油脂、チーズシーズニング（チーズパウダー、グラニュー糖、食塩、たんぱく加水分解物、オニオンパウダー）／調味料（アミノ酸等）、炭酸Ｃａ、香料、微粒二酸化ケイ素、パプリカ色素、甘味料（スクラロース）、（一部に乳成分・小麦・大豆を含む）'),
   ('https://www.matsukiyococokara-online.com/store/catalog/product/view/id/4904083473668',
    'matsukiyo LAB　糖質９．８ｇソイスナック　うましお ２９ｇ','4904083473668',
    '大豆パフ（調製豆乳粉、でんぷん）（国内製造）、植物油脂、うましおシーズニング（砂糖、デキストリン、食塩、粉末醤油、粉末昆布エキス、粉末鰹エキス、粉末酵母エキス、粉末椎茸エキス）／調味料（アミノ酸等）、炭酸Ｃａ、香料、微粒二酸化ケイ素、甘味料（スクラロース）、（一部に小麦・大豆を含む）')]
  for url,name,jan,ingredients in fixtures:
   with self.subTest(url=url):
    self.assertEqual(source(url),'matsukiyococokara-online.com')
    self.assertTrue(product_url(url))
    self.assertTrue(allowed_link(url))
    html=f'''<h1><img alt="store logo"></h1>
    <div class="p-productdetail__box_tit"><h1><big>{name}</big></h1></div>
    <dl><dt><big>JANコード</big></dt><dd><big>{jan}</big></dd></dl>
    <div class="p-explanation__txt white_space"><p>〖原材料〗
    {ingredients}
    〖栄養成分表示〗１袋（２９ｇ）当たり エネルギー１４１ｋｃａｌ</p></div>'''
    record,error=extract(html,url)
    self.assertIsNone(error)
    self.assertEqual(record['name_ja'],name)
    self.assertEqual(record['jan'],jan)
    self.assertEqual(record['ingredients_ja'],ingredients)
    self.assertEqual(record['source_publisher'],'matsukiyococokara-online.com')
    self.assertFalse(record['halal_certified'])
  category='https://www.matsukiyococokara-online.com/store/catalog/category/view/categories/009/04/01'
  self.assertTrue(allowed_link(category))
  self.assertFalse(allowed_link('https://www.matsukiyococokara-online.com/store/customer/account'))
  self.assertFalse(product_url('https://www.matsukiyococokara-online.com.evil.example/store/catalog/product/view/id/4904083473651'))


 def test_glico_official_product_title_and_inline_jan_are_captured(self):
  url='https://www.glico.com/jp/product/drink/glicomilk/47200/'
  html='''<h1>グリコ牛乳</h1><h2>グリコ牛乳 1000ml</h2>
  <h3>原材料名</h3><p>生乳100％（国産）</p>
  <p>JANコード：4971666400137</p>'''
  self.assertEqual(product_url(url),True)
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'グリコ牛乳 1000ml')
  self.assertEqual(record['ingredients_ja'],'生乳100％（国産）')
  self.assertEqual(record['jan'],'4971666400137')
  self.assertEqual(record['source_publisher'],'glico.com')
  self.assertFalse(record['halal_certified'])


class UhaSourceTests(unittest.TestCase):
 def test_uha_gummy_detail_extracts_exact_product_name_and_ingredients(self):
  url='https://www.uha-mikakuto.co.jp/catalog/gummy/gu273.html'
  ingredients='砂糖（国内製造）、果糖ぶどう糖液糖、ゼラチン、米粉、濃縮果汁（マスカット、りんご）、イヌリン／酸味料、ゲル化剤（アラビアガム）、香料'
  html=f'''<h1>グミ</h1><h2>忍者めし鋼　マスカット味</h2>
  <table class="product-data-table">
   <tr><th>原材料名</th><td>{ingredients}</td></tr>
   <tr><th>内容量</th><td>45g</td></tr>
  </table>'''
  self.assertTrue(product_url(url))
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'忍者めし鋼　マスカット味')
  self.assertEqual(record['ingredients_ja'],ingredients)
  self.assertIsNone(record['jan'])
  self.assertEqual(record['source_publisher'],'uha-mikakuto.co.jp')
  self.assertEqual(record['ingredient_field_status'],'complete_displayed_field')
  self.assertFalse(record['halal_certified'])

 def test_uha_gummy_catalogue_root_refreshes_without_treating_it_as_a_product(self):
  from crawl_japanese_ingredients import allowed_link
  root='https://www.uha-mikakuto.co.jp/catalog/gummy'
  detail='https://www.uha-mikakuto.co.jp/catalog/gummy/gu273.html'
  index='https://www.uha-mikakuto.co.jp/catalog/gummy/index.html'
  self.assertTrue(allowed_link(root))
  self.assertFalse(product_url(root))
  self.assertTrue(product_url(detail))
  self.assertFalse(allowed_link(index))
  with tempfile.TemporaryDirectory() as folder:
   c=Collector(folder,100000)
   c.enqueue([root,detail])
   c.db.execute("UPDATE queue SET status='done'")
   c.db.commit()
   c.run([root,detail],max_pages=0,minutes=0)
   states=dict(c.db.execute("SELECT url,status FROM queue"))
   self.assertEqual(states[canonical(root)],'pending')
   self.assertEqual(states[canonical(detail)],'done')
   c.db.close()


if __name__=='__main__':unittest.main()

class FujiccoExtraction(unittest.TestCase):
 def test_fujicco_labelled_h2_uses_adjacent_ingredient_paragraph_only(self):
  url='https://www.fujicco.co.jp/products/detail/20252465.html'
  ingredients='生乳、乳製品、（一部に乳成分を含む）'
  html=f'''<html><h1>カスピ海ヨーグルト　リッチモ　プレーン　900g</h1>
  <section><div class="heading2"><div><h2>原材料名</h2></div></div>
  <p class="text">{ingredients}</p>
  <h3>原材料の産地情報</h3><p>国産（生乳）</p></section></html>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'カスピ海ヨーグルト　リッチモ　プレーン　900g')
  self.assertEqual(record['ingredients_ja'],ingredients)
  self.assertIsNone(record['jan'])
  self.assertFalse(record['halal_certified'])
  self.assertTrue(product_url(url))


class KamedaSeikaExtraction(unittest.TestCase):
 def test_kameda_labeled_div_and_explicit_jan_are_extracted(self):
  url='https://www.kamedaseika.co.jp/product/320'
  ingredients='うるち米（米国産、国産）、しょうゆ、砂糖、みりん、デキストリン、たん白加水分解物、食塩、粉末しょうゆ／加工でん粉、調味料（アミノ酸等）、着色料（カラメル）、乳化剤、ソルビトール、（一部に小麦・大豆・ゼラチンを含む）'
  html=f'''<html><h1>110g 技のこだ割り</h1>
  <table><tr><th>JANコード</th><td>4901313254998</td></tr></table>
  <h2>原材料名</h2><div class="c-paragraph">{ingredients}</div></html>'''
  record,error=extract(html,url)
  self.assertIsNone(error)
  self.assertEqual(record['name_ja'],'110g 技のこだ割り')
  self.assertEqual(record['jan'],'4901313254998')
  self.assertEqual(record['ingredients_ja'],ingredients)
  self.assertFalse(record['halal_certified'])
  self.assertTrue(product_url(url))
