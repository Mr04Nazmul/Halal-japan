#!/usr/bin/env python3
"""Collect Japanese food product records with provenance; never infer halal certification."""
import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://world.openfoodfacts.org/api/v2/search"
FIELDS = "code,product_name,brands,ingredients_text,ingredients_text_ja,ingredients_text_en,labels_tags,ingredients_analysis_tags,url,last_modified_t"
OUT = Path("data/japan_ingredients.csv")
STATE = Path("data/japan_ingredients_state.json")
HEADERS = {
    "User-Agent": "JapanHalalCheckerCollector/1.0 (https://github.com/Mr04Nazmul/Halal-japan; research contact via GitHub issues)",
    "Accept": "application/json",
}
RETRYABLE_HTTP = {500, 502, 503, 504}
STOP_BATCH_HTTP = {401, 403, 429, 500, 502, 503, 504}
MAX = min(int(os.environ.get("MAX_PAGES", "30")), 1000)
# Scheduled runs rotate the starting OFF page instead of rechecking pages 1-2.
DEFAULT_START_PAGE = 1 + ((int(time.time() // 3600) * 3) % 240)
START = max(1, int(os.environ.get("START_PAGE") or DEFAULT_START_PAGE))
REQUEST_INTERVAL_SECONDS = 7


def build_search_url(page):
    query = urllib.parse.urlencode({
        "countries_tags": "en:japan",
        "page": int(page),
        "page_size": 100,
        "fields": FIELDS,
        "sort_by": "nothing",
    })
    return BASE + "?" + query


def fetch_page(page, *, opener=None, sleeper=None, attempts=2):
    """Fetch one OFF page with bounded retries and no retry on access denial."""
    opener = opener or urllib.request.urlopen
    sleeper = sleeper or time.sleep
    request = urllib.request.Request(build_search_url(page), headers=HEADERS)
    for attempt in range(attempts):
        try:
            with opener(request, timeout=45) as response:
                payload = json.load(response)
            if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
                raise ValueError("OFF response missing products array")
            return payload
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403, 429}:
                # Authentication/access/rate-limit failures will not improve
                # by requesting the next page. Stop before generating more load.
                raise
            if exc.code not in RETRYABLE_HTTP or attempt + 1 >= attempts:
                raise
            retry_after = (exc.headers.get("Retry-After") or "").strip() if exc.headers else ""
            if retry_after.isdigit() and int(retry_after) > 30:
                raise
            delay = REQUEST_INTERVAL_SECONDS * (2 ** attempt)
            if retry_after.isdigit():
                delay = max(delay, int(retry_after))
            delay = min(30, delay)
            print(f"OFF HTTP {exc.code}; retry {attempt + 2}/{attempts} in {delay}s", flush=True)
            sleeper(delay)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt + 1 >= attempts:
                raise
            delay = min(30, 3 * (2 ** attempt))
            print(f"OFF temporary connection error; retry {attempt + 2}/{attempts} in {delay}s: {type(exc).__name__}", flush=True)
            sleeper(delay)
    raise RuntimeError("OFF request exhausted attempts")


def should_stop_batch(error):
    return isinstance(error, urllib.error.HTTPError) and error.code in STOP_BATCH_HTTP


def collect(*, start_page, max_pages, output=OUT, state=STATE, fetcher=None, sleeper=None):
    fetcher = fetcher or fetch_page
    sleeper = sleeper or time.sleep
    output = Path(output)
    state = Path(state)
    output.parent.mkdir(parents=True, exist_ok=True)
    state.parent.mkdir(parents=True, exist_ok=True)

    keys = [
        "barcode", "product_name", "brand", "ingredients_ja", "ingredients_en",
        "ingredients_raw", "source", "source_url", "labels", "analysis_tags",
        "last_modified", "verification",
    ]
    seen = set()
    if output.exists():
        with output.open(encoding="utf-8", newline="") as existing_file:
            for row in csv.DictReader(existing_file):
                if row.get("barcode"):
                    seen.add(row["barcode"])

    written = 0
    pages = 0
    errors = []
    attempted_pages = 0
    last_page_attempted = None
    consecutive_failures = 0
    stop_reason = None

    with output.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        if file.tell() == 0:
            writer.writeheader()
        for page in range(int(start_page), int(start_page) + max(0, int(max_pages))):
            attempted_pages += 1
            last_page_attempted = page
            try:
                payload = fetcher(page)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
                print(f"ERROR page={page}: {exc}", flush=True)
                errors.append({"page": page, "error": str(exc)})
                consecutive_failures += 1
                if should_stop_batch(exc):
                    stop_reason = "upstream_access_or_server_failure"
                    print("STOP: upstream access/rate-limit/server failure; next scheduled run will retry.", flush=True)
                    break
                if consecutive_failures >= 4:
                    stop_reason = "four_consecutive_unavailable_pages"
                    print("STOP: four consecutive unavailable pages; next scheduled run will retry.", flush=True)
                    break
                continue

            consecutive_failures = 0
            products = payload.get("products", [])
            if not products:
                break
            for product in products:
                code = str(product.get("code") or "").strip()
                ja = product.get("ingredients_text_ja") or ""
                en = product.get("ingredients_text_en") or ""
                raw = product.get("ingredients_text") or ""
                if not code or code in seen or not (ja or en or raw):
                    continue
                writer.writerow({
                    "barcode": code,
                    "product_name": product.get("product_name", ""),
                    "brand": product.get("brands", ""),
                    "ingredients_ja": ja,
                    "ingredients_en": en,
                    "ingredients_raw": raw,
                    "source": "Open Food Facts",
                    "source_url": product.get("url") or "https://world.openfoodfacts.org/product/" + code,
                    "labels": json.dumps(product.get("labels_tags", []), ensure_ascii=False),
                    "analysis_tags": json.dumps(product.get("ingredients_analysis_tags", []), ensure_ascii=False),
                    "last_modified": product.get("last_modified_t", ""),
                    "verification": "unverified_source_data",
                })
                seen.add(code)
                written += 1
            file.flush()
            pages += 1
            state.write_text(json.dumps({
                "last_page": page,
                "pages_this_run": pages,
                "new_ingredient_products": written,
                "unique_csv_rows": len(seen),
                "errors": errors,
            }, indent=2), encoding="utf-8")
            print(f"page={page} new={written} total={len(seen)}", flush=True)
            sleeper(REQUEST_INTERVAL_SECONDS)

    summary = {
        "last_page_processed": last_page_attempted,
        "pages_this_run": pages,
        "pages_attempted": attempted_pages,
        "new_ingredient_products": written,
        "unique_csv_rows": len(seen),
        "errors": errors,
        "status": "source_unavailable" if errors and pages == 0 else "partial_source_errors" if errors else "completed",
    }
    if stop_reason:
        summary["stop_reason"] = stop_reason
    state.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    print(f"OFF ingredient collection starting at page {START}; max_pages={MAX}", flush=True)
    summary = collect(start_page=START, max_pages=MAX)
    print(
        f"Done: {summary['new_ingredient_products']} new ingredient-bearing records; "
        f"{summary['unique_csv_rows']} total; errors={len(summary['errors'])}",
        flush=True,
    )
    if summary["pages_this_run"] == 0 and summary["errors"]:
        raise SystemExit("Collection failed: no OFF pages could be fetched; see state JSON for HTTP errors")


if __name__ == "__main__":
    main()
