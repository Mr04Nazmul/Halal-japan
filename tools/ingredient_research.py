#!/usr/bin/env python3
"""Ingredient research dataset preparation, inspired by K-Dense scientific-agent-skills.
Run: python tools/ingredient_research.py [input_dir] [output_dir]
Source rows must contain product_name, ingredients_text, source_url.
This job NEVER declares a food halal-certified and NEVER uploads to Supabase.
"""
from __future__ import annotations
import csv, json, pathlib, re, sys, urllib.parse
INPUT=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "research/inbox")
OUTPUT=pathlib.Path(sys.argv[2] if len(sys.argv)>2 else "research/output")
REQUIRED=("product_name","ingredients_text","source_url")
def normalize(s): return re.sub(r"\s+"," ",str(s or "")).strip()
def main():
    OUTPUT.mkdir(parents=True,exist_ok=True)
    records=[]; rejected=[]; seen=set()
    for filename in sorted(INPUT.glob("*.csv")) if INPUT.exists() else []:
        with filename.open(encoding="utf-8-sig",newline="") as handle:
            reader=csv.DictReader(handle)
            if not reader.fieldnames or not set(REQUIRED).issubset(reader.fieldnames):
                rejected.append({"file":filename.name,"error":"missing required columns"});continue
            for line,row in enumerate(reader,2):
                name=normalize(row.get("product_name")); ingredients=normalize(row.get("ingredients_text"))
                url=normalize(row.get("source_url")); barcode=normalize(row.get("jan_code"))
                domain=urllib.parse.urlparse(url)
                if not name or not ingredients or domain.scheme!="https" or not domain.netloc:
                    rejected.append({"file":filename.name,"line":line,"error":"missing evidence or HTTPS source"});continue
                key=(barcode or name.casefold(),ingredients)
                if key in seen:continue
                seen.add(key)
                records.append({"product_name":name,"jan_code":barcode,"ingredients_text":ingredients,
                    "source_url":url,"source_file":filename.name,"reviewed":False,
                    "halal_certified":False})
    status={"candidate_records":len(records),"rejected_rows":len(rejected),
        "verified_records":0,"imported_to_supabase":0,
        "notice":"Candidates need manufacturer/label verification. No automatic halal ruling."}
    (OUTPUT/"ingredient_candidates.json").write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUTPUT/"research_status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUTPUT/"rejected.json").write_text(json.dumps(rejected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(status))
if __name__=="__main__":main()
