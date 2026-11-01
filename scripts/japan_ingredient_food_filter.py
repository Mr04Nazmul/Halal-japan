"""Reject clearly non-food product names before counting or importing ingredients.

Only definite household, cosmetic, pet-care and hygiene terms are excluded;
uncertain products remain subject to human review.
"""
import re
import unicodedata

NONFOOD_NAME=re.compile(
    r"(?:ナプキン|スカルプリッチ|ペット(?:用|フード)|ドッグフード|キャットフード|犬用|猫用|洗剤|シャンプー|化粧|石けん|石鹸|石鹼|せっけん|"
    r"(?:犬|猫)のおやつ|(?:犬|猫)のごはん|ペットのおやつ|浴用|入浴剤|ソープ|洗顔|歯みがき|歯磨き|ハンドクリーム|"
    r"ヘアトリートメント|(?:高温|使い捨て|貼らない|貼る)?カイロ)",
    re.IGNORECASE,
)

def is_nonfood_name(name):
    return isinstance(name,str) and bool(NONFOOD_NAME.search(name))

# An origin heading or packaging polymer is not a food ingredient declaration.
# Exact normalized matching avoids rejecting legitimate multi-item recipes.
INVALID_INGREDIENT_TEXT = frozenset({'主な原材料の産地', 'ポリエチレン'})

def is_nonfood_ingredient_text(value):
    if not isinstance(value,str):
        return False
    normalized = ''.join(unicodedata.normalize('NFKC',value).split())
    return normalized in INVALID_INGREDIENT_TEXT

# Do not treat HTML fragments or undecoded entities as a verified ingredient
# declaration. Preserve the source snapshot and send the page for review.
# Normal text containing an ampersand is not automatically rejected.
UNRESOLVED_HTML_ARTIFACT = re.compile(
    r"<\s*/?\s*(?:br|p|div|span|li)\b|&(?:#(?:x[0-9a-f]{2,7}|[0-9]{2,7})|lt|gt|amp|nbsp);",
    re.IGNORECASE,
)

def has_unresolved_html_artifacts(value):
    return isinstance(value, str) and bool(UNRESOLVED_HTML_ARTIFACT.search(value))
