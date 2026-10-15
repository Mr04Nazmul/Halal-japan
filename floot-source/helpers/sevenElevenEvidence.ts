/** Seven-Eleven-specific decision evidence guard.
 * Store listing or third-party excerpts can identify an item / ingredient lead,
 * but cannot certify halal or verify a current recipe.
 * Full-label reviews require dated source evidence for this exact product.
 */
type ResultLike={
 found:boolean;name?:string;brand?:string|null;source?:string;
 barcode?:string|null;ingredients?:string|null;
 verdict:'haram_ingredient'|'needs_review'|'certified'|'naturally_halal'|'ingredient_clear'|'unknown';
 reasons:string[];confidence?:'high'|'medium'|'low';
 findings?:{ingredient:string;severity:'prohibited'|'uncertain';reason:string}[];
 manufacturerEvidence?:{type:string;url:string|null;issuer:string|null;reviewedAt:string|null}[];
 coverageNote?:string;certificate?:{status:'verified'}|null;
};
export function isSevenElevenFood(row:ResultLike):boolean{
 const text=[row.brand,row.source].filter(Boolean).join(' ').normalize('NFKC').toLocaleLowerCase();
 return /7[-\s]?eleven|seven\s?premium|セブン(?:イレブン|プレミアム)/i.test(text);
}
function hasCurrentFullPackageEvidence(row:ResultLike):boolean{
 if(!row.barcode || !/^(?:\d{8}|\d{12,14})$/.test(row.barcode))return false;
 return (row.manufacturerEvidence||[]).some(e=>{
  if(e.type!=='reviewed_current_complete_package_label')return false;
  if(e.issuer!=='Seven-Eleven Japan' || !e.reviewedAt || !e.url)return false;
  if(!/^https:\/\/www\.sej\.co\.jp\//i.test(e.url))return false;
  if(!/^\d{4}-\d{2}-\d{2}$/.test(e.reviewedAt))return false;
  const d=Date.parse(e.reviewedAt+'T00:00:00.000Z');
  const days=(Date.now()-d)/86400000;
  return Number.isFinite(days)&&days>=0&&days<=120;
 });
}
export function guardSevenElevenVerdict<T extends ResultLike>(row:T):T{
 if(!row.found || !isSevenElevenFood(row))return row;
 if(row.verdict==='certified'&&row.certificate?.status==='verified')return row;
 if(row.verdict==='haram_ingredient'&&!hasCurrentFullPackageEvidence(row)){
  return {...row,verdict:'needs_review',confidence:'low',
   reasons:['Potentially prohibited ingredient is reported in available text, but an up-to-date, exact-product manufacturer/full-package declaration is not yet reviewed.',...row.reasons],
   coverageNote:(row.coverageNote||'')+' 7-Eleven strict check: treat third-party ingredient excerpts as AVOID/VERIFY, not a verified religious verdict.'};
 }
 if(row.verdict==='ingredient_clear'||row.verdict==='naturally_halal'||row.verdict==='certified'){
  return {...row,verdict:'needs_review',confidence:'low',
   reasons:['No active exact-product halal certification is on file. Ingredient screening or a store listing alone cannot establish HALAL.',...row.reasons],
   coverageNote:(row.coverageNote||'')+' 7-Eleven strict check: HALAL requires validated exact-product certification.'};
 }
 return row;
}
