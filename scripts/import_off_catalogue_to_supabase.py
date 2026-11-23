#!/usr/bin/env python3
"""Stage unique Japanese Open Food Facts ingredient records for human review only.

Reads the Japan-only ODbL catalogue plus the Japan-country-tagged subset of the
100k supplemental shards. Prefix-only and Japanese-name-only shards are not
treated as evidence that a product is sold in Japan. All OFF rows remain
discovery_only / needs_review; this script never infers halal certification.
"""
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data"
SOURCE = ROOT / "openfoodfacts-japan.json"
SHARDS = ROOT / "world-food-shards"
DISCOVERY_SOURCE = "Open Food Facts catalogue"
JP_CHARS = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
JP_KANA = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
PLACEHOLDERS = {"", "unknown", "n/a", "none", "no data", "ingredients", "?", "-"}


def valid_jan_code(code):
    """Accept only checksum-valid JAN-8 or JAN-13 values."""
    code = str(code or "")
    if not re.fullmatch(r"(?:[0-9]{8}|[0-9]{13})", code):
        return False
    digits = [int(c) for c in code]
    total = sum(
        number * (3 if index % 2 == 0 else 1)
        for index, number in enumerate(reversed(digits[:-1]))
    )
    return (10 - total % 10) % 10 == digits[-1]


def usable_ingredients(value):
    text = str(value or "").strip()
    return "" if text.lower() in PLACEHOLDERS else text


def build_review_row(record, *, require_japan_scope=False):
    """Return one review-only row, or None when evidence is insufficient."""
    if require_japan_scope and record.get("scope") != "japan_country_tag":
        return None

    code = str(record.get("code") or "").strip()
    name = str(
        record.get("product_name_ja")
        or record.get("product_name")
        or record.get("name")
        or ""
    ).strip()
    ingredients = usable_ingredients(
        record.get("ingredients_text_ja") or record.get("ingredients_text")
    )
    if not valid_jan_code(code) or not name or not ingredients:
        return None
    if not JP_CHARS.search(name) or not JP_CHARS.search(ingredients):
        return None
    # Han characters are shared with Chinese. Require kana in the ingredient
    # label, or a Japan-issued JAN prefix for all-kanji labels. This remains
    # discovery_only / needs_review; the prefix is not certification evidence.
    if not JP_KANA.search(ingredients) and not code.startswith(("45", "49")):
        return None

    expected_url = "https://world.openfoodfacts.org/product/" + code
    source_url = str(
        record.get("_sourceUrl") or record.get("source_url") or record.get("url") or ""
    ).strip()
    parsed = urllib.parse.urlsplit(source_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "world.openfoodfacts.org"
        or not parsed.path.rstrip("/").endswith("/product/" + code)
    ):
        source_url = expected_url

    return {
        "jan_code": code,
        "product_name": name[:500],
        "manufacturer": str(record.get("brands") or "")[:500] or None,
        "discovery_source": DISCOVERY_SOURCE,
        "source_url": source_url,
        "ingredients_text": ingredients[:6000],
        "evidence_level": "discovery_only",
        "status": "needs_review",
    }


def load_candidates():
    if not SOURCE.is_file() or SOURCE.stat().st_size == 0:
        raise SystemExit("Missing Japan-only OFF catalogue; refusing import")

    japan_data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if japan_data.get("license") != "ODbL-1.0":
        raise SystemExit("Unexpected Japan catalogue license; refusing import")
    japan_products = japan_data.get("products", japan_data.get("records", []))
    if not isinstance(japan_products, list):
        raise SystemExit("Invalid Japan catalogue products")

    candidates = []
    japan_candidates = 0
    for record in japan_products:
        row = build_review_row(record)
        if row:
            candidates.append(row)
            japan_candidates += 1

    shard_count = 0
    supplemental_japan_scope_records = 0
    supplemental_candidates = 0
    if not SHARDS.is_dir():
        raise SystemExit("Missing OFF supplemental shards; refusing partial import")

    for path in sorted(SHARDS.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("license") != "ODbL-1.0":
            raise SystemExit("Unexpected shard license; refusing import: " + path.name)
        records = payload.get("records")
        if not isinstance(records, list):
            raise SystemExit("Invalid shard records: " + path.name)
        shard_count += 1
        for record in records:
            if record.get("scope") == "japan_country_tag":
                supplemental_japan_scope_records += 1
            row = build_review_row(record, require_japan_scope=True)
            if row:
                candidates.append(row)
                supplemental_candidates += 1

    # Quarantine every duplicate barcode or source URL rather than choosing
    # one of multiple possibly different package/formula versions.
    barcode_counts = Counter(row["jan_code"] for row in candidates)
    duplicate_barcodes = {
        code for code, count in barcode_counts.items() if count > 1
    }
    candidates = [
        row for row in candidates if row["jan_code"] not in duplicate_barcodes
    ]
    url_counts = Counter(row["source_url"] for row in candidates)
    duplicate_urls = {
        url for url, count in url_counts.items() if count > 1
    }
    candidates = [
        row for row in candidates if row["source_url"] not in duplicate_urls
    ]

    stats = {
        "japan_catalogue_rows": len(japan_products),
        "japan_catalogue_candidates": japan_candidates,
        "supplemental_shards_scanned": shard_count,
        "supplemental_japan_country_tag_records": supplemental_japan_scope_records,
        "supplemental_japanese_ingredient_candidates": supplemental_candidates,
        "duplicate_barcodes_quarantined": len(duplicate_barcodes),
        "duplicate_source_urls_quarantined": len(duplicate_urls),
        "qualified_candidates_before_database_dedup": len(candidates),
    }
    return candidates, stats


def main():
    rows, stats = load_candidates()
    print(json.dumps(stats, ensure_ascii=False), flush=True)

    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise SystemExit("Missing JHC Supabase secrets; no import attempted")

    # Fail closed: read existing JAN identities before any write.
    existing = set()
    for table, column in (
        ("jhc_crawler_ingredient_staging", "jan_code"),
        ("halal_products", "jan_code"),
        ("jhc_floot_products", "barcode"),
        ("jhc_ingredient_research_queue", "jan_code"),
    ):
        offset = 0
        while True:
            params = urllib.parse.urlencode({
                "select": column,
                "order": column + ".asc",
                "limit": "1000",
                "offset": str(offset),
            })
            request = urllib.request.Request(
                url + "/rest/v1/" + table + "?" + params,
                headers={"apikey": key, "Authorization": "Bearer " + key},
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                page = json.load(response)
            if not isinstance(page, list):
                raise SystemExit("Invalid database response from " + table)
            existing.update(
                str(item[column]) for item in page if item.get(column)
            )
            if len(page) < 1000:
                break
            offset += 1000
        print(
            "Read existing identities from", table,
            "pages", offset // 1000 + 1, flush=True
        )

    rows = [row for row in rows if row["jan_code"] not in existing]
    print(json.dumps({
        "new_discovery_candidates_after_database_dedup": len(rows),
        "existing_unique_barcodes": len(existing),
    }), flush=True)

    confirmed = 0
    for start in range(0, len(rows), 100):
        payload = json.dumps(
            rows[start:start + 100], ensure_ascii=False
        ).encode("utf-8")
        request = urllib.request.Request(
            url + "/rest/v1/jhc_ingredient_research_queue"
            "?on_conflict=discovery_source,source_url",
            data=payload,
            method="POST",
            headers={
                "apikey": key,
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
                "Prefer": "resolution=ignore-duplicates,return=representation",
            },
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    if response.status not in (200, 201):
                        raise RuntimeError("Unexpected insert response")
                    inserted = json.load(response)
                    if not isinstance(inserted, list):
                        raise RuntimeError("No insert confirmation")
                    confirmed += len(inserted)
                break
            except (urllib.error.HTTPError, urllib.error.URLError):
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        if start % 2000 == 0:
            print("Confirmed inserted review-only rows:", confirmed, flush=True)

    print(json.dumps({
        "inserted_confirmed": confirmed,
        "status": "needs_review",
        "evidence_level": "discovery_only",
        "halal_certified": False,
        "source": "Open Food Facts ODbL 1.0",
        "collection_timestamp": "Supabase created_at default",
    }), flush=True)


if __name__ == "__main__":
    main()
