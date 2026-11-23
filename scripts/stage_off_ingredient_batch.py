#!/usr/bin/env python3
"""Import Open Food Facts records into the review-only ingredient queue.

OFF data is community-contributed, licensed under ODbL/DbCL, and is never
manufacturer-verified by this importer. Records stay discovery_only/needs_review.
Existing review decisions are never overwritten on duplicate source URLs.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

INPUT = Path("data/off_japan_ingredient_candidates.jsonl")
OFF_LICENSE_SOURCE = "Open Food Facts (database: ODbL-1.0; content: DbCL-1.0)"


def valid_ean(code):
    if not re.fullmatch(r"(?:[0-9]{8}|[0-9]{13})", str(code or "")):
        return False
    digits = [int(char) for char in code]
    check_digit = digits.pop()
    weighted_sum = sum(
        digit * (3 if index % 2 == 0 else 1)
        for index, digit in enumerate(reversed(digits))
    )
    return (10 - weighted_sum % 10) % 10 == check_digit


def build_rows(lines):
    """Build unique, attribution-labelled review rows from OFF JSONL lines."""
    data = {}
    for line in lines:
        try:
            record = json.loads(line)
            barcode = str(record.get("barcode") or "").strip()
            ingredients = str(record.get("ingredients") or "").strip()
            name = str(record.get("name") or "").strip()
            source_url = str(record.get("source_url") or "").strip()
            parsed = urlparse(source_url)
            expected_path = f"/product/{barcode}"
            if (
                not valid_ean(barcode)
                or len(name) < 2
                or len(ingredients) < 8
                or not re.search(r"[\u3040-\u30ff\u3400-\u9fff]", name)
                or not re.search(r"[\u3040-\u30ff\u3400-\u9fff]", ingredients)
                or parsed.scheme != "https"
                or parsed.netloc != "world.openfoodfacts.org"
                or parsed.path.rstrip("/") != expected_path
                or parsed.query
                or parsed.fragment
            ):
                continue
            data[barcode] = {
                "jan_code": barcode,
                "product_name": name,
                "manufacturer": record.get("brand"),
                "discovery_source": OFF_LICENSE_SOURCE,
                "source_url": source_url,
                "ingredients_text": ingredients,
                "evidence_level": "discovery_only",
                "status": "needs_review",
            }
        except (ValueError, TypeError):
            continue
    return list(data.values())


def import_rows(rows, base_url, service_key, opener=None):
    """Insert only new source URLs; never update existing review decisions."""
    opener = opener or urllib.request.urlopen
    inserted_total = 0
    for start in range(0, len(rows), 100):
        batch = rows[start:start + 100]
        payload = json.dumps(batch, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            base_url.rstrip("/") + "/rest/v1/jhc_ingredient_research_queue"
            "?on_conflict=discovery_source,source_url",
            data=payload,
            method="POST",
            headers={
                "apikey": service_key,
                "Authorization": "Bearer " + service_key,
                "Content-Type": "application/json",
                "Prefer": "resolution=ignore-duplicates,return=representation",
            },
        )
        try:
            with opener(request, timeout=60) as response:
                raw = response.read()
                returned = json.loads(raw) if raw else []
                if not isinstance(returned, list):
                    raise RuntimeError("Unexpected Supabase insert response")
                inserted = len(returned)
                inserted_total += inserted
                print(
                    f"Batch {start // 100 + 1}: attempted {len(batch)}, "
                    f"new inserts {inserted}; existing rows left unchanged",
                    flush=True,
                )
        except urllib.error.HTTPError as error:
            detail = error.read(300).decode(errors="replace")
            raise RuntimeError(f"Import failed HTTP {error.code}: {detail}") from error
    return inserted_total


def main():
    if not INPUT.exists():
        print("No ingredient candidate file; no import")
        return 0

    rows = build_rows(INPUT.read_text(encoding="utf-8").splitlines())
    print(f"Valid distinct OFF candidates: {len(rows)}", flush=True)
    if len(rows) < 1000:
        print("Threshold not reached: skip database import")
        return 0

    base_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not base_url or not service_key:
        raise RuntimeError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY; not importing"
        )

    inserted = import_rows(rows, base_url, service_key)
    print(
        f"Review-queue import complete: {inserted} new rows; "
        f"{len(rows) - inserted} existing source URLs skipped. "
        "All rows remain discovery_only/needs_review; no halal classification."
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
