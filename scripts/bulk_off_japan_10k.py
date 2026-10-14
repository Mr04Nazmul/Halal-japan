#!/usr/bin/env python3
"""Incrementally collect up to 10,000 Japan-tagged products from Open Food Facts.

Research-only data: an OFF country tag is not proof of being sold in Japan,
and community ingredients are NOT verified halal status.
Licensed ODbL 1.0; see https://world.openfoodfacts.org/terms-of-use
"""
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "openfoodfacts-japan.json"
STATE = ROOT / "data" / "off-japan-import-state.json"
API = "https://world.openfoodfacts.org/api/v2/search"
AGENT = "JapanHalalChecker/1.0 (https://github.com/Mr04Nazmul/Halal-japan)"
TARGET = max(1, min(int(os.getenv("TARGET_PRODUCTS", "10000")), 100000))
MAX_RUN_PAGES = max(1, min(int(os.getenv("MAX_PAGES_PER_RUN", "120")), 300))
PAGE_SIZE = 100
FIELDS = "code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,countries_tags,quantity,last_modified_t"


def valid_barcode(s):
    if not re.fullmatch(r"(?:\d{8}|\d{12,14})", s):
        return False
    vals = [int(ch) for ch in s]
    weighted = sum(v * (3 if i % 2 == 0 else 1)
                   for i, v in enumerate(reversed(vals[:-1])))
    return (10 - weighted % 10) % 10 == vals[-1]


def fetch_page(page):
    params = urlencode({
        "countries_tags": "en:japan", "page": page,
        "page_size": PAGE_SIZE, "fields": FIELDS, "sort_by": "created_t"
    })
    req = Request(API + "?" + params, headers={
        "User-Agent": AGENT, "Accept": "application/json"
    })
    for attempt in range(4):
        try:
            with urlopen(req, timeout=45) as res:
                payload = json.load(res)
                if not isinstance(payload.get("products"), list):
                    raise ValueError("Unexpected API response: missing products")
                return payload
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            if isinstance(exc, HTTPError) and exc.code not in (429, 500, 502, 503, 504):
                raise
            if attempt == 3:
                print(f"::warning::OFF page {page} unavailable: {exc}", flush=True)
                return None
            time.sleep(min(40, 4 * 2 ** attempt))


def normalized_product(item):
    code = str(item.get("code") or "").strip()
    tags = item.get("countries_tags") or []
    if isinstance(tags, str):
        tags = [s.strip() for s in tags.split(",")]
    if not valid_barcode(code) or "en:japan" not in tags:
        return None
    name = str(item.get("product_name_ja") or item.get("product_name") or "").strip()
    if not name:
        return None
    ingredients = str(item.get("ingredients_text_ja") or
                      item.get("ingredients_text") or "").strip()
    return {
        "code": code,
        "product_name": name[:200],
        "brands": str(item.get("brands") or "")[:160],
        "quantity": str(item.get("quantity") or "")[:100],
        "ingredients_text": ingredients[:6000],
        "last_modified_t": item.get("last_modified_t"),
        "_source": "Open Food Facts (community-maintained)",
        "_sourceUrl": "https://world.openfoodfacts.org/product/" + code,
        "_license": "ODbL-1.0",
        "_halalVerified": False,
        "_ingredientsVerified": False,
        "_verificationStatus": "needs_review",
        "_checkedVia": "community_database",
    }


def read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    existing = read_json(OUT, {})
    products = {
        p["code"]: p for p in
        existing.get("products", existing.get("records", []))
        if isinstance(p, dict) and p.get("code")
    }
    previous_count = len(products)
    state = read_json(STATE, {"next_page": 1})
    start = max(1, int(state.get("next_page", 1)))
    page = start
    fetched = 0
    added = 0
    with_ingredients = 0
    reached_end = False

    for _ in range(MAX_RUN_PAGES):
        if len(products) >= TARGET:
            break
        data = fetch_page(page)
        if data is None:
            break
        rows = data["products"]
        if not rows:
            reached_end = True
            break
        fetched += len(rows)
        for raw in rows:
            p = normalized_product(raw)
            if p is None:
                continue
            code = p["code"]
            if code not in products:
                products[code] = p
                added += 1
            elif not products[code].get("_ingredientsVerified") and not products[code].get("_halalVerified"):
                # Never overwrite manually verified records.
                products[code] = p
            if len(products) >= TARGET:
                break
        total = data.get("count")
        if isinstance(total, int) and page * PAGE_SIZE >= total:
            reached_end = True
            break
        page += 1
        time.sleep(1.3)

    with_ingredients = sum(bool(p.get("ingredients_text")) for p in products.values())
    if len(products) < previous_count:
        raise RuntimeError("Refusing to shrink existing product dataset")
    if products:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": "Open Food Facts",
            "license": "ODbL-1.0",
            "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
            "attribution": "Contains data from Open Food Facts (https://world.openfoodfacts.org), available under ODbL.",
            "scope": "Products tagged en:japan; not evidence of availability in Japanese shops",
            "disclaimer": "Community product information, not verified halal or certified ingredient origins.",
            "target": TARGET,
            "record_count": len(products),
            "ingredient_text_count": with_ingredients,
            "products": sorted(products.values(), key=lambda p: p["code"]),
        }
        OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
                       encoding="utf-8")
        STATE.write_text(json.dumps({
            "next_page": 1 if reached_end else page,
            "last_batch_new": added,
            "records_saved": len(products),
            "target": TARGET,
        }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "target": TARGET, "previous_records": previous_count,
        "page_start": start, "page_last": page,
        "api_rows_seen": fetched, "new_records": added,
        "records_saved": len(products),
        "with_ingredient_text": with_ingredients,
        "end_of_country_results": reached_end,
        "target_reached": len(products) >= TARGET,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
