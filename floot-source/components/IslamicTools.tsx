import React,{useState,useEffect,useRef} from 'react';
import styles from './IslamicTools.module.css';
type Place={id:string;name:string;lat:number;lon:number};
type Position={lat:number;lon:number};
const rad=Math.PI/180;
function qibla(lat:number,lon:number){const delta=(39.8262-lon)*rad;return (Math.atan2(Math.sin(delta),Math.cos(lat*rad)*Math.tan(21.4225*rad)-Math.sin(lat*rad)*Math.cos(delta))/rad+360)%360}
function mapUrl(lat:number,lon:number){const d=.014;return 'https://www.openstreetmap.org/export/embed.html?bbox='+[lon-d,lat-d,lon+d,lat+d].join('%2C')+'&layer=mapnik&marker='+lat+'%2C'+lon}
const prayers=['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'];
export default function IslamicTools(){
 const [point,setPoint]=useState<Position|null>(null),[times,setTimes]=useState<Record<string,string>>({}),[places,setPlaces]=useState<Place[]>([]),[selected,setSelected]=useState<Place|null>(null),[status,setStatus]=useState(''),[method,setMethod]=useState(3),[loading,setLoading]=useState(false);
 const requested=useRef(false);
 const requestId=useRef(0);
 const [mosqueError,setMosqueError]=useState(''),[prayerError,setPrayerError]=useState('');
 useEffect(()=>{if(requested.current)return;requested.current=true;setStatus('Tap Allow when your browser requests location to load mosques, prayer times and Qibla.');load();},[]);
 const load=()=>{if(!navigator.geolocation){setStatus('Location is not available in this browser.');setLoading(false);return;}const id=++requestId.current;setLoading(true);setStatus('Requesting your location…');
 navigator.geolocation.getCurrentPosition(async p=>{
  if(id!==requestId.current)return;const lat=p.coords.latitude,lon=p.coords.longitude;setPoint({lat,lon});setSelected(null);setPlaces([]);setTimes({});setMosqueError('');setPrayerError('');setStatus('Checking nearby places and prayer times…');
  const query='[out:json][timeout:20];(nwr(around:10000,'+lat+','+lon+')["amenity"="place_of_worship"]["religion"="muslim"];nwr(around:10000,'+lat+','+lon+')["building"="mosque"];);out center 50;';
  const fetchPrayer=async()=>{for(const base of ['https://api.aladhan.com/v1/timings','https://api.aladhan.com/v1/timingsByCity']){try{const url=base.includes('timingsByCity')?null:base+'?latitude='+lat+'&longitude='+lon+'&method='+method; if(!url)continue;const r=await fetch(url,{signal:AbortSignal.timeout(8500)});if(!r.ok)continue;const j=await r.json();if(j?.data?.timings)return j;}catch{}}throw Error('Prayer-time service unavailable')};
  const fetchMosques=async()=>{for(const endpoint of ['https://overpass.kumi.systems/api/interpreter','https://overpass-api.de/api/interpreter']){try{const r=await fetch(endpoint,{method:'POST',body:new URLSearchParams({data:query}),signal:AbortSignal.timeout(6500)});if(r.ok)return await r.json()}catch{}}throw Error('Mosque directory unavailable')};
  // Independent requests: mosque lookup never delays prayer times.
  fetchPrayer().then(j=>{
   if(id!==requestId.current)return;
   const entries=j?.data?.timings||{};
   if(prayers.every(name=>typeof entries[name]==='string'&&entries[name].length>0)){setTimes(entries);setPrayerError('');}
   else setPrayerError('Prayer response was incomplete. Please retry.');
  }).catch(()=>{
   if(id===requestId.current)setPrayerError('Could not fetch current prayer times. Retry or check your connection.');
  });
  fetchMosques().then(j=>{
   if(id!==requestId.current)return;
   const found=(j?.elements||[]).map((e:any)=>({
    id:String(e.type)+String(e.id),name:e.tags?.name||e.tags?.['name:en']||'Mosque / prayer space',
    lat:e.lat??e.center?.lat,lon:e.lon??e.center?.lon
   })).filter((e:Place)=>Number.isFinite(e.lat)&&Number.isFinite(e.lon))
     .sort((a:Place,b:Place)=>(a.lat-lat)**2+(a.lon-lon)**2-(b.lat-lat)**2-(b.lon-lon)**2);
   setPlaces(found);if(found.length)setSelected(found[0]);setMosqueError(found.length?'':'No mapped mosques returned nearby. Use Google Maps to search a wider area.');
  }).catch(()=>{
   if(id===requestId.current)setMosqueError('Mosque directory temporarily unavailable. Try Google Maps or Retry.');
  }).finally(()=>{
   if(id===requestId.current){setLoading(false);setStatus('');}
  });

 },()=>{setStatus('Location access was denied or timed out. Enable location permission in your browser and retry.');setLoading(false)},{timeout:10000,maximumAge:60000,enableHighAccuracy:false});
 };
 const focus=selected||point;
 return <section className={styles.islamic} style={{display:'grid',gap:18,width:'100%',minWidth:0}}>
  <div><h2>🕌 Nearby Mosques</h2><p>See mapped prayer spaces near your current location. Tap a mosque to focus the map.</p>
   <label>Prayer calculation method <select value={method} onChange={e=>{setMethod(Number(e.target.value));setStatus('Method changed. Tap Retry to refresh prayer times.')}}><option value={3}>Muslim World League</option><option value={1}>Karachi</option><option value={4}>Umm Al-Qura</option><option value={17}>JAKIM Malaysia</option></select></label>
   <p><button onClick={load} disabled={loading} style={{padding:'11px 16px',borderRadius:12,background:'#09623d',color:'#fff',border:0,fontWeight:700}}>{loading?'Searching…':point?'Retry mosque & prayer search':'📍 Find mosques near me'}</button></p><p role="status">{status}</p>
   {focus?<iframe title="Map of nearby mosque or your current location" src={mapUrl(focus.lat,focus.lon)} loading="lazy" style={{width:'100%',height:340,border:'1px solid #dce8e0',borderRadius:16}}/>:<div style={{borderRadius:16,minHeight:170,display:'grid',placeItems:'center',background:'#e8f2eb',padding:18,textAlign:'center'}}>Allow location to display the live OpenStreetMap map here.</div>}
   {point&&<><p style={{fontSize:13}}>Map centered on {selected?selected.name:'the device location'}. Pin indicates the map center; nearby mosques appear in the results below.</p><h3>Mapped mosques nearby</h3>{places.length?places.map(m=><div key={m.id} style={{display:'flex',gap:8,alignItems:'center',justifyContent:'space-between',padding:'11px 0',borderBottom:'1px solid #e6ece7'}}><button onClick={()=>setSelected(m)} style={{background:'transparent',border:0,textAlign:'left',fontWeight:600,color:'#086440',cursor:'pointer'}}>🕌 {m.name}</button><a href={'https://www.openstreetmap.org/?mlat='+m.lat+'&mlon='+m.lon+'#map=17/'+m.lat+'/'+m.lon} target="_blank" rel="noreferrer">Directions / Map ↗</a></div>):<p>{loading?'Searching mosque listings…':mosqueError||'No mosque entries were returned nearby. Try the map search below.'}</p>}<a href={'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent('mosque near '+point.lat+','+point.lon)} target="_blank" rel="noopener noreferrer" style={{display:'block',padding:'12px 14px',borderRadius:12,background:'#d9bd80',color:'#162f22',textDecoration:'none',fontWeight:800,textAlign:'center',marginTop:12}}>Find mosques in Google Maps ↗</a></>}
  </div>
  <div style={{background:'#f2f7f3',borderRadius:16,padding:18}}><h2>🕰 Prayer times · নামাজের সময়</h2><p style={{fontSize:13}}>Calculated for your location and selected method; local mosque jamaat times can differ.</p>{prayerError&&<p role="alert">{prayerError}</p>}{prayers.map(name=><div key={name} style={{display:'flex',justifyContent:'space-between',borderBottom:'1px solid #dce8df',padding:'10px 0'}}><strong>{name}</strong><span>{times[name]||'—'}</span></div>)}</div>
  <div style={{background:'#edf6ee',borderRadius:16,padding:18}}><h2>🧭 Qibla · কিবলার দিক</h2>{point?<><div style={{fontSize:34,fontWeight:800,color:'#09623d'}}>{qibla(point.lat,point.lon).toFixed(1)}°</div><p>Clockwise from true north, toward the Kaaba. Use a calibrated compass to face that bearing; this number is not a live device compass.</p></>:<p>Enable location to calculate the Qibla direction.</p>}</div>
  <small>Prayer data: AlAdhan API · Mosque locations and map: © OpenStreetMap contributors. Results depend on network access and community map coverage.</small>
 </section>;
}
