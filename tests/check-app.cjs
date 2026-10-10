/* Run with NODE_PATH pointing to a directory containing linkedom. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {parseHTML}=require('linkedom');
const html=fs.readFileSync('index.html','utf8'),{window}=parseHTML(html),document=window.document;
document.body.normalize();
// linkedom omits the browser's select.value setter and initial first-option selection.
for(const id of ['storeFilter','foodFilter']){const el=document.getElementById(id);let value=el.options[0].value;Object.defineProperty(el,'value',{get:()=>value,set:v=>{value=String(v)}})}
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
 // Catalogue browse must work offline and keep distinct non-barcode history entries.
 run("navigate('search');$('storeFilter').value='family';$('foodFilter').value='bento'");
 await run("$('browseStore').onclick()");await flush();
 assert.equal(run('window.searchProducts.length'),21);assert.ok(run("window.searchProducts.every(p=>p._store==='family'&&p._category==='bento')"));
 run("renderProduct(window.searchProducts[0])");await flush();assert.match(document.querySelector('#result').textContent,/VERIFY/);assert.match(document.querySelector('#result').textContent,/Published allergens/);assert.match(document.querySelector('#result').textContent,/857 kcal/);
 run("renderProduct(window.searchProducts[1])");await flush();assert.equal(run("savedProducts().filter(x=>x.product?._catalogId).length"),2);
 run("navigate('history')");document.querySelector('[data-history="1"]').click();assert.equal(run('currentPage'),'result');assert.equal(run('currentProduct._catalogId'),run('window.searchProducts[0]._catalogId'));
 for(const l of ['bn','ur','uz','ar','fa','id','ms']){run(`lang='${l}';localeEpoch++`);await flush();assert.notEqual(document.querySelector('#result').textContent.includes('Store food details'),true);assert.notEqual(document.querySelector('#result').textContent.includes('Published allergens'),true);assert.equal(document.querySelector('#foodFilter option[value="bento"]').textContent,run("coreText('Bento')"));}
 run("lang='en';localeEpoch++;navigate('search');$('storeFilter').value='lawson';$('foodFilter').value='noodles';$('productQuery').value='noodles'");
 await run("fetchProduct('https://world.openfoodfacts.org/cgi/search.pl')");assert.ok(run("window.searchProducts.length>0&&window.searchProducts.every(p=>p._store==='lawson'&&p._category==='noodles')"));
 // Retailer halal evidence and plain-food guidance must remain distinct.
 run("navigate('search');$('storeFilter').value='gyomu';$('foodFilter').value='halal'");await run("$('browseStore').onclick()");await flush();assert.equal(run('window.searchProducts.length'),211);
 run("renderProduct(window.searchProducts.find(p=>p.code==='4942355285274'))");await flush();assert.match(document.querySelector('#result').textContent,/Retailer halal listing/);assert.match(document.querySelector('#result').textContent,/100g/);assert.match(document.querySelector('#result').textContent,/292kcal/);assert.match(document.querySelector('#result').textContent,/VERIFY/);
 for(const l of ['bn','ur','uz','ar','fa','id','ms']){run(`lang='${l}';localeEpoch++`);await flush();assert.ok(!document.querySelector('#result').textContent.includes('Halal shopping information'));assert.ok(!document.querySelector('#result').textContent.includes('Country of origin'));}
 run("lang='en';localeEpoch++;navigate('search');$('storeFilter').value='all';$('foodFilter').value='simple'");await run("$('browseStore').onclick()");assert.equal(run('window.searchProducts.length'),6);assert.ok(run("window.searchProducts.every(p=>!p._halalEvidence&&!p.code)"));run("renderProduct(window.searchProducts[0])");await flush();assert.match(document.querySelector('#result').textContent,/not certified halal products/);
 // An exact official JAN provides retailer evidence, while available ingredients still govern flags.
 ctx.fetch=async()=>({ok:true,json:async()=>({})});await run("fetchProduct('https://world.openfoodfacts.org/api/v2/product/4942355285274.json')");assert.equal(run('currentProduct._catalogId'),'gyomu:8656');assert.match(document.querySelector('#result').textContent,/Retailer halal listing/);
 ctx.fetch=async()=>({ok:true,json:async()=>({product:{code:'4942355285274',ingredients_text:'pork',lang:'en'}})});await run("fetchProduct('https://world.openfoodfacts.org/api/v2/product/4942355285274.json')");assert.match(document.querySelector('#result').textContent,/HARAM/);assert.equal(run('currentProduct._source'),'Open Food Facts');assert.ok(run('!!currentProduct._halalEvidence'));
 // Name matches with the same exact JAN deduplicate without dropping available ingredients.
 ctx.fetch=async()=>({ok:true,json:async()=>({products:[{code:'4942355285274',product_name:'シュリンプサテXO',ingredients_text:'pork',lang:'en'}]})});run("navigate('search');$('storeFilter').value='all';$('foodFilter').value='all';$('productQuery').value='シュリンプサテXO'");await run("fetchProduct('https://world.openfoodfacts.org/cgi/search.pl')");assert.equal(run('window.searchProducts.length'),1);assert.equal(run('window.searchProducts[0].ingredients_text'),'pork');assert.ok(run('!!window.searchProducts[0]._halalEvidence'));
 // Stale lookups must not replace a page the user already left.
 let release;ctx.fetch=()=>new Promise(r=>release=()=>r({ok:true,json:async()=>({product:{code:'4900000000003',ingredients_text:'water'}})}));
 const lookup=run("fetchProduct('https://world.openfoodfacts.org/api/v2/product/4900000000003.json')");run("navigate('home')");release();await lookup;assert.equal(run('currentPage'),'home');
 console.log('PASS: seven offline UI languages, RTL, product verdicts, store filters, history, absent data and lookup cancellation');
})().catch(e=>{console.error(e);process.exitCode=1});
