export type CatalogProduct={id:string;name:string;barcode:string|null;brand:string|null;category:string|null;image:string|null;source:string;sourceUrl:string|null;ingredients:string|null};
export type CatalogResponse={items:CatalogProduct[];total:number};
const BASE='https://vjygltfnrmyghlwyjtwu.supabase.co/rest/v1/jhc_floot_products';
const KEY='sb_publishable_SL6n4Q0t_AxHywHM6iMkpg_bm-lx_Oh';
export async function getFoodCatalog(store:string,page=1):Promise<CatalogResponse>{
 const storeFilter:Record<string,string>={gyomu:'gyomu',family:'FamilyMart',seven:'7-Eleven',lawson:'Lawson',suntory:'Suntory'};
 const filter=storeFilter[store]||storeFilter.gyomu;
 const start=(Math.max(1,page)-1)*24;
 const url=new URL(BASE);
 url.searchParams.set('select','source_id,name,barcode,brand,category,image_url,evidence_source,evidence_url,ingredients');
 url.searchParams.set('evidence_source','ilike.*'+filter+'*');
 url.searchParams.set('order','source_id.desc');
 url.searchParams.set('offset',String(start));
 url.searchParams.set('limit','24');
 const r=await fetch(url,{headers:{apikey:KEY,Prefer:'count=exact'}});
 if(!r.ok)throw Error('Product catalogue connection failed (HTTP '+r.status+')');
 const rows=await r.json();
 const range=r.headers.get('content-range')||'';
 const total=Number(range.split('/').pop());
 return {total:Number.isFinite(total)?total:rows.length,items:rows.map((p:any)=>({id:String(p.source_id),name:p.name,barcode:p.barcode,brand:p.brand,category:p.category,image:p.image_url,source:p.evidence_source||'Catalogue snapshot',sourceUrl:p.evidence_url,ingredients:p.ingredients}))};
}
