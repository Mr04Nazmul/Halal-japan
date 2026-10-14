import { timingSafeEqual } from 'node:crypto';
/** JHC ingredient research discovery and review queue.
 * Server-only credentials. Search results are leads, never ingredient evidence.
 * Requires GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_ENGINE_ID, YAHOO_CLIENT_ID,
 * SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and RESEARCH_ADMIN_TOKEN.
 */
const allowedOrigins=(process.env.ALLOWED_ORIGINS||'https://mr04nazmul.github.io').split(',').map(x=>x.trim());
const janValid=x=>/^(\d{8}|\d{12,14})$/.test(x);
const clean=x=>String(x||'').trim().slice(0,180);
const allowedUrl=s=>{try{const u=new URL(s);return u.protocol==='https:'&&!u.username&&!u.password&&!/^(localhost|127\.|10\.|192\.168\.|169\.254\.)/.test(u.hostname)}catch{return false}};
async function getJSON(url){const r=await fetch(url,{signal:AbortSignal.timeout(9000)});if(!r.ok)throw Error('Provider responded '+r.status);return r.json()}
function cors(req,res){const origin=req.headers.origin;if(origin&&allowedOrigins.includes(origin)){res.setHeader('Access-Control-Allow-Origin',origin);res.setHeader('Vary','Origin')}res.setHeader('Access-Control-Allow-Headers','Content-Type, X-Research-Token');res.setHeader('Access-Control-Allow-Methods','GET, POST, OPTIONS');res.setHeader('Cache-Control','no-store')}
function safeTokenMatch(provided,secret){
 if(typeof provided!=='string'||typeof secret!=='string'||!secret)return false;
 const a=Buffer.from(provided),b=Buffer.from(secret);
 return a.length===b.length&&timingSafeEqual(a,b);
}
const compare=(a,b)=>String(a).padStart(14,'0')===String(b).padStart(14,'0');
async function discover(query,jan){
 const results=[],errors=[];
 if(process.env.GOOGLE_SEARCH_API_KEY&&process.env.GOOGLE_SEARCH_ENGINE_ID){
  try{const u=new URL('https://www.googleapis.com/customsearch/v1');u.searchParams.set('key',process.env.GOOGLE_SEARCH_API_KEY);u.searchParams.set('cx',process.env.GOOGLE_SEARCH_ENGINE_ID);u.searchParams.set('q',jan?jan+' 原材料名 メーカー 公式':query+' 原材料名 公式 メーカー');u.searchParams.set('num','7');
   const j=await getJSON(u);for(const item of j.items||[])if(allowedUrl(item.link))results.push({source:'Google Programmable Search',product_name:clean(item.title),jan_code:jan||null,source_url:item.link,excerpt:clean(item.snippet),evidence_level:'discovery_only'});
  }catch(e){errors.push('Google search unavailable: '+e.message)}
 }
 if(process.env.YAHOO_CLIENT_ID){
  try{const u=new URL('https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch');u.searchParams.set('appid',process.env.YAHOO_CLIENT_ID);u.searchParams.set(jan?'jan_code':'query',jan||query);u.searchParams.set('results','10');
   const j=await getJSON(u);for(const item of j.hits||[]){const code=String(item.janCode||'');if(!janValid(code)||(jan&&!compare(jan,code))||!allowedUrl(item.url))continue;results.push({source:'Yahoo! Shopping Japan',product_name:clean(item.name),jan_code:code,manufacturer:clean(item.brand?.name),source_url:item.url,excerpt:'Retail product metadata; complete ingredient list not verified',evidence_level:'discovery_only'})}
  }catch(e){errors.push('Yahoo search unavailable: '+e.message)}
 }
 return {results:results.slice(0,20),errors,configured:{google:!!(process.env.GOOGLE_SEARCH_API_KEY&&process.env.GOOGLE_SEARCH_ENGINE_ID),yahoo:!!process.env.YAHOO_CLIENT_ID}};
}
async function queue(items){
 if(!process.env.SUPABASE_URL||!process.env.SUPABASE_SERVICE_ROLE_KEY)throw Error('Supabase backend is not configured');
 const records=items.filter(x=>allowedUrl(x.source_url)&&clean(x.product_name)).slice(0,20).map(x=>({jan_code:janValid(String(x.jan_code||''))?x.jan_code:null,product_name:clean(x.product_name),manufacturer:clean(x.manufacturer)||null,discovery_source:x.source,source_url:x.source_url,evidence_level:'discovery_only',status:'needs_review'}));
 if(!records.length)return 0;
 const base=process.env.SUPABASE_URL.replace(/\/$/,'');const r=await fetch(base+'/rest/v1/jhc_ingredient_research_queue?on_conflict=discovery_source,source_url',{method:'POST',headers:{'apikey':process.env.SUPABASE_SERVICE_ROLE_KEY,'Authorization':'Bearer '+process.env.SUPABASE_SERVICE_ROLE_KEY,'Content-Type':'application/json','Prefer':'resolution=ignore-duplicates,return=minimal'},body:JSON.stringify(records),signal:AbortSignal.timeout(10000)});
 if(!r.ok)throw Error('Database queue rejected: '+r.status);return records.length;
}
export default async function handler(req,res){
 cors(req,res);const requestOrigin=req.headers.origin;
 if(requestOrigin&&!allowedOrigins.includes(requestOrigin))return res.status(403).json({error:'Origin not allowed'});
 if(req.method==='OPTIONS')return res.status(204).end();
 if(!['GET','POST'].includes(req.method))return res.status(405).json({error:'Method not allowed'});
 // Search and queue are admin-only to prevent unauthenticated paid-API exhaustion.
 const token=process.env.RESEARCH_ADMIN_TOKEN;
 if(!safeTokenMatch(req.headers['x-research-token'],token))return res.status(401).json({error:'Research authorization required'});
 const query=clean(req.method==='POST'?req.body?.query:req.query?.query);
 const jan=clean(req.method==='POST'?req.body?.jan_code:req.query?.jan_code);
 if(!(janValid(jan)||query.length>=3)||(!jan&&!query)||query.length>120)return res.status(400).json({error:'Provide valid JAN or product query (3+ chars)'});
 try{const found=await discover(query,jan);if(req.method==='POST'){const queued=await queue(found.results);return res.status(200).json({...found,queued_for_review:queued,auto_halal_classification:false})}return res.status(200).json({...found,auto_halal_classification:false})}
 catch(e){return res.status(502).json({error:e.message})}
}
