#!/usr/bin/env python3
"""Stage unique Japan-market Open Food Facts ingredient records for human review only.

Uses ODbL-sourced records, never infers halal status or imports into approved product tables.
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
source = ROOT / "openfoodfacts-japan.json"
if not source.is_file() or source.stat().st_size == 0:
    raise SystemExit("Missing Japan-only OFF catalogue; refusing import")
data = json.loads(source.read_text(encoding="utf-8"))
if data.get("license") != "ODbL-1.0":
    raise SystemExit("Unexpected source license; refusing import")
products = data.get("products", data.get("records", []))
if not isinstance(products, list):
    raise SystemExit("Invalid source products")

def valid_jan13(code):
    if not re.fullmatch(r"[0-9]{13}", code):
        return False
    digits = [int(c) for c in code]
    total = sum(n * (3 if i % 2 == 0 else 1) for i, n in enumerate(reversed(digits[:12])))
    return (10 - total % 10) % 10 == digits[-1]

jp_chars = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
counts = Counter(str(r.get("code", "")) for r in products)
rows = []
for r in products:
    code = str(r.get("code", ""))
    name = str(r.get("product_name") or r.get("name") or "").strip()
    ing = str(r.get("ingredients_text") or "").strip()
    if counts[code] != 1 or not valid_jan13(code) or not name or not ing:
        continue
    if not jp_chars.search(name) or not jp_chars.search(ing):
        continue
    if ing.lower() in ("unknown", "n/a", "none", "no data", "ingredients", "?", "-"):
        continue
    rows.append({
        "jan_code": code,
        "product_name": name[:500],
        "manufacturer": str(r.get("brands") or "")[:500] or None,
        "discovery_source": "Open Food Facts catalogue",
        "source_url": "https://world.openfoodfacts.org/product/" + code,
        "ingredients_text": ing[:6000],
        "evidence_level": "discovery_only",
        "status": "needs_review",
    })
print(json.dumps({"japan_catalogue_rows": len(products), "japanese_ingredient_candidates": len(rows),
                  "duplicate_barcodes_quarantined": sum(v > 1 for v in counts.values())}), flush=True)

url = os.environ.get("SUPABASE_URL", "").rstrip("/")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
if not url or not key:
    raise SystemExit("Missing JHC Supabase secrets; no import attempted")

# Fail closed: read all existing barcodes from each product/research table before writing.
existing = set()
for table, col in (("jhc_crawler_ingredient_staging", "jan_code"),
                   ("halal_products", "jan_code"),
                   ("jhc_floot_products", "barcode"),
                   ("jhc_ingredient_research_queue", "jan_code")):
    offset = 0
    while True:
        params = urllib.parse.urlencode({"select": col, "order": col + ".asc",
                                         "limit": "1000", "offset": str(offset)})
        req = urllib.request.Request(url + "/rest/v1/" + table + "?" + params,
                                     headers={"apikey": key, "Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=90) as response:
            page = json.load(response)
        if not isinstance(page, list):
            raise SystemExit("Invalid database response from " + table)
        existing.update(str(item[col]) for item in page if item.get(col))
        if len(page) < 1000:
            break
        offset += 1000
    print("Read existing identities from", table, "pages", offset // 1000 + 1, flush=True)
rows = [r for r in rows if r["jan_code"] not in existing]
print(json.dumps({"new_discovery_candidates_after_dedup": len(rows),
                  "existing_unique_barcodes": len(existing)}), flush=True)

confirmed = 0
for start in range(0, len(rows), 100):
    payload = json.dumps(rows[start:start + 100], ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url + "/rest/v1/jhc_ingredient_research_queue?on_conflict=discovery_source,source_url",
        data=payload, method="POST",
        headers={"apikey": key, "Authorization": "Bearer " + key,
                 "Content-Type": "application/json",
                 "Prefer": "resolution=ignore-duplicates,return=representation"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
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
print(json.dumps({"inserted_confirmed": confirmed, "status": "needs_review",
                  "evidence_level": "discovery_only", "halal_certified": False,
                  "source": "Open Food Facts ODbL 1.0"}), flush=True)
