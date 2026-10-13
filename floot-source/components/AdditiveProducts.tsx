import React,{useEffect,useMemo,useState} from 'react';
import {manufacturerDrinks} from '../helpers/manufacturerDrinks';
import {extraManufacturerDrinks} from '../helpers/extraManufacturerDrinks';
import {verifiedFoodRecords} from '../helpers/verifiedFoodRecords';
import {ingredientDecision} from '../helpers/ingredientDecision';
type Entry={barcode:string;name:string;brand:string;ingredients:string;source:string};
const SUPA='https://vjygltfnrmyghlwyjtwu.supabase.co';
const KEY='sb_publishable_SL6n4Q0t_AxHywHM6iMkpg_bm-lx_Oh';
const kinds=[
 {label:'Gelatin / ゼラチン',terms:['ゼラチン','gelatin']},
 {label:'Emulsifier / 乳化剤',terms:['乳化剤','emulsifier']},
 {label:'Flavouring / 香料',terms:['香料','flavoring','flavouring']}
];
const locals:Entry[]=[
 ...[...manufacturerDrinks,...extraManufacturerDrinks].map(p=>({barcode:p.barcode,name:p.name,brand:p.manufacturer,ingredients:p.ingredients,source:'Manufacturer ingredient record'})),
 ...verifiedFoodRecords.map(p=>({barcode:p.barcode,name:p.nameJa+' / '+p.name,brand:p.manufacturer,ingredients:p.ingredients,source:'Manufacturer ingredient excerpt (partial)'}))
];
export default function AdditiveProducts({onChoose}:{onChoose:(code:string)=>void}){
 const [selected,setSelected]=useState(0),[rows,setRows]=useState<Entry[]>([]),[load,setLoad]=useState(false),[error,setError]=useState('');
 const [page,setPage]=useState(0);
 const terms=kinds[selected].terms;
 const local=useMemo(()=>locals.filter(p=>terms.some(t=>p.ingredients.toLowerCase().includes(t.toLowerCase()))),[selected]);
 useEffect(()=>{let cancelled=false;setLoad(true);setError('');
 const query=new URL(SUPA+'/rest/v1/jhc_floot_products');
 query.searchParams.set('select','barcode,name,name_ja,brand,ingredients,evidence_source');
 query.searchParams.set('or','('+terms.map(t=>'ingredients.ilike.*'+t+'*').join(',')+')');
 query.searchParams.set('limit','40');query.searchParams.set('offset',String(page*40));
 fetch(query.toString(),{headers:{apikey:KEY,Accept:'application/json'}}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then((data:any[])=>{
  if(cancelled)return;
  setRows(data.filter(p=>p.ingredients).map(p=>({barcode:p.barcode||'',name:p.name_ja||p.name||'Unnamed product',brand:p.brand||'',ingredients:p.ingredients,source:p.evidence_source||'Previously collected catalogue'})));
 }).catch(()=>{if(!cancelled){setRows([]);setError('Saved catalogue is temporarily unavailable. Manufacturer records remain visible.')}}).finally(()=>{if(!cancelled)setLoad(false)});
 return()=>{cancelled=true};
 },[selected,page]);
 const merged=Array.from(new Map([...local,...rows].map((p,i)=>[p.barcode||p.name+'-'+i,p])).values());
 return <section style={{margin:'24px 0',padding:16,border:'1px solid #52735d',background:'#102a20',borderRadius:16,color:'#edf4e8'}}>
  <h2 style={{margin:'0 0 8px'}}>Japanese Food Additive Finder</h2>
  <p style={{fontSize:13}}>Search products with listed gelatin, emulsifier or flavouring. Only records with an actual ingredient match appear. Coverage is incomplete; results are not halal certification or proof of haram origin.</p>
  <div style={{display:'flex',gap:7,overflowX:'auto',marginBottom:12}}>{kinds.map((k,i)=><button key={i} onClick={()=>{setSelected(i);setPage(0);setRows([])}} style={{flexShrink:0,border:'1px solid #829789',borderRadius:20,padding:'8px 10px',color:selected===i?'#123224':'white',background:selected===i?'#e2cf9b':'#274a38'}}>{k.label}</button>)}</div>
  <p style={{fontSize:12}}>{local.length} matching local reference records + {rows.length} matching saved catalogue records on this page {load?'(loading…)':''}. Overlap removed.</p>
  {error&&<p role="status" style={{fontSize:12,color:'#ffe1a1'}}>{error}</p>}
  <div style={{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:8}}>{merged.map((p,i)=>{const d=ingredientDecision(p.ingredients);return <button key={p.barcode||p.name+i} onClick={()=>onChoose(p.barcode||p.name)} style={{minWidth:0,textAlign:'left',padding:10,color:'#f0f4ec',background:'#244235',border:'1px solid #4b6b57',borderRadius:10}}>
   <strong style={{display:'block',fontSize:12,overflowWrap:'anywhere'}}>{p.name}</strong><small style={{display:'block',opacity:.8}}>{p.brand} · {p.barcode||'JAN unavailable'}</small><span style={{display:'block',color:d.verdict==='haram_ingredient'?'#ff8c92':'#ffcf88',fontSize:12,fontWeight:800}}>{d.verdict==='haram_ingredient'?'HARAM':'AVOID · Source unverified'}</span><small style={{opacity:.8}}>Matched: {terms.filter(t=>p.ingredients.toLowerCase().includes(t.toLowerCase())).join(', ')} · {p.source}</small>
  </button>})}</div>
  {!load&&!merged.length&&<p>No matching records in available data. This does not mean Japanese products do not use this additive.</p>}
  <div style={{display:'flex',justifyContent:'space-between',marginTop:12}}><button disabled={page===0||load} onClick={()=>setPage(p=>Math.max(0,p-1))}>Previous</button><small>Saved database page {page+1}</small><button disabled={rows.length<40||load} onClick={()=>setPage(p=>p+1)}>Next</button></div>
 </section>
}
