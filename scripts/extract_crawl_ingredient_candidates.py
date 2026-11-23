#!/usr/bin/env python3
"""Convert public ingredient evidence into auditable candidates, never halal certification.

JAN is populated only when a checksum-valid JAN-13 is explicitly labelled in
captured page evidence or in the crawler's same-page explicit-label metadata.
Numeric product URLs and generic barcode candidates are not sufficient evidence.
"""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from japan_ingredient_barcodes import jan_valid
from crawl_japanese_ingredients import product_url as is_supported_product_url
from japan_ingredient_food_filter import (
    has_unresolved_html_artifacts,
    is_nonfood_ingredient_text,
    is_nonfood_name,
)
from japan_ingredient_source_terms import is_terms_restricted_url

OUT = Path("data/manufacturer_ingredient_candidates.csv")
PATHS = [
    Path("data/crawl4ai_ingredient_evidence.jsonl"),
    Path("data/http_ingredient_evidence.jsonl"),
]
STOP_LABELS = (
    r"(?:この商品に含まれる(?:アレルギー物質)?|アレルギー(?:物質|情報)?|"
    r"栄養成分(?:表示)?|内容量|保存方法|賞味期限|消費期限|原産国|製造者|"
    r"販売者|お問い合わせ|JANコード|JAN\s*CODE|JANCODE|POSコード|#{1,6}\s)"
)
JAN_LABEL = re.compile(
    r"(?:JANコード|JAN\s*CODE|JANCODE|POSコード)\s*[:：|｜]?\s*"
    r"((?:\d[\s-]?){7,12}\d)(?!\d)",
    re.IGNORECASE,
)

GENERIC_PAGE_NAMES = frozenset({
    "商品情報", "商品一覧", "商品紹介", "製品情報", "商品ラインナップ", "原料調達",
    "野菜･果実飲料の原材料について", "野菜・果実飲料の原材料について",
})
NON_DECLARATION_TEXT = re.compile(
    r"(?:などを表示したラベル|ラベルを添付し|原材料の調達における取り組み|産地情報を開示しています)",
    re.IGNORECASE,
)



def evidence_text(record):
    values = record.get("evidence", record.get("ingredient_evidence", []))
    if isinstance(values, str):
        values = [values]
    text = "\n".join(str(value) for value in values)
    return re.sub(r"[ \t]+", " ", text.replace("\\n", "\n").replace("|", " "))


def extract_ingredient_text(text):
    match = re.search(
        r"原材料名\s*[:：]?\s*(.{3,1600}?)(?=" + STOP_LABELS + r"|\Z)",
        text,
        re.S,
    )
    if not match:
        match = re.search(
            r"(?:原材料|使用原材料)\s*[:：]?\s*(.{3,1200}?)(?="
            + STOP_LABELS
            + r"|\Z)",
            text,
            re.S,
        )
    if not match:
        return ""
    ingredients = re.sub(r"\s+", " ", match.group(1)).strip(" ：:、|")
    if (
        len(ingredients) < 10
        or not re.search(r"[ぁ-んァ-ヶ一-龠]", ingredients)
        or is_nonfood_ingredient_text(ingredients)
        or has_unresolved_html_artifacts(ingredients)
        or NON_DECLARATION_TEXT.search(ingredients)
    ):
        return ""
    return ingredients[:1600]


def explicit_jan_codes(text):
    """Return only checksum-valid JAN-13 values adjacent to an explicit JAN label."""
    found = []
    for match in JAN_LABEL.finditer(text):
        code = re.sub(r"\D", "", match.group(1))
        if len(code) == 13 and jan_valid(code) and code not in found:
            found.append(code)
    return found


def explicit_jan_codes_from_page(markdown="", *html_documents):
    """Find labelled JANs in captured Markdown and the full page DOM.

    Crawl4AI's Markdown snippets can omit the product-information block even
    when it exists in the source HTML. Generic barcode candidates are never
    consulted; every returned code must still pass the explicit JAN label and
    JAN-13 checksum checks above.
    """
    parts = [str(markdown or "")]
    for document in html_documents:
        if document:
            parts.append(BeautifulSoup(str(document), "html.parser").get_text(" ", strip=True))
    return explicit_jan_codes("\n".join(parts))


def extract_candidate_records(records, exported_at=None):
    exported_at = exported_at or datetime.now(timezone.utc).isoformat()
    seen_urls = set()
    items = []
    for record in records:
        url = str(record.get("source_url") or "").strip()
        # Only exact, supported manufacturer/retailer product-detail URLs qualify.
        # Generic category, corporate, safety and marketing pages are discovery leads, not products.
        if (not url.startswith("https://") or url in seen_urls
                or is_terms_restricted_url(url) or not is_supported_product_url(url)):
            continue
        text = evidence_text(record)
        ingredients = extract_ingredient_text(text)
        if not ingredients:
            continue

        page_title = str(record.get("page_title") or record.get("title") or "")
        product_name = str(record.get("product_name") or "").strip()
        if not product_name:
            product_name = re.split(r"\s*[|｜]\s*", page_title, maxsplit=1)[0].strip()
        if not product_name:
            continue
        normalized_name = re.sub(r"\\s+", "", product_name)
        if (
            normalized_name in GENERIC_PAGE_NAMES
            or normalized_name.endswith("の原材料について")
            or is_nonfood_name(product_name)
        ):
            continue

        jan_candidates = explicit_jan_codes(text)
        # The browser crawler can capture a labelled JAN outside short ingredient
        # snippets. Trust only its separate explicit-label field, never generic
        # barcode_candidates.
        for raw in record.get("jan_candidates", []) or []:
            code = re.sub(r"\D", "", str(raw))
            if len(code) == 13 and jan_valid(code) and code not in jan_candidates:
                jan_candidates.append(code)
        jan_code = jan_candidates[0] if len(jan_candidates) == 1 else ""
        items.append(
            {
                "product_name": product_name,
                "jan_code": jan_code,
                "jan_code_candidates": json.dumps(jan_candidates, ensure_ascii=False),
                "ingredient_text": ingredients,
                "source_url": url,
                "source_type": record.get("source_type") or "official_public_page_candidate",
                "source_captured_at": record.get("captured_at") or record.get("retrieved_at") or exported_at,
                "candidate_exported_at": exported_at,
                "verification_status": (
                    record.get("verification")
                    if record.get("verification") in {"needs_human_review", "needs_manual_review"}
                    else record.get("verification_status")
                    if record.get("verification_status") in {"needs_human_review", "needs_manual_review"}
                    else "needs_human_review"
                ),
                "halal_certified": "false",
                "page_sha256": record.get("page_sha256") or "",
                "reviewed": "false",
            }
        )
        seen_urls.add(url)
    return items


def load_records(paths=PATHS):
    records = []
    for path in paths:
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8").replace("\\n{", "\n{")
        for line in raw.splitlines():
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    return records


def main():
    items = extract_candidate_records(load_records())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "product_name",
        "jan_code",
        "jan_code_candidates",
        "ingredient_text",
        "source_url",
        "source_type",
        "source_captured_at",
        "candidate_exported_at",
        "verification_status",
        "halal_certified",
        "page_sha256",
        "reviewed",
    ]
    with OUT.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(items)
    print(f"Public ingredient candidate rows: {len(items)}")


if __name__ == "__main__":
    main()
