// Apify research collector: staging only; never auto-approves halal status.
import { mkdir, writeFile } from 'node:fs/promises';
const token = process.env.APIFY_TOKEN;
if (!token) { console.error('Missing APIFY_TOKEN GitHub Actions secret'); process.exit(1); }
const actorId = process.env.APIFY_ACTOR_ID || 'bgGC9uvqqfOkeeVjY';
const queries = [
  'site:bourbon.co.jp/product/detail/ "JANコード" "原材料名"',
  'site:morinaga.co.jp/products/detail.php "JAN" "原材料"',
  'site:glico.com/jp/product/ "JAN" "原材料"',
  'site:meiji.co.jp/products/ "原材料" "JAN"',
  'site:asahi-gf.co.jp "JAN" "原材料名"',
  'site:lotte.co.jp/products/ "JAN" "原材料"',
  'site:yamazakipan.co.jp "JAN" "原材料"'
].join('\n');
const input = { queries, countryCode: 'jp' };
const endpoint = 'https://api.apify.com/v2';
async function request(url, opts={}) {
  const res = await fetch(url, { ...opts, headers: { authorization: 'Bearer '+token, 'content-type':'application/json', ...(opts.headers||{}) } });
  if (!res.ok) throw new Error('Apify HTTP '+res.status+' '+(await res.text()).slice(0,300));
  return res.json();
}
const run = await request(endpoint+'/acts/'+encodeURIComponent(actorId)+'/runs', {method:'POST',body:JSON.stringify(input)});
if (!run.data?.id) throw new Error('Actor did not return run ID; verify its input schema.');
let status=run.data.status;
let runInfo=run.data;
for (let n=0;n<100 && !['SUCCEEDED','FAILED','ABORTED','TIMED-OUT'].includes(status);n++) {
  await new Promise(resolve=>setTimeout(resolve,5000));
  const current=await request(endpoint+'/actor-runs/'+encodeURIComponent(run.data.id));
  runInfo=current.data; status=runInfo.status;
}
if (status!=='SUCCEEDED') throw new Error('Actor status '+status+' after polling; inspect Apify run '+run.data.id);
const datasetId=runInfo.defaultDatasetId;
if (!datasetId) throw new Error('No default dataset ID');
const items = await request(endpoint+'/datasets/'+encodeURIComponent(datasetId)+'/items?format=json&limit=1000&clean=true');
const jpDomains=['bourbon.co.jp','morinaga.co.jp','glico.com','meiji.co.jp','asahi-gf.co.jp','lotte.co.jp','yamazakipan.co.jp'];
const official = u=>{try { const h=new URL(u).hostname.toLowerCase();return jpDomains.some(d=>h===d||h.endsWith('.'+d));}catch{return false;}};
const candidates=[];
for (const item of Array.isArray(items)?items:[]) {
  const url=item.url||item.link||item.organicResult?.url||item.organicResult?.link||'';
  if (!official(url)) continue;
  candidates.push({url,title:String(item.title||item.name||'').slice(0,250),snippet:String(item.description||item.snippet||'').slice(0,1200),verification_status:'SOURCE_PAGE_NEEDS_JAN_AND_INGREDIENT_VERIFICATION',halal_status:'UNVERIFIED'});
}
const unique=[...new Map(candidates.map(x=>[x.url,x])).values()];
await mkdir('research/apify/output',{recursive:true});
await writeFile('research/apify/output/candidates.json',JSON.stringify({collectedAt:new Date().toISOString(),actorId,runId:run.data.id,totalSearchResults:items.length,officialCandidateUrls:unique.length,records:unique},null,2));
console.log('Collected '+unique.length+' unique official-page leads from '+items.length+' Actor results. No database import or halal certification claimed.');

