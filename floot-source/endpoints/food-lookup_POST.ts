import {schema, type LookupResult} from './food-lookup_POST.schema';
import {db} from '../helpers/db';
import {sql} from 'kysely';
import superjson from 'superjson';
import {ingredientDecision} from '../helpers/ingredientDecision';
function classify(ingredients:string|undefined|null,certified=false):Pick<LookupResult,'verdict'|'reasons'>{
 const s=(ingredients||'').toLowerCase();
 const explicit=[/\\bpork\\b/,/\\blard\\b/,/\\bporcine\\b/,/豚肉/,/豚脂/,/ラード/,/ポーク/];
 const review=[/gelatin/,/ゼラチン/,/emulsifier/,/乳化剤/,/animal fat/,/動物油脂/,/shortening/,/ショートニング/,/enzyme/,/酵素/,/flavou?r/,/香料/,/mirin/,/みりん/,/酒精/,/アルコール/,/ethanol/];
 if(['pork','lard','porcine','豚肉','豚脂','ラード','ポーク'].some(term=>s.includes(term)))return {verdict:'haram_ingredient',reasons:['Ingredient label contains a prohibited pork-derived ingredient. Confirm with manufacturer for product-specific details.']};
 if(certified)return {verdict:'certified',reasons:['Halal certification on file. Confirm current certificate and exact product match.']};
 if(!s.trim())return {verdict:'unknown',reasons:['No reliable ingredient list supplied. Halal status cannot be established.']};
 if(review.some(re=>re.test(s)))return {verdict:'needs_review',reasons:['One or more ingredients require source or processing verification.']};
 return {verdict:'needs_review',reasons:['No obvious prohibited ingredient detected, but the full supply chain, processing and certification are unverified.']};
}
export async function handle(request:Request){
 try{
  const {query}=schema.parse(superjson.parse(await request.text()));
  const barcode=/^[0-9]{8,14}$/.test(query);
  const saved=await (barcode?db.selectFrom('foodProducts').selectAll().where('barcode','=',query).limit(1):db.selectFrom('foodProducts').selectAll().where(sql<boolean>`lower(name) like ${'%'+query.toLowerCase()+'%'} or name_ja like ${'%'+query+'%'} or lower(coalesce(brand,'')) like ${'%'+query.toLowerCase()+'%'}`).limit(1)).executeTakeFirst();
  const certificate=saved?await db.selectFrom('foodVerificationEvidence').selectAll().where('productId','=',saved.id).where('evidenceType','=','certificate').where('reviewedAt','is not',null).orderBy('reviewedAt','desc').executeTakeFirst():null;
  const evidence=saved?await db.selectFrom('foodVerificationEvidence').select(['evidenceType','sourceUrl','issuer','reviewedAt']).where('productId','=',saved.id).orderBy('createdAt','desc').limit(8).execute():[];
  const manufacturerEvidence=evidence.map(e=>({type:e.evidenceType,url:e.sourceUrl,issuer:e.issuer,reviewedAt:e.reviewedAt?new Date(e.reviewedAt).toISOString():null}));
  const validCertificate=Boolean(certificate?.sourceUrl&&certificate?.certificateNumber&&certificate?.issuer&&certificate?.validUntil&&new Date(certificate.validUntil).getTime()>=Date.now());
  const fromSaved=()=>saved?{found:true,name:saved.name,barcode:saved.barcode,brand:saved.brand,ingredients:saved.ingredients,image:saved.imageUrl,source:saved.evidenceSource,productUrl:saved.evidenceUrl,...ingredientDecision(saved.ingredients,validCertificate),manufacturerEvidence,coverageNote:validCertificate?'Reviewed, unexpired product certificate recorded; check its scope with the issuer.':'Historical catalogue entry; certification and manufacturer claims not independently confirmed.'}:null;
  // Prefer exact local catalogue matches for named Japanese convenience-store products.
  if(!barcode && saved)return new Response(superjson.stringify(fromSaved() as LookupResult));
  let off:any=null;
  try{const u=barcode?'https://world.openfoodfacts.org/api/v2/product/'+encodeURIComponent(query)+'.json':'https://world.openfoodfacts.org/cgi/search.pl?search_terms='+encodeURIComponent(query)+'&search_simple=1&action=process&json=1&page_size=4';const r=await fetch(u,{headers:{'User-Agent':'JapanHalalChecker/0.1 (contact via project owner)'}});if(r.ok){const data=await r.json();off=barcode?(data.status===1?data.product:null):data.products?.[0]}}catch{}
  if(off){const ingredients=off.ingredients_text_ja||off.ingredients_text||null;const result:LookupResult={found:true,name:off.product_name_ja||off.product_name||saved?.name||'Unnamed product',barcode:off.code||query,brand:off.brands||null,ingredients,image:off.image_front_small_url||null,source:'Open Food Facts (community maintained)',productUrl:off.url||null,...ingredientDecision(ingredients),coverageNote:'Community product record cached as UNVERIFIED. Ingredients and halal certification require independent review.'};
  // Expand our search catalogue conservatively: retain provenance and never auto-certify.
  if(barcode && result.name !== 'Unnamed product' && /^[0-9]{8,14}$/.test(String(off.code||'')) && String(off.code)===query){
    try{await sql`INSERT INTO food_products (barcode,name,name_ja,brand,ingredients,image_url,evidence_source,evidence_url,verification_status,last_checked_at)
      SELECT ${query}, ${result.name}, ${off.product_name_ja||null}, ${result.brand||null}, ${ingredients}, ${result.image}, 'Open Food Facts (community maintained)', ${result.productUrl}, 'unverified', NOW()
      WHERE NOT EXISTS (SELECT 1 FROM food_products WHERE barcode=${query})`.execute(db)}catch(e){console.warn('Catalogue cache unavailable',e)}
  }
  return new Response(superjson.stringify(result));}
  // Yahoo Shopping searches may establish identity but do not establish halal status.
  const client=(process.env as unknown as Record<string,string|undefined>).YAHOO_CLIENT_ID;
  if(client){try{const url=new URL('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch');url.searchParams.set('appid',client);url.searchParams.set(barcode?'jan_code':'query',query);url.searchParams.set('results','4');const r=await fetch(url);if(r.ok){const data=await r.json();const h=data.hits?.[0];if(h){const result:LookupResult={found:true,name:h.name,barcode:h.janCode||query,brand:h.brand?.name||null,ingredients:null,image:h.image?.medium||null,source:'Yahoo! Shopping listing',productUrl:h.url||null,...ingredientDecision(null),coverageNote:'Yahoo Shopping supplies listings, not verified food ingredients or halal certification.'};return new Response(superjson.stringify(result));}}}catch{}}
  const fallback=fromSaved();
  return new Response(superjson.stringify(fallback||{found:false,verdict:'unknown',reasons:['No matching product found in connected sources.'],coverageNote:'Store-specific coverage is incomplete.'} satisfies LookupResult));
 }catch(e:any){return new Response(superjson.stringify({error:e?.message||'Search error'}),{status:400});}
}
