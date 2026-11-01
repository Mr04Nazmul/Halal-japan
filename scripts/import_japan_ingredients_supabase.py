#!/usr/bin/env python3
"""Import verified cumulative crawler products into isolated Supabase staging.
Requires GitHub Secrets SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY.
Does not touch existing product, scanner or certification tables.
"""
import json,os,sys,re,urllib.request,urllib.error
from collections import Counter
from urllib.parse import quote
from pathlib import Path

url=os.environ.get("SUPABASE_URL","").rstrip("/")
key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY","")
if not url.startswith("https://") or not key:
    sys.exit("Missing server-only SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY")
path=Path(sys.argv[1] if len(sys.argv)>1 else "crawler-state/products.json")
items=json.loads(path.read_text(encoding="utf-8"))
assert isinstance(items,list), "Expected cumulative array of ingredient products"
from japan_ingredient_barcodes import jan_valid
from japan_ingredient_food_filter import is_nonfood_name,is_nonfood_ingredient_text,has_unresolved_html_artifacts
from japan_ingredient_policy import screen
from japan_ingredient_import_dedup import filter_existing_jan_conflicts, filter_existing_source_conflicts
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
    if is_nonfood_name(name):
        reject("non-food product");continue
    if not all(isinstance(x,str) and x.strip() for x in (ingredient,name,source)):
        reject("missing product, ingredient or source field");continue
    if is_nonfood_ingredient_text(ingredient):
        reject('invalid ingredient text or packaging material');continue
    if has_unresolved_html_artifacts(ingredient):
        reject('unresolved HTML or entity in ingredient declaration');continue
    if re.match(r'^\s*(?:添加物|添加物名)\s*[:：]',ingredient):
        reject("additives-only incomplete ingredients");continue
    if p.get("ingredient_field_status")!="complete_displayed_field":
        reject("incomplete ingredient field");continue
    if rule not in ("HALAL","HARAM","UNKNOWN"):
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
    # Re-screen old crawler checkpoints using the current policy before import.
    # Product-name alcohol risks were previously mislabeled HALAL.
    decision=screen(ingredient,p.get("additives_ja") or "",product_name=name)
    # UNKNOWN means halal suitability needs review, not that the official
    # ingredient declaration is incomplete. Archive complete fields safely.
    # Keep halal_certified=False and the research-only review marker.
    rule=decision["rule_result"]
    seen.add(ident)
    rows.append(dict(identity_key=ident,jan_code=str(jan) if jan and len(str(jan))==13 else None,
        product_name=name,ingredients_ja=ingredient,additives_ja=p.get("additives_ja") or "",
        source_url=source,source_publisher=p.get("source_publisher"),
        rule_result=rule,matched_terms=decision["matched_terms"],
        rule_version=decision["rule_version"],halal_certified=False,
        evidence={"source_type":p.get("source_type"),"field_status":p.get("ingredient_field_status"),
                  "reuse_permission":p.get("reuse_permission","not_established"),
                  "original_barcode":str(jan) if jan else None,
                  "barcode_type":"JAN-8" if jan and len(str(jan))==8 else ("JAN-13" if jan else None),
                  "verification_status":"official_ingredient_field_captured_pending_human_review",
                  "research_only":True,"packaging_verified":False},
        snapshot_hash=p.get("source_html_sha256"),collected_at=p.get("retrieved_at")))
# A manufacturer URL may already exist under a URL/hash identity even when
# this checkpoint later supplies a JAN-8 or JAN-13. Check only *new*
# identities to avoid thousands of unnecessary per-URL requests on reruns.
# Fail closed: do not overwrite or silently double-count an existing source.
try:
    rows, source_conflicts = filter_existing_source_conflicts(rows, url, key)
except RuntimeError as exc:
    sys.exit(str(exc))
if source_conflicts:
    print(f"Skipped {len(source_conflicts)} candidate identities with existing source URLs; examples: {source_conflicts[:5]}", flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as report:
            report.write(f"Existing source URL collisions safely skipped: {len(source_conflicts)}.\n")
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
# A JAN-13 may already be owned by a manufacturer-researched identity.
# PostgREST on_conflict=identity_key alone cannot ignore the separate unique
# JAN constraint. Preflight only candidate JANs and preserve existing records.
try:
    rows, jan_conflicts = filter_existing_jan_conflicts(rows, url, key)
except RuntimeError as exc:
    sys.exit(str(exc))
if jan_conflicts:
    print(f"Skipped {len(jan_conflicts)} existing JAN-13 codes owned by different identities; no records overwritten. Examples: {jan_conflicts[:10]}", flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as report:
            report.write(f"Existing JAN-13 identity collisions safely skipped: {len(jan_conflicts)}.\\n")
if not rows:
    print("No rows remain after JAN-13 collision deduplication; import complete: 0 NEW rows.", flush=True)
    sys.exit(0)
print(f"Importing {len(rows)} distinct complete-ingredient records into staging only",flush=True)
newly_inserted=0
new_source_counts=Counter()
for i in range(0,len(rows),100):
    req=urllib.request.Request(url+"/rest/v1/jhc_crawler_ingredient_staging?on_conflict=identity_key&select=identity_key",
        data=json.dumps(rows[i:i+100],ensure_ascii=False).encode("utf-8"),method="POST",
        headers={"apikey":key,"Authorization":"Bearer "+key,"Content-Type":"application/json",
                 "Prefer":"resolution=ignore-duplicates,return=representation"})
    try:
        with urllib.request.urlopen(req,timeout=45) as response:
            inserted=json.loads(response.read())
        if not isinstance(inserted,list) or len(inserted)>len(rows[i:i+100]):
            sys.exit("Unexpected Supabase insert response; count is not reliable")
        source_by_identity={row['identity_key']: row.get('source_publisher') or 'unknown' for row in rows[i:i+100]}
        for returned in inserted:
            identity=returned.get('identity_key') if isinstance(returned,dict) else None
            if identity not in source_by_identity:
                sys.exit('Unexpected inserted identity in Supabase response; count is not reliable')
            new_source_counts[source_by_identity[identity]]+=1
        newly_inserted+=len(inserted)
    except urllib.error.HTTPError as e:
        sys.exit(f"Supabase import batch {i//100+1} failed: HTTP {e.code}, {e.read(500).decode(errors='replace')}")
print(f"Staging import complete: {newly_inserted} NEW unique rows; {len(rows)-newly_inserted} existing identities ignored; {rejected} quarantined.",flush=True)
print('New imports by source publisher: '+json.dumps(dict(sorted(new_source_counts.items())),ensure_ascii=False),flush=True)
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"],"a") as report:
        report.write(f"\nNewly inserted staging rows: {newly_inserted}. Existing identities ignored: {len(rows)-newly_inserted}.\n")
