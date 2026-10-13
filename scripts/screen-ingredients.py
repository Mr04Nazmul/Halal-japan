#!/usr/bin/env python3
"""Assess ingredient coverage, not halal certification. Run after bulk importer."""
import json, pathlib, re
source=pathlib.Path("data/openfoodfacts-japan.json")
if not source.exists():
    raise SystemExit("Run bulk import first: data/openfoodfacts-japan.json is missing")
data=json.loads(source.read_text(encoding="utf-8"))
results=[]
for p in data.get("products",[]):
    ing=(p.get("ingredients_text") or "").strip()
    low=ing.lower()
    prohibited=bool(re.search(r"pork|lard|porcine|豚肉|豚脂|ラード|ポークエキス|豚エキス",low))
    review=bool(re.search(r"gelatin|ゼラチン|乳化剤|emulsifier|shortening|ショートニング|香料|flavou?r|酒精|アルコール|みりん|酵素",low))
    verdict="haram_ingredient" if prohibited else "needs_review"
    reason=("Explicit pork-derived ingredient in ingredient text" if prohibited else
            "Ingredient text missing" if not ing else
            "Origin/processing of listed additives needs checking" if review else
            "No explicit pork term detected; certification and full supply chain unverified")
    results.append({"code":p.get("code"),"name":p.get("product_name"),
      "ingredient_text":ing,"ingredient_present":bool(ing),
      "ingredient_rule_result":verdict,"reason":reason,
      "source_url":p.get("_sourceUrl"),
      "halal_certified":False,"reviewed_by_manufacturer":False})
out=pathlib.Path("data/ingredient-review.json")
out.write_text(json.dumps({"disclaimer":"Automated screening only; NOT religious certification. False positives/negatives possible; review full label.","record_count":len(results),
"with_ingredients":sum(r["ingredient_present"] for r in results),
"products":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Screened",len(results),"records; ingredient text available for",sum(r["ingredient_present"] for r in results))
