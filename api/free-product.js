/** Free, keyless Japanese food discovery via Open Food Facts.
 * Public GET is read-only. Results are unverified leads, NOT halal certification.
 */
const JAN=/^(?:\d{8}|\d{12,14})$/;
const UA='JapanHalalChecker/1.0 (product research; https://github.com/Mr04Nazmul/Halal-japan)';
const origin='https://mr04nazmul.github.io';
const sanitize=x=>String(x||'').trim().slice(0,120);
const cache=new Map();
function item(p){
 const code=String(p.code||'');
 if(!JAN.test(code))return null;
 return {code,product_name:sanitize(p.product_name_ja||p.product_name||''),
  brands:sanitize(p.brands),manufacturer:sanitize(p.brands),
  ingredients_text:String(p.ingredients_text_ja||p.ingredients_text||'').slice(0,4500),
  image_url:p.image_front_url||p.image_url||'',
  _source:'Open Food Facts',_sourceUrl:'https://world.openfoodfacts.org/product/'+encodeURIComponent(code),
  ingredientsVerified:false,halalVerified:false,evidence_level:'community_database'};
}
export default async function handler(req,res){
 if(req.headers.origin===origin){res.setHeader('Access-Control-Allow-Origin',origin);res.setHeader('Vary','Origin');}
 res.setHeader('Access-Control-Allow-Methods','GET, OPTIONS');
 res.setHeader('Cache-Control','public, max-age=60, s-maxage=300');
 if(req.method==='OPTIONS')return res.status(204).end();
 if(req.method!=='GET')return res.status(405).json({error:'Method not allowed'});
 if(req.query.health==='1')return res.status(200).json({configured:true,source:'Open Food Facts',paid_api_required:false});
 const jan=sanitize(req.query.jan_code),q=sanitize(req.query.query);
 if(!(JAN.test(jan)||q.length>=3)||q.length>90)return res.status(400).json({error:'Valid JAN or product query (3-90 characters) required'});
 const key=jan?'jan:'+jan:'q:'+q;const now=Date.now();
 if(cache.get(key)?.expires>now)return res.status(200).json(cache.get(key).body);
 try{
  let url;
  if(jan){url='https://world.openfoodfacts.org/api/v2/product/'+encodeURIComponent(jan)+'.json?fields=code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,image_front_url,image_url';}
  else{const params=new URLSearchParams({search_terms:q,search_simple:'1',action:'process',json:'1',page_size:'10',fields:'code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,image_front_url,image_url'});url='https://world.openfoodfacts.org/cgi/search.pl?'+params;}
  const r=await fetch(url,{headers:{'User-Agent':UA,'Accept':'application/json'},signal:AbortSignal.timeout(9000)});
  if(!r.ok)return res.status(502).json({error:'Open Food Facts unavailable',status:r.status});
  const data=await r.json();
  const products=(jan?[data.product]:data.products||[]).filter(Boolean).map(item).filter(Boolean).filter(p=>!jan||p.code===jan);
  const body={products,source:'Open Food Facts',halalVerified:false,ingredientsVerified:false,needsManufacturerCheck:true,free:true};
  if(cache.size>90)cache.delete(cache.keys().next().value);cache.set(key,{body,expires:now+180000});
  return res.status(200).json(body);
 }catch{return res.status(502).json({error:'Product lookup temporarily unavailable'});}
}
