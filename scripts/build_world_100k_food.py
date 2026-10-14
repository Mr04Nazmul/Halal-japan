#!/usr/bin/env python3
"""Build a 100,000-product, source-attributed food catalogue.

Preserve the separate Japan-tagged products. Rank additional genuine Open Food
Facts records by evidence: Japan country tag, Japanese GS1 prefix (45/49; origin
NOT proof of Japan store availability), Japanese product name, then worldwide.
Global records are clearly labelled, NEVER advertised as Japan products.
Official Open Food Facts ODbL dump; never infer halal certification.
"""
import csv
import gzip
import io
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
JAPAN = ROOT / "data" / "openfoodfacts-japan.json"
DEST = ROOT / "data" / "world-food-shards"
INDEX = ROOT / "data" / "world-food-name-index.json"
MANIFEST = ROOT / "data" / "food-catalog-manifest.json"
SOURCE = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
TARGET = max(10000, min(int(os.getenv("FOOD_CATALOG_TARGET", "100000")), 100000))
AGENT = "JapanHalalChecker/1.0 (https://github.com/Mr04Nazmul/Halal-japan)"
csv.field_size_limit(25 * 1024 * 1024)


def valid(code):
    if not re.fullmatch(r"(?:\d{8}|\d{12,14})", code):
        return False
    digits = [int(x) for x in code]
    s = sum(x * (3 if i % 2 == 0 else 1)
            for i, x in enumerate(reversed(digits[:-1])))
    return (10 - s % 10) % 10 == digits[-1]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def main():
    base = json.loads(JAPAN.read_text(encoding="utf-8"))
    if base.get("license") != "ODbL-1.0":
        raise SystemExit("Japan research licensing not verified")
    japan = {str(p["code"]) for p in base.get("products", [])
             if p.get("code") and p.get("product_name")}
    need = TARGET - len(japan)
    if need <= 0:
        print(f"Already {len(japan)} Japan source records; no additional batch necessary")
        return
    tiers = [dict() for _ in range(4)]
    scanned = 0
    found = [0, 0, 0, 0]
    req = Request(SOURCE, headers={"User-Agent": AGENT})
    with urlopen(req, timeout=120) as response:
        with gzip.GzipFile(fileobj=response) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", errors="replace", newline="") as stream:
                reader = csv.reader(stream, delimiter="\t")
                names = next(reader)
                at = {name: i for i, name in enumerate(names)}
                needed = {"code", "product_name", "brands", "countries_tags", "ingredients_text"}
                if not needed.issubset(at):
                    raise SystemExit("Official Open Food Facts export schema changed")
                def cell(row, field):
                    idx = at.get(field)
                    return row[idx] if idx is not None and idx < len(row) else ""
                for row in reader:
                    scanned += 1
                    code = cell(row, "code").strip()
                    if code in japan or not valid(code):
                        continue
                    name_ja = cell(row, "product_name_ja").strip()
                    name = (name_ja or cell(row, "product_name").strip())[:180]
                    if not name:
                        continue
                    countries = set(x.strip() for x in cell(row, "countries_tags").split(","))
                    is_japan = "en:japan" in countries
                    japanese_prefix = len(code) == 13 and code[:2] in ("45", "49")
                    japanese_name = bool(name_ja) or bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", name))
                    tier = 0 if is_japan else 1 if japanese_prefix else 2 if japanese_name else 3
                    found[tier] += 1
                    if len(tiers[tier]) >= need or code in tiers[tier]:
                        continue
                    ingredient = (cell(row, "ingredients_text_ja") or
                                  cell(row, "ingredients_text")).strip()[:3000]
                    scope = ("japan_country_tag" if tier == 0 else
                             "japanese_barcode_prefix_only" if tier == 1 else
                             "japanese_name_only" if tier == 2 else "worldwide_only")
                    tiers[tier][code] = {
                        "code": code,
                        "product_name": name,
                        "brands": cell(row, "brands").strip()[:100],
                        "ingredients_text": ingredient,
                        "scope": scope,
                        "_source": "Open Food Facts (community-maintained)",
                        "_sourceUrl": "https://world.openfoodfacts.org/product/" + code,
                        "_license": "ODbL-1.0",
                        "_ingredientsVerified": False,
                        "_halalVerified": False,
                        "_verificationStatus": "needs_review",
                    }
                    if scanned % 350000 == 0:
                        print(f"scanned={scanned} priority_counts={[len(t) for t in tiers]}", flush=True)
    selected = {}
    counts = defaultdict(int)
    for tier in tiers:
        for code, record in tier.items():
            if len(selected) >= need:
                break
            if code in selected:
                continue
            selected[code] = record
            counts[record["scope"]] += 1
        if len(selected) >= need:
            break
    if len(japan) + len(selected) < TARGET:
        raise SystemExit(f"Only {len(japan)+len(selected)} distinct products found; do not misreport 100k")
    # 3 digit barcode-prefix shards keep camera scan fast: load ONE shard, not 100k products.
    grouped = defaultdict(list)
    name_idx = []
    for code, record in sorted(selected.items()):
        grouped[code[:3]].append(record)
        name_idx.append([code, record["product_name"], record["brands"], record["scope"]])
    DEST.mkdir(parents=True, exist_ok=True)
    for f in DEST.glob("*.json"):
        if f.stem not in grouped:
            f.unlink()
    for prefix, items in grouped.items():
        save(DEST / (prefix + ".json"), {
            "license": "ODbL-1.0",
            "scope": "Supplemental food products, not verified Japanese market",
            "records": items
        })
    save(INDEX, {"license": "ODbL-1.0", "fields": ["code", "product_name", "brands", "scope"], "records": name_idx})
    stats = {
        "target": TARGET,
        "total_unique_records": len(japan) + len(selected),
        "japan_original_records": len(japan),
        "additional_records": len(selected),
        "additional_scope_breakdown": dict(counts),
        "additional_with_ingredient_text": sum(bool(p["ingredients_text"]) for p in selected.values()),
        "source_export_rows_scanned": scanned,
        "source_candidates_by_tier": found,
        "barcode_shards": len(grouped),
        "source": "Open Food Facts",
        "license": "ODbL-1.0",
        "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
        "attribution": "Contains data from Open Food Facts (https://world.openfoodfacts.org). Licensed ODbL 1.0.",
        "caveat": "ONLY records with Japan country tag have the Japan-tag signal. Prefix 45/49 and Japanese-looking names are NOT proof that an item is sold in Japan. No halal certifications are inferred."
    }
    save(MANIFEST, stats)
    print(json.dumps(stats, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
