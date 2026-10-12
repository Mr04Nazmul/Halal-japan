import superjson from 'superjson';
export type CatalogProduct={id:string;name:string;barcode:string|null;brand:string|null;category:string|null;image:string|null;source:string;sourceUrl:string|null;ingredients:string|null;};
export type CatalogResponse={items:CatalogProduct[];total:number;};
export async function getFoodCatalog(store:string,page=1):Promise<CatalogResponse>{const r=await fetch('/_api/food-catalog?store='+encodeURIComponent(store)+'&page='+page);const v=superjson.parse<any>(await r.text());if(!r.ok)throw Error(v.error||'Catalog failed');return v;}
