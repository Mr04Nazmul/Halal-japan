#!/usr/bin/env python3
"""Resumable official Japanese product crawler. State belongs in run artifacts.

Only displayed Japanese ingredient declarations count. No name-only indexes,
allergen-only text, invented JANs, country-prefix guesses or certifications.
"""
import argparse,hashlib,json,re,sqlite3,time,unicodedata,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,urljoin,parse_qsl,urlencode,quote
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from japan_ingredient_policy import screen

UA='JapanHalalResearch/1.0 (+https://github.com/Mr04Nazmul/Halal-japan)'
EXTRACTOR_VERSION='official-fields-2026-10-17-v3'
SOURCES={
 'topvalu.net':r'/items/detail/\d{13}',
 'sbfoods.co.jp':r'/products/detail/\d+\.html',
 'muso.co.jp':r'/item/\d+\.html',
 'ohsawa-japan.co.jp':r'actmode=ItemDetail.*iid=\d+|iid=\d+.*actmode=ItemDetail',
 'sokensha.co.jp':r'/products/product_detail/\d+',
 '7premium.jp':r'/product/search/detail\?id=\d+',
 'calbee.co.jp':r'/products/detail/',
 'meiji.co.jp':r'/products/[^/]+/\d+\.html',
 'bourbon.co.jp':r'/product/detail/',
 'morinagamilk.co.jp':r'/products/[^/]+/[^/]+/\d+\.html',
 'kamedaseika.co.jp':r'/product/\d+',
 'nissin.com':r'/jp/product/items/\d+',
 'ebarafoods.com':r'/products/detail/',
 'hanamaruki.co.jp':r'/products/[^/]+/[^/]+',
 'fujicco.co.jp':r'/products/detail/\d+',
 'fujiya-peko.co.jp':r'/sweets/item/\d+',
 'glico.com':r'/jp/product/.*/\d+',
 'housefoods.jp':r'/products/catalog/(?:cd_|discontinued_)',
 'imuraya.co.jp':r'/goods/[^/]+/[^/]+/[^/]+',
 'kikkoman.co.jp':r'/products(?:-G)?/.*/detail/',
 'lotte.co.jp':r'/products/catalogue/.*/detail\d+',
 'myojofoods.co.jp':r'/products/items/\d+',
 'nagatanien.co.jp':r'/product/detail/\d+',
 'tablemark.co.jp':r'/products/.*/detail/',
 'yamamori.co.jp':r'/business/[^/]+',
}
LABELS={'原材料','原材料名','原材料名/添加物名','原材料(一括表示ラベル)'}
GENERIC_NAMES={'商品情報','商品紹介','製品情報','商品一覧','商品ラインナップ','基本情報'}
def normalized(s):return ''.join(unicodedata.normalize('NFKC',s).split())
def canonical(u):
 p=urlsplit(u)
 q=sorted((k,v) for k,v in parse_qsl(p.query) if k in {'id','iid','actmode','p','page'})
 path=quote(p.path,safe="/%:@!$&'()*+,;=-._~")
 return urlunsplit(('https',p.netloc.lower(),path.replace('/index.php/','/'),urlencode(q),''))

def source(u):
 host=(urlsplit(u).hostname or '').lower()
 return next((d for d in SOURCES if host==d or host.endswith('.'+d)),None)
def product_url(u):return bool((d:=source(u)) and re.search(SOURCES[d],u))
def allowed_link(u):
 if source(u) and 'sitemap' in urlsplit(u).path.lower() and urlsplit(u).path.endswith('.xml'):return True
 return bool(source(u) and (product_url(u) or re.search(r'/(?:items/(?:category|list)|item(?:/category)?|products?(?:/|$)|jp/product|goods/|sweets/|business/)',urlsplit(u).path)) and not re.search(r'\.(?:jpg|png|svg|pdf|zip|js|css)$',urlsplit(u).path,re.I))
def gtin(s):
 return s.isascii() and s.isdigit() and len(s) in (8,12,13,14) and (sum(int(n)*(3 if i%2==0 else 1) for i,n in enumerate(s[-2::-1]))+int(s[-1]))%10==0
def clean_label(s):return unicodedata.normalize('NFKC',s).strip().strip('【】〖〗:：/／ ')
def extract(html,url):
 soup=BeautifulSoup(html,'html.parser');fields={}
 for el in soup.select('script,style,nav,header,footer'):el.decompose()
 for dt in soup.find_all('dt'):
  dd=dt.find_next_sibling('dd')
  if dd:fields.setdefault(clean_label(dt.get_text(' ',strip=True)),[]).append(dd.get_text(' ',strip=True))
 for tr in soup.find_all('tr'):
  cells=tr.find_all(['th','td'],recursive=False)
  if len(cells)==2:fields.setdefault(clean_label(cells[0].get_text(' ',strip=True)),[]).append(cells[1].get_text(' ',strip=True))
 for el in soup.find_all(['h2','h3','h4','strong','b','p']):
  raw=unicodedata.normalize('NFKC',el.get_text(' ',strip=True))
  combined=re.match(r'^(原材料名/添加物名|原材料名|原材料|原材料\(一括表示ラベル\))\s*[/／:：]\s*(.+)$',raw,re.S)
  if combined:
   fields.setdefault(combined.group(1),[]).append(combined.group(2).strip())
   continue
  label=clean_label(raw)
  if label not in LABELS|{'添加物','JAN','JANコード','JANCODE','POSコード'}:continue
  nxt=el.find_next_sibling()
  while nxt is not None and not nxt.get_text(' ',strip=True):nxt=nxt.find_next_sibling()
  # Official sites often wrap the heading one or two divs deeper than its
  # displayed value.  Fall back to the next semantic value element in document
  # order, without flattening the whole page or guessing from free text.
  if nxt is None:
   nxt=el.find_next(lambda tag: tag.name in {'p','dd','td','li'} and clean_label(tag.get_text(' ',strip=True)) not in LABELS)
  if nxt is not None:fields.setdefault(label,[]).append(nxt.get_text(' ',strip=True))
 values=[v for k,vs in fields.items() if k in LABELS for v in vs]
 values={normalized(v):v for v in values if 1<len(v)<12000 and re.search(r'[ぁ-んァ-ヶ一-龯]',v)}
 if len(values)!=1:return None,'missing_or_ambiguous_ingredients'
 ingredients=next(iter(values.values()))
 if re.search(r'原材料名が入ります|原材料名欄では|アレルゲン情報|栄養成分表示|https?://|\ufffd',ingredients):return None,'non_ingredient_text'
 title=soup.find('h1')
 name=next(iter(fields.get('商品名',[])),title.get_text(' ',strip=True) if title else '')
 if clean_label(name) in GENERIC_NAMES and soup.title:
  # Some official product pages use a generic H1 such as 商品情報 while the
  # product identity is the first, unambiguous segment of the HTML title.
  name=re.split(r'[|｜]',soup.title.get_text(' ',strip=True),maxsplit=1)[0].strip()
 if 'ohsawa-japan.co.jp' in url:
  original_title=soup.title.get_text(' ',strip=True) if soup.title else ''
  parts=[x.strip() for x in original_title.split('|')]
  if len(parts)>2:name=parts[2]
 name=re.sub(r'\s*の詳細情報$','',name).strip()
 if not name or '\ufffd' in name or clean_label(name) in GENERIC_NAMES:return None,'missing_product_identity'
 if re.search(r'ペット|ドッグ|キャット|犬用|猫用|洗剤|シャンプー|化粧',name):return None,'non_human_food'
 codes=[]
 for k,vs in fields.items():
  if re.fullmatch(r'JAN(?:コード|CODE)?|POSコード',k):
   for v in vs:
    codes.extend(c for c in re.findall(r'(?<!\d)\d{8,14}(?!\d)',v) if gtin(c))
 codes=list(dict.fromkeys(codes))
 additives=' '.join(dict.fromkeys(fields.get('添加物',[])))
 brand=next(iter(fields.get('メーカー名',[])),source(url))
 jan=codes[0] if len(codes)==1 else None
 decision=screen(ingredients,additives)
 if decision['rule_result']=='UNKNOWN':return None,'incomplete_ingredient_declaration'
 key='jan:'+jan if jan else 'name:'+source(url)+'|'+normalized(name)
 result={'product_id':key,'name_ja':name,'brand':brand,'jan':jan,'ingredients_ja':ingredients,
 'additives_ja':additives,'source_url':url,'source_publisher':source(url),
 'source_type':'official_manufacturer_brand_or_distributor_page','retrieved_at':datetime.now(timezone.utc).isoformat(),
 'source_html_sha256':hashlib.sha256(html.encode()).hexdigest(),'ingredient_field_status':'complete_displayed_field',
 'reuse_permission':'not_established','live_database_updated':False,**decision}
 return result,None

class Collector:
 def __init__(self,path,target):
  self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True);self.target=target
  self.db=sqlite3.connect(self.path/'state.sqlite3')
  self.db.executescript('''CREATE TABLE IF NOT EXISTS queue(url TEXT PRIMARY KEY,status TEXT DEFAULT 'pending',attempts INTEGER DEFAULT 0,next_try REAL DEFAULT 0,error TEXT);
  CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY,formula TEXT,payload TEXT,conflict INTEGER DEFAULT 0);
  CREATE TABLE IF NOT EXISTS host_state(host TEXT PRIMARY KEY,next_try REAL DEFAULT 0,reason TEXT);
  CREATE TABLE IF NOT EXISTS observations(url TEXT,reason TEXT,at TEXT);
  CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT);''')
  previous=self.db.execute("SELECT value FROM metadata WHERE key='extractor_version'").fetchone()
  if not previous or previous[0]!=EXTRACTOR_VERSION:
   # Revisit only pages rejected by older field extraction.  Network failures,
   # robots decisions and accepted records are not reset.
   self.db.execute("UPDATE queue SET status='pending',attempts=0,next_try=0,error=NULL WHERE error IN ('missing_or_ambiguous_ingredients','missing_product_identity') OR error LIKE 'UnicodeEncodeError:%'")
   self.db.execute("INSERT OR REPLACE INTO metadata VALUES('extractor_version',?)",(EXTRACTOR_VERSION,))
   self.db.commit()
  self.robots={};self.last={}
 def enqueue(self,urls):
  self.db.executemany('INSERT OR IGNORE INTO queue(url) VALUES(?)',[(canonical(u),) for u in urls if allowed_link(u)])
  self.db.commit()
 def request(self,url):
  url=canonical(url)
  host=urlsplit(url).netloc;delay=2-(time.time()-self.last.get(host,0))
  if delay>0:time.sleep(delay)
  self.last[host]=time.time()
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xml;q=0.9'}),timeout=25) as r:
   if urlsplit(r.url).hostname!=urlsplit(url).hostname and not source(r.url):raise ValueError('off_source_redirect')
   data=r.read(3_000_001)
   if len(data)>3_000_000:raise ValueError('page_too_large')
   return data.decode(r.headers.get_content_charset() or 'utf-8',errors='replace')
 def permitted(self,url):
  url=canonical(url)
  host=urlsplit(url).netloc
  if host not in self.robots:
   rp=RobotFileParser()
   try:
    raw=self.request('https://'+host+'/robots.txt')
    if '<html' in raw.lower() or not re.search(r'^\s*(?:user-agent|sitemap)\s*:',raw,re.I|re.M):raise ValueError('invalid_robots_policy')
    rp.parse(raw.splitlines())
    for sm in re.findall(r'^Sitemap:\s*(https?://\S+)',raw,re.I|re.M):
     if source(sm)==source(url):self.db.execute('INSERT OR IGNORE INTO queue(url) VALUES(?)',(sm,))
   except urllib.error.HTTPError as e:
    if e.code==404:rp.parse(['User-agent: *','Allow: /'])
    else:raise
   self.robots[host]=rp
  return self.robots[host].can_fetch(UA,url)
 def count(self):return self.db.execute('SELECT count(*) FROM products WHERE conflict=0').fetchone()[0]
 def checkpoint(self):
  rows=[json.loads(x[0]) for x in self.db.execute('SELECT payload FROM products WHERE conflict=0 ORDER BY id')]
  summary={'target':self.target,'accepted_ingredient_products':len(rows),'target_reached':len(rows)>=self.target,
    'with_explicit_jan':sum(bool(x['jan']) for x in rows),'rule_results':{k:sum(x['rule_result']==k for x in rows) for k in ['HALAL','HARAM','UNKNOWN']},
    'queue':dict(self.db.execute('SELECT status,count(*) FROM queue GROUP BY status')),
    'formula_conflicts_withheld':self.db.execute('SELECT count(*) FROM products WHERE conflict=1').fetchone()[0],
    'checkpoint_at':datetime.now(timezone.utc).isoformat(),'halal_certification_performed':False,
    'extractor_version':EXTRACTOR_VERSION,
    'count_scope':'Distinct identities with full displayed Japanese ingredients from official Japanese product pages; not global/name-only indexes',
    'prior_chat_checkpoint_not_automatically_added':721}
  for name,value in [('products.json',rows),('summary.json',summary)]:
   tmp=self.path/(name+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n');tmp.replace(self.path/name)
  self.db.commit();print(json.dumps(summary,ensure_ascii=False),flush=True)
 def run(self,seeds,max_pages,minutes):
  self.enqueue(seeds);end=time.monotonic()+minutes*60;done=0
  try:
   while done<max_pages and time.monotonic()<end and self.count()<self.target:
    now=time.time()
    item=self.db.execute("SELECT url,attempts FROM queue q WHERE status='pending' AND next_try<=? AND NOT EXISTS(SELECT 1 FROM host_state h WHERE h.next_try>? AND q.url LIKE 'https://' || h.host || '/%') ORDER BY CASE WHEN url LIKE '%/detail/%' OR url LIKE '%/item/%html%' THEN 0 ELSE 1 END,rowid LIMIT 1",(now,now)).fetchone()
    if not item:break
    url,attempts=item;reason=None
    try:
     if not self.permitted(url):reason='robots_disallowed'
     else:
      html=self.request(url)
      if urlsplit(url).path.endswith('.xml'):
       links=re.findall(r'<loc>\s*([^<]+)',html)
       self.enqueue([u.replace('&amp;','&') for u in links if allowed_link(u)])
      else:
       soup=BeautifulSoup(html,'html.parser')
       self.enqueue([urljoin(url,a['href']) for a in soup.select('a[href]')])
       if product_url(url):
        record,reason=extract(html,url)
        if record:
         formula=normalized(record['ingredients_ja']+'|'+record['additives_ja'])
         old=self.db.execute('SELECT formula FROM products WHERE id=?',(record['product_id'],)).fetchone()
         if old and old[0]!=formula:self.db.execute('UPDATE products SET conflict=1 WHERE id=?',(record['product_id'],));reason='formula_conflict'
         elif not old:self.db.execute('INSERT INTO products(id,formula,payload) VALUES(?,?,?)',(record['product_id'],formula,json.dumps(record,ensure_ascii=False)))
     self.db.execute("UPDATE queue SET status='done',attempts=attempts+1,error=? WHERE url=?",(reason,url))
    except Exception as e:
     code=getattr(e,'code',None);reason=type(e).__name__+':'+str(code or str(e)[:120])
     cooldown=86400 if code in (401,403) else 3600 if code==429 else 900
     self.db.execute('INSERT OR REPLACE INTO host_state VALUES(?,?,?)',(urlsplit(url).netloc,time.time()+cooldown,reason))
     self.db.execute("UPDATE queue SET status=?,attempts=attempts+1,next_try=?,error=? WHERE url=?",('done' if code==404 or attempts>=4 else 'pending',time.time()+cooldown,reason,url))
    self.db.execute('INSERT INTO observations VALUES(?,?,?)',(url,reason,datetime.now(timezone.utc).isoformat()));self.db.commit()
    done+=1
    if done%25==0:self.checkpoint()
  finally:self.checkpoint()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--state',default='crawler-state');p.add_argument('--seeds',default='scripts/japan_ingredient_sources.json');p.add_argument('--target',type=int,default=100000);p.add_argument('--max-pages',type=int,default=1500);p.add_argument('--minutes',type=float,default=35);p.add_argument('--checkpoint-only',action='store_true')
 a=p.parse_args();c=Collector(a.state,a.target)
 if a.checkpoint_only:c.checkpoint()
 else:c.run(json.loads(Path(a.seeds).read_text()),a.max_pages,a.minutes)
