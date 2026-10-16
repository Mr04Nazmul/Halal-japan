#!/usr/bin/env python3
"""HTTP-only public ingredient page crawl fallback. Respect robots.txt and host delay.
Records are evidence only, not halal rulings or certification.
"""
import json, os, re, time, urllib.request
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from html import unescape
from pathlib import Path

SEEDS=Path("data/manufacturer_seed_urls.txt")
OUT=Path("data/http_ingredient_evidence.jsonl")
AGENT="JapanHalalCheckerResearchBot"
PAT=re.compile(r"(原材料名|原材料|使用原材料|ingredients|アレルゲン|添加物)",re.I)
TAG=re.compile(r"<[^>]+>")
MAX=min(int(os.getenv("CRAWL_MAX_URLS","25")),250)
def allowed(url):
 p=urlparse(url)
 if p.scheme!="https": return False
 rp=RobotFileParser()
 rp.set_url(f"https://{p.netloc}/robots.txt")
 try:
  rp.read()
  return rp.can_fetch(AGENT,url)
 except Exception:
  return False
def main():
 if not SEEDS.exists(): return
 urls=list(dict.fromkeys(x.strip() for x in SEEDS.read_text().splitlines() if x.strip() and not x.strip().startswith("#")))[:MAX]
 OUT.parent.mkdir(parents=True,exist_ok=True)
 with OUT.open("w",encoding="utf-8") as out:
  for url in urls:
   if not allowed(url):
    print("ROBOTS SKIP",url,flush=True);continue
   try:
    req=urllib.request.Request(url,headers={"User-Agent":AGENT,"Accept-Language":"ja"})
    with urllib.request.urlopen(req,timeout=40) as response:
     raw=response.read(4_000_000)
     encoding=response.headers.get_content_charset() or "utf-8"
    html=raw.decode(encoding,errors="replace")
    cleaned=unescape(TAG.sub(" ",html))
    cleaned=re.sub(r"\\s+"," ",cleaned)
    matched=[m.start() for m in PAT.finditer(cleaned)]
    snippets=[cleaned[max(0,n-100):n+700] for n in matched[:30]]
    if snippets:
     record={"source_url":url,"ingredient_evidence":snippets,"verification":"needs_manual_review"}
     out.write(json.dumps(record,ensure_ascii=False)+"\\n")
     print("EVIDENCE",url,len(snippets),flush=True)
    else:print("NO INGREDIENT TEXT",url,flush=True)
   except Exception as exc:print("ERROR",url,str(exc)[:240],flush=True)
   time.sleep(5)
if __name__=="__main__":main()
