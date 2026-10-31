"""User-configured ingredient screening; never a halal certificate."""
import re
import unicodedata

RULE_VERSION = 'user-ingredients-2026-10-25-v3'
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
    'fermented_seasoning': r'発酵調味料|醗酵調味料|発酵調味液|醗酵調味液|\bfermented seasoning\b',
    'distilled_alcohol': r'焼酎|ウォッカ|ウオッカ|ウイスキー|ウィスキー|ブランデー|スピリッツ|(?:^|[、,\s])ジン(?:$|[、,\s(（])',
    'cooking_alcohol': r'料理酒|みりん|味醂|酒精|アルコール|洋酒|清酒|日本酒|赤ワイン|白ワイン|輸入ワイン|ワイン(?!ビネガー|酢)|\b(?:cooking sake|rice wine|mirin|ethanol|alcohol|wine)\b',
}

def screen(ingredients, additives='', complete=True, product_name=''):
    text=unicodedata.normalize('NFKC',str(ingredients or '')).lower().strip()
    result={'rule_version':RULE_VERSION,'halal_certified':False,
            'decision_basis':'user_configured_ingredient_rules','matched_terms':[]}
    if not complete or not text or text in {'不明','unknown','n/a','none'} or re.fullmatch(r'(?:無添加|豚肉不使用|ハラール|halal|organic)[\s、,。]*',text):
        return dict(result,rule_result='UNKNOWN',reason='complete_ingredients_required')
    # A location pointer is not an ingredient declaration, even on an official page.
    if re.fullmatch(r'(?:枠外|裏面|別紙|パッケージ).{0,35}(?:記載|参照)',text):
        return dict(result,rule_result='UNKNOWN',reason='ingredient_label_location_only')
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
    # Alcoholic drinks often list only grains, grapes or preservatives.
    # Product identity is essential: ingredients alone must not mark wine/beer HALAL.
    name=unicodedata.normalize('NFKC',str(product_name or '')).lower()
    if not re.search(r'ノンアルコール|ノンアル|アルコール0|アルコールゼロ',name):
        alcohol=re.search(r'ウイスキー|ウィスキー|焼酎|ビール|清酒|日本酒|ワイン(?!ビネガー|酢)|ソーヴィニヨン|シャンパン|whisk(?:y|ey)|ロンドンドライジン|芳醇(?:芋|麦)|(?:麦|芋)職人|鬼ころし|彩の香\s*(?:麦|芋)',name)
        if alcohol:hits.append({'rule':'alcoholic_product_name','text':alcohol.group(0)})
    # Sake lees may carry residual alcohol; a complete ingredient declaration
    # is not enough to certify suitability. Do not auto-mark these as HALAL.
    # Explicitly prohibited ingredients still retain their existing rule hits.
    if not hits and (m:=re.search(r'酒粕|酒かす|\bsake lees\b',text)):
        return dict(result,rule_result='UNKNOWN',
                    matched_terms=[{'rule':'sake_lees_requires_review','text':m.group(0)}],
                    reason='sake_lees_requires_residual_alcohol_review')
    return dict(result,rule_result='HARAM' if hits else 'HALAL',matched_terms=hits,
                reason='matched_user_prohibited_terms' if hits else 'no_user_prohibited_term_in_displayed_ingredients')
