#!/usr/bin/env python3
"""Convert Crawl4AI evidence JSONL into auditable candidate CSV (not halal certification)."""
import csv, json, re
from pathlib import Path

out = Path("data/manufacturer_ingredient_candidates.csv")
paths = [Path("data/crawl4ai_ingredient_evidence.jsonl"), Path("data/http_ingredient_evidence.jsonl")]
seen, items = set(), []
stop_labels = r"(?:アレルギー(?:物質)?|栄養成分(?:表示)?|内容量|保存方法|賞味期限|消費期限|原産国|製造者|販売者|お問い合わせ)"
for path in paths:
    if not path.exists():
        continue
    raw = path.read_text(encoding="utf-8").replace("\\n{", "\n{")
    for line in raw.splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        url = r.get("source_url", "")
        match = re.search(r"/((?:45|49)\d{11})\.html(?:[?#].*)?$", url)
        if not match:
            continue
        jan = match.group(1)
        if jan in seen:
            continue
        evidences = r.get("evidence", r.get("ingredient_evidence", []))
        if isinstance(evidences, str):
            evidences = [evidences]
        evidence = "\n".join(str(x) for x in evidences).replace("\\n", "\n").replace("|", " ")
        evidence = re.sub(r"[ \t]+", " ", evidence)
        m = re.search(r"原材料名\s*[:：]?\s*(.{3,1600}?)(?=" + stop_labels + r"|\Z)", evidence, re.S)
        if not m:
            m = re.search(r"(?:原材料|使用原材料)\s*[:：]?\s*(.{3,1200}?)(?=" + stop_labels + r"|\Z)", evidence, re.S)
        if not m:
            continue
        ingredients = re.sub(r"\s+", " ", m.group(1)).strip(" ：:、|")
        if len(ingredients) < 3 or not re.search(r"[ぁ-んァ-ヶ一-龠]", ingredients):
            continue
        items.append({"jan_code": jan, "ingredient_text": ingredients[:1600], "source_url": url,
                      "source_type": "manufacturer_page", "reviewed": "false"})
        seen.add(jan)
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["jan_code", "ingredient_text", "source_url", "source_type", "reviewed"])
    writer.writeheader()
    writer.writerows(items)
print(f"Manufacturer candidate rows: {len(items)}")
