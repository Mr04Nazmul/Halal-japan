import {db} from '../helpers/db';
import {sql} from 'kysely';
import superjson from 'superjson';
import type {CatalogResponse} from './food-catalog_GET.schema';
export async function handle(req:Request){
 try{const url=new URL(req.url);const store=url.searchParams.get('store')||'gyomu';const page=Math.max(1,Math.min(100,Number(url.searchParams.get('page'))||1));const filt=store==='gyomu'?'gyomu':store==='family'?'FamilyMart':store==='seven'?'7-Eleven':store==='lawson'?'Lawson':store==='suntory'?'Suntory':'gyomu';
 const base=db.selectFrom('foodProducts').where('evidenceSource','ilike','%'+filt+'%');
 const [rows,count]=await Promise.all([base.selectAll().orderBy('id','desc').limit(24).offset((page-1)*24).execute(),base.select(sql<number>`count(*)::int`.as('n')).executeTakeFirst()]);
 const body:CatalogResponse={total:Number(count?.n||0),items:rows.map(p=>({id:String(p.id),name:p.name,barcode:p.barcode,brand:p.brand,category:p.category,image:p.imageUrl,source:p.evidenceSource,sourceUrl:p.evidenceUrl,ingredients:p.ingredients}))};
 return new Response(superjson.stringify(body));}catch(e:any){return new Response(superjson.stringify({error:e.message}),{status:400})}
}
