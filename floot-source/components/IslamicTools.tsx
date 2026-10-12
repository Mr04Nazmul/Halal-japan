import React,{useState} from 'react';
type Place={id:string;name:string;lat:number;lon:number};
type Position={lat:number;lon:number};
const rad=Math.PI/180;
function qibla(lat:number,lon:number){const delta=(39.8262-lon)*rad;return (Math.atan2(Math.sin(delta),Math.cos(lat*rad)*Math.tan(21.4225*rad)-Math.sin(lat*rad)*Math.cos(delta))/rad+360)%360}
function mapUrl(lat:number,lon:number){const d=.014;return 'https://www.openstreetmap.org/export/embed.html?bbox='+[lon-d,lat-d,lon+d,lat+d].join('%2C')+'&layer=mapnik&marker='+lat+'%2C'+lon}
const prayers=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];
export default function IslamicTools(){
 const [point,setPoint]=useState<Position|null>(null),[times,setTimes]=useState<Record<string,string>>({}),[places,setPlaces]=useState<Place[]>([]),[selected,setSelected]=useState<Place|null>(null),[status,setStatus]=useState(''),[method,setMethod]=useState(3),[loading,setLoading]=useState(false);
 const load=()=>{if(!navigator.geolocation){setStatus('Location is not available in this browser.');return;}setLoading(true);setStatus('Requesting your location…');
 navigator.geolocation.getCurrentPosition(async p=>{
  const lat=p.coords.latitude,lon=p.coords.longitude;setPoint({lat,lon});setSelected(null);setPlaces([]);setTimes({});setStatus('Loading prayer times and nearby mapped mosques…');
  const query='[out:json][timeout:20];(nwr(around:10000,'+lat+','+lon+')["amenity"="place_of_worship"]["religion"="muslim"];nwr(around:10000,'+lat+','+lon+')["building"="mosque"];);out center 50;';
  const results=await Promise.allSettled([fetch('https://api.aladhan.com/v1/timings?latitude='+lat+'&longitude='+lon+'&method='+method).then(r=>{if(!r.ok)throw Error('Prayer service unavailable');return r.json()}),fetch('https://overpass.kumi.systems/api/interpreter',{method:'POST',body:new URLSearchParams({data:query})}).then(r=>{if(!r.ok)throw Error('Map service unavailable');return r.json()})]);
  if(results[0].status==='fulfilled')setTimes(results[0].value?.data?.timings||{});
  if(results[1].status==='fulfilled')setPlaces((results[1].value?.elements||[]).map((e:any)=>({id:String(e.type)+String(e.id),name:e.tags?.name||e.tags?.['name:en']||'Mosque / prayer space',lat:e.lat??e.center?.lat,lon:e.lon??e.center?.lon})).filter((e:Place)=>Number.isFinite(e.lat)&&Number.isFinite(e.lon)).sort((a:Place,b:Place)=>(a.lat-lat)**2+(a.lon-lon)**2-(b.lat-lat)**2-(b.lon-lon)**2));
  setStatus(results.every(r=>r.status==='fulfilled')?'': 'One or more live services could not respond; try refreshing.');setLoading(false);
 },()=>{setStatus('Location access was denied or timed out. Enable location permission in your browser and retry.');setLoading(false)},{timeout:12000,enableHighAccuracy:true});
 };
 const focus=selected||point;
 return <section style={{display:'grid',gap:18}}>
  <div><h2>🕌 Nearby Mosques</h2><p>See mapped prayer spaces near your current location. Tap a mosque to focus the map.</p>
   <label>Prayer calculation method <select value={method} onChange={e=>setMethod(Number(e.target.value))}><option value={3}>Muslim World League</option><option value={1}>Karachi</option><option value={4}>Umm Al-Qura</option><option value={17}>JAKIM Malaysia</option></select></label>
   <p><button onClick={load} disabled={loading} style={{padding:'11px 16px',borderRadius:12,background:'#09623d',color:'#fff',border:0,fontWeight:700}}>{loading?'Loading…':point?'Refresh nearby mosques & times':'📍 Find mosques near me'}</button></p><p role="status">{status}</p>
   {focus?<iframe title="Map of nearby mosque or your current location" src={mapUrl(focus.lat,focus.lon)} loading="lazy" style={{width:'100%',height:290,border:'1px solid #dce8e0',borderRadius:16}}/>:<div style={{borderRadius:16,minHeight:170,display:'grid',placeItems:'center',background:'#e8f2eb',padding:18,textAlign:'center'}}>Allow location to display the live OpenStreetMap map here.</div>}
   {point&&<><p style={{fontSize:13}}>Showing map centered on {selected?selected.name:'your location'}. Map pin marks the selected location, not all mosques.</p><h3>Mapped mosques nearby</h3>{places.length?places.map(m=><div key={m.id} style={{display:'flex',gap:8,alignItems:'center',justifyContent:'space-between',padding:'11px 0',borderBottom:'1px solid #e6ece7'}}><button onClick={()=>setSelected(m)} style={{background:'transparent',border:0,textAlign:'left',fontWeight:600,color:'#086440',cursor:'pointer'}}>🕌 {m.name}</button><a href={'https://www.openstreetmap.org/?mlat='+m.lat+'&mlon='+m.lon+'#map=17/'+m.lat+'/'+m.lon} target="_blank" rel="noreferrer">Directions / Map ↗</a></div>):<p>There are no mapped mosque results from this search. OpenStreetMap records may be incomplete.</p>}</>}
  </div>
  <div style={{background:'#f2f7f3',borderRadius:16,padding:18}}><h2>🕰 Prayer times · নামাজের সময়</h2><p style={{fontSize:13}}>Calculated for your location and selected method; local mosque jamaat times can differ.</p>{prayers.map(name=><div key={name} style={{display:'flex',justifyContent:'space-between',borderBottom:'1px solid #dce8df',padding:'10px 0'}}><strong>{name}</strong><span>{times[name]||'—'}</span></div>)}</div>
  <div style={{background:'#edf6ee',borderRadius:16,padding:18}}><h2>🧭 Qibla · কিবলার দিক</h2>{point?<><div style={{fontSize:34,fontWeight:800,color:'#09623d'}}>{qibla(point.lat,point.lon).toFixed(1)}°</div><p>Clockwise from true north, toward the Kaaba. Use a calibrated compass to face that bearing; this number is not a live device compass.</p></>:<p>Enable location to calculate the Qibla direction.</p>}</div>
  <small>Prayer data: AlAdhan API · Mosque locations and map: © OpenStreetMap contributors. Results depend on network access and community map coverage.</small>
 </section>;
}
