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
rejections={}
def reject(reason):
    rejections[reason]=rejections.get(reason,0)+1
for p in items:
    ident=p.get("product_id")
    ingredient=p.get("ingredients_ja")
    name=p.get("name_ja")
    source=p.get("source_url")
    rule=p.get("rule_result")
    jan=p.get("jan")
    if not isinstance(ident,str) or not ident:
        reject("missing identity");continue
    if ident in seen:
        reject("duplicate identity");continue
    if not all(isinstance(x,str) and x.strip() for x in (ingredient,name,source)):
        reject("missing product, ingredient or source field");continue
    if p.get("ingredient_field_status")!="complete_displayed_field":
        reject("incomplete ingredient field");continue
    if rule not in ("HALAL","HARAM"):
        reject("unreviewed rules result");continue
    if p.get("halal_certified") is not False:
        reject("unclear certification flag");continue
    if not source.startswith("https://"):
        reject("unsafe source URL");continue
    if jan and not jan_valid(jan):
        reject("invalid JAN");continue
    # The crawler's local accepted identity is the only import identity.
    if jan and ident!="jan:"+str(jan):
        reject("JAN identity mismatch");continue
    seen.add(ident)
    rows.append(dict(identity_key=ident,jan_code=str(jan) if jan else None,
        product_name=name,ingredients_ja=ingredient,additives_ja=p.get("additives_ja") or "",
        source_url=source,source_publisher=p.get("source_publisher"),
        rule_result=rule,matched_terms=p.get("matched_terms") or [],
        rule_version=p.get("rule_version"),halal_certified=False,
        evidence={"source_type":p.get("source_type"),"field_status":p.get("ingredient_field_status"),
                  "reuse_permission":p.get("reuse_permission","not_established")},
        snapshot_hash=p.get("source_html_sha256"),collected_at=p.get("retrieved_at")))
# Preserve valid rows while quarantining and counting invalid records.
# If more than 5% are rejected, fail rather than silently importing corrupt batches.
rejected=len(items)-len(rows)
print(f"Validation: {len(rows)} importable / {len(items)} provided; {rejected} rejected: {json.dumps(rejections,sort_keys=True)}",flush=True)
if not rows or rejected>max(10,int(len(items)*0.05)):
    sys.exit("Safety check: empty batch or more than 5% rejected; refusing import")
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as report:
        report.write(f"## Staging import validation\\n\\nAccepted: {len(rows)} / {len(items)}. Quarantined (not imported): {rejected}.\\n\\n")
        for reason,count in sorted(rejections.items()):
            report.write(f"- {reason}: {count}\\n")
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
