#!/usr/bin/env python3
"""Import sourced ingredients from collected CSV, without overwriting existing halal decisions.
Requires GitHub Actions secrets JHC_SUPABASE_URL and JHC_SUPABASE_SERVICE_ROLE_KEY.
"""
import csv,json,os,time,urllib.request,urllib.parse,urllib.error
from pathlib import Path
base=os.environ["SUPABASE_URL"].rstrip("/")+"/rest/v1"
key=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
headers={"apikey":key,"Authorization":"Bearer "+key,"Content-Type":"application/json"}
def api(method,path,data=None,extra=None):
    req=urllib.request.Request(base+path,data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,
        headers={**headers,**(extra or {})},method=method)
    with urllib.request.urlopen(req,timeout=45) as r:
        return json.loads(r.read() or b"[]")
def batches(seq,n):
    for i in range(0,len(seq),n):yield seq[i:i+n]
source=Path("data/japan_ingredients.csv")
if not source.exists():raise SystemExit("Missing candidate CSV")
records={}
with source.open(encoding="utf-8",newline="") as f:
    for r in csv.DictReader(f):
        code=(r.get("barcode") or "").strip()
        ingredient=(r.get("ingredients_ja") or r.get("ingredients_raw") or r.get("ingredients_en") or "").strip()
        if code.isdigit() and len(code) in (8,12,13,14) and ingredient and (r.get("product_name") or "").strip():
            records.setdefault(code,(r,ingredient))
print("Unique sourced candidates:",len(records),flush=True)
created=0; ingredients_added=0
for subset in batches(list(records),40):
    products=[{"jan_code":code,"name_ja":records[code][0]["product_name"],
      "brand":records[code][0].get("brand",""),"product_url":records[code][0].get("source_url",""),
      "assessment":"needs_verification","assessment_note":"Community-sourced ingredient list; not halal certified"} for code in subset]
    # Ignore existing records; do not touch verified user data or decisions.
    api("POST","/halal_products?on_conflict=jan_code",products,{"Prefer":"resolution=ignore-duplicates,return=minimal"})
    existing=api("GET","/halal_products?select=id,jan_code&jan_code=in.("+",".join(subset)+")")
    lookup={r["jan_code"]:r["id"] for r in existing}
    ids=list(lookup.values())
    if not ids:continue
    present=api("GET","/product_ingredients?select=product_id,language_code&product_id=in.("+",".join(ids)+")")
    have={(r["product_id"],r["language_code"]) for r in present}
    items=[]
    for code in subset:
        pid=lookup.get(code)
        if not pid:continue
        row,ingredient=records[code]
        language="ja" if row.get("ingredients_ja") else ("en" if row.get("ingredients_en") else "und")
        if (pid,language) not in have:
            items.append({"product_id":pid,"ingredient_text":ingredient,"language_code":language,"reviewed":False})
    if items:api("POST","/product_ingredients",items,{"Prefer":"return=minimal"});ingredients_added+=len(items)
    created+=len(existing)
    time.sleep(0.5)
print(json.dumps({"matched_product_ids":created,"ingredient_records_added":ingredients_added}))
