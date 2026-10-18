#!/usr/bin/env python3
"""Public-page discovery for Japanese food research, not a private app database extractor.
Agent-Reach uses Jina Reader as its web-reading channel. This script gathers limited
source URL/title evidence only, without copying third-party guide texts or issuing verdicts.
"""
import json, re, os, time
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from html import unescape

SEEDS=[
 "https://halaljapan.app/guides/",
 "https://halaljapan.app/guides/japanese-halal-ingredients-labels/",
 "https://halaljapan.app/methodology/",
]
UA="JapanHalalCheckerResearchBot/1.0 (public-source metadata)"
OUTPUT=Path("data/research/agent_reach_public_sources.json")
ALLOW={"halaljapan.app"}
def robots_ok(url):
 p=urlparse(url)
 if p.scheme!="https" or p.hostname not in ALLOW:return False
 robot=RobotFileParser();robot.set_url(f"{p.scheme}://{p.netloc}/robots.txt")
 try: robot.read();return robot.can_fetch(UA,url)
 except Exception:return False
def fetch(url):
 req=Request(url,headers={"User-Agent":UA,"Accept":"text/html"})
 with urlopen(req,timeout=20) as r:
  if "text/html" not in r.headers.get("Content-Type",""):return ""
  return r.read(600000).decode("utf-8","replace")
def links(html,base):
 result=[]
 for href in re.findall(r'<a\b[^>]*\bhref\s*=\s*["\']([^"\']+)',html,re.I):
  u=urljoin(base,unescape(href)).split("#")[0]
  parsed=urlparse(u)
  if parsed.scheme=="https" and parsed.hostname in ALLOW and (parsed.path.startswith("/guides/") or parsed.path.startswith("/products/")):
   if u not in result:result.append(u)
 return result
def main():
 results=[];seen=set()
 for url in SEEDS:
  if not robots_ok(url):
   print("robots blocked/unavailable",url);continue
  try:
   raw=fetch(url)
   title=re.search(r'<title[^>]*>(.*?)</title>',raw,re.I|re.S)
   results.append({"url":url,"title":re.sub(r"<[^>]*>","",unescape(title.group(1))).strip()[:160] if title else "",
    "kind":"public_reference_only","product_ingredient_verified":False})
   seen.add(url)
   for link in links(raw,url):
    if link not in seen: results.append({"url":link,"kind":"discovered_reference_only","product_ingredient_verified":False});seen.add(link)
  except Exception as e:print("fetch failed",url,type(e).__name__)
  time.sleep(2)
 OUTPUT.parent.mkdir(parents=True,exist_ok=True)
 OUTPUT.write_text(json.dumps({"source":"Public halaljapan.app references; independent site, not our project","candidate_product_rows":0,"records":results},ensure_ascii=False,indent=2)+"\n")
 print(f"references={len(results)} verified_product_records=0 output={OUTPUT}")
if __name__=="__main__":main()
