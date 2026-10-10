/* Official catalogue parser. Store item IDs are not JAN barcodes. */
globalThis.HALAL_STORE_PARSER=function(document,config,date){
 const clean=x=>(x?.textContent||'').replace(/\s+/g,' ').trim(),absolute=x=>{try{return new URL(x,config.url).href}catch{return ''}},records=[];
 const add=(id,name,url,image,extra={})=>{if(!id||!name)return;records.push({code:'',product_name:name,brands:{family:'FamilyMart',seven:'7-Eleven',lawson:'Lawson'}[config.store],ingredients_text:'',lang:'ja',image_url:absolute(image||''),_source:config.store==='seven'?'7-Eleven Japan':config.store==='family'?'FamilyMart Japan':'Lawson Japan',_sourceUrl:absolute(url||config.url),_catalogId:config.store+':'+id,_store:config.store,_category:config.category,_snapshotDate:date,...extra})};
 if(config.store==='family')for(const info of document.querySelectorAll('.item_basic_info')){
  const row=info.closest('li'),title=info.querySelector('p.name'),a=title?.querySelector('a'),img=row?.querySelector('.conL img')||row?.querySelector('img'),src=img?.getAttribute('src')||'',id=(a?.getAttribute('href')||src).match(/\/(\d+)\.(?:html|jpg)/)?.[1];
  const nutrients=Array.from(row?.querySelectorAll('table.item_nutritional_info td.con_nut')||[]).map(clean);
  add(id,clean(title),a?.getAttribute('href'),src,{_allergens:Array.from(row?.querySelectorAll('table.item_allergen img[alt]')||[]).map(x=>x.getAttribute('alt')).filter(Boolean),_nutrition:nutrients.length===5?Object.fromEntries(['energy_kcal','protein_g','fat_g','carbohydrates_g','salt_g'].map((k,i)=>[k,nutrients[i]])):{},_region:Array.from(row?.querySelectorAll('.ly-mod-tag-area-on em')||[]).map(clean).join('、'),_availability:clean(row?.querySelector('dd.aten'))});
 }else if(config.store==='seven')for(const row of document.querySelectorAll('.list_inner')){
  const a=row.querySelector('.item_ttl a'),href=a?.getAttribute('href')||'',id=href.match(/\/item\/(\d+)\//)?.[1],img=row.querySelector('img');
  add(id,clean(a),href,img?.getAttribute('data-original')||img?.getAttribute('src'),{_region:clean(row.querySelector('.item_region')),_availability:clean(row.querySelector('.item_launch'))});
 }else if(config.store==='lawson')for(const a of document.querySelectorAll('a[href*="/recommend/original/detail/"]')){
  const href=a.getAttribute('href')||'',id=href.match(/\/(\d+_\d+)\.html/)?.[1],row=a.closest('li'),name=clean(row?.querySelector('.ttl'));if(!name)continue;
  const energy=clean(row).match(/(?:1包装当たり|1個当たり|1食当たり)([\d.]+)kcal/);
  add(id,name,href,a.querySelector('img')?.getAttribute('src'),{_nutrition:energy?{energy_kcal:energy[1]}:{},_availability:clean(row.querySelector('.ico_new')),_region:Array.from(row.querySelectorAll('.smalltxt')).map(clean).join(' ')});
 }
 return Array.from(new Map(records.map(p=>[p._catalogId,p])).values());
};
