/* Japan Halal Checker places/prayer tools.
 * OSM listings are community-contributed, never independently certified.
 * Prayer times are astronomical estimates, not mosque-published timetables.
 */
(() => {
 'use strict';
 const $=id=>document.getElementById(id);
 const cities={
  Kobe:[34.6901,135.1955], Osaka:[34.6937,135.5023],
  Kyoto:[35.0116,135.7681],Tokyo:[35.6762,139.6503],
  Nagoya:[35.1815,136.9066],Fukuoka:[33.5904,130.4017],
  Sapporo:[43.0618,141.3545],Nara:[34.6851,135.8048]
 };
 const messages={
  en:{externalMosques:'Open mosque search ↗',externalFood:'Open halal restaurant search ↗',title:'Nearby halal food & mosques',subtitle:'Explore community-mapped places and calculated prayer times in Japan.',location:'Choose location',city:'City',radius:'Search radius',useGPS:'Use my current location',refresh:'Refresh map',mapTitle:'Live OpenStreetMap listings',type:'Place type',all:'All places',mosques:'Mosques',food:'Halal food listings',placeSearch:'Filter results',search:'Search by name',osmDisclaimer:'Locations and halal tags are community-contributed OpenStreetMap data, not checked halal certification. Ask each restaurant about ingredients and current practices.',directory:'See our researched restaurant directory ↗',prayerTitle:"Today's prayer times in Japan",method:'Calculation method',asrRule:'Asr calculation',prayerDisclaimer:'Astronomical estimates in Japan Standard Time (JST). Local mosques may use different timetables; follow your mosque for exact times.',qiblaTitle:'Qibla direction',qiblaNote:'Bearing clockwise from true north. Align north using a compass before following the arrow.',fajr:'Fajr',sunrise:'Sunrise',dhuhr:'Dhuhr',asr:'Asr',maghrib:'Maghrib',isha:'Isha',loading:'Loading places from OpenStreetMap…',loaded:'Places shown',empty:'No matching places in this area. Try another city or radius.',network:'Live locations unavailable. Please retry. No unverified places were added.',gpsDenied:'Location unavailable or permission denied. Select a city instead.',geo:'Your current position',north:'clockwise from true north',mapError:'Map library unavailable. Check internet and reload.',prayerError:'Prayer calculation library is unavailable. Please retry online.',directions:'Open directions ↗',osm:'View OpenStreetMap source ↗',mosqueType:'Mosque · OSM listing',foodType:'Food · OSM halal tag (not certified)',notCertified:'Certification not independently checked',today:'JST',coords:'Selected area',attribution:'Listings: OpenStreetMap contributors'},
  bn:{externalMosques:'মসজিদের লাইভ সার্চ ↗',externalFood:'হালাল রেস্টুরেন্টের লাইভ সার্চ ↗',title:'কাছের হালাল খাবার ও মসজিদ',subtitle:'জাপানের কমিউনিটি ম্যাপে থাকা জায়গা, নামাজের সময় এবং কিবলা দেখো।',location:'লোকেশন নির্বাচন',city:'শহর',radius:'খোঁজার দূরত্ব',useGPS:'আমার লোকেশন ব্যবহার',refresh:'ম্যাপ রিফ্রেশ',mapTitle:'লাইভ OpenStreetMap লোকেশন',type:'জায়গার ধরন',all:'সব জায়গা',mosques:'মসজিদ',food:'হালাল খাবারের তালিকা',placeSearch:'ফলাফল ফিল্টার',search:'নাম দিয়ে খোঁজো',osmDisclaimer:'OpenStreetMap-এর লোকেশন ও হালাল ট্যাগ সাধারণ ব্যবহারকারীরা যোগ করেন। এগুলো আমাদের যাচাইকৃত হালাল সনদ নয়। রেস্টুরেন্টে উপাদান ও বর্তমান নিয়ম নিশ্চিত করো।',directory:'আমাদের সংগৃহীত রেস্টুরেন্ট ডিরেক্টরি ↗',prayerTitle:'জাপানে আজকের নামাজের সময়',method:'সময় গণনার পদ্ধতি',asrRule:'আসরের হিসাব',prayerDisclaimer:'জাপান সময় (JST) অনুযায়ী জ্যোতির্বৈজ্ঞানিক আনুমানিক হিসাব। স্থানীয় মসজিদের সময়সূচি আলাদা হতে পারে।',qiblaTitle:'কিবলার দিক',qiblaNote:'উত্তর থেকে ঘড়ির কাঁটার দিকে দিক। ফোনের তীর ধরার আগে কম্পাস দিয়ে উত্তর মিলিয়ে নাও।',fajr:'ফজর',sunrise:'সূর্যোদয়',dhuhr:'জোহর',asr:'আসর',maghrib:'মাগরিব',isha:'এশা',loading:'OpenStreetMap থেকে জায়গা খোঁজা হচ্ছে…',loaded:'মোট পাওয়া গেছে',empty:'এখানে মিলে যাওয়া জায়গা নেই। অন্য শহর বা বেশি দূরত্ব বেছে নাও।',network:'লাইভ লোকেশন পাওয়া যায়নি। আবার চেষ্টা করো। অনুমান করে কোনো জায়গা যোগ করা হয়নি।',gpsDenied:'লোকেশন পাওয়া যায়নি অথবা অনুমতি দেওয়া হয়নি। শহর বেছে নাও।',geo:'তোমার বর্তমান লোকেশন',north:'উত্তর থেকে ঘড়ির কাঁটার দিকে',mapError:'ম্যাপ লাইব্রেরি লোড হয়নি। ইন্টারনেট চেক করো।',prayerError:'নামাজের হিসাব লাইব্রেরি লোড হয়নি। ইন্টারনেট চেক করো।',directions:'দিকনির্দেশনা ↗',osm:'OpenStreetMap উৎস ↗',mosqueType:'মসজিদ · OSM তথ্য',foodType:'খাবার · OSM হালাল ট্যাগ (সনদ নয়)',notCertified:'হালাল সনদ স্বাধীনভাবে যাচাই হয়নি',today:'জাপান সময়',coords:'নির্বাচিত এলাকা',attribution:'তথ্য: OpenStreetMap ব্যবহারকারীরা'},
  ja:{externalMosques:'モスクを地図で検索 ↗',externalFood:'ハラール料理店を地図で検索 ↗',title:'近くのハラール料理・モスク',subtitle:'日本のコミュニティ地図、礼拝時間、キブラの方角を確認できます。',location:'場所を選択',city:'都市',radius:'検索範囲',useGPS:'現在地を使う',refresh:'地図を更新',mapTitle:'OpenStreetMapの掲載情報',type:'施設の種類',all:'すべて',mosques:'モスク',food:'ハラール料理の掲載情報',placeSearch:'絞り込み',search:'名前で検索',osmDisclaimer:'掲載場所とハラールタグはOpenStreetMap利用者が登録した情報で、認証の確認ではありません。最新の原材料や対応内容は各店舗に直接ご確認ください。',directory:'調査済み店舗リストを見る ↗',prayerTitle:'日本の今日の礼拝時間',method:'計算方式',asrRule:'アスルの計算',prayerDisclaimer:'日本標準時（JST）の天文計算による目安です。地域のモスクの礼拝時刻表と異なることがあります。',qiblaTitle:'キブラの方角',qiblaNote:'真北から時計回りの角度です。矢印を見る前にコンパスで北を合わせてください。',fajr:'ファジュル',sunrise:'日の出',dhuhr:'ズフル',asr:'アスル',maghrib:'マグリブ',isha:'イシャー',loading:'OpenStreetMapから検索中…',loaded:'見つかった場所',empty:'該当する場所がありません。都市や検索範囲を変更してください。',network:'位置情報を取得できません。再試行してください。未確認の場所は追加していません。',gpsDenied:'位置情報の利用が拒否または失敗しました。都市を選択してください。',geo:'現在地',north:'真北から時計回り',mapError:'地図ライブラリを読み込めません。通信環境を確認してください。',prayerError:'礼拝時間の計算ライブラリが読み込めません。通信環境を確認してください。',directions:'経路を表示 ↗',osm:'OpenStreetMapの元データ ↗',mosqueType:'モスク · OSM掲載',foodType:'飲食店 · OSMハラールタグ（認証ではありません）',notCertified:'認証は独立に確認していません',today:'日本標準時',coords:'選択中の地域',attribution:'情報提供: OpenStreetMap利用者'}
 };
 const state={lat:cities.Kobe[0],lon:cities.Kobe[1],city:'Kobe',gps:false,places:[],map:null,markers:null,request:0,lastKey:'',lastTime:0};
 const lang=()=>messages[$('lang').value]||messages.en;
 const t=k=>lang()[k]||messages.en[k]||k;
 const safe=v=>String(v||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','"':'&quot;',"'":'&#39;'}[c]));
 const distance=(a,b,c,d)=>{const rad=Math.PI/180,dl=(d-b)*rad,df=(c-a)*rad,A=Math.sin(df/2)**2+Math.cos(a*rad)*Math.cos(c*rad)*Math.sin(dl/2)**2;return 6371*2*Math.atan2(Math.sqrt(A),Math.sqrt(1-A))};
 function qiblaBearing(lat,lon){
  const r=Math.PI/180,p=lat*r,delta=(39.8262-lon)*r,k=21.4225*r;
  return (Math.atan2(Math.sin(delta),Math.cos(p)*Math.tan(k)-Math.sin(p)*Math.cos(delta))/r+360)%360;
 }
 function translate(){
  document.documentElement.lang=$('lang').value;
  document.querySelectorAll('[data-i]').forEach(el=>{el.textContent=t(el.dataset.i)});
  document.querySelectorAll('[data-placeholder]').forEach(el=>{el.placeholder=t(el.dataset.placeholder)});
  updateLocationText();drawPlaces();drawPrayers();drawQibla();
 }
 function updateLocationText(){
  $('locationInfo').textContent=(state.gps?t('geo'):state.city)+' · '+state.lat.toFixed(4)+', '+state.lon.toFixed(4);
  // If the free Overpass servers are overloaded, these links still open real map searches.
  const coords=state.lat.toFixed(5)+','+state.lon.toFixed(5);
  const mosque=$('liveMosques'),food=$('liveFood');
  if(mosque){mosque.href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent('mosque near '+coords);mosque.textContent=t('externalMosques');}
  if(food){food.href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent('halal restaurants near '+coords);food.textContent=t('externalFood');}
 }
 function drawQibla(){
  const bearing=qiblaBearing(state.lat,state.lon);
  $('qiblaDegrees').textContent=bearing.toFixed(1)+'°';
  $('qiblaDesc').textContent=t('north');
  $('needle').style.transform='rotate('+bearing+'deg)';
 }
 function jstDate(){
  const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
  const n=k=>Number(parts.find(p=>p.type===k).value);
  return {y:n('year'),m:n('month'),d:n('day')};
 }
 function drawPrayers(){
  const d=jstDate();
  $('prayerDate').textContent=d.y+'-'+String(d.m).padStart(2,'0')+'-'+String(d.d).padStart(2,'0')+' · '+t('today')+' · '+(state.gps?t('geo'):state.city);
  $('prayerGrid').replaceChildren();
  if(!window.adhan){$('prayerGrid').textContent=t('prayerError');return;}
  try{
   const coords=new adhan.Coordinates(state.lat,state.lon),methods={MWL:adhan.CalculationMethod.MuslimWorldLeague,Egyptian:adhan.CalculationMethod.Egyptian,Karachi:adhan.CalculationMethod.Karachi,Singapore:adhan.CalculationMethod.Singapore};
   const params=methods[$('method').value]();params.madhab=$('asr').value==='hanafi'?adhan.Madhab.Hanafi:adhan.Madhab.Shafi;
   // The coordinates are in Japan and formatting is explicitly in JST.
   const times=new adhan.PrayerTimes(coords,new Date(d.y,d.m-1,d.d),params);
   const clock=date=>new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit',hour12:false}).format(date);
   for(const key of ['fajr','sunrise','dhuhr','asr','maghrib','isha']){
    const tile=document.createElement('div');tile.className='prayer';
    const label=document.createElement('span');label.textContent=t(key);
    const value=document.createElement('strong');value.textContent=times[key] instanceof Date&&Number.isFinite(times[key].getTime())?clock(times[key]):'—';
    tile.append(label,value);$('prayerGrid').append(tile);
   }
  }catch(e){$('prayerGrid').textContent=t('prayerError');}
 }
 function initializeMap(){
  if(!window.L){$('mapStatus').textContent=t('mapError');return;}
  if(state.map)return;
  state.map=L.map('map',{scrollWheelZoom:false}).setView([state.lat,state.lon],12);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(state.map);
  state.markers=L.layerGroup().addTo(state.map);
 }
 function redrawPins(rows){
  if(!state.map)return;
  state.markers.clearLayers();
  for(const p of rows){
   const marker=L.circleMarker([p.lat,p.lon],{radius:8,weight:2,color:p.kind==='mosque'?'#096b46':'#aa8232',fillColor:p.kind==='mosque'?'#42bd79':'#e0b75c',fillOpacity:.9});
   const node=document.createElement('div');const strong=document.createElement('strong');strong.textContent=p.name;
   const info=document.createElement('div');info.textContent=p.kind==='mosque'?t('mosqueType'):t('foodType');
   const link=document.createElement('a');link.href='https://www.openstreetmap.org/'+p.osmType+'/'+p.osmId;link.target='_blank';link.rel='noopener';link.textContent=t('osm');
   node.append(strong,info,link);marker.bindPopup(node);marker.addTo(state.markers);
  }
 }
 function drawPlaces(){
  const type=$('type').value,q=$('query').value.trim().toLocaleLowerCase();
  const rows=state.places.filter(p=>(type==='all'||p.kind===type)&&(!q||(p.name+' '+p.address).toLocaleLowerCase().includes(q)));
  $('places').replaceChildren();redrawPins(rows);
  if(!rows.length&&state.places.length&&$('mapStatus').dataset.loaded==='yes'){$('mapStatus').textContent=t('empty');}
  else if(state.places.length&&$('mapStatus').dataset.loaded==='yes'){$('mapStatus').textContent=t('loaded')+': '+rows.length+' · '+t('attribution');}
  for(const p of rows.slice(0,70)){
   const card=document.createElement('article');card.className='place '+(p.kind==='mosque'?'mosque':'eat');
   const name=document.createElement('b');name.textContent=p.name;
   const category=document.createElement('small');category.textContent=(p.kind==='mosque'?t('mosqueType'):t('foodType'))+' · '+p.km.toFixed(1)+' km';
   const address=document.createElement('small');address.textContent=p.address||t('notCertified');
   const osm=document.createElement('a');osm.href='https://www.openstreetmap.org/'+p.osmType+'/'+p.osmId;osm.target='_blank';osm.rel='noopener';osm.textContent=t('osm');
   const link=document.createElement('a');link.href='https://www.google.com/maps/dir/?api=1&destination='+encodeURIComponent(p.lat+','+p.lon);link.target='_blank';link.rel='noopener';link.textContent=t('directions');
   const links=document.createElement('div');links.className='row';links.append(osm,link);card.append(name,category,address,links);
   $('places').append(card);
  }
 }
 function normalize(elements){
  const seen=new Set(),rows=[];
  for(const p of elements){
   const tags=p.tags||{},lat=p.lat??p.center?.lat,lon=p.lon??p.center?.lon;
   if(!Number.isFinite(lat)||!Number.isFinite(lon))continue;
   const kind=tags.religion==='muslim'||tags.building==='mosque'?'mosque':'restaurant';
   if(kind==='restaurant'&&!['yes','only'].includes(tags['diet:halal']))continue;
   const key=p.type+'/'+p.id;if(seen.has(key))continue;seen.add(key);
   const name=tags['name:en']||tags['name:ja']||tags.name|| (kind==='mosque'?'Unnamed mosque':'Unnamed food listing');
   const address=[tags['addr:street'],tags['addr:housenumber'],tags['addr:city']].filter(Boolean).join(' ');
   rows.push({osmType:p.type,osmId:p.id,lat,lon,kind,name,address,km:distance(state.lat,state.lon,lat,lon)});
  }
  return rows.sort((a,b)=>a.km-b.km).slice(0,90);
 }
 async function loadPlaces(force=false){
  const request=++state.request,radius=Number($('radius').value);
  const key=state.lat.toFixed(4)+'|'+state.lon.toFixed(4)+'|'+radius;
  if(!force&&key===state.lastKey&&Date.now()-state.lastTime<300000){drawPlaces();return;}
  initializeMap();
  if(state.map)state.map.setView([state.lat,state.lon],radius<5000?13:12);
  $('mapStatus').dataset.loaded='no';$('mapStatus').textContent=t('loading');
  $('places').replaceChildren();
  // Overpass returns only geo-tagged, public community listings; no synthetic markers.
  const coord='(around:'+radius+','+state.lat.toFixed(5)+','+state.lon.toFixed(5)+')';
  const query='[out:json][timeout:22];(nwr'+coord+'["amenity"="place_of_worship"]["religion"="muslim"];nwr'+coord+'["building"="mosque"];nwr'+coord+'["amenity"~"^(restaurant|fast_food|cafe)$"]["diet:halal"~"^(yes|only)$"];);out center 120;';
  for(const api of ['https://overpass.private.coffee/api/interpreter','https://overpass-api.de/api/interpreter']){
   try{
    const controller=new AbortController();const tm=setTimeout(()=>controller.abort(),24000);
    let response;
    try{response=await fetch(api,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded;charset=UTF-8'},body:new URLSearchParams({data:query}),signal:controller.signal})}finally{clearTimeout(tm)}
    if(!response.ok)throw Error('OSM service '+response.status);
    const data=await response.json();if(!Array.isArray(data.elements))throw Error('Invalid OSM schema');
    if(request!==state.request)return;
    state.places=normalize(data.elements);state.lastKey=key;state.lastTime=Date.now();
    $('mapStatus').dataset.loaded='yes';drawPlaces();
    if(!state.places.length)$('mapStatus').textContent=t('empty');
    return;
   }catch(err){if(request!==state.request)return;}
  }
  state.places=[];state.lastKey='';$('mapStatus').textContent=t('network');redrawPins([]);
 }
 $('city').addEventListener('change',()=>{state.city=$('city').value;[state.lat,state.lon]=cities[state.city];state.gps=false;updateLocationText();drawQibla();drawPrayers();loadPlaces();});
 $('gps').addEventListener('click',()=>{
  if(!navigator.geolocation){$('locationInfo').textContent=t('gpsDenied');return;}
  $('gps').disabled=true;
  navigator.geolocation.getCurrentPosition(pos=>{
   $('gps').disabled=false;state.lat=pos.coords.latitude;state.lon=pos.coords.longitude;state.gps=true;updateLocationText();drawQibla();drawPrayers();loadPlaces(true);
  },()=>{$('gps').disabled=false;$('locationInfo').textContent=t('gpsDenied');},{enableHighAccuracy:false,timeout:12000,maximumAge:300000});
 });
 $('load').addEventListener('click',()=>loadPlaces(true));
 $('radius').addEventListener('change',()=>loadPlaces(true));
 $('type').addEventListener('change',drawPlaces);
 $('query').addEventListener('input',drawPlaces);
 $('method').addEventListener('change',drawPrayers);
 $('asr').addEventListener('change',drawPrayers);
 $('lang').addEventListener('change',translate);
 $('lang').value=(navigator.language||'en').startsWith('ja')?'ja':(navigator.language||'').startsWith('bn')?'bn':'en';
 translate();initializeMap();loadPlaces();
 // Expose pure helpers for automated regression tests without leaking user's location.
 window.JHCLocationMath={qiblaBearing,distance};
})();