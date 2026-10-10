/* Only parse cards from Gyomu Super's explicit halal category, never its generic sidebar. */
globalThis.HALAL_GYOMU_PARSER=function(document,page,date,saved=[]){
 if(!document.querySelector('.bread_cramb')?.textContent.includes('ハラール'))return [];
 const url='https://www.gyomusuper.jp/product/list.php?gc_id=312&page='+page,records=[];
 for(const card of document.querySelectorAll('.item_wrap .item')){const a=card.querySelector('a'),href=a?.getAttribute('href')||'',id=href.match(/go_id=(\d+)/)?.[1],name=card.querySelector('.item_name')?.textContent.trim();if(!id||!name)continue;const img=card.querySelector('img'),old=saved.find(p=>p._catalogId==='gyomu:'+id);
 records.push({...old,code:old?.code||'',product_name:old?.product_name||name,brands:'Gyomu Super',ingredients_text:'',lang:'ja',image_url:img?new URL(img.getAttribute('data-original')||img.getAttribute('src'),url).href:'',_source:'Gyomu Super official catalogue',_sourceUrl:new URL(href,url).href,_catalogId:'gyomu:'+id,_store:'gyomu',_category:'halal',_snapshotDate:old?._snapshotDate||date,_catalogCheckedDate:date,_catalogPage:page,_halalEvidence:{kind:'retailer-listing',url}});
 }return Array.from(new Map(records.map(p=>[p._catalogId,p])).values());
};
