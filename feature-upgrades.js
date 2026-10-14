/* Japan Halal Checker feature additions. Scanner and existing lookup functions are left intact. */
(function(){
'use strict';
if (!document.getElementById('premiumHome') || !window.HALAL_API_BASE) return;
const byId = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {
 en:{favorites:'Favorites',saved:'Saved products',searches:'Recent searches',brand:'Filter brand',status:'Halal status',all:'All evidence levels',halal:'Halal (verified)',haram:'Haram',doubtful:'Doubtful',unknown:'Unknown',noFavorites:'No saved products yet.',noSearches:'No recent searches.',category:'Collection',newCategory:'New collection name',add:'Add',clearSearches:'Clear search history',clearConfirm:'Clear saved searches on this device?',remove:'Remove',save:'Save favorite',unsave:'Saved ✓',evidence:'Verification & evidence',source:'Source',reason:'Reason',ingredients:'Ingredient evidence',missing:'Full ingredients not available',results:'No results match these filters.',filterHelp:'Results are guidance; official certification is not assumed.',allCollections:'All collections',saveOnly:'Saved on this device (no account sync).'},
 bn:{favorites:'পছন্দের পণ্য',saved:'সেভ করা পণ্য',searches:'আগের সার্চ',brand:'ব্র্যান্ড ফিল্টার',status:'হালাল স্ট্যাটাস',all:'সব ফলাফল',halal:'হালাল (যাচাইকৃত)',haram:'হারাম',doubtful:'সন্দেহজনক',unknown:'তথ্য নেই',noFavorites:'কোনো পণ্য সেভ করা হয়নি।',noSearches:'আগের কোনো সার্চ নেই।',category:'কালেকশন',newCategory:'নতুন কালেকশনের নাম',add:'যোগ করো',clearSearches:'সার্চ হিস্ট্রি মুছে ফেলো',clearConfirm:'এই ফোনে সেভ করা সার্চ মুছবে?',remove:'সরাও',save:'ফেভারিটে রাখো',unsave:'সেভ হয়েছে ✓',evidence:'যাচাই ও প্রমাণ',source:'তথ্যের উৎস',reason:'কারণ',ingredients:'উপাদানের প্রমাণ',missing:'সম্পূর্ণ উপাদানের তালিকা নেই',results:'এই ফিল্টারে পণ্য পাওয়া যায়নি।',filterHelp:'এই ফলাফল নির্দেশনা; সার্টিফিকেশনের দাবি নয়।',allCollections:'সব কালেকশন',saveOnly:'শুধু এই ফোনে সেভ থাকবে।'},
 ja:{favorites:'お気に入り',saved:'保存した商品',searches:'検索履歴',brand:'ブランドで絞る',status:'ハラール判定',all:'すべて',halal:'ハラール（検証済み）',haram:'ハラーム',doubtful:'要確認',unknown:'不明',noFavorites:'お気に入りはまだありません。',noSearches:'検索履歴はありません。',category:'コレクション',newCategory:'新しいコレクション名',add:'追加',clearSearches:'検索履歴を削除',clearConfirm:'この端末の検索履歴を削除しますか？',remove:'削除',save:'お気に入りに追加',unsave:'保存済み ✓',evidence:'検証・根拠',source:'情報源',reason:'理由',ingredients:'原材料の根拠',missing:'原材料が不足しています',results:'該当商品がありません。',filterHelp:'表示内容は参考情報で、認証とは限りません。',allCollections:'すべてのコレクション',saveOnly:'この端末にのみ保存されます。'}
};
function L(k){return (labels[typeof lang==='string'?lang:'en']||labels.en)[k]||labels.en[k]||k;}
const read = (key,def) => {try {const v=JSON.parse(localStorage.getItem(key)||'null');return Array.isArray(v)?v:def;}catch{return def;}};
const store = (key,value) => {try {localStorage.setItem(key,JSON.stringify(value));}catch(_){}};
const FAVORITES='jhc_favorites_v1', HISTORY='jhc_search_history_v1', COLLECTIONS='jhc_favorite_collections_v1';
const keyOf = p => String(p && (p._catalogId || p.code || p.barcode || p.source_id || p.product_name) || '').trim();
const nameOf = p => String(p.product_name||p.name||p.product_name_ja||p.product_name_en||p.code||'Product');
const ingredientsOf = p => String(p.ingredients_text||p.ingredients_text_ja||p.ingredients_text_en||p.ingredients||'');
const validHttps = u => {try {let x=new URL(String(u));return x.protocol==='https:'?x.href:'';}catch{return '';}};
const verificationLevels = {
 HALAL_LV1:['HALAL LV1','Product-specific halal certificate verified, current and matching the exact product.'],
 HALAL_LV2:['HALAL LV2','Manufacturer-confirmed ingredients and production evidence; not a halal certificate.'],
 HALAL_LV3:['HALAL LV3','Verified whole unprocessed food and origin; ingredient-level guidance, not certification.'],
 HARAM_LV1:['HARAM LV1','Explicit pork or prohibited animal-derived ingredient in the ingredient list.'],
 HARAM_LV2:['HARAM LV2','Alcoholic drink or cooking alcohol explicitly listed.'],
 DOUBTFUL:['DOUBTFUL','Ingredient screening does not establish halal status. Check sources, processing and certification.'],
 UNKNOWN_PRODUCT:['UNKNOWN PRODUCT','Full ingredient evidence is not available. No halal claim can be made.']
};
function verdict(p) {
 const ing=ingredientsOf(p).normalize('NFKC');
 const low=ing.toLowerCase();
 // A product-specific reviewed record may provide one of the three halal levels.
 const v=p._verifiedAssessment;
 if(v && v.published===true && v.exact_product_match===true && validHttps(v.evidence_url) && v.reviewed_at && 
   ['HALAL_LV1','HALAL_LV2','HALAL_LV3'].includes(v.classification) &&
   (v.classification!=='HALAL_LV1'||(v.cert_valid_until && Date.parse(v.cert_valid_until+'T23:59:59Z')>=Date.now()))) {
  return {code:v.classification,why:String(v.rationale||verificationLevels[v.classification][1]),url:validHttps(v.evidence_url)};
 }
 const pork=/豚肉|豚脂|豚由来|ポークエキス|豚エキス|豚骨|ラード|ベーコン|ハム|豚ゼラチン|豚コラーゲン|豚血|猪肉|猪油|猪血|\b(?:pork|porcine|lard|bacon|pig blood|pork extract|pork gelatin)\b/i;
 const alcohol=/ワイン|ビール|日本酒|みりん|料理酒|ウイスキー|ブランデー|\b(?:wine|beer|rum|vodka|whiskey|whisky|brandy|sake|mirin)\b/i;
 if(pork.test(low))return {code:'HARAM_LV1',why:'Explicit pork-related ingredient on the supplied label.'};
 if(alcohol.test(low))return {code:'HARAM_LV2',why:'Alcoholic beverage or cooking alcohol explicitly appears on the supplied label.'};
 if(!low.trim())return {code:'UNKNOWN_PRODUCT',why:'Ingredients are missing. Allergen lists and store descriptions are not substitutes.'};
 const check = typeof halalAssessment==='function'?halalAssessment(ing):null;
 if(check?.status==='haram')return {code:'HARAM_LV1',why:check.reasons.join('; ')};
 return {code:'DOUBTFUL',why:check?.reasons?.join('; ')||verificationLevels.DOUBTFUL[1]};
}
const style=document.createElement('style');
style.id='jhc-feature-style';
style.textContent='.home-tile:nth-child(5){background:linear-gradient(135deg,#078a57,#034c38)}.jhc-filter-panel{background:#f4f8f5;border:1px solid #dceae0;padding:13px;border-radius:16px;margin:14px 0}.jhc-filter-panel label{display:block;font-size:12px;font-weight:700;color:#3e5b49;margin-bottom:5px}.jhc-filter-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.jhc-filter-grid input,.jhc-filter-grid select,.jhc-collections input,.jhc-collections select{width:100%;min-width:0;padding:11px;border:1px solid #cbded0;border-radius:10px;background:white;font:inherit;font-size:13px}.jhc-filter-caption{margin:8px 0 0;font-size:11px;color:#65786b}.jhc-mini-status{display:inline-flex;align-items:center;gap:4px;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:800;background:#fff0ce;color:#7e5500;margin-top:6px}.jhc-mini-status.haram{background:#ffe4e0;color:#a22c1b}.jhc-mini-status.halal{background:#dff5e4;color:#12653b}.jhc-mini-status.unknown{background:#e8edf0;color:#526672}.jhc-verify{padding:14px;border:1px solid #dae7df;border-radius:15px;background:#f7faf8;margin:16px 0}.jhc-verify h4{font-size:15px;margin:0 0 8px}.jhc-verify p{font-size:12px;line-height:1.6;overflow-wrap:anywhere}.jhc-verify .btn{margin-top:8px}.jhc-page{padding-top:8px}.jhc-collections{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0}.jhc-collections input{flex:1;min-width:155px}.jhc-collections button{padding:10px 12px}.jhc-fav-card{display:flex;gap:9px;align-items:center;background:#f7faf8;border:1px solid #e0ebe3;border-radius:13px;padding:11px;margin:9px 0}.jhc-fav-card img{height:62px;width:62px;object-fit:contain}.jhc-fav-card .jhc-fav-info{flex:1;min-width:0}.jhc-fav-card .jhc-fav-info b{display:block;font-size:13px;overflow-wrap:anywhere}.jhc-fav-card select{max-width:100%;padding:5px;border-radius:7px;border:1px solid #d0e4d5;background:white;font-size:12px}.jhc-fav-card button{font-size:12px;white-space:normal}.jhc-search-entry{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid #e5ece7}.jhc-search-entry button:first-child{flex:1;text-align:left;background:transparent;border:0;color:#123b26;font:inherit;font-weight:650}.jhc-search-entry button:last-child{border:0;background:none;color:#7c8980}.jhc-section-actions{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}@media(max-width:380px){.jhc-filter-grid{grid-template-columns:1fr}}';
document.head.appendChild(style);
const searchPanel=byId('searchPanel');
const filter=document.createElement('div');
filter.id='jhcAdvancedFilters';filter.className='jhc-filter-panel';
filter.innerHTML='<div class="jhc-filter-grid"><div><label id="jhcBrandLabel" for="jhcBrandFilter"></label><input id="jhcBrandFilter" autocomplete="off" placeholder="Suntory / FamilyMart"></div><div><label id="jhcStatusLabel" for="jhcStatusFilter"></label><select id="jhcStatusFilter"><option value="all"></option><option value="halal"></option><option value="haram"></option><option value="doubtful"></option><option value="unknown"></option></select></div></div><p class="jhc-filter-caption" id="jhcFilterHelp"></p>';
searchPanel.querySelector('.field').insertAdjacentElement('afterend',filter);
const favoritePage=document.createElement('section');
favoritePage.id='jhcFavoritePage';favoritePage.className='jhc-page page-hidden';
favoritePage.innerHTML='<h2 class="screen-heading" id="jhcFavoritesTitle"></h2><p class="sub" id="jhcFavoritesNote"></p><div class="jhc-collections"><input id="jhcNewCollection" maxlength="80" aria-label="New collection name"><button class="btn secondary" type="button" id="jhcAddCollection"></button></div><div class="jhc-collections"><select id="jhcCollectionFilter" aria-label="Collection"></select></div><div id="jhcFavoritesList"></div>';
byId('premiumHistory').insertAdjacentElement('afterend',favoritePage);
const homeTile=document.createElement('button');homeTile.className='home-tile';homeTile.type='button';homeTile.dataset.go='favorites';homeTile.innerHTML='<span aria-hidden="true">♡</span><b id="jhcFavoriteTileText"></b>';byId('premiumHome').querySelector('.home-tiles').appendChild(homeTile);
const historyLink=document.createElement('button');historyLink.className='btn secondary';historyLink.type='button';historyLink.dataset.go='favorites';historyLink.id='jhcHistoryToFavorites';byId('premiumHistory').querySelector('h2').insertAdjacentElement('afterend',historyLink);
const searchHistoryPanel=document.createElement('div');searchHistoryPanel.id='jhcRecentSearches';searchHistoryPanel.className='settings-card';byId('premiumHistory').appendChild(searchHistoryPanel);
const levels=document.createElement('div');levels.className='settings-card';levels.innerHTML='<h3>Evidence levels explained</h3><p>HALAL LV1: verified exact-product certification; LV2: reviewed manufacturer evidence; LV3: verified unprocessed food guidance, not certification.</p><p>HARAM LV1: explicit pork; LV2: explicitly listed alcoholic drinks/cooking alcohol. DOUBTFUL: insufficient source verification. UNKNOWN: ingredients missing.</p><p>No product is called certified halal merely because its ingredient keywords look clear.</p>';byId('premiumGuide').appendChild(levels);
function renderLabels(){
 byId('jhcBrandLabel').textContent=L('brand');byId('jhcStatusLabel').textContent=L('status');
 byId('jhcFilterHelp').textContent=L('filterHelp');
 [...byId('jhcStatusFilter').options].forEach(x=>{x.textContent=L(x.value==='all'?'all':x.value);});
 byId('jhcFavoritesTitle').textContent=L('favorites');byId('jhcFavoritesNote').textContent=L('saveOnly');
 byId('jhcNewCollection').placeholder=L('newCategory');byId('jhcAddCollection').textContent=L('add');
 byId('jhcFavoriteTileText').textContent=L('favorites');historyLink.textContent='♡ '+L('favorites');
}
function favoriteItems(){return read(FAVORITES,[]);}
function favoriteCollections(){return ['Saved',...read(COLLECTIONS,[]).filter(x=>typeof x==='string'&&x!=='Saved')];}
function isSaved(p){return favoriteItems().some(f=>f.key===keyOf(p));}
function toggleFavorite(p){
 const key=keyOf(p);if(!key)return;
 const arr=favoriteItems(),ix=arr.findIndex(x=>x.key===key);
 if(ix>=0)arr.splice(ix,1);
 else arr.unshift({key,category:'Saved',product:p,addedAt:Date.now()});
 store(FAVORITES,arr.slice(0,250));renderFavorites();addResultEvidence(p);
}
function renderFavorites(){
 const options=favoriteCollections(),sel=byId('jhcCollectionFilter'),value=sel.value||'all';
 sel.innerHTML='<option value="all">'+esc(L('allCollections'))+'</option>'+options.map(c=>'<option value="'+esc(c)+'">'+esc(c)+'</option>').join('');
 sel.value=options.includes(value)?value:'all';
 const fav=favoriteItems().filter(f=>sel.value==='all'||f.category===sel.value);
 byId('jhcFavoritesList').innerHTML=fav.length?fav.map(f=>{
  const p=f.product||{},img=validHttps(p.image_url||p.image_front_small_url||'');
  const opts=options.map(c=>'<option value="'+esc(c)+'"'+(f.category===c?' selected':'')+'>'+esc(c)+'</option>').join('');
  const v=verdict(p),type=v.code.startsWith('HARAM')?'haram':v.code.startsWith('HALAL')?'halal':v.code==='UNKNOWN_PRODUCT'?'unknown':'';
  return '<div class="jhc-fav-card" data-fav-key="'+esc(f.key)+'">'+(img?'<img src="'+esc(img)+'" loading="lazy" alt="">':'')+'<div class="jhc-fav-info"><b data-original>'+esc(nameOf(p))+'</b><span class="jhc-mini-status '+type+'">'+esc(verificationLevels[v.code][0])+'</span><select data-fav-collection aria-label="'+esc(L('category'))+'">'+opts+'</select></div><button class="btn secondary" data-fav-open="'+esc(f.key)+'">View</button><button class="btn secondary" data-fav-remove="'+esc(f.key)+'" aria-label="'+esc(L('remove'))+'">×</button></div>';
 }).join(''):'<p class="sub">'+esc(L('noFavorites'))+'</p>';
}
byId('jhcAddCollection').addEventListener('click',()=>{
 const input=byId('jhcNewCollection');const name=input.value.trim();
 if(!name||name.length>80)return;
 store(COLLECTIONS,[...new Set([...read(COLLECTIONS,[]),name])].slice(0,50));input.value='';renderFavorites();
});
byId('jhcCollectionFilter').addEventListener('change',renderFavorites);
favoritePage.addEventListener('click',e=>{
 const remove=e.target.closest('[data-fav-remove]');
 if(remove){store(FAVORITES,favoriteItems().filter(f=>f.key!==remove.dataset.favRemove));renderFavorites();return;}
 const open=e.target.closest('[data-fav-open]');if(open){const f=favoriteItems().find(x=>x.key===open.dataset.favOpen);if(f&&typeof renderProduct==='function')renderProduct(f.product);return;}
});
favoritePage.addEventListener('change',e=>{
 const select=e.target.closest('[data-fav-collection]');if(!select)return;
 const key=select.closest('[data-fav-key]')?.dataset.favKey;
 store(FAVORITES,favoriteItems().map(f=>f.key===key?{...f,category:select.value}:f));renderFavorites();
});
function recentSearches(){return read(HISTORY,[]);}
function logSearch(q,type){
 q=String(q||'').trim().slice(0,400);if(!q)return;
 store(HISTORY,[{q,type,time:Date.now()},...recentSearches().filter(x=>!(x.q===q&&x.type===type))].slice(0,30));
}
function renderSearchHistory(){
 const p=byId('jhcRecentSearches');const rows=recentSearches();
 p.innerHTML='<h3>'+esc(L('searches'))+'</h3>'+(rows.length?rows.map((x,i)=>'<div class="jhc-search-entry"><button type="button" data-replay-search="'+i+'">⌕ '+esc(x.q)+'<small style="display:block;font-size:10px;color:#789">'+esc(new Date(x.time).toLocaleString())+'</small></button><button type="button" data-remove-search="'+i+'" aria-label="Remove">×</button></div>').join(''):'<p class="sub">'+esc(L('noSearches'))+'</p>')+'<button type="button" class="btn secondary" id="jhcClearSearches">'+esc(L('clearSearches'))+'</button>';
}
searchHistoryPanel.addEventListener('click',e=>{
 if(e.target.closest('#jhcClearSearches')){if(confirm(L('clearConfirm'))){store(HISTORY,[]);renderSearchHistory();}return;}
 const r=e.target.closest('[data-remove-search]');
 if(r){const index=Number(r.dataset.removeSearch);store(HISTORY,recentSearches().filter((_,i)=>i!==index));renderSearchHistory();return;}
 const replay=e.target.closest('[data-replay-search]');
 if(replay){const rec=recentSearches()[Number(replay.dataset.replaySearch)];if(!rec)return;navigate('search');
   if(rec.type==='barcode'){byId('barcode').value=rec.q;byId('lookupBtn').click();}
   else{byId('productQuery').value=rec.q;byId('searchBtn').click();}
 }
});
byId('homeSearch').addEventListener('submit',()=>{const q=byId('homeQuery').value.trim();logSearch(q,/^\d{8,14}$/.test(q)?'barcode':'text');});
byId('searchBtn').addEventListener('click',()=>logSearch(byId('productQuery').value,'text'));
byId('lookupBtn').addEventListener('click',()=>logSearch(byId('barcode').value,'barcode'));
const priorRenderHistory=renderHistory;
renderHistory=function(){priorRenderHistory();renderSearchHistory();renderLabels();};
const priorNavigate=window.navigate;
navigate=window.navigate=function(page){
 if(page==='favorites'){
  priorNavigate('history');byId('premiumHistory').classList.add('page-hidden');
  favoritePage.classList.remove('page-hidden');currentPage='favorites';
  document.body.dataset.page='favorites';
  byId('pageTitle').textContent=L('favorites');
  document.querySelectorAll('.bottom-nav button').forEach(b=>b.classList.remove('active'));
  renderLabels();renderFavorites();window.scrollTo(0,0);return;
 }
 priorNavigate(page);favoritePage.classList.add('page-hidden');
 if(page==='history')renderSearchHistory();
};
function evidenceHTML(p){
 const v=verdict(p),meta=verificationLevels[v.code],cls=v.code.startsWith('HALAL')?'halal':v.code.startsWith('HARAM')?'haram':v.code==='UNKNOWN_PRODUCT'?'unknown':'';
 const url=validHttps(v.url||p._sourceUrl||p.evidence_url||'');
 const src=String(p._source||p.evidence_source||p.brands||'Not available');
 const evidence=(url?'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(src)+' ↗</a>':esc(src+' — no verified source link'));
 return '<section class="jhc-verify" id="jhcVerification" aria-label="Verification details"><h4>'+esc(L('evidence'))+'</h4><span class="jhc-mini-status '+cls+'">'+esc(meta[0])+'</span><p><strong>'+esc(L('reason'))+':</strong> '+esc(v.why)+'</p><p><strong>'+esc(L('source'))+':</strong> '+evidence+'</p><p><strong>'+esc(L('ingredients'))+':</strong> '+esc(ingredientsOf(p)?'Available; check the original label.':L('missing'))+'</p><button type="button" id="jhcFavoriteToggle" class="btn secondary" data-fav-toggle="1">'+(isSaved(p)?'♥ '+esc(L('unsave')):'♡ '+esc(L('save')))+'</button></section>';
}
function addResultEvidence(p){
 const result=byId('result');if(!result || !result.classList.contains('show') || !p)return;
 result.querySelector('#jhcVerification')?.remove();
 result.insertAdjacentHTML('beforeend',evidenceHTML(p));
}
const previousSave=saveProduct;
saveProduct=function(p,assessment){previousSave(p,assessment);if(p)addResultEvidence(p);};
document.addEventListener('click',e=>{
 if(e.target.closest('[data-fav-toggle]') && currentProduct)toggleFavorite(currentProduct);
});
let sourceProducts=[],remoteRequest=0;
const prevShowStoreResults=showStoreResults;
function applyFilters(){
 const brand=byId('jhcBrandFilter').value.trim().toLocaleLowerCase(),status=byId('jhcStatusFilter').value;
 return sourceProducts.filter(p=>{
  if(brand && !String(p.brands||p.brand||'').toLocaleLowerCase().includes(brand))return false;
  const v=verdict(p).code;
  return status==='all'||(status==='halal'&&v.startsWith('HALAL'))||(status==='haram'&&v.startsWith('HARAM'))||(status==='doubtful'&&v==='DOUBTFUL')||(status==='unknown'&&v==='UNKNOWN_PRODUCT');
 });
}
function showFiltered(){
 const filtered=applyFilters();
 if(!filtered.length&&sourceProducts.length){
  window.searchProducts=[];
  byId('shoppingNotice').hidden=true;
  byId('searchResults').innerHTML='<div class="notice">'+esc(L('results'))+'</div>';return;
 }
 prevShowStoreResults(filtered);
 byId('searchResults').querySelectorAll('[data-search-result]').forEach(b=>{
  const p=window.searchProducts?.[Number(b.dataset.searchResult)];if(!p)return;
  const v=verdict(p),cls=v.code.startsWith('HALAL')?'halal':v.code.startsWith('HARAM')?'haram':v.code==='UNKNOWN_PRODUCT'?'unknown':'';
  b.querySelector('div')?.insertAdjacentHTML('beforeend','<span class="jhc-mini-status '+cls+'">'+esc(verificationLevels[v.code][0])+'</span>');
 });
}
function uniqueProducts(products){
 const map=new Map();
 products.forEach(p=>{
  const key=keyOf(p);if(!key)return;
  if(!map.has(key))map.set(key,p);
  else {const prev=map.get(key);if(!ingredientsOf(prev)&&ingredientsOf(p))map.set(key,{...prev,...p});}
 });
 return [...map.values()];
}
async function queryPublicProducts(query,token){
 // The Supabase public catalogue allows SELECT; never put a service-role key in frontend code.
 if(!query||query==='all'||query.length<2)return;
 const needle=query.replace(/[(),.*%]/g,' ').trim().slice(0,70);
 if(!needle)return;
 try{
  const root=String(window.HALAL_API_BASE||'').replace(/\/$/,'');
  if(!/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(root))return;
  const key=String(window.HALAL_API_PUBLIC_KEY||'');if(!key)return;
  const u=new URL(root+'/rest/v1/jhc_floot_products');
  u.searchParams.set('select','source_id,barcode,name,name_ja,brand,ingredients,image_url,evidence_source,evidence_url,category');
  u.searchParams.set('or','(name.ilike.*'+needle+'*,name_ja.ilike.*'+needle+'*,brand.ilike.*'+needle+'*,barcode.eq.'+(/^\d{8,14}$/.test(needle)?needle:'0')+')');
  u.searchParams.set('limit','50');
  const r=await fetch(u,{headers:{apikey:key,Authorization:'Bearer '+key},signal:AbortSignal.timeout?AbortSignal.timeout(8000):undefined});
  if(!r.ok)return;
  const rows=await r.json();if(!Array.isArray(rows)||token!==remoteRequest || currentPage!=='search')return;
  const mapped=rows.map(x=>({code:x.barcode||'',product_name:x.name_ja||x.name,brands:x.brand||'',ingredients_text:x.ingredients||'',image_url:x.image_url||'',_catalogId:'floot:'+x.source_id,_source:x.evidence_source||'Floot public catalogue',_sourceUrl:x.evidence_url||'',_category:x.category||'',_store:''}));
  if(mapped.length){sourceProducts=uniqueProducts([...sourceProducts,...mapped]);showFiltered();}
 }catch(e){/* A missing network connection leaves existing offline and provider results usable. */}
}
showStoreResults=function(products){
 sourceProducts=uniqueProducts(Array.isArray(products)?products:[]);
 showFiltered();
 const currentQuery=String(lastLookup||byId('productQuery').value||'').trim();
 const ticket=++remoteRequest;
 if(currentPage==='search' && currentQuery!=='all')queryPublicProducts(currentQuery,ticket);
};
for(const event of ['input','change']){
 byId('jhcBrandFilter').addEventListener(event,()=>{if(currentPage==='search')showFiltered();});
 byId('jhcStatusFilter').addEventListener(event,()=>{if(currentPage==='search')showFiltered();});
}
byId('language').addEventListener('change',()=>{renderLabels();renderFavorites();if(currentPage==='history')renderSearchHistory();});
renderLabels();renderFavorites();
})();