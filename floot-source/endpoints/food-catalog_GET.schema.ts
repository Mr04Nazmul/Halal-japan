export type CatalogProduct={id:string;name:string;barcode:string|null;brand:string|null;category:string|null;image:string|null;source:string;sourceUrl:string|null;ingredients:string|null;};
export type CatalogResponse={items:CatalogProduct[];total:number;};
export async function getFoodCatalog(_store:string,_page=1):Promise<CatalogResponse>{
 // The original Floot foodProducts database is not available on static GitHub Pages.
 // Never invent retailer stock, HALAL certification, or claim a connected catalogue.
 return {items:[],total:0};
}
