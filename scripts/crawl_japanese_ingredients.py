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
from japan_ingredient_food_filter import is_nonfood_name,is_nonfood_ingredient_text,has_unresolved_html_artifacts

UA='JapanHalalResearch/1.0 (+https://github.com/Mr04Nazmul/Halal-japan)'
EXTRACTOR_VERSION='official-fields-2026-11-01-v9-asahi-maintenance'
SOURCES={
 'suntory.co.jp':r'/d/\d{13}/?$',
 'morinaga.co.jp':r'/products/detail\.php\?id=PRD\d{4}-\d{2}-\d{4}$',
 'topvalu.net':r'/items/detail/\d{13}',
 'kewpie.co.jp':r'/products/detail/\d{13}/?$',
 'pokkasapporo-fb.jp':r'/products/(?:[^/]+/){2}[A-Za-z0-9]+\.html$',
 'asahiinryo.co.jp':r'/products/(?:[^/]+/){2}(?:[A-Za-z0-9_-]+\.html)?$',
 'itoen.jp':r'/products/\d+/?$',
 'ucc.co.jp':r'/product/(?:regular|instant|drink|coffee|gift|drip-pod)/[^?#]+\.html$',
 'sbfoods.co.jp':r'/products/detail/\d+\.html',
 'kyoritsu-foods.co.jp':r'(?:/product/\d+/|/item-detail/\d+)$',
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
 'kagome.co.jp':r'/foodservice/(?:dry|frozen|chilled)/\d+/?\Z',
 'agf.ajinomoto.co.jp':r'/product/detail/\d+/?$',
 'dydo.co.jp':r'/products/detail/\d+/?$',
 'natori.co.jp':r'/products_search/[^/]+/item_\d+/?$',
}
class TemporarySourceMaintenance(RuntimeError):
 """Official product site is temporarily unavailable; retry after a host cooldown."""
 pass

def is_temporary_maintenance(html,url):
 # Asahi's current security-maintenance page is not a product page.
 # Require distinctive site-specific text to avoid rejecting normal products.
 if source(url)!='asahiinryo.co.jp':return False
 plain=''.join(BeautifulSoup(html,'html.parser').stripped_strings)
 return ('ただいまメンテナンス中です' in plain
         or ('一時停止しています' in plain and '安全性が確認' in plain))

LABELS={'原材料','原材料名','原材料名/添加物名','原材料(一括表示ラベル)'}
GENERIC_NAMES={'商品情報','商品紹介','製品情報','商品一覧','商品ラインナップ','基本情報'}
def normalized(s):return ''.join(unicodedata.normalize('NFKC',s).split())
def canonical(u):
 p=urlsplit(u)
 # Keep TOPVALU's actual catalogue pagination parameters: dropping sort and
 # direction can turn valid page=2 links into inaccessible pages, starving
 # official product discovery. Other hosts retain the strict query allowlist.
 allowed={'id','iid','actmode','p','page'}
 if (p.hostname or '').lower() in {'topvalu.net','www.topvalu.net'} and re.fullmatch(r'/items/(?:list|category)/\d+/?',p.path):
  allowed.update({'direction','sort'})
 # DyDo's official catalogue uses four named pagination parameters.
 # Preserve only those parameters on its exact catalogue path.
 if (p.hostname or '').lower() in {'dydo.co.jp','www.dydo.co.jp'} and p.path.rstrip('/')=='/products/list':
  allowed.update({'rt_bn_product_category_list_s_skip','rt_bn_product_list_1-2_skip',
                  'rt_bn_product_list_all_skip','rt_bn_product_list_skip'})
 if (p.hostname or '').lower() in {'natori.co.jp','www.natori.co.jp'} and p.path=='/products_search/search':
  # Natori's official category pages require these filters for pagination.
  allowed.update({'formid','ible-categoryselectbox1','ible-categoryselectbox2',
                  'ible-checkboxsolo1','ible-keyword1'})
 keep_blank=(p.hostname or '').lower() in {'dydo.co.jp','www.dydo.co.jp'} and p.path.rstrip('/')=='/products/list'
 q=sorted((k,v) for k,v in parse_qsl(p.query,keep_blank_values=keep_blank) if k in allowed)
 path=quote(p.path,safe="/%:@!$&'()*+,;=-._~")
 return urlunsplit(('https',p.netloc.lower(),path.replace('/index.php/','/'),urlencode(q),''))

def source(u):
 host=(urlsplit(u).hostname or '').lower()
 return next((d for d in SOURCES if host==d or host.endswith('.'+d)),None)
def product_url(u):return bool((d:=source(u)) and re.search(SOURCES[d],u))
def sitemap_url(u):
 path=urlsplit(u).path.lower()
 return bool(source(u) and 'sitemap' in path and path.endswith('.xml'))
def allowed_link(u):
 if sitemap_url(u):return True
 # These are marketing/recipe link graphs, not official product detail URLs.
 # Relative links on House Foods special pages can recursively create
 # hundreds of thousands of synthetic paths. Never enqueue them.
 host=source(u);path=urlsplit(u).path
 if host=='housefoods.jp' and path.startswith('/products/special/'):return False
 if host=='kagome.co.jp' and path.startswith('/products/brand/'):return False
 return bool(source(u) and (product_url(u) or re.search(r'/(?:items/(?:category|list)|items/?$|item(?:/category)?|products?(?:/|$)|products\.html$|products_search/|jp/product|goods/|sweets/|business/|foodservice/)',urlsplit(u).path)) and not re.search(r'\.(?:jpg|png|svg|pdf|zip|js|css)$',urlsplit(u).path,re.I))
def gtin(s):
 return s.isascii() and s.isdigit() and len(s) in (8,12,13,14) and (sum(int(n)*(3 if i%2==0 else 1) for i,n in enumerate(s[-2::-1]))+int(s[-1]))%10==0
def clean_label(s):return unicodedata.normalize('NFKC',s).strip().strip('【】〖〗:：/／ ')
def extract(html,url):
 soup=BeautifulSoup(html,'html.parser');fields={}
 for el in soup.select('script,style,nav,header,footer'):el.decompose()
 for dt in soup.find_all('dt'):
  dd=dt.find_next_sibling('dd')
  if dd:fields.setdefault(clean_label(dt.get_text(' ',strip=True)),[]).append(dd.get_text(' ',strip=True))
 # AGF's actual official product detail HTML uses div-based labelled rows,
 # not dt/dd or th/td. Read only adjacent labelled values from this
 # manufacturer-specific structure, never unlabelled page text.
 if source(url)=='agf.ajinomoto.co.jp':
  for row in soup.select('div.agf-cs-product-table-row'):
   heading=row.select_one('.agf-cs-product-table-heading')
   value=row.select_one('.agf-cs-product-table-data')
   if heading and value:
    label=clean_label(heading.get_text(' ',strip=True))
    if label in LABELS|{'添加物','JAN','JANコード','JANCODE','POSコード'}:
     fields.setdefault(label,[]).append(value.get_text(' ',strip=True))
 for tr in soup.find_all('tr'):
  cells=tr.find_all(['th','td'],recursive=False)
  if len(cells)==2:fields.setdefault(clean_label(cells[0].get_text(' ',strip=True)),[]).append(cells[1].get_text(' ',strip=True))
 for el in soup.find_all(['h2','h3','h4','strong','b','p']):
  raw=unicodedata.normalize('NFKC',el.get_text(' ',strip=True))
  combined=re.match(r'^[●•\s]*(原材料名/添加物名|原材料名|原材料|原材料\(一括表示ラベル\))\s*(?:[/／:：]|…|\.\.\.)\s*(.+)$',raw,re.S)
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
 # A labelled full declaration (原材料名) takes precedence over generic
 # 原材料 rows in provenance/origin tables.  Combining those unrelated fields
 # wrongly made valid Nissin product pages appear ambiguous.  Still reject
 # conflicting values within the same declaration tier; never guess a recipe.
 declared_labels=('原材料名','原材料名/添加物名','原材料(一括表示ラベル)')
 declared=[v for k in declared_labels for v in fields.get(k,[])]
 values=declared if declared else fields.get('原材料',[])
 values={normalized(v):v for v in values if 1<len(v)<12000 and re.search(r'[ぁ-んァ-ヶ一-龯]',v)}
 if len(values)!=1:return None,'missing_or_ambiguous_ingredients'
 ingredients=next(iter(values.values()))
 if is_nonfood_ingredient_text(ingredients):return None,'non_ingredient_text'
 if has_unresolved_html_artifacts(ingredients):return None,'unresolved_html_in_ingredient_field'
 if re.match(r'^\s*(?:添加物|添加物名)\s*[:：]',ingredients):return None,'additives_only_incomplete_ingredients'
 if re.search(r'原材料名が入ります|原材料名欄では|アレルゲン情報|栄養成分表示|https?://|\ufffd',ingredients):return None,'non_ingredient_text'
 # Some official product pages render an empty decorative H1 before the
 # actual product title. Ignore blank headings rather than rejecting valid food.
 title=next((h for h in soup.find_all('h1') if h.get_text(' ',strip=True)),None)
 name=next(iter(fields.get('商品名',[])),title.get_text(' ',strip=True) if title else '')
 if not name and soup.title:
  name=re.split(r'[|｜]',soup.title.get_text(' ',strip=True),maxsplit=1)[0].strip()
 if clean_label(name) in GENERIC_NAMES and soup.title:
  # Some official product pages use a generic H1 such as 商品情報 while the
  # product identity is the first, unambiguous segment of the HTML title.
  name=re.split(r'[|｜]',soup.title.get_text(' ',strip=True),maxsplit=1)[0].strip()
 if 'ohsawa-japan.co.jp' in url:
  original_title=soup.title.get_text(' ',strip=True) if soup.title else ''
  parts=[x.strip() for x in original_title.split('|')]
  if len(parts)>2:name=parts[2]
 if source(url)=='suntory.co.jp':
  # Use the first product heading, not the generic site title.
  product_heading=next((h.get_text(' ',strip=True) for h in soup.find_all(['h1','h2']) if h.get_text(' ',strip=True) and '商品情報' not in h.get_text(' ',strip=True) and '原材料' not in h.get_text(' ',strip=True)),None)
  if product_heading:name=product_heading
 if source(url)=='agf.ajinomoto.co.jp':
  # AGF H1 is a short brand title; the first product H2 has the full name.
  product_heading=next((h.get_text(' ',strip=True) for h in soup.find_all('h2') if '商品詳細' not in h.get_text(' ',strip=True) and re.search(r'\d',h.get_text(' ',strip=True))),None)
  if product_heading:name=product_heading
 name=re.sub(r'\s*の詳細情報$','',name).strip()
 if not name or '\ufffd' in name or clean_label(name) in GENERIC_NAMES:return None,'missing_product_identity'
 if is_nonfood_name(name):return None,'non_human_food'
 codes=[]
 for k,vs in fields.items():
  if re.fullmatch(r'JAN(?:コード|CODE)?|POSコード',k) or (source(url)=='kyoritsu-foods.co.jp' and k=='コード'):
   for v in vs:
    codes.extend(c for match in re.findall(r'(?<!\d)(?:\d-?){7,13}\d(?!\d)',v) if (c:=re.sub(r'\D','',match)) and gtin(c))
 # The official Kyoritsu shop displays JAN next to a free-standing label.
 # Use only an adjacent, checksum-valid JAN-13; never infer it from a URL.
 if urlsplit(url).hostname=='shop.kyoritsu-foods.co.jp' and not codes:
  for raw_code in re.findall(r'JANコード\s*([0-9]{13})(?![0-9])',soup.get_text(' ',strip=True)):
   if gtin(raw_code):codes.append(raw_code)
 codes=list(dict.fromkeys(codes))
 additives=' '.join(dict.fromkeys(fields.get('添加物',[])))
 brand=next(iter(fields.get('メーカー名',[])),source(url))
 jan=codes[0] if len(codes)==1 else None
 decision=screen(ingredients,additives,product_name=name)
 # A complete displayed ingredient field is valid research data even when
 # halal suitability cannot be established from its contents. Keep UNKNOWN
 # pending review rather than treating it as an incomplete declaration.
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
   # Keep the earlier AGF repair's requeue one-time only. This upgrade
   # targets Asahi maintenance, not unrelated manufacturer field failures.
   if not previous or 'v8-agf-div' not in previous[0] and 'v9-asahi-maintenance' not in previous[0]:
    self.db.execute("""UPDATE queue SET status='pending',attempts=0,next_try=0,error=NULL
     WHERE (url LIKE 'https://agf.ajinomoto.co.jp/product/detail/%'
      AND error IN ('missing_or_ambiguous_ingredients','missing_product_identity','incomplete_ingredient_declaration'))
      OR error LIKE 'UnicodeEncodeError:%'""")
   # Earlier Asahi maintenance responses were mistaken for permanently
   # missing ingredients. Retry those product pages once, then back off
   # the whole host while maintenance remains active.
   self.db.execute("""UPDATE queue SET status='pending',attempts=0,next_try=0,error=NULL
    WHERE (url LIKE 'https://%.asahiinryo.co.jp/products/%'
       OR url LIKE 'https://asahiinryo.co.jp/products/%')
      AND error IN ('missing_or_ambiguous_ingredients','temporary_source_maintenance')""")
   # Revisit invalid legacy accepted records without altering prior artifacts.
   invalid=[]
   for ident,payload in self.db.execute('SELECT id,payload FROM products'):
    try:record=json.loads(payload)
    except (TypeError,ValueError):continue
    if is_nonfood_ingredient_text(record.get('ingredients_ja')):
     invalid.append((ident,record.get('source_url')))
   for ident,url in invalid:
    self.db.execute('DELETE FROM products WHERE id=?',(ident,))
    if url:
     self.db.execute("UPDATE queue SET status='pending',attempts=0,next_try=0,error=NULL WHERE url=?",(url,))
   if invalid:print(f"Quarantined {len(invalid)} invalid legacy checkpoint records",flush=True)
   self.db.execute("INSERT OR REPLACE INTO metadata VALUES('extractor_version',?)",(EXTRACTOR_VERSION,))
   self.db.commit()
  # A 404 only means this URL is missing; it must not throttle every other
  # product page on the same official host. Clear legacy 404 host cooldowns.
  self.db.execute("DELETE FROM host_state WHERE reason='HTTPError:404'")
  self.db.commit()
  self.robots={};self.last={}
 def enqueue(self,urls):
  links=[canonical(u) for u in urls if allowed_link(u)]
  self.db.executemany('INSERT OR IGNORE INTO queue(url) VALUES(?)',[(u,) for u in links])
  # Newly discovered official product pages should be eligible immediately,
  # without waiting behind thousands of already queued navigation pages.
  if getattr(self,'product_priority_ready',False):
   self.db.executemany('INSERT OR IGNORE INTO product_priority(url) VALUES(?)',
    [(u,) for u in links if product_url(u)])
   self.db.executemany('INSERT OR IGNORE INTO sitemap_priority(url) VALUES(?)',
    [(u,) for u in links if sitemap_url(u)])
  self.db.commit()
 def request(self,url):
  url=canonical(url)
  host=urlsplit(url).netloc;delay=2-(time.time()-self.last.get(host,0))
  if delay>0:time.sleep(delay)
  self.last[host]=time.time()
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xml;q=0.9'}),timeout=25) as r:
   if urlsplit(r.url).hostname!=urlsplit(url).hostname and not source(r.url):
    final=urlsplit(r.url)
    if (source(url)=='asahiinryo.co.jp'
        and final.hostname=='p22sorrysite.z11.web.core.windows.net'
        and final.path.startswith('/maintenance_')):
     raise TemporarySourceMaintenance('asahi_security_maintenance_redirect')
    raise ValueError('off_source_redirect')
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
     if source(sm)==source(url):self.enqueue([sm])
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
  if hasattr(self,'run_started_at'):
   counts=self.db.execute("SELECT reason,count(*) FROM observations WHERE at>=? AND reason IS NOT NULL AND reason NOT IN ('discovery_navigation_page','discovery_sitemap','already_known_product','accepted_new_product') GROUP BY reason ORDER BY count(*) DESC LIMIT 12",(self.run_started_at,)).fetchall()
   outcomes=self.db.execute("SELECT COALESCE(reason,'unclassified'),count(*) FROM observations WHERE at>=? GROUP BY COALESCE(reason,'unclassified') ORDER BY count(*) DESC LIMIT 12",(self.run_started_at,)).fetchall()
   host_outcomes={}
   for observed_url,observed_reason in self.db.execute('SELECT url,reason FROM observations WHERE at>=?',(self.run_started_at,)):
    key=(urlsplit(observed_url).hostname or 'unknown')+' | '+(observed_reason or 'unclassified')
    host_outcomes[key]=host_outcomes.get(key,0)+1
   summary['current_run']={
    'top_host_outcomes':dict(sorted(host_outcomes.items(),key=lambda item:-item[1])[:15]),
    'started_at':self.run_started_at,
    'pages_processed':self.db.execute('SELECT count(*) FROM observations WHERE at>=?',(self.run_started_at,)).fetchone()[0],
    'new_accepted':len(rows)-self.run_start_count,
    'initial_pending_product_pages':getattr(self,'initial_pending_product_pages',None),
    'top_rejection_reasons':dict(counts),
    'page_outcomes':dict(outcomes),
    'stop_reason':getattr(self,'run_stop_reason','in_progress'),
    'active_host_cooldowns':[
     {'host':host,'reason':reason,
      'retry_at':datetime.fromtimestamp(next_try,timezone.utc).isoformat()}
     for host,next_try,reason in self.db.execute(
      'SELECT host,next_try,reason FROM host_state WHERE next_try>? ORDER BY next_try LIMIT 15',
      (time.time(),))]}
  elif (self.path/'summary.json').exists():
   # The workflow's --checkpoint-only finalizer runs in a fresh process.
   # Preserve metrics from the bounded crawl instead of erasing them.
   try:
    previous=json.loads((self.path/'summary.json').read_text())
    if previous.get('accepted_ingredient_products')==len(rows) and 'current_run' in previous:
     summary['current_run']=previous['current_run']
   except (OSError,ValueError,TypeError):pass
  for name,value in [('products.json',rows),('summary.json',summary)]:
   tmp=self.path/(name+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n');tmp.replace(self.path/name)
  self.db.commit();print(json.dumps(summary,ensure_ascii=False),flush=True)
 def run(self,seeds,max_pages,minutes):
  # Refresh official catalogue entry points once per persistent checkpoint.
  # Product links discovered there enter the priority queue, ahead of the
  # large legacy navigation backlog. Respect robots.txt and host pacing.
  seeds=list(dict.fromkeys(seeds))
  self.run_started_at=datetime.now(timezone.utc).isoformat()
  self.run_start_count=self.count()
  self.enqueue(seeds)
  # Revisit a bounded number of previously successful catalogue entry points
  # on each run. Without this, the persistent queue marks every seed as done
  # forever, so new products are never discovered from updated catalogues.
  # Never retry rejected/robots-blocked pages or completed product records.
  refreshed_by_host={}
  for raw in seeds:
   url=canonical(raw)
   if product_url(url) or sitemap_url(url):continue
   parsed=urlsplit(url)
   if parsed.query and source(url)!='natori.co.jp':continue
   if not re.fullmatch(r'/(?:items/?|items/list/\d+/?|products/?|products/list/?|products/new\.php|products\.html|products_search/search|product/?)',parsed.path):continue
   host=parsed.netloc
   limit=8 if source(url) in {'topvalu.net','natori.co.jp'} else 1
   if refreshed_by_host.get(host,0)>=limit:continue
   updated=self.db.execute("UPDATE queue SET status='pending',attempts=0,next_try=0 WHERE url=? AND status='done' AND error IS NULL",(url,))
   if updated.rowcount:refreshed_by_host[host]=refreshed_by_host.get(host,0)+1
  self.db.commit()
  # Seeded official product URLs must not starve behind an ever-growing discovery queue.
  # This TEMP table is recreated on each run; it does not alter persistent checkpoints.
  self.db.execute("CREATE TEMP TABLE IF NOT EXISTS seed_priority(url TEXT PRIMARY KEY)")
  self.db.executemany("INSERT OR IGNORE INTO seed_priority(url) VALUES(?)",[(canonical(u),) for u in seeds if allowed_link(u)])
  # Newly supplied product seeds outrank older pending product URLs, but
  # navigation seeds must not starve any queued product URLs.
  self.db.execute("CREATE TEMP TABLE IF NOT EXISTS seed_product_priority(url TEXT PRIMARY KEY)")
  self.db.executemany("INSERT OR IGNORE INTO seed_product_priority(url) VALUES(?)",
   [(canonical(u),) for u in seeds if product_url(u)])
  # Prioritize all supported official product URL patterns, not just /detail/
  # and /item/. TEMP state keeps the persisted checkpoint schema unchanged.
  self.db.execute("CREATE TEMP TABLE IF NOT EXISTS product_priority(url TEXT PRIMARY KEY)")
  pending_products=[(u,) for (u,) in self.db.execute("SELECT url FROM queue WHERE status='pending'") if product_url(u)]
  self.initial_pending_product_pages=len(pending_products)
  self.db.executemany("INSERT OR IGNORE INTO product_priority(url) VALUES(?)",pending_products)
  # Robots-advertised sitemaps can reveal thousands of direct product URLs.
  # Process them before the long navigation backlog, without trusting off-site XML.
  self.db.execute("CREATE TEMP TABLE IF NOT EXISTS sitemap_priority(url TEXT PRIMARY KEY)")
  pending_sitemaps=[(u,) for (u,) in self.db.execute("SELECT url FROM queue WHERE status='pending'") if sitemap_url(u)]
  self.db.executemany("INSERT OR IGNORE INTO sitemap_priority(url) VALUES(?)",pending_sitemaps)
  self.product_priority_ready=True
  end=time.monotonic()+minutes*60;done=0
  self.run_stop_reason='in_progress'
  try:
   while done<max_pages and time.monotonic()<end and self.count()<self.target:
    now=time.time()
    # Process new product seeds, all queued product pages, then sitemaps
    # before seeded catalogue navigation. Previously seed navigation could
    # consume the entire 35-minute budget despite queued product URLs.
    # Keep the rotating navigation fallback for older catalogue pages.
    # The indexed TEMP tables avoid calling Python regexes for every queued
    # URL on every iteration, which matters for 100k+ pending URLs.
    item=None
    for priority in ('seed_product_priority','product_priority','sitemap_priority','seed_priority'):
     item=self.db.execute(f"SELECT q.url,q.attempts FROM {priority} p JOIN queue q ON q.url=p.url WHERE q.status='pending' AND q.next_try<=? AND NOT EXISTS(SELECT 1 FROM host_state h WHERE h.next_try>? AND q.url LIKE 'https://' || h.host || '/%') ORDER BY q.rowid LIMIT 1",(now,now)).fetchone()
     if item:break
    if not item:
     # Ignore legacy marketing-link explosions without deleting checkpoint
     # rows. Official product detail and catalogue pages remain eligible.
     # A previous run queued >305k recursive /products/special/ URLs.
     # A large backlog of navigation links from one manufacturer can starve
     # discovery on other official hosts. Rotate hosts only in this fallback:
     # seeded products, pending products and sitemaps still take precedence.
     previous_host=getattr(self,'last_navigation_host',None)
     if previous_host:
      item=self.db.execute("SELECT q.url,q.attempts FROM queue q WHERE q.status='pending' AND q.next_try<=? AND NOT EXISTS(SELECT 1 FROM host_state h WHERE h.next_try>? AND q.url LIKE 'https://' || h.host || '/%') AND q.url NOT LIKE ? AND q.url NOT LIKE 'https://housefoods.jp/products/special/%' AND q.url NOT LIKE 'https://www.kagome.co.jp/products/brand/%' ORDER BY q.rowid LIMIT 1",(now,now,'https://'+previous_host+'/%')).fetchone()
     if not item:
      item=self.db.execute("SELECT q.url,q.attempts FROM queue q WHERE q.status='pending' AND q.next_try<=? AND NOT EXISTS(SELECT 1 FROM host_state h WHERE h.next_try>? AND q.url LIKE 'https://' || h.host || '/%') AND q.url NOT LIKE 'https://housefoods.jp/products/special/%' AND q.url NOT LIKE 'https://www.kagome.co.jp/products/brand/%' ORDER BY q.rowid LIMIT 1",(now,now)).fetchone()
    if not item:
     self.run_stop_reason='no_eligible_pending_urls'
     break
    url,attempts=item;reason=None
    if not product_url(url) and not sitemap_url(url):
     self.last_navigation_host=urlsplit(url).netloc
    try:
     if not self.permitted(url):reason='robots_disallowed'
     else:
      html=self.request(url)
      if is_temporary_maintenance(html,url):
       raise TemporarySourceMaintenance('asahi_security_maintenance_page')
      if urlsplit(url).path.endswith('.xml'):
       links=re.findall(r'<loc>\s*([^<]+)',html)
       self.enqueue([u.replace('&amp;','&') for u in links if allowed_link(u)])
       reason='discovery_sitemap'
      else:
       soup=BeautifulSoup(html,'html.parser')
       self.enqueue([urljoin(url,a['href']) for a in soup.select('a[href]')])
       if product_url(url):
        record,reason=extract(html,url)
        if record:
         formula=normalized(record['ingredients_ja']+'|'+record['additives_ja'])
         old=self.db.execute('SELECT formula FROM products WHERE id=?',(record['product_id'],)).fetchone()
         if old and old[0]!=formula:self.db.execute('UPDATE products SET conflict=1 WHERE id=?',(record['product_id'],));reason='formula_conflict'
         elif not old:
          self.db.execute('INSERT INTO products(id,formula,payload) VALUES(?,?,?)',(record['product_id'],formula,json.dumps(record,ensure_ascii=False)))
          reason='accepted_new_product'
         else:reason='already_known_product'
       else:reason='discovery_navigation_page'
     queue_error=None if reason in {'discovery_navigation_page','discovery_sitemap','already_known_product','accepted_new_product'} else reason
     self.db.execute("UPDATE queue SET status='done',attempts=attempts+1,error=? WHERE url=?",(queue_error,url))
    except TemporarySourceMaintenance:
     # Do not permanently reject legitimate product URLs during an
     # upstream outage, or burn the full crawl budget on maintenance pages.
     reason='temporary_source_maintenance'
     cooldown=6*3600
     host=urlsplit(url).netloc
     self.db.execute('INSERT OR REPLACE INTO host_state VALUES(?,?,?)',(host,time.time()+cooldown,reason))
     self.db.execute("UPDATE queue SET status='pending',attempts=attempts+1,next_try=?,error=? WHERE url=?",
      (time.time()+cooldown,reason,url))
    except Exception as e:
     code=getattr(e,'code',None);reason=type(e).__name__+':'+str(code or str(e)[:120])
     cooldown=0 if code==404 else 86400 if code in (401,403) else 3600 if code==429 else 900
     if code!=404:
      self.db.execute('INSERT OR REPLACE INTO host_state VALUES(?,?,?)',(urlsplit(url).netloc,time.time()+cooldown,reason))
     self.db.execute("UPDATE queue SET status=?,attempts=attempts+1,next_try=?,error=? WHERE url=?",('done' if code==404 or attempts>=4 else 'pending',time.time()+cooldown,reason,url))
    self.db.execute('INSERT INTO observations VALUES(?,?,?)',(url,reason,datetime.now(timezone.utc).isoformat()));self.db.commit()
    done+=1
    if done%25==0:self.checkpoint()
  finally:
   if self.run_stop_reason=='in_progress':
    if self.count()>=self.target:self.run_stop_reason='target_reached'
    elif done>=max_pages:self.run_stop_reason='page_budget'
    elif time.monotonic()>=end:self.run_stop_reason='time_budget'
    else:self.run_stop_reason='interrupted'
   self.checkpoint()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--state',default='crawler-state');p.add_argument('--seeds',default='scripts/japan_ingredient_sources.json');p.add_argument('--target',type=int,default=100000);p.add_argument('--max-pages',type=int,default=1500);p.add_argument('--minutes',type=float,default=35);p.add_argument('--checkpoint-only',action='store_true')
 a=p.parse_args();c=Collector(a.state,a.target)
 if a.checkpoint_only:c.checkpoint()
 else:c.run(json.loads(Path(a.seeds).read_text()),a.max_pages,a.minutes)