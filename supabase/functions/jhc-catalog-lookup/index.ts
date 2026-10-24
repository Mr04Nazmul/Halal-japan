// Single-item, read-only lookup into private JHC product catalogue.
// The service role key never leaves Supabase Edge Functions.
const ORIGIN = "https://mr04nazmul.github.io";
const DATA_URL = Deno.env.get("SUPABASE_URL") || "";
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
const MAX_REQUESTS_PER_MINUTE = 12;
const headersFor = (origin: string|null) => ({
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "private, no-store",
  "X-Content-Type-Options": "nosniff",
  "Access-Control-Allow-Origin": origin === ORIGIN ? ORIGIN : "null",
  "Access-Control-Allow-Headers": "Authorization, apikey, Content-Type",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Vary": "Origin"
});
function response(data: unknown, status: number, origin: string|null) {
  return new Response(JSON.stringify(data), { status, headers: headersFor(origin) });
}
async function fingerprint(req: Request): Promise<string> {
  // Trust edge-injected address where available; never store or return raw IP.
  const ip = req.headers.get("cf-connecting-ip")
    || req.headers.get("x-real-ip")
    || (req.headers.get("x-forwarded-for") || "").split(",")[0].trim()
    || "unknown";
  const raw = new TextEncoder().encode(ip);
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(SERVICE_KEY), {name:"HMAC",hash:"SHA-256"},false,["sign"]);
  const signed = await crypto.subtle.sign("HMAC",key,raw);
  return Array.from(new Uint8Array(signed)).map(b=>b.toString(16).padStart(2,"0")).join("");
}
async function serviceFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(DATA_URL + path, {
    ...options,
    headers: {
      "apikey": SERVICE_KEY,
      "Authorization": "Bearer " + SERVICE_KEY,
      "Content-Type": "application/json",
      "Accept": "application/json",
      ...options.headers
    },
    signal: AbortSignal.timeout(7500)
  });
  return res;
}

// Parse only labelled fields from one exact-JAN public manufacturer page.
// Scripts, recommendation text and general allergen dictionaries are not ingredients.
function plainHtml(value:string):string{
 return value.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi,' ')
  .replace(/<[^>]+>/g,' ').replace(/&#(x[0-9a-f]+|[0-9]+);/gi,(_,n)=>{
   const v=n[0].toLowerCase()==='x'?parseInt(n.slice(1),16):parseInt(n,10);
   return v>0&&v<=0x10ffff?String.fromCodePoint(v):' ';
  }).replace(/&(nbsp|amp|lt|gt|quot|apos);/g,(_,n)=>({nbsp:' ',amp:'&',lt:'<',gt:'>',quot:'"',apos:"'"}[n]||' ')).replace(/\s+/g,' ').trim();
}
function parseTopvaluDeclaration(html:string,jan:string){
 const clean=html.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi,' ');
 const fields=new Map<string,string[]>();
 for(const m of clean.matchAll(/<dt\b[^>]*>([\s\S]*?)<\/dt>\s*<dd\b[^>]*>([\s\S]*?)<\/dd>/gi)){
  const key=plainHtml(m[1]).normalize('NFKC').replace(/[\s:]/g,'');
  const value=plainHtml(m[2]);fields.set(key,[...(fields.get(key)||[]),value]);
 }
 const nutrition=[...(fields.get('栄養成分')||[]),...(fields.get('栄養成分表示')||[])].join(' ');
 if(!/エネルギー|熱量/.test(nutrition))return null;
 const ids=fields.get('JAN')||[];
 if(!ids.some(x=>x.normalize('NFKC').replace(/\s/g,'')===jan))return null;
 const ingredients=[...new Set(fields.get('原材料名')||[])];
 const additives=[...new Set(fields.get('添加物')||[])];
 const name=clean.match(/<h1\b[^>]*class=["'][^"']*\bitem-detail__name\b[^"']*["'][^>]*>([\s\S]*?)<\/h1>/i);
 if(!name||ingredients.length!==1||!ingredients[0]||ingredients[0].length>8000||additives.length>1)return null;
 return {barcode:jan,name:plainHtml(name[1]),name_ja:plainHtml(name[1]),brand:'AEON TOPVALU',
  ingredients:ingredients[0]+(additives[0]?'／'+additives[0]:''),image_url:null,
  evidence_source:'AEON TOPVALU live official exact-JAN ingredient declaration',
  evidence_url:'https://www.topvalu.net/items/detail/'+jan+'/',category:'Official online ingredients',
  ingredient_declaration_reviewed:true,reviewed_at:new Date(Date.now()+9*3600000).toISOString().slice(0,10)};
}
async function researchOfficialBarcode(jan:string){
 if(!/^\d{13}$/.test(jan))return null;
 // Use stored URL only as a private discovery lead; never export private scraped labels.
 const leadParams=new URLSearchParams({select:'source_url',jan_code:'eq.'+jan,source_publisher:'eq.topvalu.net',limit:'1'});
 const leadResponse=await serviceFetch('/rest/v1/jhc_crawler_ingredient_staging?'+leadParams.toString());
 const leads=leadResponse.ok?await leadResponse.json():[];
 const expected='https://www.topvalu.net/items/detail/'+jan+'/';
 if(!Array.isArray(leads)||!leads.some(x=>String(x.source_url||'').replace(/\/$/,'')===expected.replace(/\/$/,'')))return null;
 // Destination is constructed from a numeric JAN, never accepted from user input.
 const page=await fetch(expected,{redirect:'error',signal:AbortSignal.timeout(4500),headers:{Accept:'text/html','User-Agent':'JapanHalalChecker/1.0 (single-product ingredient research)'}});
 if(!page.ok||!String(page.headers.get('content-type')||'').includes('text/html'))return null;
 const html=await page.text();if(html.length>800000)return null;
 return parseTopvaluDeclaration(html,jan);
}

Deno.serve(async (req: Request) => {
  const origin = req.headers.get("origin");
  if (req.method === "OPTIONS") {
    if (origin !== ORIGIN) return response({error:"Origin not allowed"},403,origin);
    return new Response(null,{status:204,headers:headersFor(origin)});
  }
  if (origin && origin !== ORIGIN) return response({error:"Origin not allowed"},403,origin);
  if (req.method !== "GET") return response({error:"GET only"},405,origin);
  if (!DATA_URL || !SERVICE_KEY) return response({error:"Lookup unavailable"},503,origin);

  const url = new URL(req.url);
  const jan = (url.searchParams.get("jan_code") || "").trim();
  const query = (url.searchParams.get("query") || "").trim().replace(/[(),.*%_\\\/]/g," ").replace(/\s+/g," ");
  const isJan = /^(?:\d{8}|\d{12,14})$/.test(jan);
  if ((jan && !isJan) || (jan && query) || (!isJan && (query.length < 4 || query.length > 70)))
    return response({error:"Enter a valid JAN/EAN barcode or a 4–70 character product name"},400,origin);
  try {
    const fp = await fingerprint(req);
    const gate = await serviceFetch("/rest/v1/rpc/jhc_catalog_allow_request", {
      method:"POST",body:JSON.stringify({p_fingerprint:fp,p_max_hits:MAX_REQUESTS_PER_MINUTE})
    });
    if (!gate.ok) return response({error:"Lookup protection temporarily unavailable"},503,origin);
    if (await gate.json() !== true) return response({error:"Too many lookups; retry after a minute"},429,origin);

    const params = new URLSearchParams({
      select:"barcode,name,name_ja,brand,ingredients,image_url,evidence_source,evidence_url,category",
      limit:"1"
    });
    if (isJan) {
      const variants = new Set([jan]);
      const padded=jan.padStart(14,"0");
      for (const len of [12,13,14]) if (/^0*$/.test(padded.slice(0,14-len))) variants.add(padded.slice(14-len));
      params.set("barcode","in.("+Array.from(variants).join(",")+")");
    } else {
      // Strip PostgREST filter metacharacters before inserting into a predicate.
      const safe = query.replace(/[^\p{L}\p{N}\s&\-ー・々ぁ-ゔァ-ヴ]/gu, " ").replace(/\s+/g," ").trim();
      if (safe.length < 4) return response({error:"More characters are required"},400,origin);
      params.set("or","(name.ilike.*"+safe+"*,name_ja.ilike.*"+safe+"*)");
    }
    const found = await serviceFetch("/rest/v1/jhc_floot_products?"+params.toString());
    if (!found.ok) return response({error:"Catalog not available"},502,origin);
    const rows=await found.json();
    let p=Array.isArray(rows) ? rows[0] : null;
    // Separate licensed Japan-market community data from private manufacturer
    // research. Never return arbitrary staging records or caller-supplied filters.
    if(isJan && !String(p?.ingredients||'').trim()){
      const variants=new Set([jan]),padded=jan.padStart(14,"0");
      for(const len of [12,13,14])if(/^0*$/.test(padded.slice(0,14-len)))variants.add(padded.slice(14-len));
      const licensed=new URLSearchParams({
        select:"jan_code,product_name,ingredients_ja,source_url,evidence",
        jan_code:"in.("+Array.from(variants).join(",")+")",
        source_publisher:"eq.Open Food Facts (Hugging Face bulk export)",
        "evidence->>source_license":"like.ODbL%",
        "evidence->>market_country":"eq.Japan",
        "evidence->>obsolete":"eq.false",
        order:"collected_at.desc",limit:"1"
      });
      try{
        const extra=await serviceFetch("/rest/v1/jhc_crawler_ingredient_staging?"+licensed.toString());
        const extraRows=extra.ok?await extra.json():[];
        const item=Array.isArray(extraRows)?extraRows[0]:null;
        if(item && String(item.ingredients_ja||'').trim() && variants.has(String(item.jan_code)) &&
           String(item.evidence?.source_license||'').startsWith('ODbL') && item.evidence?.market_country==='Japan' &&
           item.evidence?.obsolete===false && item.source_url==='https://world.openfoodfacts.org/product/'+item.jan_code){
          p={barcode:item.jan_code,name:item.product_name,name_ja:item.product_name,
            brand:item.evidence?.brand||null,ingredients:item.ingredients_ja,image_url:null,
            evidence_source:"Open Food Facts Japan (ODbL-1.0 / DbCL-1.0; community-contributed)",
            evidence_url:item.source_url,category:"Japan licensed community ingredient record"};
        }
      }catch{/* Retain a partial catalogue identity if the supplementary source fails. */}
    }
    if(isJan && !String(p?.ingredients||'').trim()){
      try{const researched=await researchOfficialBarcode(jan);if(researched)p=researched;}
      catch{/* A missing page, maintenance, redirect or timeout is not ingredient evidence. */}
    }
    // One narrow result; never support offset, list, export or raw database access.
    return response({record:p?{
      barcode:p.barcode||null,name:p.name||null,name_ja:p.name_ja||null,brand:p.brand||null,
      ingredients:p.ingredients||null,image_url:p.image_url||null,
      evidence_source:p.evidence_source||null,evidence_url:p.evidence_url||null,category:p.category||null,
      ingredient_declaration_reviewed:p.ingredient_declaration_reviewed===true,reviewed_at:p.reviewed_at||null
    }:null,source:"JHC protected product lookup",bulk_export:false},200,origin);
  } catch {
    return response({error:"Catalog temporarily unavailable"},502,origin);
  }
});
