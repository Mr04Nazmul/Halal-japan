/* Run with NODE_PATH pointing to a directory containing linkedom. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {parseHTML}=require('linkedom');
const html=fs.readFileSync('index.html','utf8'),{window}=parseHTML(html),document=window.document;
document.body.normalize();
let pending=[],requests=[],stored={};
const visible=e=>!e.closest('.page-hidden,.hidden')&&e.style.display!=='none';
window.HTMLElement.prototype.getClientRects=function(){return visible(this)?[{}]:[]};
const nf={SHOW_TEXT:4,FILTER_REJECT:2,FILTER_ACCEPT:1};
const nativeWalk=document.createTreeWalker.bind(document);
document.createTreeWalker=(root,what,filter)=>{const walker=nativeWalk(root,what);return {currentNode:null,nextNode(){while(walker.nextNode()){if(!filter||filter.acceptNode(walker.currentNode)===1){this.currentNode=walker.currentNode;return true}}return false}}};
const ctx=vm.createContext({document,window:null,navigator:{},NodeFilter:nf,localStorage:{getItem:k=>stored[k]||null,setItem:(k,v)=>stored[k]=v,removeItem:k=>delete stored[k]},location:{origin:'https://mr04nazmul.github.io',hostname:'mr04nazmul.github.io',protocol:'https:'},URL,TextEncoder,AbortController,AbortSignal,console,setTimeout:f=>(pending.push(f),pending.length),clearTimeout:()=>{},fetch:async u=>{requests.push(String(u));return {ok:true,json:async()=>({product:{code:'4900000000000',product_name:'Sample',ingredients_text:'pork, gelatin',lang:'en'}})}}});
vm.runInContext('window=globalThis;window.scrollTo=()=>{};',ctx);
for(const script of document.querySelectorAll('script')){const src=script.getAttribute('src');if(src?.startsWith('./'))vm.runInContext(fs.readFileSync(src.split('?')[0],'utf8'),ctx,{filename:src});else if(!src)vm.runInContext(script.textContent,ctx,{filename:'inline'});}
const run=s=>vm.runInContext(s,ctx);
run("window.HALAL_API_BASE='';window.HALAL_API_PATH='';");
async function flush(){pending=[];await run('localizeUI()');}
(async()=>{
 assert.deepEqual(Array.from(run('HALAL_LOCALES.map(x=>x[0])')),['en','ja','bn','ur','uz','ar','fa','id','ms']);
 const missing=new Set();
 for(const l of ['bn','ur','uz','ar','fa','id','ms']){
  run(`lang=${JSON.stringify(l)};localeEpoch++`);
  for(const p of ['home','scan','search','ingredients','history','guide','settings','about','loading','details']){
   run(`navigate(${JSON.stringify(p)})`);await flush();
   const nodes=run(`(()=>{const a=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);while(w.nextNode()){const n=w.currentNode,e=n.parentElement;if(!e||e.closest('script,style,svg,option,textarea,[data-original],#languageNotice')||!e.getClientRects().length)continue;const src=localeSources.get(n)?.raw?.trim();if(src&&/[\\p{L}]/u.test(src)&&!['Open Food Facts','Wikidata','Yahoo! Japan','ℹ️'].includes(src)){const key=TEXT_ALIASES[src]||src;if(!LOCAL_TEXT[lang]?.[key])a.push(key)}}return a})()`);
   nodes.forEach(x=>missing.add(x));
   assert.equal(document.documentElement.dir,['ar','fa','ur'].includes(l)?'rtl':'ltr');
   assert.equal(document.getElementById('languageNotice').hidden,true,'Bundled page text should not need online translation');
  }
 }
 assert.deepEqual([...missing],[],'Missing offline UI translations');
 assert.equal(requests.length,0,'UI must not send online translation requests');
 run("lang='en';localeEpoch++;navigate('search')");
 await run("fetchProduct('https://world.openfoodfacts.org/api/v2/product/4900000000000.json')");await flush();
 assert.equal(run('currentPage'),'result');assert.match(document.querySelector('#result').textContent,/HARAM/);
 // Verified official JAN snapshots must not be confused with another size or certify halal.
 const official=run("window.HALAL_MANUFACTURER_RECORDS.find(p=>p.code==='4901777411760')");assert.ok(official);run("renderProduct(window.HALAL_MANUFACTURER_RECORDS.find(p=>p.code==='4901777411760'))");await flush();assert.match(document.querySelector('#result').textContent,/VERIFY/);assert.match(document.querySelector('#result').textContent,/Saved manufacturer record/);
 // Missing product falls back without crashing; retail metadata cannot produce HALAL.
 ctx.fetch=async u=>({ok:true,json:async()=>({})});
 await run("fetchProduct('https://world.openfoodfacts.org/api/v2/product/4900000000001.json')");await flush();
 assert.equal(run('currentPage'),'search');assert.match(document.querySelector('#searchResults').textContent,/No record found/);
 run("renderProduct({code:'4900000000002',product_name:'Retail only',_source:'Yahoo! Shopping Japan',ingredients_text:''})");await flush();
 assert.match(document.querySelector('#result').textContent,/VERIFY/);
 // Stale lookups must not replace a page the user already left.
 let release;ctx.fetch=()=>new Promise(r=>release=()=>r({ok:true,json:async()=>({product:{code:'4900000000003',ingredients_text:'water'}})}));
 const lookup=run("fetchProduct('https://world.openfoodfacts.org/api/v2/product/4900000000003.json')");run("navigate('home')");release();await lookup;assert.equal(run('currentPage'),'home');
 console.log('PASS: seven offline UI languages, RTL, product verdicts, absent data and lookup cancellation');
})().catch(e=>{console.error(e);process.exitCode=1});
