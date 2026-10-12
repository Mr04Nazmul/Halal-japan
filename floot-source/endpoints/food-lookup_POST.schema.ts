import {z} from 'zod';
import {ingredientDecision} from '../helpers/ingredientDecision';
export const schema=z.object({query:z.string().trim().min(2).max(140)});
export type LookupResult={found:boolean; name?:string; barcode?:string|null; brand?:string|null; ingredients?:string|null; image?:string|null; source?:string; productUrl?:string|null; verdict:'haram_ingredient'|'needs_review'|'certified'|'unknown'; reasons:string[]; confidence?:'high'|'medium'|'low'; findings?:{ingredient:string;severity:'prohibited'|'uncertain';reason:string}[]; manufacturerEvidence?:{type:string;url:string|null;issuer:string|null;reviewedAt:string|null}[]; coverageNote?:string;};
export async function postFoodLookup(body:z.infer<typeof schema>):Promise<LookupResult>{
 const query=schema.parse(body).query;
 const isBarcode=/^\d{8,14}$/.test(query);
 const api=isBarcode?'https://world.openfoodfacts.org/api/v2/product/'+encodeURIComponent(query)+'.json':'https://world.openfoodfacts.org/cgi/search.pl?search_terms='+encodeURIComponent(query)+'&search_simple=1&action=process&json=1&page_size=5';
 const response=await fetch(api,{headers:{Accept:'application/json'}});
 if(!response.ok)throw Error('Open Food Facts lookup unavailable (HTTP '+response.status+'). Please try again.');
 const payload=await response.json();
 const item=isBarcode?(payload.status===1?payload.product:null):payload.products?.find((p:any)=>p.product_name||p.product_name_ja);
 if(!item)return {found:false,verdict:'unknown',reasons:['No matching public product record; do not assume halal.'],coverageNote:'This standalone GitHub Pages edition queries Open Food Facts; its coverage is incomplete.'};
 if(isBarcode && String(item.code||'')!==query)return {found:false,verdict:'unknown',reasons:['Barcode did not exactly match returned product.']};
 const ingredients=item.ingredients_text_ja||item.ingredients_text||null;
 return {found:true,name:item.product_name_ja||item.product_name||'Unnamed product',barcode:item.code||null,brand:item.brands||null,ingredients,image:item.image_front_small_url||item.image_front_url||null,source:'Open Food Facts (community supplied)',productUrl:item.url||null,...ingredientDecision(ingredients),manufacturerEvidence:[],coverageNote:'Unverified community data. No halal certification or manufacturer confirmation is implied. Check the exact package.'};
}
