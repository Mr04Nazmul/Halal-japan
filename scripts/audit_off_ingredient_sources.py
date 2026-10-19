#!/usr/bin/env python3
"""Audit the original OFF CSV export for ingredient texts and ingredient-label photos.

This is a source audit, NOT ingredient verification or halal certification.
Rechecks every barcode in the 100k research catalogue against the source bulk
export, including alternate-language ingredient fields and label-photo links.
"""
import csv, gzip, io, json, os, re
from pathlib import Path
from collections import Counter, defaultdict
from urllib.request import urlopen, Request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data"
SOURCE="https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv.gz"
UA="JapanHalalChecker/1.0 (+https://github.com/Mr04Nazmul/Halal-japan)"
csv.field_size_limit(25*1024*1024)

def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")

def main():
    jp=json.loads((OUT/"openfoodfacts-japan.json").read_text(encoding="utf-8"))
    manifest=json.loads((OUT/"food-catalog-manifest.json").read_text(encoding="utf-8"))
    products={}
    for p in jp["products"]:
        products[str(p["code"])]={"scope":"japan_country_tag","has_text":bool((p.get("ingredients_text") or "").strip())}
    for file in sorted((OUT/"world-food-shards").glob("*.json")):
        j=json.loads(file.read_text(encoding="utf-8"))
        for p in j.get("records",[]):
            barcode=str(p["code"])
            if barcode in products:
                # Overlapping shards are expected; preserve the existing Japanese record.
                if not products[barcode]["has_text"] and (p.get("ingredients_text") or "").strip():
                    products[barcode]["has_text"]=True
                continue
            products[barcode]={"scope":p.get("scope") or "unknown","has_text":bool((p.get("ingredients_text") or "").strip())}
    if len(products)!=100000 or len(products)!=manifest.get("total_unique_records"):
        raise ValueError("Source audit aborted: expected exactly 100k unique barcodes")
    scopes=defaultdict(Counter)
    for p in products.values():
        st=scopes[p["scope"]]
        st["records"]+=1
        if p["has_text"]:st["existing_ingredient_text"]+=1
    matched=set()
    photo_leads=[]
    new_text_leads=[]
    bad_image_urls=0
    req=Request(SOURCE,headers={"User-Agent":UA})
    with urlopen(req,timeout=120) as response:
        with gzip.GzipFile(fileobj=response) as gz:
            with io.TextIOWrapper(gz,encoding="utf-8",errors="replace",newline="") as inp:
                reader=csv.reader(inp,delimiter="\t")
                header=next(reader)
                at={field:index for index,field in enumerate(header)}
                if not {"code","ingredients_text","image_ingredients_url"}.issubset(at):
                    raise ValueError("OFF data export lacks ingredient text / photo fields")
                alt=[s for s in header if re.fullmatch(r"ingredients_text_[a-z]{2}",s)]
                alt.sort(key=lambda s: (s!="ingredients_text_ja",s!="ingredients_text_en",s))
                def get(row,field):
                    i=at.get(field,-1)
                    return row[i].strip() if 0<=i<len(row) else ""
                for row in reader:
                    code=get(row,"code")
                    p=products.get(code)
                    if not p or code in matched:continue
                    matched.add(code)
                    st=scopes[p["scope"]]
                    st["source_match"]+=1
                    original=get(row,"ingredients_text")
                    typed=get(row,"ingredients_text_ja")
                    if original:st["source_main_text"]+=1
                    if typed:st["source_japanese_text"]+=1
                    if not p["has_text"]:
                        st["missing_existing_text"]+=1
                        candidate=original or typed
                        which="ingredients_text" if original else "ingredients_text_ja"
                        if not candidate:
                            for name in alt:
                                candidate=get(row,name)
                                if candidate:
                                    which=name
                                    break
                        if candidate:
                            st["recoverable_text_in_export"]+=1
                            if len(new_text_leads)<2500:
                                new_text_leads.append({
                                    "code":code,"scope":p["scope"],"field":which,
                                    "ingredients_text":candidate[:6000],
                                    "source_url":"https://world.openfoodfacts.org/product/"+code,
                                    "verified":False
                                })
                    image=get(row,"image_ingredients_url")
                    if image:
                        st["source_has_label_photo"]+=1
                        if not p["has_text"]:
                            st["missing_text_but_photo"]+=1
                            if image.startswith("https://") and (
                                ".openfoodfacts.org/" in image or "images.openfoodfacts.org/" in image
                            ):
                                if len(photo_leads)<7500:
                                    photo_leads.append({
                                        "code":code,"scope":p["scope"],
                                        "source_url":"https://world.openfoodfacts.org/product/"+code,
                                        "image_ingredients_url":image,
                                        "ocr_status":"not_run",
                                        "manufacturer_verified":False
                                    })
                            else:
                                bad_image_urls+=1
    priority={"japan_country_tag":0,"japanese_barcode_prefix_only":1,
              "japanese_name_only":2,"worldwide_only":3}
    photo_leads.sort(key=lambda p: (priority.get(p["scope"],5),p["code"]))
    new_text_leads.sort(key=lambda p: (priority.get(p["scope"],5),p["code"]))
    totals=Counter()
    for st in scopes.values():totals.update(st)
    report={
        "method":"Audited 100000 catalogue barcodes against the official Open Food Facts TSV/CSV bulk export",
        "source":SOURCE,"license":"ODbL-1.0",
        "disclaimer":"Community ingredient lists and photo URLs are not validated manufacturer declarations or halal certification.",
        "source_rows_matched":len(matched),
        "records_absent_from_new_export":len(products)-len(matched),
        "source_fields":{"ingredient_text":"ingredients_text","japanese_text":"ingredients_text_ja",
                         "alternate_ingredient_languages_scanned":alt,
                         "ingredient_label_photo":"image_ingredients_url"},
        "totals":dict(totals),
        "scope_counts":{k:dict(v) for k,v in sorted(scopes.items())},
        "photo_leads_saved":len(photo_leads),
        "alternate_ingredient_text_leads_saved":len(new_text_leads),
        "photo_lead_url_errors":bad_image_urls
    }
    save("ingredient-source-audit.json",report)
    save("ingredient-photo-leads.json",{"license":"ODbL-1.0","note":"Label photo leads from OFF, not yet OCR verified","records":photo_leads})
    save("ingredient-text-recovery-leads.json",{"license":"ODbL-1.0","note":"Alternate-language text leads from OFF; requires verification","records":new_text_leads})
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)

if __name__=="__main__":
    main()
