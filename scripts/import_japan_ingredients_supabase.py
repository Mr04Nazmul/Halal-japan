#!/usr/bin/env python3
"""Import verified cumulative crawler products into isolated Supabase staging.
Requires GitHub Secrets SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY.
Does not touch existing product, scanner or certification tables.
"""
import json,os,re,sys,urllib.request,urllib.error
from pathlib import Path

url=os.environ.get("SUPABASE_URL","").rstrip("/")
key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
if not url.startswith("https://") or not key:
    sys.exit("Missing server-only SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY")
path=Path(sys.argv[1] if len(sys.argv)>1 else "crawler-state/products.json")
items=json.loads(path.read_text(encoding="utf-8"))
assert isinstance(items,list), "Expected cumulative array of ingredient products"
def jan_valid(j):
    if not j or not re.fullmatch(r"[0-9]{13}",str(j)):return False
    s=str(j)
    return (10-sum(int(d)*(1 if i%2==0 else 3) for i,d in enumerate(s[:12]))%10)%10==int(s[-1])
rows=[]
seen=set()
for p in items:
    ident=p.get("product_id")
    ingredient=p.get("ingredients_ja")
    name=p.get("name_ja")
    source=p.get("source_url")
    rule=p.get("rule_result")
    jan=p.get("jan")
    if not isinstance(ident,str) or not ident or ident in seen: continue
    if not all(isinstance(x,str) and x.strip() for x in (ingredient,name,source)): continue
    if p.get("ingredient_field_status")!="complete_displayed_field":continue
    if rule not in ("HALAL","HARAM"): continue
    if p.get("halal_certified") is not False:continue
    if not source.startswith("https://"): continue
    if jan and not jan_valid(jan): continue
    # The crawler's local accepted identity is the only import identity.
    if jan and ident!="jan:"+str(jan):continue
    seen.add(ident)
    rows.append(dict(identity_key=ident,jan_code=str(jan) if jan else None,
        product_name=name,ingredients_ja=ingredient,additives_ja=p.get("additives_ja") or "",
        source_url=source,source_publisher=p.get("source_publisher"),
        rule_result=rule,matched_terms=p.get("matched_terms") or [],
        rule_version=p.get("rule_version"),halal_certified=False,
        evidence={"source_type":p.get("source_type"),"field_status":p.get("ingredient_field_status"),
                  "reuse_permission":p.get("reuse_permission","not_established")},
        snapshot_hash=p.get("source_html_sha256"),collected_at=p.get("retrieved_at")))
if len(rows)!=len(items):
    sys.exit(f"Safety check: {len(rows)} importable but {len(items)} cumulative items; refusing partial snapshot")
print(f"Importing {len(rows)} distinct complete-ingredient records into staging only",flush=True)
for i in range(0,len(rows),100):
    req=urllib.request.Request(url+"/rest/v1/jhc_crawler_ingredient_staging?on_conflict=identity_key",
        data=json.dumps(rows[i:i+100],ensure_ascii=False).encode("utf-8"),method="POST",
        headers={"apikey":key,"Authorization":"Bearer "+key,"Content-Type":"application/json",
                 "Prefer":"resolution=ignore-duplicates,return=minimal"})
    try:
        with urllib.request.urlopen(req,timeout=45) as response:response.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"Supabase import batch {i//100+1} failed: HTTP {e.code}, {e.read(500).decode(errors='replace')}")
print(f"All {len(rows)} records processed idempotently (existing identities were ignored).",flush=True)
