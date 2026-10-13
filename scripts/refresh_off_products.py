#!/usr/bin/env python3
"""Ingest attributed community product records from Open Food Facts, safely.
Does not infer halal certification or replace manufacturer data.
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEST = Path("data/auto-products.json")
API = "https://world.openfoodfacts.org/cgi/search.pl"
FIELDS = "code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,ingredients_text_en,ingredients_text_with_allergens,labels_tags,states_tags,link"
params = {
    "action": "process", "json": "1", "search_simple": "1",
    "tagtype_0": "countries", "tag_contains_0": "contains",
    "tag_0": "japan", "page_size": "100", "page": "1",
    "fields": FIELDS,
}
url = API + "?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={
    "User-Agent": "JapanHalalCheckerResearch/1.0 (public ingredient research; github.com/Mr04Nazmul/Halal-japan)",
    "Accept": "application/json",
})
with urllib.request.urlopen(req, timeout=40) as response:
    payload = json.load(response)
products = []
seen = set()
for p in payload.get("products", []):
    jan = str(p.get("code") or "").strip()
    name = str(p.get("product_name_ja") or p.get("product_name") or "").strip()
    ingredients = str(p.get("ingredients_text_ja") or p.get("ingredients_text") or p.get("ingredients_text_en") or "").strip()
    if not (jan.isdigit() and 8 <= len(jan) <= 14 and name and ingredients) or jan in seen:
        continue
    seen.add(jan)
    products.append({
        "jan": jan, "name": name, "brand": str(p.get("brands") or ""),
        "ingredients": ingredients[:8000],
        "source": "https://world.openfoodfacts.org/product/" + jan,
        "sourceType": "community_openfoodfacts",
        "verificationStatus": "unverified_community_data",
        "halalCertification": None,
        "halalStatus": "verification_required",
        "license": "Open Database License (ODbL) - Open Food Facts",
    })
if not products:
    raise SystemExit("No eligible products returned; leaving existing data untouched")
out = {
    "schemaVersion": 1,
    "description": "Automatically refreshed Open Food Facts community records. No halal/haram certification or definitive decision.",
    "source": "Open Food Facts", "sourceUrl": "https://world.openfoodfacts.org/",
    "license": "ODbL", "attribution": "Data © Open Food Facts contributors",
    "retrievedAt": datetime.now(timezone.utc).isoformat(),
    "recordCount": len(products), "records": products,
}
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(products)} community records to {DEST}")
