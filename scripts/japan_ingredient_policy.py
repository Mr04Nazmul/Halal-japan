"""User-configured ingredient screening; never a halal certificate."""
import re
import unicodedata

RULE_VERSION = 'user-ingredients-2026-10-17-v1'
TERMS = {
    'pork': r'豚肉|豚脂|豚骨|豚エキス|豚由来|ポーク|ラード|\b(?:pork|porcine|lard)\b',
    'gelatin': r'ゼラチン|\bgelatine?\b',
    'emulsifier': r'乳化剤|\bemulsifiers?\b',
    'flavouring': r'香料|\bflavou?r(?:ing|ings)?\b',
    'collagen': r'コラーゲン|\bcollagen\b',
    'shortening': r'ショートニング|\bshortening\b',
    'lecithin': r'レシチン|\blecithin\b',
    'processed_fat': r'加工油脂|\bprocessed fats?\b',
    'hydrolyzed_protein': r'(?:たんぱく|たん白|タンパク|蛋白)加水分解物|\bhydroly[sz]ed protein\b',
    'fermented_seasoning': r'発酵調味料|醗酵調味料|\bfermented seasoning\b',
    'cooking_alcohol': r'料理酒|みりん|味醂|酒精|アルコール|洋酒|\b(?:cooking sake|rice wine|mirin|ethanol|alcohol)\b',
}

def screen(ingredients, additives='', complete=True):
    text=unicodedata.normalize('NFKC',str(ingredients or '')).lower().strip()
    result={'rule_version':RULE_VERSION,'halal_certified':False,
            'decision_basis':'user_configured_ingredient_rules','matched_terms':[]}
    if not complete or not text or text in {'不明','unknown','n/a','none'} or re.fullmatch(r'(?:無添加|豚肉不使用|ハラール|halal|organic)[\s、,。]*',text):
        return dict(result,rule_result='UNKNOWN',reason='complete_ingredients_required')
    text+=' '+unicodedata.normalize('NFKC',str(additives or '')).lower()
    # Remove only explicit absence claims; subsequent positive ingredients stay.
    text=re.sub(r'(?:豚肉|ポーク|ラード|ゼラチン|乳化剤|香料|アルコール|酒精)\s*(?:は|を)?\s*(?:不使用|無添加|含まれていません|含まない)', ' ', text)
    text=re.sub(r'\b(?:no|without|free from)\s+(?:pork|lard|gelatine?|emulsifiers?|flavou?ring|alcohol)\b',' ',text)
    if not re.sub(r'[\s、,。.()/／・-]','',text):
        return dict(result,rule_result='UNKNOWN',reason='absence_claim_is_not_a_complete_declaration')
    text=re.sub(r'(?:植物性|植物由来|大豆由来|ひまわり由来|なたね由来)\s*(?:の)?\s*乳化剤',' plant_emulsifier ',text)
    text=re.sub(r'乳化剤\s*\(\s*(?:植物性|植物由来|大豆由来|ひまわり由来|なたね由来)\s*\)',' plant_emulsifier ',text)
    text=re.sub(r'\b(?:plant[- ]based|vegetable[- ]derived|soy[- ]derived)\s+emulsifiers?\b',' plant_emulsifier ',text)
    hits=[{'rule':name,'text':m.group(0)} for name,pattern in TERMS.items() if (m:=re.search(pattern,text))]
    return dict(result,rule_result='HARAM' if hits else 'HALAL',matched_terms=hits,
                reason='matched_user_prohibited_terms' if hits else 'no_user_prohibited_term_in_displayed_ingredients')
