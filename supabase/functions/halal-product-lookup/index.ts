import {MANUFACTURER_RECORDS} from './manufacturer-records.js';
import {parseSuntory} from './suntory.js';
/* Deployed configuration remains on the backend; no Yahoo Client ID is shipped to browsers. */
const appid = Deno.env.get('HALAL_YAHOO_CLIENT_ID') || '__YAHOO_PRIVATE_CONFIG__';
const same=(a,b)=>/^\d{8,14}$/.test(String(a))&&String(a).padStart(14,'0')===String(b).padStart(14,'0');
const cache=new Map();let lastYahoo=0,lastUPC=0;
async function jsonFetch(url){const r=await fetch(url,{signal:AbortSignal.timeout(8000)});if(!r.ok)return {error:r.status};return {data:await r.json()};}
Deno.serve(async req=>{
 const origin=req.headers.get('origin');const cors={'Access-Control-Allow-Origin':'https://mr04nazmul.github.io','Access-Control-Allow-Headers':'authorization, apikey, content-type','Access-Control-Allow-Methods':'GET, OPTIONS','Vary':'Origin'};
 const reply=(j,status=200)=>new Response(JSON.stringify(j),{status,headers:{...cors,'Content-Type':'application/json','Cache-Control':'no-store'}});
 if(req.method==='OPTIONS')return new Response(null,{status:204,headers:cors});
 if(req.method!=='GET')return reply({error:'Method not allowed'},405);
 if(origin&&origin!=='https://mr04nazmul.github.io')return reply({error:'Origin not allowed'},403);
 // The Supabase gateway validates the caller's JWT (verify_jwt=true).
 const u=new URL(req.url),code=u.searchParams.get('jan_code')||'',q=(u.searchParams.get('query')||'').trim(),source=u.searchParams.get('source')||'yahoo';
 const configured=appid!=='__YAHOO_PRIVATE_CONFIG__';
 if(u.searchParams.get('health')==='1')return reply({configured,backend:'online'});
 if(code?!/^(\d{8}|\d{12,14})$/.test(code):!q||q.length>100)return reply({error:'Invalid lookup'},400);
 if(!['yahoo','upcitemdb','suntory'].includes(source))return reply({error:'Invalid source'},400);
 const now=Date.now(),key=source+'|'+(code||q),stored=cache.get(key);if(stored&&stored.expires>now)return reply(stored.value);
 let result;
 if(source==='suntory'){
  if(!code.startsWith('490177'))return reply({products:[],source:'Suntory'});
  const snapshot=MANUFACTURER_RECORDS.find(p=>p.code===code);
  const fallback=()=>snapshot?reply({products:[snapshot],source:'Suntory',savedRecord:true,halalVerified:false,ingredientsVerified:true}):reply({error:'Manufacturer lookup unavailable'},502);
  try{const r=await fetch('https://products.suntory.co.jp/d/'+code+'/',{signal:AbortSignal.timeout(8000)});if(!r.ok)return fallback();const html=new TextDecoder('shift_jis').decode(await r.arrayBuffer());const product=parseSuntory(html,code);result={products:product?[product]:[],source:'Suntory',halalVerified:false,ingredientsVerified:!!product};}catch{return fallback()}
 }else if(source==='upcitemdb'){
  if(!code)return reply({products:[],source:'UPCitemdb'});
  if(now-lastUPC<2000)return reply({error:'UPCitemdb rate limit'},429);lastUPC=now;
  const upstream=await jsonFetch('https://api.upcitemdb.com/prod/trial/lookup?upc='+encodeURIComponent(code)).catch(()=>({error:502}));
  if(upstream.error)return reply({error:'UPCitemdb unavailable',upstreamStatus:upstream.error},upstream.error===429?429:502);
  const products=(upstream.data.items||[]).filter(x=>[x.ean,x.upc,x.gtin].some(b=>same(b,code))).map(x=>({code,product_name:x.title||'',brands:x.brand||'',image_url:(x.images||[]).find(x=>String(x).startsWith('https://'))||'',ingredients_text:'',_source:'UPCitemdb',_sourceUrl:'https://www.upcitemdb.com/upc/'+encodeURIComponent(code)}));
  result={products,source:'UPCitemdb',halalVerified:false,ingredientsVerified:false};
 }else{
  if(!configured)return reply({error:'Yahoo API not configured'},503);
  if(now-lastYahoo<1100)return reply({error:'Yahoo rate limit'},429);lastYahoo=now;
  const yahoo=new URL('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch');yahoo.searchParams.set('appid',appid);yahoo.searchParams.set(code?'jan_code':'query',code||q);yahoo.searchParams.set('results','12');yahoo.searchParams.set('image_size','300');
  const upstream=await jsonFetch(yahoo).catch(()=>({error:502}));
  if(upstream.error)return reply({error:upstream.error===403?'Yahoo returned 403':'Yahoo unavailable',upstreamStatus:upstream.error},502);
  const products=(upstream.data.hits||[]).filter(x=>/^\d{8,14}$/.test(String(x.janCode))&&(!code||same(x.janCode,code))).map(x=>({code:String(x.janCode),product_name:x.name||'',brands:x.brand?.name||'',image_url:x.image?.medium||x.image?.small||'',ingredients_text:'',_source:'Yahoo! Shopping Japan',_sourceUrl:x.url||''}));
  result={products,source:'Yahoo! Shopping Japan',halalVerified:false,ingredientsVerified:false};
 }
 for(const [k,v]of cache)if(v.expires<=now)cache.delete(k);if(cache.size>=100)cache.delete(cache.keys().next().value);cache.set(key,{value:result,expires:now+60000});return reply(result);
});
