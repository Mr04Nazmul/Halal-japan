#!/usr/bin/env python3
"""Import Japanese product identities from Open Food Facts. No halal certification inference.
Data: Open Food Facts (ODbL 1.0); comply with attribution/share-alike.
"""
import json, os, pathlib, re, time, urllib.parse, urllib.request
OUT=pathlib.Path("data/openfoodfacts-japan.json")
TARGET=int(os.environ.get("TARGET_PRODUCTS","1200"))
MAX_PAGES=int(os.environ.get("MAX_PAGES","12"))
URL="https://world.openfoodfacts.org/api/v2/search"
FIELDS="code,product_name,product_name_ja,brands,ingredients_text_ja,ingredients_text,countries_tags,url,last_modified_t"
records={}
for page in range(1,MAX_PAGES+1):
    params=urllib.parse.urlencode({"countries_tags":"en:japan","fields":FIELDS,"page_size":100,"page":page})
    req=urllib.request.Request(URL+"?"+params,headers={"User-Agent":"JapanHalalChecker/1.0 (GitHub: Mr04Nazmul/Halal-japan)"})
    try:
        with urllib.request.urlopen(req,timeout=40) as r: data=json.load(r)
    except Exception as exc:
        print("API page unavailable",page,str(exc)); break
    products=data.get("products",[])
    if not products: break
    for p in products:
        code=str(p.get("code","")).strip()
        if not re.fullmatch(r"\\d{8}|\\d{13}",code): continue
        name=(p.get("product_name_ja") or p.get("product_name") or "").strip()
        if not name: continue
        if code in records: continue
        records[code]={"code":code,"product_name":name,"brands":p.get("brands") or "",
           "ingredients_text":p.get("ingredients_text_ja") or p.get("ingredients_text") or "",
           "_source":"Open Food Facts (community-maintained)","_sourceUrl":p.get("url") or "https://world.openfoodfacts.org/product/"+code,
           "_license":"ODbL-1.0","_halalVerified":False,"_ingredientsVerified":False,
           "_verificationStatus":"needs_review","_checkedVia":"community_database"}
        if len(records)>=TARGET: break
    print(f"page={page}, collected={len(records)}")
    if len(records)>=TARGET: break
    time.sleep(2)
if len(records)<TARGET:
    raise SystemExit(f"Only {len(records)} records fetched. Keeping existing file unchanged; target {TARGET}.")
OUT.parent.mkdir(exist_ok=True,parents=True)
OUT.write_text(json.dumps({"source":"Open Food Facts","license":"ODbL-1.0","license_url":"https://opendatacommons.org/licenses/odbl/1-0/",
"disclaimer":"Community product identities; not verified halal ratings. Ingredient data may be incomplete or outdated.",
"record_count":len(records),"products":list(records.values())},ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
print("Wrote",len(records),"products to",OUT)
