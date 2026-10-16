#!/usr/bin/env python3
"""Crawl public Japanese food pages for ingredient evidence (NOT halal certification).
Usage: python scripts/crawl4ai_ingredients.py
Set CRAWL_SEEDS_FILE to a newline-delimited URL list. Respect robots.txt and host pacing.
"""
import asyncio, hashlib, json, os, re
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

SEEDS = Path(os.getenv("CRAWL_SEEDS_FILE", "data/manufacturer_seed_urls.txt"))
OUT = Path("data/crawl4ai_ingredient_evidence.jsonl")
MAX_URLS = min(max(int(os.getenv("CRAWL_MAX_URLS", "25")), 1), 250)
AGENT = "JapanHalalCheckerResearchBot"
PATTERN = re.compile(r"(原材料名|原材料|使用原材料|ingredients|アレルゲン|添加物)", re.I)
BARCODE = re.compile(r"(?<!\d)(?:45|49)\d{11}(?!\d)")
robots_cache = {}

def allowed(url):
    p = urlparse(url)
    if p.scheme != "https" or not p.hostname: return False
    host = p.hostname
    if host not in robots_cache:
        rp = RobotFileParser()
        rp.set_url(f"https://{host}/robots.txt")
        try: rp.read()
        except Exception: return False
        robots_cache[host] = rp
    return robots_cache[host].can_fetch(AGENT,url)

async def main():
    if not SEEDS.exists():
        print(f"No seeds: {SEEDS}")
        return
    urls = list(dict.fromkeys(s.strip() for s in SEEDS.read_text().splitlines()
                              if s.strip() and not s.lstrip().startswith("#")))[:MAX_URLS]
    OUT.parent.mkdir(exist_ok=True, parents=True)
    existing = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            try: existing.add(json.loads(line)["source_url"])
            except (ValueError, KeyError): pass
    browser = BrowserConfig(headless=True, verbose=False)
    cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=45000)
    async with AsyncWebCrawler(config=browser) as crawler:
        with OUT.open("a", encoding="utf-8") as f:
            for url in urls:
                if url in existing or not allowed(url):
                    print("SKIP", url, flush=True)
                    continue
                try:
                    result = await crawler.arun(url=url, config=cfg)
                    if result.success:
                        md = result.markdown or ""
                        lines = md.splitlines()
                        evidence = []
                        for i,line in enumerate(lines):
                            if PATTERN.search(line):
                                evidence.append("\n".join(lines[max(0,i-1):min(len(lines),i+5)])[:2000])
                        if evidence:
                            record={"source_url":url,"host":urlparse(url).hostname,
                                    "evidence":evidence[:25],
                                    "barcode_candidates":list(dict.fromkeys(BARCODE.findall(md)))[:20],
                                    "page_sha256":hashlib.sha256(md.encode()).hexdigest(),
                                    "verification":"needs_human_review",
                                    "halal_certified":False}
                            f.write(json.dumps(record,ensure_ascii=False)+"\n")
                            f.flush()
                            print("EVIDENCE",url,flush=True)
                        else: print("NO INGREDIENT TEXT",url,flush=True)
                    else: print("ERROR",url,str(result.error_message)[:150],flush=True)
                except Exception as exc: print("ERROR",url,str(exc)[:150],flush=True)
                await asyncio.sleep(5)
if __name__=="__main__":
    asyncio.run(main())
