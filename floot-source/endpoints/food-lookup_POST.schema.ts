import {z} from 'zod';
import {ingredientDecision} from '../helpers/ingredientDecision';
import {yamayoProducts} from '../helpers/yamayoProducts';
import {topvaluProducts} from '../helpers/topvaluProducts';
import {guardSevenElevenVerdict} from '../helpers/sevenElevenEvidence';
import {sevenOfficialItems} from '../helpers/sevenOfficialCatalog';
import {manufacturerDrinks} from '../helpers/manufacturerDrinks';
import {extraManufacturerDrinks} from '../helpers/extraManufacturerDrinks';
import {verifiedFoodRecords} from '../helpers/verifiedFoodRecords';
import {findVerifiedHalalCertificate,type DisplayHalalCertificate} from '../helpers/verifiedHalalCertificates';
export const schema=z.object({query:z.string().trim().min(2).max(140)});
export type LookupResult={found:boolean; name?:string; barcode?:string|null; brand?:string|null; ingredients?:string|null; image?:string|null; source?:string; productUrl?:string|null; verdict:'haram_ingredient'|'needs_review'|'certified'|'naturally_halal'|'ingredient_clear'|'unknown'; reasons:string[]; confidence?:'high'|'medium'|'low'; findings?:{ingredient:string;severity:'prohibited'|'uncertain';reason:string}[]; manufacturerEvidence?:{type:string;url:string|null;issuer:string|null;reviewedAt:string|null}[]; coverageNote?:string; certificate?:DisplayHalalCertificate|null;};
const SUPA='https://vjygltfnrmyghlwyjtwu.supabase.co';
const PUBLIC_KEY='sb_publishable_SL6n4Q0t_AxHywHM6iMkpg_bm-lx_Oh';

// EAN-13, UPC-A and GTIN-14 can identify the same retail item with leading zeroes.
// Keep 8-digit EAN codes intact; never strip non-zero prefixes.
function barcodeVariants(code:string):string[]{
 if(!/^\d{8,14}$/.test(code))return [];
 const normalized=code.padStart(14,'0');
 const variants=new Set<string>([code]);
 for(const len of [12,13,14]){
  const prefix=normalized.slice(0,14-len);
  if(/^0*$/.test(prefix))variants.add(normalized.slice(14-len));
 }
 return Array.from(variants).filter(v=>/^\d{8,14}$/.test(v));
}
function barcodeEquivalent(left:string,right:string):boolean{
 return /^\d{8,14}$/.test(String(left))&&/^\d{8,14}$/.test(String(right))
  &&String(left).padStart(14,'0')===String(right).padStart(14,'0');
}

// The public browser uses a single-item Edge Function. No direct table REST reads.
// This is a legacy PUBLIC anon JWT, never a service_role/secret key.
const CATALOG_ANON_JWT='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZqeWdsdGZucm15Z2hsd3lqdHd1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTEyNDI1NDEsImV4cCI6MjEwNjgxODU0MX0.nwq8t1ybnwBFIYNmc1h8tbIbCGUE9FZMQErPLD3ECdQ';
async function lookupSaved(query:string,isBarcode:boolean){
 const u=new URL(SUPA+'/functions/v1/jhc-catalog-lookup');
 if(isBarcode)u.searchParams.set('jan_code',query);
 else u.searchParams.set('query',query);
 const r=await fetch(u,{headers:{apikey:PUBLIC_KEY,Authorization:'Bearer '+CATALOG_ANON_JWT},signal:AbortSignal.timeout(8000)});
 if(!r.ok)throw Error('Protected catalogue lookup unavailable HTTP '+r.status);
 const body=await r.json();
 return body.record||null;
}

const wholeFoods:Record<string,string>={
 'banana':'Banana (whole fresh fruit)','কলা':'কলা (তাজা ফল)','バナナ':'バナナ（生の果物）',
 'apple':'Apple (whole fresh fruit)','আপেল':'আপেল (তাজা ফল)','りんご':'りんご（生の果物）',
 'orange':'Orange (whole fresh fruit)','কমলা':'কমলা (তাজা ফল)','オレンジ':'オレンジ（生の果物）',
 'mango':'Mango (whole fresh fruit)','আম':'আম (তাজা ফল)','マンゴー':'マンゴー（生の果物）',
 'grapes':'Grapes (whole fresh fruit)','আঙুর':'আঙুর (তাজা ফল)','ぶどう':'ぶどう（生の果物）',
 'rice':'Rice (plain, uncooked)','চাল':'চাল (সাধারণ)','米':'米（無添加）',
 'potato':'Potato (whole fresh vegetable)','আলু':'আলু (তাজা সবজি)','じゃがいも':'じゃがいも（生の野菜）'
};
// Separate Open Food Facts Japan research feed (ODbL): exact barcode or named
// product leads, never treated as halal certification or manufacturer confirmation.
type JapanResearchRow={code:string;product_name:string;brands?:string;ingredients_text?:string;source_url?:string;license?:string;};
let japanResearchRows:JapanResearchRow[]|null=null;
let japanResearchPending:Promise<JapanResearchRow[]>|null=null;
async function readJapanResearch():Promise<JapanResearchRow[]>{
 if(japanResearchRows)return japanResearchRows;
 if(!japanResearchPending)japanResearchPending=(async()=>{
  // Import both the incremental 10k dataset and older source-attributed snapshot.
  // These are research leads, not manufacturer-verified halal products.
  const files:[string,string][]=[
   ['./data/openfoodfacts-japan.json','products'],
   ['./data/off-japan-research.json','records']
  ];
  const sets=await Promise.all(files.map(async([url,key])=>{
   try{
    const r=await fetch(url,{signal:AbortSignal.timeout(20000)});
    if(!r.ok)return [];
    const j=await r.json();
    if(j.license!=='ODbL-1.0'||!Array.isArray(j[key]))return [];
    return j[key] as JapanResearchRow[];
   }catch{return [];}
  }));
  const byCode=new Map<string,JapanResearchRow>();
  for(const rows of sets)for(const p of rows){
   const code=String(p.code||'');
   if(!/^\d{8,14}$/.test(code)||!p.product_name)continue;
   const prev=byCode.get(code);
   if(!prev||(!prev.ingredients_text&&p.ingredients_text))byCode.set(code,p);
  }
  japanResearchRows=Array.from(byCode.values());
  return japanResearchRows;
 })().finally(()=>{japanResearchPending=null});
 return japanResearchPending;
}
async function lookupJapanResearch(query:string,isBarcode:boolean):Promise<LookupResult|null>{
 const rows=await readJapanResearch();
 const lower=query.toLocaleLowerCase();
 const matches=rows.filter(p=>isBarcode?barcodeEquivalent(p.code,query):(p.product_name+' '+(p.brands||'')).toLocaleLowerCase().includes(lower));
 if(!matches.length)return null;
 matches.sort((a,b)=>Number(!!b.ingredients_text?.trim())-Number(!!a.ingredients_text?.trim()));
 const p=matches[0],ingredients=p.ingredients_text||null;
 return {found:true,name:p.product_name,barcode:p.code,brand:p.brands||null,ingredients,
  image:null,source:'Open Food Facts Japan research (ODbL; community-contributed)',
  productUrl:p.source_url||'https://world.openfoodfacts.org/product/'+encodeURIComponent(p.code),
  ...ingredientDecision(ingredients),coverageNote:'Japan-tagged Open Food Facts community snapshot, not verified manufacturer ingredients or halal certification. Check the actual label.'};
}

// Supplemental Open Food Facts barcode shards. Loaded on demand; never display
// worldwide-only records as evidence a product is stocked or certified in Japan.
type WorldProduct={code:string;product_name:string;brands?:string;ingredients_text?:string;scope:string;};
const worldBarcodeCache=new Map<string,WorldProduct[]>();
let worldNameIndex: Array<[string,string,string,string]>|null=null;
let worldNamePending:Promise<Array<[string,string,string,string]>>|null=null;
async function readWorldBarcode(code:string):Promise<WorldProduct|null>{
 for(const candidate of barcodeVariants(code)){
  const key=candidate.slice(0,3);
  let records=worldBarcodeCache.get(key);
  if(!records){
   try{
    const res=await fetch('./data/world-food-shards/'+key+'.json',{signal:AbortSignal.timeout(6500)});
    if(!res.ok){
     if(res.status===404)worldBarcodeCache.set(key,[]);
     continue;
    }
    const body=await res.json();
    if(body.license!=='ODbL-1.0'||!Array.isArray(body.records))continue;
    records=body.records as WorldProduct[];
    if(worldBarcodeCache.size>=12)worldBarcodeCache.delete(worldBarcodeCache.keys().next().value as string);
    worldBarcodeCache.set(key,records);
   }catch{continue;}
  }
  const match=records.find(row=>barcodeEquivalent(row.code,code));
  if(match)return match;
 }
 return null;
}
async function readWorldNameIndex():Promise<Array<[string,string,string,string]>>{
 if(worldNameIndex)return worldNameIndex;
 if(!worldNamePending)worldNamePending=(async()=>{
  try{
   const res=await fetch('./data/world-food-name-index.json',{signal:AbortSignal.timeout(20000)});
   if(!res.ok)return [];
   const data=await res.json();
   if(data.license!=='ODbL-1.0'||!Array.isArray(data.records))return [];
   worldNameIndex=data.records as Array<[string,string,string,string]>;
   return worldNameIndex;
  }catch{return []}
 })().finally(()=>{worldNamePending=null});
 return worldNamePending;
}
async function lookupSupplementaryFood(query:string,isBarcode:boolean):Promise<LookupResult|null>{
 let row:WorldProduct|null=null;
 if(isBarcode){row=await readWorldBarcode(query)}
 else if(query.length>=3){
  const idx=await readWorldNameIndex();
  const lower=query.toLocaleLowerCase();
  // Prefer Japan-related indicators, but they do not prove Japanese availability.
  const match=idx.find(([code,name,brand,scope])=>scope!=='worldwide_only'&&
      (name+' '+brand+' '+code).toLocaleLowerCase().includes(lower))||
   idx.find(([code,name,brand])=>(name+' '+brand+' '+code).toLocaleLowerCase().includes(lower));
  if(match)row=await readWorldBarcode(match[0]);
 }
 if(!row)return null;
 const scopeNote:Record<string,string>={
  japan_country_tag:'Country tagged Japan by a community contributor; not manufacturer verified.',
  japanese_barcode_prefix_only:'Barcode prefix may be registered through GS1 Japan; it DOES NOT confirm Japanese store availability.',
  japanese_name_only:'Japanese-looking name only; Japanese store availability is NOT confirmed.',
  worldwide_only:'GLOBAL product only; NOT confirmed to be sold in Japan.'
 };
 return {found:true,name:row.product_name,barcode:row.code,brand:row.brands||null,
  ingredients:row.ingredients_text||null,image:null,
  source:'Open Food Facts worldwide supplemental food index (community data, ODbL)',
  productUrl:'https://world.openfoodfacts.org/product/'+encodeURIComponent(row.code),
  ...ingredientDecision(row.ingredients_text||null),
  coverageNote:(scopeNote[row.scope]||'Market availability unverified')+
  ' Ingredient text and halal certification have NOT been independently verified. Check the current physical label.'};
}

async function lookupProductWithoutCertificate(body:z.infer<typeof schema>):Promise<LookupResult>{
 const query=schema.parse(body).query;
 // Manufacturer-supplied JAN and full package ingredients with express reuse permission.
 // Never substitute the JAN of a mixed gift set for an individual juice bottle.
 const yamayo=yamayoProducts.find(p=>
  /^\d{8,14}$/.test(query)?barcodeEquivalent(p.code,query):
  p.name.normalize('NFKC').toLocaleLowerCase()===query.normalize('NFKC').toLocaleLowerCase()
 );
 if(yamayo){
  const decision=ingredientDecision(yamayo.ingredients,false,yamayo.ingredientListComplete);
  return {found:true,name:yamayo.name,barcode:yamayo.code,brand:yamayo.brand,
   ingredients:yamayo.ingredients,image:null,
   source:'Yamayo manufacturer-supplied JAN and full package 原材料名 (reuse authorized)',
   productUrl:yamayo.sourceUrl,...decision,
   manufacturerEvidence:[{type:yamayo.evidence,issuer:'株式会社ヤマヨ',
    url:yamayo.sourceUrl,reviewedAt:yamayo.checkedAt}],
   coverageNote:'Yamayo supplied original product labels and JAN spreadsheets in October 2026 and explicitly permitted secondary use of product information. The listed ingredients are product-specific; gift sets are excluded. HALAL · Ingredient Check is not religious certification. Formulations can change.'};
 }
 // JAN-exact product ingredient information from AEON's public TOPVALU catalogue.
 // Explicitly separate current-package confirmation from an online declaration.
 const topvalu=topvaluProducts.find(p=>
  /^\d{8,14}$/.test(query)?barcodeEquivalent(p.code,query):
  p.name.normalize('NFKC').toLocaleLowerCase()===query.normalize('NFKC').toLocaleLowerCase()
 );
 if(topvalu){
  const statement=topvalu.ingredients+(topvalu.additives?'／'+topvalu.additives:'');
  const decision=ingredientDecision(statement,false,topvalu.officialOnlineIngredientDeclaration);
  return {found:true,name:topvalu.name,barcode:topvalu.code,brand:topvalu.brand,
   ingredients:statement,image:null,source:'AEON TOPVALU public official product page (JAN, 原材料名 and 添加物)',
   productUrl:topvalu.sourceUrl,...decision,
   manufacturerEvidence:[{type:'official online product ingredient and additive declaration (NOT an independent halal certificate)',
    issuer:'AEON TOPVALU',url:topvalu.sourceUrl,reviewedAt:topvalu.checkedAt}],
   coverageNote:'Exact JAN matched to TOPVALU official online ingredient and additive listing, checked '+topvalu.checkedAt+'. This is an ingredient-screening result, NOT halal certification, nor independent confirmation of ingredient manufacturing origin. TOPVALU says formulas can change and actual package information prevails. No right to bulk republish the entire TOPVALU product catalogue is assumed.'};
 }
 // Seven-Eleven fresh-food in-store EAN code: observed on user's photographed package. Not a globally registered manufacturer JAN.
 if(query==='2044706200126'){
   return {found:true,name:'CAFE BOX チキンケバブライス / Chicken Kebab Rice',barcode:query,brand:'7-Eleven Japan',ingredients:null,image:null,source:'User-provided package photograph (barcode) + Seven-Eleven public product listing (name)',productUrl:'https://www.sej.co.jp/products/a/bento/',...ingredientDecision(null),manufacturerEvidence:[{type:'Product identity and in-store code from packaging; ingredient declaration not yet supplied',url:'https://www.sej.co.jp/products/a/bento/',issuer:'Seven-Eleven Japan',reviewedAt:null}],coverageNote:'Package-front matched to CAFE BOX チキンケバブライス; the 20-prefix may be an in-store code. This particular package ingredient list, additive sources and halal certification are NOT verified. Price/region/version may vary.'};
 }
 // Barcode-matched official manufacturer product record, distinct from a halal certificate.
 if(query==='4902179023964'){
   const ingredients='糖類（砂糖（タイ製造）、果糖ぶどう糖液糖）、全粉乳、コーヒー、脱脂粉乳、ココナッツオイル、デキストリン、食塩／カラメル色素、香料、乳化剤、ビタミンＣ、カゼインＮａ、甘味料（アセスルファムK、ステビア）';
   return {found:true,name:'Ajīwau Cafe Au Lait 500ml / あじわうカフェオレ 500ml',barcode:query,brand:'Sangaria / サンガリア',ingredients,image:null,source:'Sangaria official manufacturer ingredients',productUrl:'https://sangaria.co.jp/products/ajiwau/',...ingredientDecision(ingredients,false,true),manufacturerEvidence:[{type:'official ingredient list',url:'https://sangaria.co.jp/products/ajiwau/',issuer:'Sangaria',reviewedAt:null}],coverageNote:'Official JAN-matched ingredient list. Flavoring and emulsifier sources are not certified in this record; HALAL LV3 shown in another app is not independent manufacturer certification.'};
 }
 const isBarcode=/^\d{8,14}$/.test(query);
 // An official name/URL proves identity only, never JAN, 原材料名 or halal suitability.
 if(!isBarcode){
  const normalize=(value:string)=>value.replace(/\\s+/g,'').toLocaleLowerCase();
  const exact=sevenOfficialItems.find(item=>normalize(item.name)===normalize(query));
  if(exact)return {found:true,name:exact.name,barcode:null,brand:'7-Eleven Japan',ingredients:null,
    image:null,source:'7-Eleven Japan official product listing (identity only)',productUrl:exact.url,
    ...ingredientDecision(null),manufacturerEvidence:[],
    coverageNote:'Official product name identified. JAN, current full ingredient label, additives and halal status are NOT verified. Check package 原材料名; availability and formulations vary by region and date.'};
 }
 // Manufacturer-confirmed Meiji Tokachi drinking yogurt (400g).
 // Two official JANs correspond to different product revisions; never conflate certification with ingredients.
 const meijiTokachiPage:Record<string,string>={
   '4902705133099':'https://www.meiji.co.jp/products/yogurt/4902705133099.html',
   '4902705131279':'https://www.meiji.co.jp/products/yogurt/4902705131279.html'
 };
 if(meijiTokachiPage[query]){
   const ingredients='乳製品（国内製造、外国製造）、砂糖';
   const productUrl=meijiTokachiPage[query];
   return {found:true,name:'明治北海道十勝ミルクきわだつのむヨーグルト 400g / Meiji Tokachi Drinking Yogurt',barcode:query,brand:'Meiji / 明治',ingredients,image:null,source:'Meiji official manufacturer product information',productUrl,...ingredientDecision(ingredients),manufacturerEvidence:[{type:'manufacturer ingredient declaration (NOT halal certification)',url:productUrl,issuer:'Meiji',reviewedAt:'2026-10-15'}],coverageNote:'Official listed ingredients are dairy ingredients and sugar. No prohibited ingredient is identified in this declaration, but halal certification has NOT been confirmed. Check the barcode and ingredients on your physical package; revisions may differ.'};
 }
 const selectedFood=verifiedFoodRecords.find(p=>p.barcode===query)||
 (!isBarcode?verifiedFoodRecords.find(p=>p.name.toLowerCase()===query.toLowerCase()||p.nameJa===query):undefined);
 if(selectedFood) return {found:true,name:selectedFood.nameJa+' / '+selectedFood.name,barcode:selectedFood.barcode,brand:selectedFood.manufacturer,ingredients:selectedFood.ingredients,image:null,source:'Nissin official ingredient excerpt',productUrl:selectedFood.url,...ingredientDecision(selectedFood.ingredients),manufacturerEvidence:[{type:'Manufacturer full ingredient declaration',url:selectedFood.url,issuer:'Nissin Foods',reviewedAt:null}],coverageNote:'Only identified prohibited ingredients are summarized here; this is NOT the full ingredients list. Open the official product page for the complete label.'};

 const norm=query.toLocaleLowerCase();
 const allManufacturers=[...manufacturerDrinks,...extraManufacturerDrinks];
 const verified=allManufacturers.find(p=>p.barcode===query)||
   (!isBarcode?allManufacturers.find(p=>p.name.toLocaleLowerCase()===norm)||
   allManufacturers.find(p=>p.name.toLocaleLowerCase().includes(norm)):undefined);
 if(verified){
   const decision=ingredientDecision(verified.ingredients,false,true);
   return {found:true,name:verified.name,barcode:verified.barcode,brand:verified.manufacturer,ingredients:verified.ingredients,image:null,source:verified.manufacturer+' official manufacturer product catalogue',productUrl:verified.url,...decision,manufacturerEvidence:[{type:'manufacturer product and ingredients',url:verified.url,issuer:verified.manufacturer,reviewedAt:null}],coverageNote:'JAN and ingredient information sourced from manufacturer. This is NOT halal certification; verify package and ingredient origins.'};
 }

 // Start independent lookups together, rather than waiting for a slow external
 // database before even checking the already-published local barcode shards.
 const savedTask=lookupSaved(query,isBarcode).catch(e=>{console.warn('Saved product catalogue unavailable',e);return null;});
 const japanTask=lookupJapanResearch(query,isBarcode).catch(()=>null);
 const worldTask=lookupSupplementaryFood(query,isBarcode).catch(()=>null);
 const saved=await savedTask;
 // A name/barcode-only record is a useful identification, not an ingredient answer.
 // Prefer ingredient-bearing local records and continue searching otherwise.
 let noIngredientFallback:LookupResult|null=null;
 if(saved && (!isBarcode || barcodeEquivalent(String(saved.barcode||''),query))){
  const fromSevenPremiumPackageNotes=String(saved.evidence_source||'').includes('selected excerpts');
  const fromYamayoManufacturer=String(saved.evidence_source||'').startsWith('Manufacturer Yamayo ');
  const yamayoGummy=fromYamayoManufacturer&&String(saved.category||'').includes('Gummy');
  const yamayoGift=fromYamayoManufacturer&&String(saved.category||'').includes('gift set');
  const yamayoCoverage=yamayoGummy
   ?'Yamayo manufacturer confirmation (October 2026): gelatin IS used in this gummy; full ingredient label was not supplied. No halal certification. Confirm current package for other ingredients.'
   :yamayoGift
   ?'Yamayo manufacturer JAN catalog plus current individual juice labels (October 2026): ingredient text is COMPILED FROM THE INCLUDED JUICE COMPONENTS, not a separate gift box ingredient label. No halal certification.'
   :'Yamayo manufacturer original juice label supplied with written permission in October 2026. This is an ingredient label, NOT a halal certificate. Always check current packaging; formulation may change.';
  const savedResult:LookupResult={found:true,name:saved.name_ja||saved.name,barcode:saved.barcode,brand:saved.brand,ingredients:saved.ingredients,image:saved.image_url,source:saved.evidence_source||'Floot catalogue snapshot',productUrl:saved.evidence_url,...ingredientDecision(saved.ingredients),manufacturerEvidence:[],coverageNote:fromYamayoManufacturer?yamayoCoverage:fromSevenPremiumPackageNotes?'Seven Premium package-ingredient excerpt sourced from a THIRD-PARTY review. This is NOT the complete label and has not been confirmed by Seven-Eleven or the manufacturer. The scanned product, ingredients and availability may have changed. Check current packaging; do not assume Halal certification.':'Migrated product record; NOT independently certified. Ingredient details may be outdated.'};
  if(String(saved.ingredients||'').trim())return savedResult;
  noIngredientFallback=savedResult;
 }
 if(isBarcode){
  const indexedWorld=await worldTask;
  if(indexedWorld?.ingredients?.trim())return indexedWorld;
  if(indexedWorld&&!noIngredientFallback)noIngredientFallback=indexedWorld;
  const offlineJapan=await japanTask;
  if(offlineJapan?.ingredients?.trim())return offlineJapan;
  if(offlineJapan&&!noIngredientFallback)noIngredientFallback=offlineJapan;
 }else{
  const offlineJapan=await japanTask;
  if(offlineJapan?.ingredients?.trim())return offlineJapan;
  if(offlineJapan&&!noIngredientFallback)noIngredientFallback=offlineJapan;
  const indexedWorld=await worldTask;
  if(indexedWorld?.ingredients?.trim())return indexedWorld;
  if(indexedWorld&&!noIngredientFallback)noIngredientFallback=indexedWorld;
 }
 // Open Food Facts is community-maintained (ODbL); query on demand instead of copying its entire database.
 const api=isBarcode
  ?'https://world.openfoodfacts.org/api/v2/product/'+encodeURIComponent(query)+'.json?fields=code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,image_front_small_url,image_front_url,url'
  :'https://world.openfoodfacts.org/cgi/search.pl?search_terms='+encodeURIComponent(query)+'&search_simple=1&action=process&json=1&page_size=20&fields=code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,image_front_small_url,image_front_url,url,countries_tags';
 let payload:any;
 try{
  const response=await fetch(api,{headers:{Accept:'application/json'},signal:AbortSignal.timeout(8500)});
  if(!response.ok)throw Error('Open Food Facts HTTP '+response.status);
  payload=await response.json();
 }catch{
  if(noIngredientFallback)return {...noIngredientFallback,coverageNote:(noIngredientFallback.coverageNote||'')+' Live ingredient lookup unavailable; check the current package label.'};
  throw Error('Open Food Facts lookup unavailable. Please try again.');
 }
 const item=isBarcode?(payload.status===1?payload.product:null):
 (payload.products||[]).filter((p:any)=>p.product_name||p.product_name_ja).sort((a:any,b:any)=>{
   const score=(p:any)=>Number((p.countries_tags||[]).includes('en:japan'))*5+Number(!!(p.ingredients_text_ja||p.ingredients_text))*3+Number(!!p.image_front_small_url);
   return score(b)-score(a);
 })[0];
 if(!item)return noIngredientFallback||{found:false,verdict:'unknown',reasons:['No matching public product record; do not assume halal.'],coverageNote:'This standalone GitHub Pages edition queries Open Food Facts; its coverage is incomplete.'};
 if(isBarcode && !barcodeEquivalent(String(item.code||''),query))return noIngredientFallback||{found:false,verdict:'unknown',reasons:['Barcode did not exactly match returned product.']};
 const ingredients=item.ingredients_text_ja||item.ingredients_text||null;
 if(!ingredients && noIngredientFallback)return noIngredientFallback;
 return {found:true,name:item.product_name_ja||item.product_name||'Unnamed product',barcode:item.code||null,brand:item.brands||null,ingredients,image:item.image_front_small_url||item.image_front_url||null,source:'Open Food Facts (community supplied; ODbL attribution)',productUrl:item.url||null,...ingredientDecision(ingredients),manufacturerEvidence:[],coverageNote:'Open Food Facts data is user-contributed under ODbL. Japanese records and labels may be incomplete; no halal certification is implied. Check the exact package.'};
}

/**
 * Only promote exact product/brand/JAN matches in the locally reviewed
 * issuer certificate registry. Public product databases and photos NEVER
 * confer halal certification. Underlying suspicious/prohibited ingredients
 * must not be silently overridden.
 */
export async function postFoodLookup(body:z.infer<typeof schema>):Promise<LookupResult>{
 const result=await lookupProductWithoutCertificate(body);
 if(!result.found)return {...result,certificate:null};
 const cert=findVerifiedHalalCertificate(result.barcode,result.name,result.brand);
 if(!cert || result.verdict==='haram_ingredient')return guardSevenElevenVerdict({...result,certificate:null});
 return guardSevenElevenVerdict({...result,certificate:cert,verdict:'certified',confidence:'high',
  reasons:['An issuer-verified, in-date halal certificate has been matched to this exact product, brand and barcode. Check the source and current packaging.'],
  coverageNote:(result.coverageNote||'')+' Product-specific halal certificate checked against issuer evidence on '+cert.verifiedAt+'.'});
}
