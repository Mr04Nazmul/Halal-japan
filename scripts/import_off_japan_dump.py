#!/usr/bin/env python3
"""Build a Japan-tagged Open Food Facts product snapshot from the official bulk export.

OFF asks projects fetching > a few hundred products to use CSV/JSONL exports,
not paginated search API. No inferred halal certifications or ingredient origins.
Official export: https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz
ODbL 1.0; attribute and share derived OFF database according to its license.
"""
import csv
import gzip
import io
import json
import os
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "openfoodfacts-japan.json"
SOURCE = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
TARGET = max(1, min(int(os.environ.get("TARGET_PRODUCTS", "10000")), 100000))
USER_AGENT = "JapanHalalChecker/1.0 (https://github.com/Mr04Nazmul/Halal-japan)"
csv.field_size_limit(25 * 1024 * 1024)


def valid_barcode(code):
    if not re.fullmatch(r"(?:\d{8}|\d{12,14})", code):
        return False
    digits = [int(x) for x in code]
    checksum = sum(n * (3 if i % 2 == 0 else 1)
                   for i, n in enumerate(reversed(digits[:-1])))
    return (10 - checksum % 10) % 10 == digits[-1]


def existing_products():
    if not OUT.exists():
        return {}
    old = json.loads(OUT.read_text(encoding="utf-8"))
    return {str(p["code"]): p for p in old.get("products", [])
            if isinstance(p, dict) and p.get("code")}


def collect():
    products = existing_products()
    initial = len(products)
    examined = 0
    matches = 0
    headers = None
    # Response body is decompressed as a stream; no multi-GB temporary files.
    req = Request(SOURCE, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=120) as response:
            with gzip.GzipFile(fileobj=response) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", errors="replace",
                                      newline="") as text:
                    reader = csv.reader(text, delimiter="\t")
                    headers = next(reader)
                    required = ["code", "product_name", "brands", "countries_tags",
                                "ingredients_text", "last_modified_t"]
                    index = {name: headers.index(name) for name in required}
                    for row in reader:
                        examined += 1
                        if examined % 150000 == 0:
                            print(f"examined={examined} Japan_matches={matches} accepted={len(products)}", flush=True)
                        if len(row) <= max(index.values()):
                            continue
                        countries = set(row[index["countries_tags"]].split(","))
                        if "en:japan" not in countries:
                            continue
                        matches += 1
                        code = row[index["code"]].strip()
                        name = row[index["product_name"]].strip()
                        if not valid_barcode(code) or not name:
                            continue
                        ingredient = row[index["ingredients_text"]].strip()
                        prev = products.get(code)
                        if prev and (prev.get("_ingredientsVerified") or prev.get("_halalVerified")):
                            continue
                        products[code] = {
                            "code": code,
                            "product_name": name[:200],
                            "brands": row[index["brands"]][:160],
                            "ingredients_text": ingredient[:6000],
                            "last_modified_t": row[index["last_modified_t"]],
                            "_source": "Open Food Facts (community-maintained)",
                            "_sourceUrl": "https://world.openfoodfacts.org/product/" + code,
                            "_license": "ODbL-1.0",
                            "_halalVerified": False,
                            "_ingredientsVerified": False,
                            "_verificationStatus": "needs_review",
                            "_checkedVia": "community_database"
                        }
                        if len(products) >= TARGET:
                            break
    except Exception as exc:
        print(f"::warning::Official bulk export failed: {type(exc).__name__}: {exc}", flush=True)
        if len(products) == initial:
            raise SystemExit("No new products imported; previous database unchanged")

    if len(products) < initial:
        raise SystemExit("Refusing to shrink database")
    if not products:
        raise SystemExit("No qualifying Japan-tagged product records")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "source": "Open Food Facts",
        "license": "ODbL-1.0",
        "license_url": "https://opendatacommons.org/licenses/odbl/1-0/",
        "attribution": "Contains data from Open Food Facts (https://world.openfoodfacts.org), ODbL 1.0.",
        "scope": "en:japan country tag; not proof of Japanese store availability",
        "disclaimer": "Community ingredients may be incorrect or missing. No product classified as certified halal.",
        "target": TARGET,
        "record_count": len(products),
        "ingredient_text_count": sum(bool(p.get("ingredients_text")) for p in products.values()),
        "products": sorted(products.values(), key=lambda p: p["code"]),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({
        "examined": examined, "country_matches": matches,
        "previous": initial, "saved": len(products),
        "ingredient_text_count": data["ingredient_text_count"],
        "target_reached": len(products) >= TARGET,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    collect()
