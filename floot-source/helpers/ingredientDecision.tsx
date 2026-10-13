export type IngredientFinding={ingredient:string;severity:'prohibited'|'uncertain';reason:string};
export type IngredientDecision={verdict:'haram_ingredient'|'needs_review'|'certified'|'ingredient_clear'|'unknown';reasons:string[];confidence:'high'|'medium'|'low';findings:IngredientFinding[];};
export function ingredientDecision(input:string|null|undefined, certificateValid=false, completeManufacturerIngredients=false):IngredientDecision{
 const s=(input||'').toLowerCase();
 // A declared vegetable/soy-derived emulsifier is not by itself an uncertain animal additive.
 // Normalize only explicit source-qualified phrases; unqualified 乳化剤 still needs review.
 const normalized=s
  .replace(/植物性乳化剤|植物由来乳化剤|植物性の乳化剤|乳化剤[（(](?:植物性|植物由来|大豆由来|ひまわり由来|なたね由来)[）)]/g,' confirmed_plant_emulsifier ')
  .replace(/(?:plant[- ]based|vegetable[- ]derived|soy[- ]derived) emulsifiers?/g,' confirmed_plant_emulsifier ');
 const rules:{terms:string[];severity:'prohibited'|'uncertain';reason:string}[]=[
 {terms:['pork','porcine','lard','豚肉','豚脂','ラード','ポーク','豚エキス','ポークエキス'],severity:'prohibited',reason:'Pork-derived ingredient is prohibited.'},
 {terms:['gelatin','ゼラチン'],severity:'prohibited',reason:'HARAM under this website’s custom strict-screening rule for gelatin; gelatin can also come from permissible sources, so this is not a universal halal ruling.'},
 {terms:['emulsifier','乳化剤','e471','e472'],severity:'uncertain',reason:'Emulsifier source can be vegetable or animal-derived; verify manufacturer information.'},
 {terms:['flavoring','flavouring','香料'],severity:'uncertain',reason:'Flavoring carriers and extraction method may require confirmation.'},
 {terms:['meat extract','肉エキス','ビーフエキス','チキンエキス','beef extract','chicken extract'],severity:'uncertain',reason:'Meat-derived ingredients require animal origin and slaughter verification.'},
 {terms:['enzyme','酵素','rennet','レンネット'],severity:'uncertain',reason:'Enzyme source may be microbial or animal; confirm origin.'},
 {terms:['酒精','ethanol','alcohol','アルコール','wine','rum'],severity:'uncertain',reason:'Alcohol-related ingredient identified; verify formulation and applicable halal standard.'},
 {terms:['料理酒','本みりん','cooking sake','hon-mirin'],severity:'prohibited',reason:'Alcoholic cooking sake or hon-mirin identified.'},
 {terms:['collagen','コラーゲン','placenta','プラセンタ','lecithin','レシチン','加工油脂','processed fat','hydrolyzed protein','たんぱく加水分解物','発酵調味料','fermented seasoning','マーガリン','margarine'],severity:'uncertain',reason:'Source, processing and/or alcohol-related formulation must be verified.'},
 {terms:['shortening','ショートニング','animal fat','動物油脂'],severity:'uncertain',reason:'Fat or shortening source requires verification.'}
 ];
 const findings:IngredientFinding[]=[];
 for(const r of rules){const hit=r.terms.find(term=>(r.terms.includes('乳化剤')?normalized:s).includes(term));if(hit)findings.push({ingredient:hit,severity:r.severity,reason:r.reason})}
 if(findings.some(f=>f.severity==='prohibited'))return {verdict:'haram_ingredient',reasons:findings.map(f=>f.reason),confidence:'high',findings};
 if(certificateValid)return {verdict:'certified',reasons:['Recorded certificate is reviewed and currently valid; verify exact product scope and issuing authority.'],confidence:'high',findings};
 if(!s.trim())return {verdict:'unknown',reasons:['Complete ingredient information is unavailable. No halal conclusion can be drawn.'],confidence:'low',findings};
 if(findings.length)return {verdict:'needs_review',reasons:findings.map(f=>f.reason),confidence:'medium',findings};
 if(completeManufacturerIngredients)return {verdict:'ingredient_clear',reasons:['HALAL (ingredient screen only): no prohibited or source-uncertain ingredient detected in the manufacturer ingredient list. Not halal certified; processing and shared facilities have not been established.'],confidence:'medium',findings};
 return {verdict:'needs_review',reasons:['No clearly prohibited terms in available ingredients. This is NOT halal certification; sources, processing and cross-contact remain unverified.'],confidence:'low',findings};
}
