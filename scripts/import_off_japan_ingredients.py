#!/usr/bin/env python3
"""Collect Open Food Facts Japanese ingredient evidence without claiming halal status.
Uses public paginated OFF API with finite caps and source URLs. No DB writes.
"""
import argparse,json,re,time,urllib.parse,urllib.request
from pathlib import Path

# The OFF 'countries=japan' search can also return global catalogue products.
# Keep only candidates with a Japanese-language name AND ingredient list.
# This is a language/identity gate, not manufacturer verification or halal approval.
JP_TEXT = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
JP_KANA = re.compile(r"[\u3040-\u30ff]")

def valid_ean(code):
 if len(code) not in (8,13) or not code.isascii() or not code.isdigit():return False
 digits=[int(c) for c in code]
 total=sum(d*(3 if i%2==0 else 1) for i,d in enumerate(reversed(digits[:-1])))
 return (10-total%10)%10==digits[-1]

def is_japanese_ingredient_candidate(code,name,ingredients):
 name=str(name or "").strip();ingredients=str(ingredients or "").strip()
 return (valid_ean(code) and len(name)>1 and len(ingredients)>=8
         and bool(JP_TEXT.search(name)) and bool(JP_TEXT.search(ingredients))
         and bool(JP_KANA.search(name) or JP_KANA.search(ingredients)))

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--pages",type=int,default=2)
 p.add_argument("--page-size",type=int,default=100)
 p.add_argument("--output",default="data/off_japan_ingredient_candidates.jsonl")
 a=p.parse_args()
 a.pages=max(1,min(a.pages,20)); a.page_size=max(1,min(a.page_size,100))
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 seen=set();total=0;rejected=0
 with out.open("w",encoding="utf8") as f:
  for page in range(1,a.pages+1):
   params={"action":"process","json":"1","tagtype_0":"countries","tag_contains_0":"contains","tag_0":"japan","fields":"code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,url","page":str(page),"page_size":str(a.page_size)}
   url="https://world.openfoodfacts.org/cgi/search.pl?"+urllib.parse.urlencode(params)
   req=urllib.request.Request(url,headers={"User-Agent":"JapanHalalCheckerResearch/1.0 (source-linked educational research)"})
   try:
    with urllib.request.urlopen(req,timeout=45) as response: products=json.load(response).get("products",[])
   except Exception as exc:
    print(f"page {page} failed: {exc}");continue
   for row in products:
    code=str(row.get("code") or "").strip()
    ingredients=(row.get("ingredients_text_ja") or row.get("ingredients_text") or "").strip()
    name=(row.get("product_name_ja") or row.get("product_name") or "").strip()
    if not is_japanese_ingredient_candidate(code,name,ingredients):
     rejected+=1;continue
    if code in seen:continue
    seen.add(code)
    item={"barcode":code,"name":name,"brand":row.get("brands"),"ingredients":ingredients,"source_url":row.get("url") or "https://world.openfoodfacts.org/product/"+code,"source":"Open Food Facts","verification":"requires_review"}
    f.write(json.dumps(item,ensure_ascii=False)+"\n");total+=1
   print(f"page={page} ingredient_records={total}",flush=True)
   time.sleep(2)
 print(json.dumps({"ingredient_records":total,"rejected_non_japanese_or_invalid_ean":rejected,"output":str(out)}))
if __name__=="__main__":main()
