#!/usr/bin/env python3
"""HTTP-only public ingredient crawl fallback. Respect robots.txt and host delay."""
import json, os, re, time, urllib.request
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from html import unescape
from pathlib import Path

SEEDS = Path("data/manufacturer_seed_urls.txt")
OUT = Path("data/http_ingredient_evidence.jsonl")
ATTEMPTED = Path("data/http_attempted_urls.txt")
AGENT = "JapanHalalCheckerResearchBot"
PAT = re.compile(r"(原材料名|原材料|使用原材料|ingredients|アレルゲン|添加物)", re.I)
TAG = re.compile(r"<[^>]+>")
TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
MAX = min(max(int(os.getenv("CRAWL_MAX_URLS", "50")), 1), 250)

def allowed(url):
    p = urlparse(url)
    if p.scheme != "https": return False
    rp = RobotFileParser()
    rp.set_url(f"https://{p.netloc}/robots.txt")
    try:
        rp.read()
        return rp.can_fetch(AGENT, url)
    except Exception:
        return False

def main():
    if not SEEDS.exists():
        print(f"No seeds: {SEEDS}", flush=True); return
    all_urls = list(dict.fromkeys(x.strip() for x in SEEDS.read_text(encoding="utf-8").splitlines()
                                  if x.strip() and not x.strip().startswith("#")))
    attempted = set(ATTEMPTED.read_text(encoding="utf-8").splitlines()) if ATTEMPTED.exists() else set()
    urls = [u for u in all_urls if u not in attempted][:MAX]
    print(f"HTTP seeds={len(all_urls)} previously_attempted={len(attempted)} this_run={len(urls)}", flush=True)
    if not urls:
        print("No unseen URLs for HTTP fallback.", flush=True); return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if OUT.exists():
        for line in OUT.read_text(encoding="utf-8").splitlines():
            try: existing.add(json.loads(line)["source_url"])
            except (ValueError, KeyError): pass
    for url in urls:
        attempted.add(url)
        if url in existing:
            print("ALREADY HAVE HTTP EVIDENCE", url, flush=True)
        elif not allowed(url):
            print("ROBOTS SKIP", url, flush=True)
        else:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept-Language": "ja"})
                with urllib.request.urlopen(req, timeout=40) as response:
                    raw = response.read(4_000_000)
                    encoding = response.headers.get_content_charset() or "utf-8"
                html = raw.decode(encoding, errors="replace")
                title_match = TITLE.search(html)
                title = re.sub(r"\s+", " ", unescape(TAG.sub(" ", title_match.group(1)))).strip() if title_match else ""
                cleaned = unescape(TAG.sub(" ", html))
                cleaned = re.sub(r"\s+", " ", cleaned)
                matched = [m.start() for m in PAT.finditer(cleaned)]
                snippets = [cleaned[max(0,n-100):n+1000] for n in matched[:30]]
                if snippets:
                    record={"source_url":url,"page_title":title,"ingredient_evidence":snippets,
                            "verification":"needs_manual_review","halal_certified":False}
                    with OUT.open("a", encoding="utf-8") as out:
                        out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    existing.add(url)
                    print("EVIDENCE", url, "snippets=",len(snippets), flush=True)
                else:
                    print("NO INGREDIENT TEXT", url, flush=True)
            except Exception as exc:
                print("ERROR", url, str(exc)[:240], flush=True)
        ATTEMPTED.write_text("\n".join(sorted(attempted)) + "\n", encoding="utf-8")
        time.sleep(5)

if __name__ == "__main__":
    main()
