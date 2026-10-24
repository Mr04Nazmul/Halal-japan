/**
 * Small, manually reviewed reference subset. These records confirm ingredient
 * identity/source questions, NOT a food product's halal certification.
 * The 577-row upstream MIT dataset is PRIVATE pending human review.
 * Original data copyright (c) 2026 Cahya DSN, MIT license:
 * https://github.com/cahyadsn/halal/blob/master/LICENSE
 */
export type ReviewedEcode={
 code:string;
 name:string;
 japanese:string;
 evidence:string;
 sourceUrl:string;
 note:string;
 action:'identity_only'|'verify_source'|'precaution';
 engineSeverity:'uncertain'|'prohibited'|null;
};
export const REVIEWED_ECODES:ReadonlyArray<ReviewedEcode>=[
 {code:'E120',name:'Carmine / Cochineal',japanese:'カルミン酸色素・コチニール色素',evidence:'EFSA: obtained from cochineal insects.',sourceUrl:'https://www.efsa.europa.eu/en/topics/topic/food-additives',note:'Insect-derived colouring. Religious interpretations differ; ask a trusted certifier if necessary. Do not mark a whole product Halal.',action:'precaution',engineSeverity:'uncertain'},
 {code:'E300',name:'Ascorbic acid / Vitamin C',japanese:'アスコルビン酸・ビタミンC',evidence:'EFSA: vitamin C is also known as E300.',sourceUrl:'https://www.efsa.europa.eu/en/topics/topic/food-additives',note:'Identity checked, but this alone is not proof of whole-product halal certification.',action:'identity_only',engineSeverity:null},
 {code:'E322',name:'Lecithins',japanese:'レシチン',evidence:'EFSA: lecithins occur in egg yolks, soybeans and other foods.',sourceUrl:'https://www.efsa.europa.eu/en/topics/topic/food-additives',note:'Source may vary. Confirm origin when required; lecithin code alone does not certify food.',action:'verify_source',engineSeverity:'uncertain'},
 {code:'E406',name:'Agar / Agar-agar',japanese:'寒天・アガー',evidence:'FAO/JECFA: extracted from marine red algae.',sourceUrl:'https://www.fao.org/4/W6355E/w6355e03.htm',note:'Seaweed-derived gelling agent; not equivalent to animal gelatin. This code does not certify the other ingredients.',action:'identity_only',engineSeverity:null},
 {code:'E422',name:'Glycerol',japanese:'グリセリン',evidence:'EFSA EU specification review discusses glycerol from vegetable oils and fats.',sourceUrl:'https://www.efsa.europa.eu/sites/default/files/2024-03/06-emerging-changes-in-eu-specifications-authorised-food-additives.pdf',note:'A specific Japanese supplier or label may require additional source confirmation; an E-number alone is not a certificate.',action:'verify_source',engineSeverity:'uncertain'},
 {code:'E441',name:'Gelatine / Gelatin (legacy E-code)',japanese:'ゼラチン',evidence:'FAO/JECFA: edible gelatin is produced from animal collagen; coding conventions vary internationally.',sourceUrl:'https://www.fao.org/fileadmin/user_upload/jecfa_additives/docs/Monograph1/Additive-171.pdf',note:'Gelatin identity does not establish species. Verify the exact product’s fish, bovine or porcine source and any required halal evidence.',action:'verify_source',engineSeverity:'uncertain'},
 {code:'E471',name:'Mono- and diglycerides of fatty acids',japanese:'脂肪酸グリセリンエステル',evidence:'EFSA: source oils/fats may include plants, tallow or lard.',sourceUrl:'https://efsa.onlinelibrary.wiley.com/doi/full/10.2903/j.efsa.2017.5045',note:'Source must be checked for this exact product. Never assume automatically halal or haram from E471 alone.',action:'verify_source',engineSeverity:'uncertain'}
];
/** Detect only exact, standalone E-codes: no E4412 or E120a suffix matches. */
export function findEcodeMentions(text:string):ReviewedEcode[]{
 const s=String(text||'').normalize('NFKC').toLowerCase();
 return REVIEWED_ECODES.filter(r=>{
  const token=r.code.toLowerCase().slice(1);
  const e=new RegExp('(?:^|[^a-z0-9])e\\s*[- ]?'+token+'(?![a-z0-9])','i');
  const found=e.test(s);if(!found)return false;
  const negative=new RegExp('(?:no|without|free from)\\s+e\\s*[- ]?'+token+'(?![a-z0-9])|(?:^|[^a-z0-9])e\\s*[- ]?'+token+'[- ]?free\\b','i');
  return !negative.test(s);
 });
}

