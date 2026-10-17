#!/usr/bin/env python3
"""Stage unique, source-backed Open Food Facts ingredient text for review. Never certify halal."""
import json,os,re,time,urllib.request,urllib.error
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"data"
sources=[p for p in [ROOT/"openfoodfacts-japan.json",*sorted((ROOT/"world-food-shards").glob("*.json"))] if p.exists() and p.stat().st_size > 0]
if not sources:
    print(json.dumps({"error":"No non-empty source dataset files available","candidate_ingredient_rows":0}),flush=True)
    raise SystemExit(1)
counts=Counter()
for path in sources:
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in {path}: {e}")
    if data.get("license")!="ODbL-1.0":raise SystemExit("Unexpected license "+str(path))
    for row in data.get("products",data.get("records",[])):
        code=str(row.get("code",""))
        if re.fullmatch(r"(?:[0-9]{8}|[0-9]{12,14})",code):counts[code]+=1
rows=[]
for path in sources:
    data=json.loads(path.read_text(encoding="utf-8"))
    for r in data.get("products",data.get("records",[])):
        code=str(r.get("code",""))
        ing=str(r.get("ingredients_text") or "").strip()
        name=str(r.get("product_name") or r.get("name") or "").strip()
        if counts[code]!=1 or not ing or not name:continue
        if ing.lower() in ("unknown","n/a","none","no data","ingredients","?","-"):continue
        source="https://world.openfoodfacts.org/product/"+code
        rows.append({"jan_code":code,"product_name":name[:500],"manufacturer":str(r.get("brands") or "")[:500] or None,
          "discovery_source":"Open Food Facts catalogue",
          "source_url":source,"ingredients_text":ing[:6000],
          "evidence_level":"discovery_only","status":"needs_review"})
print(json.dumps({"files":len(sources),"candidate_ingredient_rows":len(rows),"duplicate_barcodes_quarantined":sum(v>1 for v in counts.values())}),flush=True)
url=os.environ.get("SUPABASE_URL","").rstrip("/")
key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
if not url or not key:raise SystemExit("Missing GitHub secrets: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
inserted_attempted=0
for start in range(0,len(rows),100):
    data=json.dumps(rows[start:start+100],ensure_ascii=False).encode("utf-8")
    request=urllib.request.Request(url+"/rest/v1/jhc_ingredient_research_queue?on_conflict=discovery_source,source_url",data=data,method="POST",
      headers={"apikey":key,"Authorization":"Bearer "+key,"Content-Type":"application/json","Prefer":"resolution=ignore-duplicates,return=minimal"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request,timeout=90) as res:
                if res.status not in (200,201,204):raise RuntimeError("Unexpected status "+str(res.status))
            break
        except (urllib.error.HTTPError,urllib.error.URLError) as e:
            if attempt==3:raise
            time.sleep(2**attempt)
    inserted_attempted+=len(rows[start:start+100])
    if start%2000==0:print("Submitted",inserted_attempted,"records",flush=True)
print(json.dumps({"submitted":inserted_attempted,"status":"needs_review","source":"Open Food Facts ODbL 1.0"}),flush=True)
