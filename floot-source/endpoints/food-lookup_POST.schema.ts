import {z} from 'zod';
import {ingredientDecision} from '../helpers/ingredientDecision';
import {manufacturerDrinks} from '../helpers/manufacturerDrinks';
import {extraManufacturerDrinks} from '../helpers/extraManufacturerDrinks';
import {verifiedFoodRecords} from '../helpers/verifiedFoodRecords';
export const schema=z.object({query:z.string().trim().min(2).max(140)});
export type LookupResult={found:boolean; name?:string; barcode?:string|null; brand?:string|null; ingredients?:string|null; image?:string|null; source?:string; productUrl?:string|null; verdict:'haram_ingredient'|'needs_review'|'certified'|'naturally_halal'|'ingredient_clear'|'unknown'; reasons:string[]; confidence?:'high'|'medium'|'low'; findings?:{ingredient:string;severity:'prohibited'|'uncertain';reason:string}[]; manufacturerEvidence?:{type:string;url:string|null;issuer:string|null;reviewedAt:string|null}[]; coverageNote?:string;};
const SUPA='https://vjygltfnrmyghlwyjtwu.supabase.co';
const PUBLIC_KEY='sb_publishable_SL6n4Q0t_AxHywHM6iMkpg_bm-lx_Oh';
async function lookupSaved(query:string,isBarcode:boolean){
 const u=new URL(SUPA+'/rest/v1/jhc_floot_products');
 u.searchParams.set('select','source_id,barcode,name,name_ja,brand,ingredients,image_url,evidence_source,evidence_url,category');
 if(isBarcode)u.searchParams.set('barcode','eq.'+query);
 else u.searchParams.set('or','(name.ilike.*'+query.replace(/[,*()]/g,'')+'*,name_ja.ilike.*'+query.replace(/[,*()]/g,'')+'*,brand.ilike.*'+query.replace(/[,*()]/g,'')+'*)');
 u.searchParams.set('limit','1');
 const r=await fetch(u,{headers:{apikey:PUBLIC_KEY}});
 if(!r.ok)throw Error('Catalogue backend HTTP '+r.status);
 const rows=await r.json();return rows[0]||null;
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
export async function postFoodLookup(body:z.infer<typeof schema>):Promise<LookupResult>{
 const query=schema.parse(body).query;
 // Barcode-matched official manufacturer product record, distinct from a halal certificate.
 if(query==='4902179023964'){
   const ingredients='糖類（砂糖（タイ製造）、果糖ぶどう糖液糖）、全粉乳、コーヒー、脱脂粉乳、ココナッツオイル、デキストリン、食塩／カラメル色素、香料、乳化剤、ビタミンＣ、カゼインＮａ、甘味料（アセスルファムK、ステビア）';
   return {found:true,name:'Ajīwau Cafe Au Lait 500ml / あじわうカフェオレ 500ml',barcode:query,brand:'Sangaria / サンガリア',ingredients,image:null,source:'Sangaria official manufacturer ingredients',productUrl:'https://sangaria.co.jp/products/ajiwau/',...ingredientDecision(ingredients,false,true),manufacturerEvidence:[{type:'official ingredient list',url:'https://sangaria.co.jp/products/ajiwau/',issuer:'Sangaria',reviewedAt:null}],coverageNote:'Official JAN-matched ingredient list. Flavoring and emulsifier sources are not certified in this record; HALAL LV3 shown in another app is not independent manufacturer certification.'};
 }
 const isBarcode=/^[0-9]{8,14}$/.test(query);
 const selectedFood=verifiedFoodRecords.find(p=>p.barcode===query)||
 (!isBarcode?verifiedFoodRecords.find(p=>p.name.toLowerCase()===query.toLowerCase()||p.nameJa===query):undefined);
 if(selectedFood) return {found:true,name:selectedFood.nameJa+' / '+selectedFood.name,barcode:selectedFood.barcode,brand:selectedFood.manufacturer,ingredients:selectedFood.ingredients,image:null,source:'Nissin official ingredient excerpt',productUrl:selectedFood.url,...ingredientDecision(selectedFood.ingredients),manufacturerEvidence:[{type:'Manufacturer ingredient excerpt (not full list)',url:selectedFood.url,issuer:'Nissin Foods',reviewedAt:null}],coverageNote:'Only identified prohibited ingredients are summarized here; this is NOT the full ingredients list. Open the official product page for the complete label.'};

 const norm=query.toLocaleLowerCase();
 const allManufacturers=[...manufacturerDrinks,...extraManufacturerDrinks];
 const verified=allManufacturers.find(p=>p.barcode===query)||
   (!isBarcode?allManufacturers.find(p=>p.name.toLocaleLowerCase()===norm)||
   allManufacturers.find(p=>p.name.toLocaleLowerCase().includes(norm)):undefined);
 if(verified){
   const decision=ingredientDecision(verified.ingredients,false,true);
   return {found:true,name:verified.name,barcode:verified.barcode,brand:verified.manufacturer,ingredients:verified.ingredients,image:null,source:verified.manufacturer+' official manufacturer product catalogue',productUrl:verified.url,...decision,manufacturerEvidence:[{type:'manufacturer product and ingredients',url:verified.url,issuer:verified.manufacturer,reviewedAt:null}],coverageNote:'JAN and ingredient information sourced from manufacturer. This is NOT halal certification; verify package and ingredient origins.'};
 }

 let saved:any=null;
 try{saved=await lookupSaved(query,isBarcode)}catch(e){console.warn('Saved product catalogue unavailable',e)}
 if(saved && (!isBarcode || saved.barcode===query)){
   return {found:true,name:saved.name_ja||saved.name,barcode:saved.barcode,brand:saved.brand,ingredients:saved.ingredients,image:saved.image_url,source:saved.evidence_source||'Floot catalogue snapshot',productUrl:saved.evidence_url,...ingredientDecision(saved.ingredients),manufacturerEvidence:[],coverageNote:'Migrated product record; NOT independently certified. Ingredient details may be outdated.'};
 }
 // Open Food Facts is community-maintained (ODbL); query on demand instead of copying its entire database.
 const api=isBarcode
  ?'https://world.openfoodfacts.org/api/v2/product/'+encodeURIComponent(query)+'.json?fields=code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,image_front_small_url,image_front_url,url'
  :'https://world.openfoodfacts.org/cgi/search.pl?search_terms='+encodeURIComponent(query)+'&search_simple=1&action=process&json=1&page_size=20&fields=code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,image_front_small_url,image_front_url,url,countries_tags';
 const response=await fetch(api,{headers:{Accept:'application/json'}});
 if(!response.ok)throw Error('Open Food Facts lookup unavailable (HTTP '+response.status+'). Please try again.');
 const payload=await response.json();
 const item=isBarcode?(payload.status===1?payload.product:null):
 (payload.products||[]).filter((p:any)=>p.product_name||p.product_name_ja).sort((a:any,b:any)=>{
   const score=(p:any)=>Number((p.countries_tags||[]).includes('en:japan'))*5+Number(!!(p.ingredients_text_ja||p.ingredients_text))*3+Number(!!p.image_front_small_url);
   return score(b)-score(a);
 })[0];
 if(!item)return {found:false,verdict:'unknown',reasons:['No matching public product record; do not assume halal.'],coverageNote:'This standalone GitHub Pages edition queries Open Food Facts; its coverage is incomplete.'};
 if(isBarcode && String(item.code||'')!==query)return {found:false,verdict:'unknown',reasons:['Barcode did not exactly match returned product.']};
 const ingredients=item.ingredients_text_ja||item.ingredients_text||null;
 return {found:true,name:item.product_name_ja||item.product_name||'Unnamed product',barcode:item.code||null,brand:item.brands||null,ingredients,image:item.image_front_small_url||item.image_front_url||null,source:'Open Food Facts (community supplied; ODbL attribution)',productUrl:item.url||null,...ingredientDecision(ingredients),manufacturerEvidence:[],coverageNote:'Open Food Facts data is user-contributed under ODbL. Japanese records and labels may be incomplete; no halal certification is implied. Check the exact package.'};
}
