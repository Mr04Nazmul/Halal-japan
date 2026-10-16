#!/usr/bin/env python3
"""Collect Japanese food product records with provenance; never infer halal certification."""
import csv, json, os, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path

BASE = "https://world.openfoodfacts.org/api/v2/search"
FIELDS = "code,product_name,brands,ingredients_text,ingredients_text_ja,ingredients_text_en,labels_tags,ingredients_analysis_tags,url,last_modified_t"
OUT = Path("data/japan_ingredients.csv")
STATE = Path("data/japan_ingredients_state.json")
HEADERS = {"User-Agent": "JapanHalalCheckerCollector/1.0 (https://github.com/Mr04Nazmul/Halal-japan; research contact via GitHub issues)", "Accept": "application/json"}
MAX = min(int(os.environ.get("MAX_PAGES", "30")), 1000)
START = max(1,int(os.environ.get("START_PAGE","1")))
OUT.parent.mkdir(parents=True,exist_ok=True)
keys = ["barcode","product_name","brand","ingredients_ja","ingredients_en","ingredients_raw","source","source_url","labels","analysis_tags","last_modified","verification"]
seen = set()
if OUT.exists():
    with OUT.open(encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            if row.get("barcode"): seen.add(row["barcode"])
written=0; pages=0; errors=[]
with OUT.open("a",encoding="utf-8",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=keys)
    if f.tell()==0: writer.writeheader()
    for page in range(START,START+MAX):
        query=urllib.parse.urlencode({"countries_tags":"en:japan","page":page,"page_size":100,"fields":FIELDS,"sort_by":"nothing"})
        req=urllib.request.Request(BASE+"?"+query,headers=HEADERS)
        payload=None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req,timeout=45) as response:
                    payload=json.load(response)
                break
            except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as exc:
                print(f'ERROR page={page} attempt={attempt+1}: {exc}',flush=True)
                if attempt<2: time.sleep(30*(attempt+1))
        if payload is None:
            errors.append({'page':page,'error':'upstream_unavailable'})
            print('STOP: source unavailable; next scheduled run will retry',flush=True)
            break
        products=payload.get("products",[])
        if not products: break
        for p in products:
            code=str(p.get("code") or "").strip()
            ja=p.get("ingredients_text_ja") or ""
            en=p.get("ingredients_text_en") or ""
            raw=p.get("ingredients_text") or ""
            if not code or code in seen or not (ja or en or raw): continue
            writer.writerow({"barcode":code,"product_name":p.get("product_name",""),"brand":p.get("brands",""),"ingredients_ja":ja,"ingredients_en":en,"ingredients_raw":raw,"source":"Open Food Facts","source_url":p.get("url") or "https://world.openfoodfacts.org/product/"+code,"labels":json.dumps(p.get("labels_tags",[]),ensure_ascii=False),"analysis_tags":json.dumps(p.get("ingredients_analysis_tags",[]),ensure_ascii=False),"last_modified":p.get("last_modified_t",""),"verification":"unverified_source_data"})
            seen.add(code);written+=1
        f.flush();pages+=1
        STATE.write_text(json.dumps({"last_page":page,"pages_this_run":pages,"new_ingredient_products":written,"unique_csv_rows":len(seen),"errors":errors},indent=2))
        print(f"page={page} new={written} total={len(seen)}",flush=True)
        time.sleep(7)
STATE.write_text(json.dumps({"last_page_processed":START+pages-1,"pages_this_run":pages,"new_ingredient_products":written,"unique_csv_rows":len(seen),"errors":errors,"status":"source_unavailable" if errors else "completed"},indent=2))
print(f"Done: {written} new ingredient-bearing records; {len(seen)} total; errors={len(errors)}")
