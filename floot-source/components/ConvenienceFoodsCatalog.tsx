import React,{useState} from 'react';
import {convenienceFoods} from '../helpers/convenienceFoods';
export default function ConvenienceFoodsCatalog({onChoose}:{onChoose:(name:string)=>void}){
 const [q,setQ]=useState(''),[store,setStore]=useState('All');
 const items=convenienceFoods.filter(p=>(store==='All'||p.store===store)&&[p.name,p.category,p.store].join(' ').toLowerCase().includes(q.toLowerCase()));
 return <section style={{margin:'25px 0',padding:16,border:'1px solid #6d765568',borderRadius:18,background:'#11291f'}}>
 <h2 style={{color:'#f2db9f'}}>Convenience Store Foods</h2>
 <p style={{color:'#aec9b3',fontSize:12}}>7-Eleven / FamilyMart / Lawson — verified product listings only. Check actual Japanese package ingredients for HALAL/HARAM.</p>
 <input aria-label="Search convenience-store foods" placeholder="Search onigiri, bento, sandwich, Japanese name" value={q} onChange={e=>setQ(e.target.value)} style={{width:'100%',boxSizing:'border-box',background:'#0b1f18',color:'white',padding:12,border:'1px solid #557258',borderRadius:10}}/>
 <div style={{display:'flex',flexWrap:'wrap',gap:6,margin:'12px 0'}}>{['All','Seven Eleven','FamilyMart','Lawson'].map(st=><button key={st} onClick={()=>setStore(st)} style={{background:store===st?'#e4c17e':'#29513e',color:store===st?'#0a241c':'white',border:0,borderRadius:16,padding:'7px 10px'}}>{st}</button>)}</div>
 <div style={{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:9}}>
 {items.map(p=><button key={p.url+p.name} onClick={()=>onChoose(p.name)} style={{background:'#19362a',border:'1px solid #557557',borderRadius:12,color:'#f0ecd9',padding:12,textAlign:'left'}}>
 <strong style={{fontSize:12,overflowWrap:'anywhere'}}>{p.name}</strong><small style={{display:'block',margin:'8px 0',color:'#bad2c0'}}>{p.store} · {p.category}</small>
 <span style={{color:'#e7c686',fontSize:11}}>VERIFY · Package ingredients required</span></button>)}
 </div><p style={{fontSize:11,color:'#afc5b0'}}>Official catalogue entries are not barcode records. Region and recipe may vary; see each product's source.</p>
 </section>;
}