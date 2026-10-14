#!/usr/bin/env python3
"""Extract Japan-tagged records from a licensed Halal & Healthy / Open Food Facts SQLite world pack.
Usage: python3 scripts/extract_japan_pack.py /path/to/world.sqlite --output data/japan-world-sample.json
Input must be decompressed SQLite; never hardcode download links (resolve manifest each release).
This outputs records for review, not automatically certified halal products.
"""
import argparse, json, sqlite3, re, datetime, pathlib
def valid_ean(code):
    if not re.fullmatch(r"\d{8}|\d{12,14}", code or ""): return False
    if len(code) not in (8,12,13,14): return False
    digits=list(map(int,code))
    total=sum(d*(3 if i%2 else 1) for i,d in enumerate(reversed(digits[:-1])))
    return (10-total%10)%10==digits[-1]
def main():
    p=argparse.ArgumentParser();p.add_argument("db");p.add_argument("--output",default="data/japan-world-sample.json");p.add_argument("--limit",type=int,default=500);args=p.parse_args()
    if not 1<=args.limit<=10000: raise SystemExit("Limit must be 1..10000")
    db=sqlite3.connect("file:"+pathlib.Path(args.db).resolve().as_posix()+"?mode=ro",uri=True)
    db.row_factory=sqlite3.Row
    columns={row[1] for row in db.execute("PRAGMA table_info(products)")}
    needed={"code","product_name","brands","ingredients_text","countries_tags","last_modified_t"}
    if not needed.issubset(columns): raise SystemExit("Pack schema mismatch; no import")
    stats=dict(scanned=0,japan_tagged=0,valid_barcode=0,with_ingredients=0,exported=0)
    items=[]
    rows=db.execute("SELECT code,product_name,brands,ingredients_text,countries_tags,last_modified_t FROM products")
    for row in rows:
        stats["scanned"]+=1
        country={t.strip() for t in (row["countries_tags"] or "").split(",")}
        if "en:japan" not in country: continue
        stats["japan_tagged"]+=1
        code=str(row["code"] or "")
        if not valid_ean(code): continue
        stats["valid_barcode"]+=1
        ingredients=(row["ingredients_text"] or "").strip()
        if ingredients: stats["with_ingredients"]+=1
        name=(row["product_name"] or "").strip()
        if not name: continue
        item={"code":code,"product_name":name[:200],"brands":(row["brands"] or "")[:160],
          "ingredients_text":ingredients[:8000],"ingredients_present":bool(ingredients),
          "source":"Open Food Facts via Halal & Healthy World pack",
          "source_url":"https://world.openfoodfacts.org/product/"+code,
          "source_license":"ODbL-1.0","source_attribution":"Contains data from Open Food Facts (https://world.openfoodfacts.org), made available under the Open Database License.",
          "last_modified_t":row["last_modified_t"],"halal_verified":False,"verification_status":"needs_review"}
        if len(items)<args.limit: items.append(item)
    stats["exported"]=len(items)
    out={"generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "scope":"country tag en:japan only; does not establish in-store availability in Japan",
      "license":"ODbL-1.0","stats":stats,"records":items}
    path=pathlib.Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(stats,indent=2))
if __name__=="__main__":main()
