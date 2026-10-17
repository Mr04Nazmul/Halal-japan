#!/usr/bin/env python3
"""Import OFF ingredient candidates into a review-only Supabase staging queue.
Only when >=1000 distinct source-backed, complete ingredient records exist.
Never writes halal_products or changes classification.
"""
import json,os,sys,urllib.request,urllib.error
from pathlib import Path
p=Path("data/off_japan_ingredient_candidates.jsonl")
if not p.exists():sys.exit("No ingredient candidate file; no import")
data={}
for line in p.read_text(encoding="utf8").splitlines():
 try:
  r=json.loads(line)
  barcode=str(r.get("barcode") or "").strip()
  ing=str(r.get("ingredients") or "").strip()
  name=str(r.get("name") or "").strip()
  src=str(r.get("source_url") or "").strip()
  if len(barcode) not in (8,12,13,14) or not barcode.isdigit() or len(ing)<8 or not name or not src.startswith("https://"):continue
  data[barcode]={"jan_code":barcode,"product_name":name,"manufacturer":r.get("brand"),"discovery_source":"Open Food Facts","source_url":src,"ingredients_text":ing,"evidence_level":"third_party_unverified","status":"needs_review"}
 except (ValueError,TypeError):continue
print(f"Valid distinct ingredient candidates in current batch: {len(data)}",flush=True)
if len(data)<1000:
 print("Threshold not reached: skip database import")
 sys.exit(0)
url=os.environ.get("SUPABASE_URL","").rstrip("/")
key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
if not url or not key:sys.exit("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY GitHub Actions secrets; not importing")
rows=list(data.values())
for start in range(0,len(rows),100):
 payload=json.dumps(rows[start:start+100],ensure_ascii=False).encode()
 req=urllib.request.Request(url+"/rest/v1/jhc_ingredient_research_queue?on_conflict=discovery_source,source_url",data=payload,method="POST",headers={"apikey":key,"Authorization":"Bearer "+key,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"})
 try:
  with urllib.request.urlopen(req,timeout=60) as response:print(f"Imported staging batch {start//100+1}: {response.status}",flush=True)
 except urllib.error.HTTPError as e:sys.exit(f"Import failed HTTP {e.code}: {e.read(300).decode(errors='replace')}")
print("Import completed to needs_review staging queue; no halal classification made")
