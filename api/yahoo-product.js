/** Yahoo Shopping v3. Retail metadata is not ingredient evidence or halal certification. */
const ENDPOINT='https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch';
const CACHE=new Map();let lastCall=0;
const exact=(a,b)=>/^\d{8,14}$/.test(String(a))&&String(a).padStart(14,'0')===String(b).padStart(14,'0');
export default async function handler(req,res){
 const origin=req.headers?.origin;
 const allowed=(process.env.ALLOWED_ORIGINS||'https://mr04nazmul.github.io').split(',').map(x=>x.trim());
 if(origin&&allowed.includes(origin)){res.setHeader('Access-Control-Allow-Origin',origin);res.setHeader('Vary','Origin');}
 res.setHeader('Access-Control-Allow-Methods','GET, OPTIONS');
 res.setHeader('Cache-Control','no-store');
 if(req.method==='OPTIONS')return res.status(204).end();
 if(req.method!=='GET')return res.status(405).json({error:'Method not allowed'});
 if(origin&&!allowed.includes(origin))return res.status(403).json({error:'Origin not allowed'});
 const appid=process.env.YAHOO_CLIENT_ID;
 if(req.query.health==='1')return res.status(appid?200:503).json({configured:!!appid});
 const code=String(req.query.jan_code||''),query=String(req.query.query||'').trim();
 if(code?!/^(\d{8}|\d{12,14})$/.test(code):!query||query.length>100)return res.status(400).json({error:'Invalid lookup'});
 if(!appid)return res.status(503).json({error:'Yahoo API not configured'});
 const key=code?'jan:'+code:'q:'+query,now=Date.now(),cached=CACHE.get(key);
 if(cached&&cached.expires>now)return res.status(200).json(cached.value);
 // Per-instance guard; shared serverless rate limits still need a provider-side/shared limiter.
 if(now-lastCall<1100){res.setHeader('Retry-After','2');return res.status(429).json({error:'Please retry in a moment'});}
 lastCall=now;
 const url=new URL(ENDPOINT);url.searchParams.set('appid',appid);url.searchParams.set(code?'jan_code':'query',code||query);url.searchParams.set('results','12');url.searchParams.set('image_size','300');
 try{
  const response=await fetch(url,{signal:AbortSignal.timeout(8000)});
  if(!response.ok)return res.status(502).json({error:'Yahoo lookup unavailable'});
  const json=await response.json();
  const products=(json.hits||[]).filter(x=>/^\d{8,14}$/.test(String(x.janCode))&&(!code||exact(x.janCode,code))).map(x=>({code:String(x.janCode),product_name:x.name||'',brands:x.brand?.name||'',image_url:x.image?.medium||x.image?.small||'',ingredients_text:'',_source:'Yahoo! Shopping Japan',_sourceUrl:x.url||''}));
  const value={products,source:'Yahoo! Shopping Japan',halalVerified:false,ingredientsVerified:false};
  for(const [k,v] of CACHE)if(v.expires<=now)CACHE.delete(k);
  if(CACHE.size>=100)CACHE.delete(CACHE.keys().next().value);
  CACHE.set(key,{expires:now+60000,value});return res.status(200).json(value);
 }catch{return res.status(502).json({error:'Yahoo lookup failed'});}
}
