#!/usr/bin/env python3
"""Convert Crawl4AI evidence JSONL into auditable candidate CSV (not halal certification).
Only creates records when an exact JAN from the URL and 原材料名 evidence are present.
"""
import csv, json, re
from pathlib import Path
from urllib.parse import urlparse
out=Path("data/manufacturer_ingredient_candidates.csv")
paths=[Path("data/crawl4ai_ingredient_evidence.jsonl"),Path("data/http_ingredient_evidence.jsonl")]
seen=set()
items=[]
for path in paths:
    if not path.exists():continue
    for line in path.read_text(encoding="utf-8").splitlines():
        try:r=json.loads(line)
        except ValueError:continue
        url=r.get("source_url","")
        code=re.search(r"/((?:45|49)\d{11})\.html(?:\?|$)",url)
        if not code:continue
        jan=code.group(1)
        if jan in seen:continue
        evidences=r.get("evidence",r.get("ingredient_evidence",[]))
        evidence="\n".join(evidences)
        m=re.search(r"(?:\|\s*原材料名\s*\|\s*|原材料名\s*[:：]\s*)([^\n|]{3,1200})",evidence)
        if not m:continue
        ingredients=m.group(1).strip()
        if len(ingredients)<3:continue
        items.append({"jan_code":jan,"ingredient_text":ingredients,"source_url":url,"source_type":"manufacturer_page","reviewed":"false"})
        seen.add(jan)
out.parent.mkdir(parents=True,exist_ok=True)
with out.open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=["jan_code","ingredient_text","source_url","source_type","reviewed"])
    writer.writeheader()
    writer.writerows(items)
print(f"Manufacturer candidate rows: {len(items)}")
