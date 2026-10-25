"""Reject clearly non-food product names before counting or importing ingredients.

Only definite household, cosmetic, pet-care and hygiene terms are excluded;
uncertain products remain subject to human review.
"""
import re

NONFOOD_NAME=re.compile(
    r"(?:ペット(?:用|フード)|ドッグフード|キャットフード|犬用|猫用|洗剤|シャンプー|化粧|石けん|石鹸|石鹼|せっけん|"
    r"(?:犬|猫)のおやつ|(?:犬|猫)のごはん|ペットのおやつ|浴用|入浴剤|ソープ|洗顔|歯みがき|歯磨き|ハンドクリーム)",
    re.IGNORECASE,
)

def is_nonfood_name(name):
    return isinstance(name,str) and bool(NONFOOD_NAME.search(name))
