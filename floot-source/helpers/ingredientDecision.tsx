export type IngredientFinding={ingredient:string;severity:'prohibited'|'uncertain';reason:string};
export type IngredientDecision={verdict:'haram_ingredient'|'needs_review'|'certified'|'unknown';reasons:string[];confidence:'high'|'medium'|'low';findings:IngredientFinding[];};
export function ingredientDecision(input:string|null|undefined, certificateValid=false):IngredientDecision{
 const s=(input||'').toLowerCase();
 const rules:{terms:string[];severity:'prohibited'|'uncertain';reason:string}[]=[
 {terms:['pork','porcine','lard','豚肉','豚脂','ラード','ポーク','豚エキス','ポークエキス','bacon','ベーコン','ham (pork)','pork gelatin','豚由来ゼラチン','pig fat'],severity:'prohibited',reason:'Pork-derived ingredient is prohibited.'},
 {terms:['gelatin','ゼラチン'],severity:'uncertain',reason:'Gelatin may be animal-derived; source and halal processing must be verified.'},
 {terms:['emulsifier','乳化剤','e471','e472'],severity:'uncertain',reason:'Emulsifier source can be vegetable or animal-derived; verify manufacturer information.'},
 {terms:['flavoring','flavouring','香料'],severity:'uncertain',reason:'Flavoring carriers and extraction method may require confirmation.'},
 {terms:['meat extract','肉エキス','ビーフエキス','チキンエキス','beef extract','chicken extract'],severity:'uncertain',reason:'Meat-derived ingredients require animal origin and slaughter verification.'},
 {terms:['enzyme','酵素','rennet','レンネット'],severity:'uncertain',reason:'Enzyme source may be microbial or animal; confirm origin.'},
 {terms:['mirin','みりん','料理酒','酒精','ethanol','alcohol','アルコール','wine','rum'],severity:'uncertain',reason:'Alcohol-related ingredient identified; verify formulation and applicable halal standard.'},
 {terms:['shortening','ショートニング','animal fat','動物油脂'],severity:'uncertain',reason:'Fat or shortening source requires verification.'}
 ];
 const findings:IngredientFinding[]=[];
 // Ingredient lists may mention derived ingredients without showing their origin; avoid automatic certification.
 // Explicit pork terms take precedence. Alcohol terms require product context and applicable standard.
 for(const r of rules){const hit=r.terms.find(term=>s.includes(term));if(hit)findings.push({ingredient:hit,severity:r.severity,reason:r.reason})}
 if(findings.some(f=>f.severity==='prohibited'))return {verdict:'haram_ingredient',reasons:findings.map(f=>f.reason),confidence:'high',findings};
 if(certificateValid)return {verdict:'certified',reasons:['Recorded certificate is reviewed and currently valid; verify exact product scope and issuing authority.'],confidence:'high',findings};
 if(!s.trim())return {verdict:'unknown',reasons:['Complete ingredient information is unavailable. No halal conclusion can be drawn.'],confidence:'low',findings};
 if(findings.length)return {verdict:'needs_review',reasons:findings.map(f=>f.reason),confidence:'medium',findings};
 return {verdict:'needs_review',reasons:['No clearly prohibited terms in available ingredients. This is NOT halal certification; sources, processing and cross-contact remain unverified.'],confidence:'low',findings};
}
