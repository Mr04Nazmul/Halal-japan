export type IngredientFinding={ingredient:string;severity:'prohibited'|'uncertain';reason:string};
export type IngredientDecision={verdict:'haram_ingredient'|'needs_review'|'certified'|'ingredient_clear'|'unknown';reasons:string[];confidence:'high'|'medium'|'low';findings:IngredientFinding[];};

/**
 * Ingredient-only screening. No database source is treated as a halal certificate
 * without separate, product-specific certification evidence.
 * This function never infers the source of an ambiguous additive.
 */
export function ingredientDecision(input:string|null|undefined, certificateValid=false, completeManufacturerIngredients=false):IngredientDecision{
 const original=(input||'').normalize('NFKC').toLowerCase().trim();
 if(!original)return {verdict:'unknown',reasons:['Ingredient information is unavailable. Scan the 原材料名 section or obtain an official product label.'],confidence:'low',findings:[]};
 // Labels such as "halal", "organic" or "no additives" are not an ingredient list.
 if(/^(?:halal|ハラール|認証済み|certified|無添加|organic|オーガニック)(?:\s|、|,|。)*(?:豚肉不使用|ゼラチン不使用|アルコール不使用)?(?:\s|、|,|。)*$/.test(original))return {verdict:'unknown',reasons:['Marketing or absence claims alone are not a complete ingredient declaration.'],confidence:'low',findings:[]};

 // Do not treat precautionary allergen/factory statements as actual ingredients.
 // These warnings are important for allergies, but not evidence that the food contains pork.
 let s=original
  .replace(/(?:本品|本製品|同一工場|同じ工場|当工場|製造工場)[^。\n]{0,180}(?:製造|取り扱|使用|含む)[^。\n]{0,80}。?/g,' ')
  .replace(/(?:may contain traces? of|manufactured in (?:a )?facility that (?:also )?processes)[^.。\n]*/g,' ')
  .replace(/(?:コンタミネーション|交差接触)[^。\n]{0,100}。?/g,' ');

 // Explicit *absence* statements must not trigger forbidden-ingredient matches.
 // Only remove the explicit negative claim; keep any later positive declaration intact.
 s=s
  .replace(/(?:豚肉|豚脂|豚骨|豚由来(?:原料|成分|エキス)?|ポークエキス|ポーク|ラード|ゼラチン|香料|乳化剤|酒精|アルコール)\s*(?:は|を)?\s*(?:不使用|無添加|含ま(?:ない|れていません)|ゼロ)/g,' ')
  .replace(/(?:no added|no|without|free from)\s+(?:pork|lard|porcine|gelatin|gelatine|emulsifier|flavou?ring|alcohol|ethanol)(?:\s+ingredients?)?/g,' ')
  .replace(/(?:pork|gelatin|gelatine|alcohol|ethanol|lard|emulsifier|flavou?ring)[-\s]?free\b/g,' ')
  .replace(/(?:ノンアルコール|アルコールフリー|ゼラチンフリー|ポークフリー)/g,' ');

 // Product-specific provenance: plant-sourced additives named as such are not
 // treated the same as additives whose source is omitted.
 s=s
  .replace(/(?:植物性|植物由来|大豆由来|ひまわり由来|なたね由来)\s*(?:の)?\s*乳化剤/g,' plant_source_verified ')
  .replace(/乳化剤\s*[(（]\s*(?:植物性|植物由来|大豆由来|ひまわり由来|なたね由来)\s*[)）]/g,' plant_source_verified ')
  .replace(/(?:plant[- ]based|vegetable[- ]derived|soy[- ]derived)\s+emulsifiers?\b/g,' plant_source_verified ');

 const terms:{label:string;pattern:RegExp;severity:'prohibited'|'uncertain';reason:string}[]=[
  {label:'Pork or pork-derived ingredient',pattern:/(?:豚肉|豚脂|豚骨|豚エキス|豚由来|ポーク|ラード|(?:^|[^a-z])(?:pork|porcine|lard)(?:$|[^a-z]))/,severity:'prohibited',reason:'Pork-derived ingredient identified in the declaration.'},
  {label:'Gelatin / ゼラチン',pattern:/(?:ゼラチン|(?:^|[^a-z])gelatine?(?:$|[^a-z]))/,severity:'prohibited',reason:'Gelatin is flagged as HARAM under this app’s strict precautionary rule. Source-specific halal rulings may differ; confirm certification if relevant.'},
  {label:'Alcoholic cooking wine',pattern:/(?:料理酒|本みりん|飲用酒|(?:^|[^a-z])(?:cooking sake|hon-mirin|rice wine)(?:$|[^a-z]))/,severity:'prohibited',reason:'Alcoholic cooking wine or hon-mirin is declared.'},
  {label:'Emulsifier origin',pattern:/(?:乳化剤|(?:^|[^a-z])(?:emulsifiers?|e[\s-]?47[12])(?:$|[^a-z0-9]))/,severity:'uncertain',reason:'Emulsifier origin is not confirmed as plant, microbial or halal-certified.'},
  {label:'Flavoring origin',pattern:/(?:香料|(?:^|[^a-z])(?:flavou?rings?|flavou?r agents?)(?:$|[^a-z]))/,severity:'uncertain',reason:'Flavoring carriers or extraction methods may require manufacturer confirmation.'},
  {label:'Meat and broth origin',pattern:/(?:肉エキス|牛肉|鶏肉|チキンエキス|ビーフエキス|鶏ガラスープ|肉骨粉|(?:^|[^a-z])(?:chicken|beef|meat extracts?|chicken extracts?|beef extracts?|meat broth)(?:$|[^a-z]))/,severity:'uncertain',reason:'Non-pork meat, extract or broth needs source and slaughter verification.'},
  {label:'Enzyme source',pattern:/(?:酵素|レンネット|(?:^|[^a-z])(?:enzymes?|rennet)(?:$|[^a-z]))/,severity:'uncertain',reason:'Enzymes and rennet can have animal or microbial origins.'},
  {label:'Alcohol-related ingredients',pattern:/(?:酒精|アルコール|みりん|洋酒|酒粕|(?:^|[^a-z])(?:ethanol|alcohol|wine|rum|sake)(?:$|[^a-z]))/,severity:'uncertain',reason:'Alcohol-related component or seasoning requires product-specific assessment.'},
  {label:'Animal or processed-source ingredient',pattern:/(?:コラーゲン|プラセンタ|レシチン|加工油脂|たんぱく加水分解物|発酵調味料|マーガリン|ショートニング|動物油脂|豚以外の動物性油脂|(?:^|[^a-z])(?:collagen|placenta|lecithin|processed fat|hydroly[sz]ed protein|fermented seasoning|margarine|shortening|animal fat)(?:$|[^a-z]))/,severity:'uncertain',reason:'The source or processing of this ingredient needs verification.'}
 ];
 const findings:IngredientFinding[]=[];
 for(const term of terms){if(term.pattern.test(s))findings.push({ingredient:term.label,severity:term.severity,reason:term.reason});}
 const prohibited=findings.filter(f=>f.severity==='prohibited');
 if(prohibited.length)return {verdict:'haram_ingredient',reasons:prohibited.map(f=>f.reason),confidence:'high',findings};
 // The caller must separately establish an authentic, in-date, exact-product
 // certificate before it is allowed to pass certificateValid=true.
 if(certificateValid)return {verdict:'certified',reasons:['Product-specific halal certificate indicated by a separately verified record; confirm certificate scope and expiry.'],confidence:'high',findings};
 if(!s.replace(/[\s,:、/／・()（）\-]/g,'').trim())return {verdict:'unknown',reasons:['Only absence claims or factory notices were supplied. Full product ingredient list is still needed.'],confidence:'low',findings:[]};
 if(findings.length)return {verdict:'needs_review',reasons:findings.map(f=>f.reason),confidence:'medium',findings};
 if(completeManufacturerIngredients)return {verdict:'ingredient_clear',reasons:['HALAL · Ingredient Check only: no flagged ingredient in the complete manufacturer declaration. Not certified; processing and cross-contact are not verified.'],confidence:'medium',findings};
 return {verdict:'needs_review',reasons:['No clearly prohibited ingredients detected in the available text, but its completeness, ingredient origins and halal certification have NOT been verified.'],confidence:'low',findings};
}
