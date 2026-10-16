#!/usr/bin/env python3
"""Turn licensed Kaggle/Open Food Facts CSV exports into Japan-only ingredient evidence.
No halal certification is inferred and no existing Supabase rows are overwritten.
Usage: python scripts/import_kaggle_japan_food.py /path/to/export.csv
"""
import csv, gzip, json, sys
from pathlib import Path

if len(sys.argv)<2: raise SystemExit("Usage: import_kaggle_japan_food.py INPUT.csv[.gz]")
src=Path(sys.argv[1])
out=Path("data/kaggle_japan_ingredient_candidates.csv")
out.parent.mkdir(parents=True,exist_ok=True)
def op(p): return gzip.open(p,"rt",encoding="utf-8",errors="replace",newline="") if str(p).endswith(".gz") else p.open(encoding="utf-8",errors="replace",newline="")
def get(row,*names):
    for n in names:
        if row.get(n) and row[n].strip(): return row[n].strip()
    return ""
def japan(row):
    tags=(get(row,"countries_tags","countries","country","country_tags")+" "+get(row,"code","barcode","ean","jan")).lower()
    return any(t in tags for t in ("en:japan","日本","japan")) # Barcode prefix alone cannot prove sale in Japan
columns=["barcode","product_name","brand","ingredients_ja","ingredients_en","ingredients_raw","source","source_url","verification"]
seen=set(); total=0; written=0
with op(src) as fi, out.open("w",encoding="utf-8",newline="") as fo:
    reader=csv.DictReader(fi,delimiter="\t" if src.name.endswith(".tsv") else ",")
    writer=csv.DictWriter(fo,fieldnames=columns);writer.writeheader()
    for row in reader:
        total+=1
        if not japan(row): continue
        barcode=get(row,"code","barcode","ean","jan")
        if not barcode.isdigit() or len(barcode) not in (8,12,13,14) or barcode in seen: continue
        ja=get(row,"ingredients_text_ja")
        en=get(row,"ingredients_text_en")
        raw=get(row,"ingredients_text","ingredients")
        if not (ja or en or raw):continue
        seen.add(barcode)
        writer.writerow({"barcode":barcode,"product_name":get(row,"product_name_ja","product_name","product_name_en","name"),
          "brand":get(row,"brands","brand"),"ingredients_ja":ja,"ingredients_en":en,"ingredients_raw":raw,
          "source":"Open Food Facts via Kaggle CSV","source_url":"https://world.openfoodfacts.org/product/"+barcode,
          "verification":"unverified_source_data"})
        written+=1
print(json.dumps({"source_rows":total,"japan_unique_products_with_ingredients":written,"output":str(out)}))
