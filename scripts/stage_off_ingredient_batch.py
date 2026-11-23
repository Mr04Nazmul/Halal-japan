#!/usr/bin/env python3
"""Import only a large, deduplicated OFF batch into a review-only queue.

This never writes halal_products/product_ingredients or changes halal status.
Duplicates are ignored, not merged, so existing review decisions are preserved.
"""
import json
import os
import urllib.request
from pathlib import Path

from import_off_japan_ingredients import (
    OFF_PRODUCT,
    SOURCE_ATTRIBUTION,
    SOURCE_LICENSE,
    VERIFICATION_STATUS,
    is_japanese_ingredient_candidate,
)

MIN_QUALIFIED = 1000
BATCH_SIZE = 100
CANDIDATE_FILE = Path("data/off_japan_ingredient_candidates.jsonl")


def load_candidates(path=CANDIDATE_FILE):
    if not path.exists():
        return {}
    data = {}
    for line in path.read_text(encoding="utf8").splitlines():
        try:
            row = json.loads(line)
            barcode = str(row.get("barcode") or "").strip()
            name = str(row.get("name") or "").strip()
            ingredients = str(row.get("ingredients") or "").strip()
            source_url = str(row.get("source_url") or "").strip()
            collected_at = str(row.get("collected_at") or "").strip()
            if not is_japanese_ingredient_candidate(barcode, name, ingredients):
                continue
            if source_url != OFF_PRODUCT + barcode:
                continue
            if row.get("source") != "Open Food Facts":
                continue
            if row.get("source_license") != SOURCE_LICENSE:
                continue
            if row.get("source_attribution") != SOURCE_ATTRIBUTION:
                continue
            if row.get("verification_status") != VERIFICATION_STATUS:
                continue
            if row.get("halal_certified") is not False or not collected_at:
                continue
            data.setdefault(barcode, row)
        except (ValueError, TypeError, AttributeError):
            continue
    return data


def to_queue_row(row):
    return {
        "jan_code": row["barcode"],
        "product_name": row["name"],
        "manufacturer": row.get("brand"),
        "discovery_source": "Open Food Facts",
        "source_url": row["source_url"],
        "ingredients_text": row["ingredients"],
        "evidence_level": "third_party_unverified_odbl_dbcl_pending_review",
        "status": "needs_review",
        "collected_at": row["collected_at"],
        "verification_status": VERIFICATION_STATUS,
        "source_license": SOURCE_LICENSE,
        "source_attribution": SOURCE_ATTRIBUTION,
        "halal_certified": False,
    }


def post_batch(url, key, rows, opener=urllib.request.urlopen):
    payload = json.dumps(rows, ensure_ascii=False).encode("utf8")
    request = urllib.request.Request(
        url + "/rest/v1/jhc_ingredient_research_queue?on_conflict=discovery_source,source_url",
        data=payload,
        method="POST",
        headers={
            "apikey": key,
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
            "Prefer": "resolution=ignore-duplicates,return=representation",
        },
    )
    with opener(request, timeout=60) as response:
        body = response.read().decode("utf8")
    if not body.strip():
        return 0
    result = json.loads(body)
    return len(result) if isinstance(result, list) else 0


def main():
    data = load_candidates()
    print(f"Valid distinct licensed Japanese ingredient candidates: {len(data)}", flush=True)
    if len(data) < MIN_QUALIFIED:
        print(f"Threshold not reached ({len(data)}/{MIN_QUALIFIED}); skip database import", flush=True)
        return 0
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise SystemExit("Missing Supabase secrets; not importing")
    rows = [to_queue_row(row) for row in data.values()]
    inserted = 0
    for start in range(0, len(rows), BATCH_SIZE):
        inserted += post_batch(url, key, rows[start:start + BATCH_SIZE])
        print(f"Processed staging batch {start // BATCH_SIZE + 1}; confirmed new rows so far: {inserted}", flush=True)
    print(f"New unique rows inserted into needs_review queue: {inserted}", flush=True)
    print("No halal classification or certification was made.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
