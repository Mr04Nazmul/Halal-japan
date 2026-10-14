/* Japan Halal Checker enhancements, 2026-10-14.
   Additive client-side features. Existing barcode scanner and product sources are left intact.
   Halal levels require reviewer-backed evidence; never assume halal from missing keywords. */
(function () {
  'use strict';
  var byId = function(id){ return document.getElementById(id); };
  if (!byId('premiumHome') || !byId('searchPanel') || typeof window.renderProduct !== 'function') return;
  var html = function(value){return String(value == null ? '' : value).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c];});};
  var safeUrl = function(value){try{var u=new URL(String(value));return u.protocol==='https:'?u.href:'';}catch(e){return '';}};
  var dictionary = {
    en:{saved:'Favorites', searches:'Recent searches', collection:'Collection', save:'Save to favorites', remove:'Remove', empty:'Nothing saved yet.', noSearch:'No searches yet.', clear:'Clear searches', brand:'Brand', assessment:'Halal assessment', every:'All statuses', halal:'Halal verified', haram:'Haram concern', doubtful:'Doubtful', unknown:'Unknown', evidence:'Verification evidence', reason:'Decision reason', ingredients:'Ingredient information', source:'Information source', notCertified:'A shop listing or ingredient keyword check is not halal certification.', caution:'Ingredient source or certification has not been verified.', sourceMissing:'Complete ingredients have not been provided.', levelGuide:'Assessment levels', favoritesHint:'Saved only on this device. No account required.', historyHint:'Searches are saved only on this device.', view:'View', recent:'Search history', noMatches:'No products match these filters.', updated:'Record date', origin:'Evidence type', certificate:'Certificate', filtered:'Matching products', scanHistory:'Recent scans', brandPlaceholder:'Filter by brand', categoryPlaceholder:'Category name'},
    bn:{saved:'পছন্দের পণ্য', searches:'সাম্প্রতিক সার্চ', collection:'কালেকশন', save:'পছন্দের তালিকায় রাখো', remove:'মুছে ফেলো', empty:'এখনো কোনো পণ্য সেভ নেই।', noSearch:'এখনো কোনো সার্চ নেই।', clear:'সার্চ হিস্ট্রি মুছো', brand:'ব্র্যান্ড', assessment:'হালাল যাচাই', every:'সব স্ট্যাটাস', halal:'যাচাইকৃত হালাল', haram:'হারাম সম্পর্কিত', doubtful:'সন্দেহজনক', unknown:'অজানা', evidence:'যাচাইয়ের প্রমাণ', reason:'সিদ্ধান্তের কারণ', ingredients:'উপাদানের তথ্য', source:'তথ্যের উৎস', notCertified:'দোকানের তালিকা বা ingredient check হালাল সনদ নয়।', caution:'উপাদানের উৎস বা সার্টিফিকেশন যাচাই হয়নি।', sourceMissing:'সম্পূর্ণ উপাদানের তথ্য পাওয়া যায়নি।', levelGuide:'যাচাইয়ের স্তর', favoritesHint:'শুধু এই ফোনে সেভ থাকবে। অ্যাকাউন্ট লাগবে না।', historyHint:'সার্চের তথ্য শুধু এই ফোনে থাকবে।', view:'দেখো', recent:'সার্চ হিস্ট্রি', noMatches:'এই ফিল্টারে কোনো পণ্য নেই।', updated:'তথ্যের তারিখ', origin:'প্রমাণের ধরন', certificate:'সার্টিফিকেট', filtered:'মিলে যাওয়া পণ্য', scanHistory:'সাম্প্রতিক স্ক্যান', brandPlaceholder:'ব্র্যান্ড দিয়ে ফিল্টার', categoryPlaceholder:'কালেকশনের নাম'},
    ja:{saved:'お気に入り', searches:'最近の検索', collection:'コレクション', save:'お気に入りに保存', remove:'削除', empty:'保存した商品はありません。', noSearch:'検索履歴はありません。', clear:'検索履歴を削除', brand:'ブランド', assessment:'ハラール判定', every:'すべて', halal:'確認済みハラール', haram:'ハラームの懸念', doubtful:'要確認', unknown:'不明', evidence:'確認資料', reason:'判定理由', ingredients:'原材料情報', source:'情報元', notCertified:'店頭掲載や成分チェックはハラール認証ではありません。', caution:'原材料の由来や認証を確認できていません。', sourceMissing:'完全な原材料情報がありません。', levelGuide:'判定レベル', favoritesHint:'この端末のみに保存されます。', historyHint:'検索履歴はこの端末のみに保存されます。', view:'表示', recent:'検索履歴', noMatches:'条件に合う商品がありません。', updated:'情報の日付', origin:'証拠の種類', certificate:'証明書', filtered:'検索結果', scanHistory:'最近のスキャン', brandPlaceholder:'ブランドで絞り込み', categoryPlaceholder:'コレクション名'}
  };
  function t(k){var code=typeof lang==='string'?lang:'en';return (dictionary[code]||dictionary.en)[k]||dictionary.en[k]||k;}
  function readStore(key){try{var v=JSON.parse(localStorage.getItem(key)||'[]');return Array.isArray(v)?v:[];}catch(e){return [];}}
  function writeStore(key,rows){try{localStorage.setItem(key,JSON.stringify(rows));return true;}catch(e){return false;}}
  var favoritesKey='jhc_favorites_v1', searchesKey='jhc_searches_v1';
  function productKey(p){return String(p._catalogId||p.code||p.barcode||p._sourceUrl||(p.brands||'')+':'+(p.product_name||p.name||''));}
  function compactProduct(p){var keys=['_catalogId','_category','_store','_source','_sourceUrl','_snapshotDate','_halalEvidence','_quantity','_country','_region','_nutrition','_allergens','code','product_name','product_name_ja','product_name_en','brands','image_url','image_front_small_url','ingredients_text','ingredients_text_ja','ingredients_text_en','labels_tags','lang'];var result={};keys.forEach(function(k){if(p[k]!==undefined)result[k]=p[k];});return result;}
  function listFavorites(){return readStore(favoritesKey);}
  function listSearches(){return readStore(searchesKey);}
  function noteSearch(value,type){var q=String(value||'').trim().slice(0,400);if(!q)return;var rows=listSearches().filter(function(x){return !(x.q===q&&x.type===type);});rows.unshift({q:q,type:type,time:Date.now()});writeStore(searchesKey,rows.slice(0,50));}
  function classification(p){
    var ingredients=String(p.ingredients_text||p.ingredients_text_ja||p.ingredients_text_en||'');
    var evidence=p._verification;
    var levels=['HALAL_LV1','HALAL_LV2','HALAL_LV3','HARAM_LV1','HARAM_LV2','DOUBTFUL','UNKNOWN_PRODUCT'];
    // These fields are accepted only from explicit, published reviewer-backed verification.
    if(evidence&&evidence.published===true&&evidence.reviewed_at&&safeUrl(evidence.source_url)&&levels.indexOf(evidence.classification)>=0)
      return {level:evidence.classification,reason:String(evidence.rationale||'Reviewed evidence attached'),source:safeUrl(evidence.source_url),reviewedAt:evidence.reviewed_at};
    if(!ingredients.trim())return {level:'UNKNOWN_PRODUCT',reason:t('sourceMissing'),source:'',reviewedAt:''};
    var checked=halalAssessment(ingredients,p.labels_tags?.join(',')||'');
    if(checked.status==='haram'){
      var pork=/(豚|ポーク|ラード|pork|porcine|lard|bacon|pig blood)/i.test(ingredients);
      return {level:pork?'HARAM_LV1':'HARAM_LV2',reason:checked.reasons.join('; '),source:'',reviewedAt:''};
    }
    return {level:'DOUBTFUL',reason:(checked.reasons||[]).join('; ')||t('caution'),source:'',reviewedAt:''};
  }
  function statusGroup(p){var level=classification(p).level;return level.startsWith('HALAL')?'halal':level.startsWith('HARAM')?'haram':level==='DOUBTFUL'?'doubtful':'unknown';}
  var style=document.createElement('style');style.id='jhcEnhancedStyles';style.textContent=[
    '.jhc-launches{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:15px 0}',
    '.jhc-launches button{border:1px solid #cfe3d7;background:#f3fbf4;color:#075438;padding:13px 8px;border-radius:14px;font-weight:750;font-size:13px}',
    '.jhc-panel{background:#f7faf8;border:1px solid #e1ebe5;border-radius:14px;padding:14px;margin:14px 0}',
    '.jhc-panel h3{margin:0 0 10px;font-size:16px}',
    '.jhc-filter-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}',
    '.jhc-filter-grid label{font-size:12px;font-weight:700;color:#365443}',
    '.jhc-filter-grid input,.jhc-filter-grid select,.jhc-save-row input{display:block;width:100%;min-width:0;margin-top:5px;border:1px solid #cbded0;background:#fff;border-radius:10px;padding:11px;color:#142c23;font:inherit;font-size:13px}',
    '.jhc-save-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:end}',
    '.jhc-save-row .btn{white-space:normal;font-size:12px}',
    '.jhc-level{display:inline-block;font-size:12px;font-weight:800;border-radius:10px;padding:7px 10px;background:#fff2c9;color:#6d5113}',
    '.jhc-level.red{background:#ffe3df;color:#8d291e}.jhc-level.green{background:#dff5e0;color:#145c34}.jhc-level.gray{background:#e9eeeb;color:#55645b}',
    '.jhc-evidence p{margin:8px 0;font-size:13px;overflow-wrap:anywhere}',
    '.jhc-mini{display:flex;gap:9px;align-items:center;justify-content:space-between;padding:13px 0;border-bottom:1px solid #e2eae4}',
    '.jhc-mini>div{flex:1;min-width:0}.jhc-mini b{display:block;font-size:13px;overflow-wrap:anywhere}.jhc-mini small{display:block;color:#678074;font-size:11px}',
    '.jhc-mini button{border:1px solid #d6e4d9;background:#fff;color:#0c5334;padding:9px;border-radius:10px;font-size:12px}',
    '.jhc-inline-btn{border:0;background:#e6f3ea;color:#075438;border-radius:11px;padding:11px;font-weight:750;font-size:12px;cursor:pointer}',
    '.jhc-legend{font-size:12px;color:#63766d;line-height:1.8}',
    '@media(max-width:340px){.jhc-filter-grid{grid-template-columns:1fr}.jhc-save-row{grid-template-columns:1fr}}'
  ].join('');document.head.appendChild(style);
  var home=byId('premiumHome');
  var launches=document.createElement('div');launches.className='jhc-launches';
  launches.innerHTML='<button type="button" data-jhc-page="favorites">★ '+html(t('saved'))+'</button><button type="button" data-jhc-page="searchHistory">⌕ '+html(t('searches'))+'</button>';
  var homeNote=home.querySelector('.home-note');if(homeNote)homeNote.insertAdjacentElement('afterend',launches);else home.appendChild(launches);
  var searchPanel=byId('searchPanel');
  var filterPanel=document.createElement('div');filterPanel.className='jhc-panel';
  filterPanel.innerHTML='<h3>'+html(t('filtered'))+'</h3><div class="jhc-filter-grid"><label>'+html(t('brand'))+'<input id="jhcBrandFilter" type="search" placeholder="'+html(t('brandPlaceholder'))+'"></label><label>'+html(t('assessment'))+'<select id="jhcStatusFilter"><option value="all">'+html(t('every'))+'</option><option value="halal">'+html(t('halal'))+'</option><option value="haram">'+html(t('haram'))+'</option><option value="doubtful">'+html(t('doubtful'))+'</option><option value="unknown">'+html(t('unknown'))+'</option></select></label></div>';
  searchPanel.insertBefore(filterPanel,searchPanel.querySelector('.settings-card'));
  var guide=byId('premiumGuide');
  if(guide){
    var legend=document.createElement('div');legend.className='jhc-panel jhc-legend';legend.innerHTML='<h3>'+html(t('levelGuide'))+'</h3>'+
      '<b>HALAL LV1</b> — independently verified current certificate<br>'+
      '<b>HALAL LV2</b> — documented manufacturer confirmation<br>'+
      '<b>HALAL LV3</b> — ingredients and origin reviewed with evidence<br>'+
      '<b>HARAM LV1</b> — explicit prohibited animal ingredient<br>'+
      '<b>HARAM LV2</b> — other verified prohibited ingredient<br>'+
      '<b>DOUBTFUL</b> — source or formulation unresolved<br>'+
      '<b>UNKNOWN</b> — not enough product data<br>'+
      '<small>'+html(t('notCertified'))+'</small>';
    guide.appendChild(legend);
  }
  var favoritesSection=document.createElement('section');favoritesSection.id='jhcFavoritesPage';favoritesSection.className='page-hidden';favoritesSection.innerHTML='<h2 class="screen-heading">'+html(t('saved'))+'</h2><p class="sub">'+html(t('favoritesHint'))+'</p><div id="jhcFavoritesRows"></div>';home.insertAdjacentElement('afterend',favoritesSection);
  var searchesSection=document.createElement('section');searchesSection.id='jhcSearchHistoryPage';searchesSection.className='page-hidden';searchesSection.innerHTML='<h2 class="screen-heading">'+html(t('recent'))+'</h2><p class="sub">'+html(t('historyHint'))+'</p><div id="jhcSearchRows"></div><button type="button" class="btn secondary" id="jhcClearSearches">'+html(t('clear'))+'</button>';favoritesSection.insertAdjacentElement('afterend',searchesSection);
  var baseNavigate=window.navigate;
  window.navigate=function(page){
    favoritesSection.classList.add('page-hidden');searchesSection.classList.add('page-hidden');
    if(page!=='favorites'&&page!=='searchHistory')return baseNavigate(page);
    baseNavigate('home');
    home.classList.add('page-hidden');
    var active=page==='favorites'?favoritesSection:searchesSection;active.classList.remove('page-hidden');
    if(typeof currentPage!=='undefined')currentPage=page;
    document.body.dataset.page=page;
    byId('pageTitle').textContent=page==='favorites'?t('saved'):t('recent');
    byId('backButton').textContent='‹';
    if(page==='favorites')renderFavorites();else renderSearches();
    window.scrollTo(0,0);
  };
  function renderFavorites(){
    var all=listFavorites();
    byId('jhcFavoritesRows').innerHTML=all.length?all.map(function(x,i){
      var p=x.product||{};
      return '<div class="jhc-mini"><div><b>'+html(p.product_name||p.product_name_ja||p.code||'Product')+'</b><small>'+html(x.category||'Saved')+' · '+html(p.brands||'')+'</small></div><button type="button" data-jhc-favorite-open="'+i+'">'+html(t('view'))+'</button><button type="button" data-jhc-favorite-remove="'+i+'">'+html(t('remove'))+'</button></div>';
    }).join(''):'<p class="sub">'+html(t('empty'))+'</p>';
  }
  function renderSearches(){
    var all=listSearches();byId('jhcSearchRows').innerHTML=all.length?all.map(function(x,i){
      return '<div class="jhc-mini"><div><b>'+html(x.q)+'</b><small>'+html(x.type==='barcode'?'JAN / barcode':'Product search')+' · '+new Date(x.time).toLocaleString()+'</small></div><button type="button" data-jhc-search-open="'+i+'">'+html(t('view'))+'</button></div>';
    }).join(''):'<p class="sub">'+html(t('noSearch'))+'</p>';
  }
  function levelColor(level){return level.startsWith('HALAL')?'green':level.startsWith('HARAM')?'red':level==='UNKNOWN_PRODUCT'?'gray':'';}
  function detailEnhancement(p){
    var box=byId('result');if(!box)return;
    var previous=box.querySelector('#jhcProductEnhancements');if(previous)previous.remove();
    var info=classification(p),src=safeUrl(p._sourceUrl||''),cert=safeUrl(p._halalEvidence?.url||'');
    var dates=p._snapshotDate||'',key=productKey(p),saved=listFavorites().find(function(item){return item.key===key;});
    var panel=document.createElement('section');panel.id='jhcProductEnhancements';panel.className='jhc-panel jhc-evidence';
    panel.innerHTML='<h3>'+html(t('assessment'))+'</h3><span class="jhc-level '+levelColor(info.level)+'">'+html(info.level.replace(/_/g,' '))+'</span>'+
      '<p><b>'+html(t('reason'))+':</b> '+html(info.reason)+'</p>'+
      '<h3>'+html(t('evidence'))+'</h3><p><b>'+html(t('source'))+':</b> '+html(p._source||'Unverified product listing')+'</p>'+
      (src?'<p><a href="'+html(src)+'" target="_blank" rel="noopener">Source record ↗</a></p>':'')+
      (cert?'<p><a href="'+html(cert)+'" target="_blank" rel="noopener">Retailer listing ↗</a></p>':'')+
      (dates?'<p><b>'+html(t('updated'))+':</b> '+html(dates)+'</p>':'')+
      (info.reviewedAt?'<p><b>Reviewed:</b> '+html(info.reviewedAt)+'</p>':'')+
      (info.source?'<p><a href="'+html(info.source)+'" target="_blank" rel="noopener">Verified evidence ↗</a></p>':'')+
      '<p class="small">'+html(t('notCertified'))+'</p>'+
      '<div class="jhc-save-row"><label class="small">'+html(t('collection'))+'<input id="jhcFavoriteCategory" maxlength="80" type="text" value="'+html(saved?.category||'Saved')+'" placeholder="'+html(t('categoryPlaceholder'))+'"></label><button class="btn" type="button" id="jhcFavoriteSave">'+html(t('save'))+'</button></div>'+
      (saved?'<button type="button" class="jhc-inline-btn" id="jhcFavoriteUnsave">'+html(t('remove'))+'</button>':'');
    box.appendChild(panel);
    byId('jhcFavoriteSave').onclick=function(){
      var category=String(byId('jhcFavoriteCategory').value||'Saved').trim().slice(0,80)||'Saved';
      var updated=listFavorites().filter(function(item){return item.key!==key;});
      updated.unshift({key:key,category:category,product:compactProduct(p),time:Date.now()});
      if(writeStore(favoritesKey,updated.slice(0,150)))detailEnhancement(p);
    };
    if(byId('jhcFavoriteUnsave'))byId('jhcFavoriteUnsave').onclick=function(){
      writeStore(favoritesKey,listFavorites().filter(function(x){return x.key!==key;}));detailEnhancement(p);
    };
  }
  var oldRenderProduct=window.renderProduct;
  window.renderProduct=function(p){oldRenderProduct(p);detailEnhancement(p);};
  // Keep raw search results so changing filters does not cause network requests or change scanner state.
  var oldShowStoreResults=window.showStoreResults, unfiltered=null, searchEpoch=0, catalogPromise=null;
  function filtered(products){
    var brand=String(byId('jhcBrandFilter')?.value||'').trim().normalize('NFKC').toLowerCase();
    var status=String(byId('jhcStatusFilter')?.value||'all');
    var store=String(byId('storeFilter')?.value||'all');
    var category=String(byId('foodFilter')?.value||'all');
    return products.filter(function(p){
      if(brand&&!String(p.brands||p.brand||'').normalize('NFKC').toLowerCase().includes(brand))return false;
      if(status!=='all'&&statusGroup(p)!==status)return false;
      if(store!=='all'&&p._store!==store)return false;
      if(category!=='all'&&p._category!==category)return false;
      return true;
    });
  }
  function showFiltered(){if(!Array.isArray(unfiltered))return;oldShowStoreResults(filtered(unfiltered));if(unfiltered.length&&!filtered(unfiltered).length){byId('searchResults').innerHTML='<div class="notice">'+html(t('noMatches'))+'</div>';}}
  function fetchPublicCatalog(){
    if(catalogPromise)return catalogPromise;
    catalogPromise=(async function(){
      var base=String(window.HALAL_API_BASE||''),key=String(window.HALAL_API_PUBLIC_KEY||'');
      if(!/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(base)||!key)return [];
      var u=new URL('/rest/v1/jhc_floot_products',base);
      u.searchParams.set('select','source_id,barcode,name,name_ja,brand,ingredients,image_url,evidence_source,evidence_url,category');
      u.searchParams.set('limit','1000');
      var res=await fetch(u.toString(),{headers:{apikey:key,Authorization:'Bearer '+key},signal:typeof AbortSignal.timeout==='function'?AbortSignal.timeout(10000):undefined});
      if(!res.ok)throw Error('Public product catalogue unavailable');
      var rows=await res.json();
      return Array.isArray(rows)?rows.map(function(r){
        return {_catalogId:'jhc:'+r.source_id,code:r.barcode||'',product_name:r.name_ja||r.name||'',brands:r.brand||'',ingredients_text:r.ingredients||'',image_url:r.image_url||'',_source:r.evidence_source||'Supabase catalogue',_sourceUrl:r.evidence_url||'',_category:r.category||'',_searchTerms:r.name||''};
      }):[];
    })().catch(function(){catalogPromise=null;return [];});
    return catalogPromise;
  }
  function uniqueMerge(a,b){var found=new Set();return a.concat(b).filter(function(p){var key=p.code&&/^\d{8,14}$/.test(String(p.code))?String(p.code).padStart(14,'0'):productKey(p);if(found.has(key))return false;found.add(key);return true;});}
  window.showStoreResults=function(products){
    unfiltered=Array.isArray(products)?products.slice():[];showFiltered();
    // Only enrich an explicit name/brand search with the already-public, RLS-authorized catalogue.
    var query=String(typeof lastLookup==='string'?lastLookup:'').trim();
    var store=byId('storeFilter')?.value||'all',category=byId('foodFilter')?.value||'all';
    var epoch=++searchEpoch;
    if(!query||query==='all'||/^\d{8,14}$/.test(query)||store!=='all'||category!=='all')return;
    fetchPublicCatalog().then(function(rows){
      if(epoch!==searchEpoch||typeof currentPage==='undefined'||currentPage!=='search')return;
      var q=query.normalize('NFKC').toLowerCase();
      var matches=rows.filter(function(p){return [p.product_name,p.brands,p._searchTerms,p.code,p._category].some(function(value){return String(value||'').normalize('NFKC').toLowerCase().includes(q);});}).slice(0,50);
      if(matches.length){unfiltered=uniqueMerge(unfiltered,matches);showFiltered();}
    });
  };
  byId('jhcBrandFilter').addEventListener('input',showFiltered);
  byId('jhcStatusFilter').addEventListener('change',showFiltered);
  byId('storeFilter').addEventListener('change',showFiltered);
  byId('foodFilter').addEventListener('change',showFiltered);
  byId('searchBtn').addEventListener('click',function(){noteSearch(byId('productQuery').value,'text');});
  byId('lookupBtn').addEventListener('click',function(){noteSearch(byId('barcode').value,'barcode');});
  byId('homeSearch').addEventListener('submit',function(){var q=byId('homeQuery').value;noteSearch(q,/^\d{8,14}$/.test(q)?'barcode':'text');},true);
  document.addEventListener('click',function(ev){
    var e=ev.target.closest('[data-jhc-page],[data-jhc-favorite-open],[data-jhc-favorite-remove],[data-jhc-search-open]');
    if(!e)return;
    if(e.dataset.jhcPage){window.navigate(e.dataset.jhcPage);return;}
    if(e.dataset.jhcFavoriteOpen!==undefined){var f=listFavorites()[Number(e.dataset.jhcFavoriteOpen)];if(f&&f.product)window.renderProduct(f.product);return;}
    if(e.dataset.jhcFavoriteRemove!==undefined){var idx=Number(e.dataset.jhcFavoriteRemove),all=listFavorites();if(idx>=0&&idx<all.length){all.splice(idx,1);writeStore(favoritesKey,all);renderFavorites();}return;}
    if(e.dataset.jhcSearchOpen!==undefined){var s=listSearches()[Number(e.dataset.jhcSearchOpen)];if(!s)return;window.navigate('search');if(s.type==='barcode'){byId('barcode').value=s.q;byId('lookupBtn').click();}else{byId('productQuery').value=s.q;byId('searchBtn').click();}return;}
  });
  byId('jhcClearSearches').onclick=function(){localStorage.removeItem(searchesKey);renderSearches();};
  // Expose test-only pure logic for safe verification without touching camera/network.
  window.JHCFeatures={classify:classification,group:statusGroup,filterProducts:filtered};
})();