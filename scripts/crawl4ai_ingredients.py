#!/usr/bin/env python3
"""Crawl public Japanese food pages for ingredient evidence (NOT halal certification).
Unseen URLs are prioritized; attempt history and evidence are persisted between workflow runs.
"""
import asyncio, hashlib, json, os, re
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

SEEDS = Path(os.getenv("CRAWL_SEEDS_FILE", "data/manufacturer_seed_urls.txt"))
OUT = Path("data/crawl4ai_ingredient_evidence.jsonl")
ATTEMPTED = Path("data/crawl4ai_attempted_urls.txt")
MAX_URLS = min(max(int(os.getenv("CRAWL_MAX_URLS", "50")), 1), 250)
AGENT = "JapanHalalCheckerResearchBot"
PATTERN = re.compile(r"(原材料名|原材料|使用原材料|ingredients|アレルゲン|添加物)", re.I)
BARCODE = re.compile(r"(?<!\d)(?:45|49)\d{11}(?!\d)")
robots_cache = {}

def allowed(url):
    p = urlparse(url)
    if p.scheme != "https" or not p.hostname:
        return False
    host = p.hostname
    if host not in robots_cache:
        from urllib.robotparser import RobotFileParser
        rp = RobotFileParser()
        rp.set_url(f"https://{host}/robots.txt")
        try:
            rp.read()
        except Exception:
            return False
        robots_cache[host] = rp
    return robots_cache[host].can_fetch(AGENT, url)

async def main():
    if not SEEDS.exists():
        print(f"No seeds: {SEEDS}")
        return
    all_urls = list(dict.fromkeys(s.strip() for s in SEEDS.read_text(encoding="utf-8").splitlines()
                                  if s.strip() and not s.lstrip().startswith("#")))
    attempted = set(ATTEMPTED.read_text(encoding="utf-8").splitlines()) if ATTEMPTED.exists() else set()
    urls = [u for u in all_urls if u not in attempted][:MAX_URLS]
    print(f"Seeds={len(all_urls)} previously_attempted={len(attempted)} this_run={len(urls)}", flush=True)
    if not urls:
        print("No unseen seed URLs. Add more official source URLs to continue collection.", flush=True)
        return
    OUT.parent.mkdir(exist_ok=True, parents=True)
    existing = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            try: existing.add(json.loads(line)["source_url"])
            except (ValueError, KeyError): pass
    browser = BrowserConfig(headless=True, verbose=False)
    cfg = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=45000)
    async with AsyncWebCrawler(config=browser) as crawler:
        for url in urls:
            attempted.add(url)
            if url in existing:
                print("ALREADY HAVE EVIDENCE", url, flush=True)
            elif not allowed(url):
                print("ROBOTS/HTTPS SKIP", url, flush=True)
            else:
                try:
                    result = await crawler.arun(url=url, config=cfg)
                    if result.success:
                        md = result.markdown or ""
                        lines = md.splitlines()
                        evidence = []
                        for i, line in enumerate(lines):
                            if PATTERN.search(line):
                                evidence.append("\n".join(lines[max(0,i-1):min(len(lines),i+5)])[:2000])
                        metadata = getattr(result, "metadata", {}) or {}
                        title = metadata.get("title", "") if isinstance(metadata, dict) else ""
                        if evidence:
                            record={"source_url":url,"host":urlparse(url).hostname,"page_title":title,
                                    "evidence":evidence[:25],
                                    "barcode_candidates":list(dict.fromkeys(BARCODE.findall(md)))[:20],
                                    "page_sha256":hashlib.sha256(md.encode()).hexdigest(),
                                    "verification":"needs_human_review","halal_certified":False}
                            with OUT.open("a", encoding="utf-8") as f:
                                f.write(json.dumps(record,ensure_ascii=False)+"\n")
                            existing.add(url)
                            print("EVIDENCE",url,"snippets=",len(evidence),flush=True)
                        else:
                            print("NO INGREDIENT TEXT",url,flush=True)
                    else:
                        print("ERROR",url,str(result.error_message)[:150],flush=True)
                except Exception as exc:
                    print("ERROR",url,str(exc)[:150],flush=True)
            ATTEMPTED.write_text("\n".join(sorted(attempted)) + "\n", encoding="utf-8")
            await asyncio.sleep(5)
if __name__=="__main__":
    asyncio.run(main())
