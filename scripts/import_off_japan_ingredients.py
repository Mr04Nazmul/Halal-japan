#!/usr/bin/env python3
"""Collect licensed, community-contributed Japanese ingredient candidates from OFF.

This is a supplemental research queue only. It does not establish manufacturer
verification, halal status, or certification. Search pagination is bounded to
10 pages per category; API requests are paced to respect upstream limits.
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
USER_AGENT = "JapanHalalCheckerResearch/1.2 (https://github.com/Mr04Nazmul/Halal-japan)"
OFF_API = "https://world.openfoodfacts.org/api/v2/search"
OFF_PRODUCT = "https://world.openfoodfacts.org/product/"
SOURCE_LICENSE = "Open Food Facts database: ODbL 1.0; individual contents: Database Contents License 1.0"
SOURCE_ATTRIBUTION = "Open Food Facts contributors"
VERIFICATION_STATUS = "community_contributed_unverified_pending_human_review"
OFF_CATEGORIES = (
    "beverages", "snacks", "biscuits-and-cakes", "chocolates",
    "confectioneries", "noodles", "instant-foods", "soups",
    "condiments", "sauces", "dairy-products", "frozen-foods",
)


def valid_ean(code):
    code = str(code or "")
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


def build_search_url(category, page, page_size):
    if category not in OFF_CATEGORIES:
        raise ValueError(f"Unapproved OFF category: {category}")
    page = max(1, min(int(page), 10))
    page_size = max(1, min(int(page_size), 100))
    params = {
        "countries_tags": "en:japan",
        "categories_tags_en": category,
        "page": str(page),
        "page_size": str(page_size),
        "fields": "code,product_name_ja,product_name,brands,ingredients_text_ja,ingredients_text",
    }
    return OFF_API + "?" + urllib.parse.urlencode(params)


def fetch_search_page(url, *, opener=None, sleeper=None, attempts=3):
    """Fetch one OFF API page; retry transient errors only, never bypass 4xx."""
    opener = opener or urllib.request.urlopen
    sleeper = sleeper or time.sleep
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    for attempt in range(attempts):
        try:
            with opener(request, timeout=45) as response:
                payload = json.load(response)
            if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
                raise ValueError("OFF response missing products array")
            return payload
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRYABLE_HTTP or attempt + 1 == attempts:
                raise
            retry_after = (exc.headers.get("Retry-After") or "").strip() if exc.headers else ""
            delay = 3 * (2 ** attempt)
            if retry_after.isdigit():
                if int(retry_after) > 30:
                    raise
                delay = max(delay, int(retry_after))
            delay = min(30, delay)
            print(f"OFF HTTP {exc.code}; retry {attempt + 2}/{attempts} in {delay}s", flush=True)
            sleeper(delay)
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            if attempt + 1 == attempts:
                raise
            delay = min(30, 3 * (2 ** attempt))
            print(f"OFF temporary response error; retry {attempt + 2}/{attempts} in {delay}s: {type(exc).__name__}", flush=True)
            sleeper(delay)
    raise RuntimeError("OFF request exhausted attempts")


def collect_candidates(categories=OFF_CATEGORIES, *, pages_per_category=10,
                       page_size=100, fetcher=fetch_search_page,
                       sleeper=time.sleep, delay=7):
    pages_per_category = max(1, min(int(pages_per_category), 10))
    page_size = max(1, min(int(page_size), 100))
    delay = max(0, min(int(delay), 15))
    seen = set()
    rows = []
    stats = {
        "categories_queried": [],
        "failed_categories": [],
        "pages_requested": 0,
        "failed_pages": 0,
        "rejected_non_japanese_or_invalid_ean": 0,
        "duplicate_barcodes": 0,
    }
    for category in categories:
        if category not in OFF_CATEGORIES:
            continue
        stats["categories_queried"].append(category)
        for page in range(1, pages_per_category + 1):
            url = build_search_url(category, page, page_size)
            stats["pages_requested"] += 1
            try:
                payload = fetcher(url)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
                stats["failed_pages"] += 1
                stats["failed_categories"].append(category)
                print(f"category={category} page={page} failed after bounded retries: {exc}", flush=True)
                break
            products = payload["products"]
            count = int(payload.get("count") or 0)
            page_count = int(payload.get("page_count") or len(products))
            for product in products:
                code = str(product.get("code") or "").strip()
                name = (product.get("product_name_ja") or product.get("product_name") or "").strip()
                ingredients = (product.get("ingredients_text_ja") or product.get("ingredients_text") or "").strip()
                if not is_japanese_ingredient_candidate(code, name, ingredients):
                    stats["rejected_non_japanese_or_invalid_ean"] += 1
                    continue
                if code in seen:
                    stats["duplicate_barcodes"] += 1
                    continue
                seen.add(code)
                collected_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
                rows.append({
                    "barcode": code,
                    "name": name,
                    "brand": product.get("brands"),
                    "ingredients": ingredients,
                    "source_url": OFF_PRODUCT + code,
                    "source": "Open Food Facts",
                    "source_category": category,
                    "source_license": SOURCE_LICENSE,
                    "source_attribution": SOURCE_ATTRIBUTION,
                    "collected_at": collected_at,
                    "verification": "requires_review",
                    "verification_status": VERIFICATION_STATUS,
                    "halal_certified": False,
                })
            print(f"category={category} page={page} page_count={page_count} unique_candidates={len(rows)}", flush=True)
            if page_count < page_size or (count and page * page_size >= count):
                break
            if delay:
                sleeper(delay)
    stats["unique_candidates"] = len(rows)
    return rows, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories-limit", type=int, default=12)
    parser.add_argument("--pages-per-category", type=int, default=10)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--delay", type=int, default=7)
    parser.add_argument("--output", default="data/off_japan_ingredient_candidates.jsonl")
    args = parser.parse_args()
    category_limit = max(1, min(args.categories_limit, len(OFF_CATEGORIES)))
    categories = OFF_CATEGORIES[:category_limit]
    rows, stats = collect_candidates(
        categories,
        pages_per_category=args.pages_per_category,
        page_size=args.page_size,
        delay=args.delay,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    stats["output"] = str(output)
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
