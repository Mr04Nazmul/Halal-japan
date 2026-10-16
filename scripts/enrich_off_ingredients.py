#!/usr/bin/env python3
"""Recover missing ingredients by EXACT barcode from OFF's ODbL bulk dataset.

No scraping of private sources; never replace an existing label, guess a JAN,
claim manufacturer verification, or claim halal certification.
"""
import csv
import gzip
import io
import json
import os
import re
from pathlib import Path
from datetime import date
from collections import Counter
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
SOURCE="https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
UA="JapanHalalChecker/1.0 (+https://github.com/Mr04Nazmul/Halal-japan)"
csv.field_size_limit(25*1024*1024)

def save(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    tmp.replace(path)

def usable(t):
    s=str(t or "").strip()
    return "" if s.lower() in ("","unknown","n/a","none","ingredients","no data","?","-") else s[:6000]

def run(root=ROOT, export_gzip=None):
    d=root/"data"
    jpfile=d/"openfoodfacts-japan.json"
    manfile=d/"food-catalog-manifest.json"
    jp=json.loads(jpfile.read_text(encoding="utf-8"))
    manifest=json.loads(manfile.read_text(encoding="utf-8"))
    if jp.get("license")!="ODbL-1.0" or manifest.get("license")!="ODbL-1.0":
        raise ValueError("Expected Open Food Facts ODbL-1.0 inputs")
    groups=[(jpfile,jp,jp["products"])]
    for file in sorted((d/"world-food-shards").glob("*.json")):
        payload=json.loads(file.read_text(encoding="utf-8"))
        if payload.get("license")!="ODbL-1.0":raise ValueError("Incorrect shard license")
        groups.append((file,payload,payload["records"]))
    seen=set()
    duplicates=set()
    missing={}
    before=0
    entries=0
    for filename,_,products in groups:
        for p in products:
            code=str(p.get("code",""))
            if not re.fullmatch(r"(?:\d{8}|\d{12,14})",code):
                raise ValueError("Invalid barcode: "+code)
            entries+=1
            if code in seen:
                # Older catalogue can have duplicate records for a barcode.
                # Do NOT enrich either duplicate: product version is ambiguous.
                duplicates.add(code)
                missing.pop(code,None)
            else:
                seen.add(code)
                if not usable(p.get("ingredients_text")) and code not in duplicates:
                    missing[code]=(filename,p)
            if usable(p.get("ingredients_text")):before+=1
    if entries!=manifest["total_unique_records"] or len(jp["products"])!=manifest["japan_original_records"]:
        raise ValueError("Catalogue inventory and manifest disagree; no changes made")
    if duplicates:
        print("WARNING: quarantined duplicated catalogue barcodes:",len(duplicates),
              "example:",next(iter(sorted(duplicates))),flush=True)
    updated=set()
    added=Counter()
    scanned=0
    source_path=export_gzip or os.getenv("OFF_EXPORT_FILE")
    response=open(source_path,"rb") if source_path else urlopen(Request(SOURCE,headers={"User-Agent":UA}),timeout=120)
    with response as stream,gzip.GzipFile(fileobj=stream) as gz:
        with io.TextIOWrapper(gz,encoding="utf-8",errors="replace",newline="") as txt:
            reader=csv.reader(txt,delimiter="\t")
            header=next(reader)
            cols={name:i for i,name in enumerate(header)}
            if not {"code","ingredients_text"}.issubset(cols):raise ValueError("OFF export missing fields")
            fields=[x for x in ("ingredients_text_ja","ingredients_text","ingredients_text_en") if x in cols]
            fields.extend(sorted(x for x in cols if re.fullmatch(r"ingredients_text_[a-z]{2}",x) and x not in fields))
            for row in reader:
                scanned+=1
                code=row[cols["code"]] if len(row)>cols["code"] else ""
                if code not in missing:continue
                field,ingredient=next(((x,usable(row[cols[x]])) for x in fields if len(row)>cols[x] and usable(row[cols[x]])),(None,""))
                if not ingredient:continue
                filename,p=missing.pop(code)
                p["ingredients_text"]=ingredient
                p["_ingredientSourceField"]=field
                p["_ingredientSource"]="Open Food Facts official export (community-contributed)"
                p["_ingredientTextRecoveredOn"]=date.today().isoformat()
                p["_ingredientsVerified"]=False
                p["_halalVerified"]=False
                p["_verificationStatus"]="needs_review"
                updated.add(filename)
                added["japan" if filename==jpfile else "supplemental"]+=1
                if scanned%500000==0:print("scanned",scanned,"new texts",sum(added.values()),flush=True)
    totals=Counter()
    for filename,payload,products in groups:
        for p in products:
            if usable(p.get("ingredients_text")):totals["japan" if filename==jpfile else "supplemental"]+=1
        if filename in updated:save(filename,payload)
    after=sum(totals.values())
    if after!=before+sum(added.values()):raise ValueError("Counts inconsistent")
    jp["ingredient_text_count"]=totals["japan"]
    if jpfile in updated:save(jpfile,jp)
    manifest.update({
        "additional_with_ingredient_text":totals["supplemental"],
        "japan_with_ingredient_text":totals["japan"],
        "all_with_ingredient_text":after,
        "ingredient_enrichment_last_run":date.today().isoformat(),
        "ingredient_enrichment_distinct_barcodes":len(seen),
        "ingredient_enrichment_duplicate_entries_quarantined":entries-len(seen),
        "ingredient_enrichment_source":SOURCE,
        "ingredient_enrichment_scope":"OFF community text only; neither halal nor manufacturer confirmation"
    })
    save(manfile,manifest)
    report={
        "date":date.today().isoformat(),"source":SOURCE,"license":"ODbL-1.0",
        "rows_scanned":scanned,"catalogue_total":entries,
        "catalogue_distinct_barcodes":len(seen),
        "duplicate_barcode_groups_quarantined":len(duplicates),
        "duplicate_entries":entries-len(seen),
        "with_ingredient_text_before":before,
        "new_japan_texts":added["japan"],
        "new_supplemental_texts":added["supplemental"],
        "new_ingredient_texts":sum(added.values()),
        "with_ingredient_text_after":after,
        "japan_with_ingredient_text_after":totals["japan"],
        "supplemental_with_ingredient_text_after":totals["supplemental"],
        "modified_files":len(updated),
        "note":"OFF user-contributed data, exact barcode only, not proof of complete label, halal status or Japanese store availability"
    }
    save(root/"docs"/"ingredient-enrichment-report.json",report)
    print(json.dumps(report,indent=2,ensure_ascii=False),flush=True)
    return report

if __name__=="__main__":
    run()
