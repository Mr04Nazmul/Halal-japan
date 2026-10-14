#!/usr/bin/env python3
"""Collect Japan-tagged Open Food Facts records into a source-attributed research batch.
This does not certify halal status or claim current availability in stores.
"""
import json, os, pathlib, re, time, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/"data"/"off-japan-research.json"
FIELDS="code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,countries_tags,quantity,last_modified_t"
USER_AGENT="JapanHalalChecker/1.0 (public-data-research; github.com/Mr04Nazmul/Halal-japan)"
def valid(code):
    if not re.fullmatch(r"(?:[0-9]{8}|[0-9]{12}|[0-9]{13}|[0-9]{14})",code):return False
    ds=[int(c) for c in code]
    return (10-sum(d*(3 if i%2==0 else 1) for i,d in enumerate(reversed(ds[:-1])))%10)%10==ds[-1]
def get(page):
    params=urllib.parse.urlencode({"countries_tags":"en:japan","page_size":100,"page":page,
        "fields":FIELDS,"sort_by":"last_modified_t"})
    req=urllib.request.Request("https://world.openfoodfacts.org/api/v2/search?"+params,
       headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as response:
        if response.status != 200: raise RuntimeError("Unexpected HTTP status")
        return json.load(response)
def main():
    pages=max(1,min(3,int(os.environ.get("OFF_PAGES","2"))))
    previous={"records":[]}
    if OUT.exists():previous=json.loads(OUT.read_text(encoding="utf-8"))
    records={str(p["code"]):p for p in previous.get("records",[]) if p.get("code")}
    added=changed=seen=0
    for page in range(1,pages+1):
        data=get(page)
        if not isinstance(data.get("products"),list):raise RuntimeError("Unexpected OFF schema")
        for p in data["products"]:
            seen+=1
            code=str(p.get("code") or "").strip()
            tag=p.get("countries_tags") or []
            if isinstance(tag,str):tag=[s.strip() for s in tag.split(",")]
            if not valid(code) or "en:japan" not in tag:continue
            name=str(p.get("product_name_ja") or p.get("product_name") or "").strip()
            if not name:continue
            item={"code":code,"product_name":name[:200],"brands":str(p.get("brands") or "")[:160],
                "quantity":str(p.get("quantity") or "")[:80],
                "ingredients_text":str(p.get("ingredients_text_ja") or p.get("ingredients_text") or "")[:6000],
                "country_tag":"en:japan","last_modified_t":p.get("last_modified_t"),
                "source":"Open Food Facts","source_url":"https://world.openfoodfacts.org/product/"+code,
                "license":"ODbL-1.0","halal_verified":False,"review_status":"needs_verification"}
            if code not in records:added+=1
            elif records[code]!=item:changed+=1
            records[code]=item
        if page<pages:time.sleep(2)
    if not seen:raise RuntimeError("No products returned; old data retained")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    payload={"attribution":"Contains data from Open Food Facts (https://world.openfoodfacts.org), made available under the Open Database License.",
             "license":"ODbL-1.0","scope":"en:japan country tags only; not proof of availability or halal certification",
             "record_count":len(records),"records":sorted(records.values(),key=lambda p:p["code"])}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"api_rows_checked":seen,"new":added,"updated":changed,"total_saved":len(records)}))
if __name__=="__main__":main()
