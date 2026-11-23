#!/usr/bin/env python3
"""Collect review-only Japanese ingredient candidates from Open Food Facts.

Public, bounded API requests. Never imports into the live database or infers
halal certification. Manufacturer/packaging verification remains separate.
"""
import argparse
import datetime
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

JP_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
JP_KANA = re.compile(r"[\u3040-\u30ff]")
RETRYABLE_HTTP = {429, 500, 502, 503, 504}
STOP_BATCH_HTTP = {401, 403, 429, 500, 502, 503, 504}
USER_AGENT = "JapanHalalCheckerResearch/1.1 (https://github.com/Mr04Nazmul/Halal-japan)"


def valid_ean(code):
    if len(code) not in (8, 13) or not code.isascii() or not code.isdigit():
        return False
    digits = [int(c) for c in code]
    total = sum(d * (3 if i % 2 == 0 else 1)
                for i, d in enumerate(reversed(digits[:-1])))
    return (10 - total % 10) % 10 == digits[-1]


def is_japanese_ingredient_candidate(code, name, ingredients):
    name = str(name or "").strip()
    ingredients = str(ingredients or "").strip()
    return (valid_ean(code) and len(name) > 1 and len(ingredients) >= 8
            and bool(JP_TEXT.search(name)) and bool(JP_TEXT.search(ingredients))
            and bool(JP_KANA.search(name) or JP_KANA.search(ingredients)))


def fetch_page(url, *, opener=None, sleeper=None, attempts=3):
    """Fetch one OFF page and return its products plus total page count."""
    opener = opener or urllib.request.urlopen
    sleeper = sleeper or time.sleep
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(attempts):
        try:
            with opener(request, timeout=45) as response:
                payload = json.load(response)
            products = payload.get("products")
            if not isinstance(products, list):
                raise ValueError("OFF response missing products array")
            raw_page_count = payload.get("page_count")
            try:
                page_count = int(raw_page_count) if raw_page_count is not None else None
            except (TypeError, ValueError):
                page_count = None
            if page_count is not None and page_count < 1:
                page_count = None
            return products, page_count
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRYABLE_HTTP or attempt + 1 == attempts:
                raise
            retry_after = (exc.headers.get("Retry-After") or "").strip() if exc.headers else ""
            delay = 3 * (2 ** attempt)
            if retry_after.isdigit():
                # Respect upstream rate limits: do not retry if wait exceeds budget.
                if int(retry_after) > 30:
                    raise
                delay = max(delay, int(retry_after))
            delay = min(30, delay)
            print(f"OFF HTTP {exc.code}; retry {attempt + 2}/{attempts} in {delay}s", flush=True)
            sleeper(delay)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt + 1 == attempts:
                raise
            delay = min(30, 3 * (2 ** attempt))
            print(f"OFF temporary connection error; retry {attempt + 2}/{attempts} in {delay}s: {type(exc).__name__}", flush=True)
            sleeper(delay)
    raise RuntimeError("OFF request exhausted attempts")


def fetch_products(url, *, opener=None, sleeper=None, attempts=3):
    """Backward-compatible products-only wrapper used by existing callers."""
    products, _ = fetch_page(url, opener=opener, sleeper=sleeper, attempts=attempts)
    return products


def page_sequence(start_page, pages, page_count=None):
    """Select a bounded, non-repeating page window and wrap at OFF's page_count."""
    start_page = max(1, int(start_page))
    pages = max(1, min(int(pages), 20))
    if page_count is None or int(page_count) < 1:
        return [start_page + offset for offset in range(pages)]
    page_count = int(page_count)
    count = min(pages, page_count)
    first = ((start_page - 1) % page_count) + 1
    return [((first - 1 + offset) % page_count) + 1 for offset in range(count)]


def should_stop_batch(error):
    """Stop paging after access denial, rate limiting, or exhausted server errors."""
    return isinstance(error, urllib.error.HTTPError) and error.code in STOP_BATCH_HTTP


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--start-page", type=int, default=1,
                        help="first OFF result page; wraps using the API page_count")
    parser.add_argument("--output", default="data/off_japan_ingredient_candidates.jsonl")
    args = parser.parse_args()
    pages = max(1, min(args.pages, 20))
    page_size = max(1, min(args.page_size, 100))
    start_page = max(1, args.start_page)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    total = rejected = failed_pages = 0

    def page_url(page):
        params = {
            "action": "process", "json": "1", "tagtype_0": "countries",
            "tag_contains_0": "contains", "tag_0": "japan",
            "fields": "code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja",
            "page": str(page), "page_size": str(page_size),
        }
        return "https://world.openfoodfacts.org/cgi/search.pl?" + urllib.parse.urlencode(params)

    # Probe the requested page for OFF's current page_count. This lets scheduled
    # runs rotate through the full catalogue instead of rescanning pages 1..N.
    probe_products = None
    page_count = None
    stop_after_probe = False
    try:
        probe_products, page_count = fetch_page(page_url(start_page))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        failed_pages += 1
        print(f"page-count probe for page {start_page} failed: {exc}", flush=True)
        stop_after_probe = should_stop_batch(exc)
        if stop_after_probe:
            print("Stopping OFF batch after access/rate-limit/server failure; no further pages requested.",
                  flush=True)
    page_numbers = [] if stop_after_probe else page_sequence(start_page, pages, page_count)
    print(json.dumps({"start_page": start_page, "page_count": page_count,
                      "pages_requested": pages, "page_window": page_numbers}), flush=True)

    with output.open("w", encoding="utf8") as file:
        for page in page_numbers:
            if page == start_page and probe_products is not None:
                products = probe_products
            else:
                try:
                    products, _ = fetch_page(page_url(page))
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
                    failed_pages += 1
                    print(f"page {page} failed after retries: {exc}", flush=True)
                    if should_stop_batch(exc):
                        print("Stopping OFF batch after access/rate-limit/server failure.",
                              flush=True)
                        break
                    continue
            for row in products:
                code = str(row.get("code") or "").strip()
                ingredients = (row.get("ingredients_text_ja") or row.get("ingredients_text") or "").strip()
                name = (row.get("product_name_ja") or row.get("product_name") or "").strip()
                if not is_japanese_ingredient_candidate(code, name, ingredients):
                    rejected += 1
                    continue
                if code in seen:
                    continue
                seen.add(code)
                item = {
                    "barcode": code,
                    "name": name,
                    "brand": row.get("brands"),
                    "ingredients": ingredients,
                    "source_url": "https://world.openfoodfacts.org/product/" + code,
                    "source": "Open Food Facts",
                    "collected_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "verification": "requires_review",
                    "halal_certified": False,
                }
                file.write(json.dumps(item, ensure_ascii=False) + "\n")
                total += 1
            print(f"page={page} ingredient_records={total}", flush=True)
            time.sleep(2)
    print(json.dumps({
        "start_page": start_page,
        "page_count": page_count,
        "pages_requested": pages,
        "page_window": page_numbers,
        "ingredient_records": total,
        "rejected_non_japanese_or_invalid_ean": rejected,
        "failed_pages": failed_pages,
        "output": str(output),
    }))


if __name__ == "__main__":
    main()
