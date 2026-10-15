import React,{useMemo,useState} from 'react';
import {sevenOfficialItems as items} from '../helpers/sevenOfficialCatalog';
const categories=['All','Bento','Onigiri','Bread','Dessert'];
export default function SevenElevenOfficialCatalog({onChoose}:{onChoose:(q:string)=>void}){
 const [category,setCategory]=useState('All'),[search,setSearch]=useState('');
 const visible=useMemo(()=>items.filter(p=>(category==='All'||p.category===category)&&p.name.includes(search)),[category,search]);
 return <section style={{padding:16,border:'1px solid #537657',borderRadius:18,margin:'20px 0',background:'#10291f',color:'#f2f5ea'}}>
 <h2>7-Eleven Japan — Official Product Discovery</h2>
 <p style={{fontSize:13}}>A small set of source-linked product names from Seven-Eleven Japan's public pages. Product availability varies by region and time. These are discovery references, not imported barcode records or ingredient lists. Exact JAN, additive sources, factory details and halal status remain unverified.</p>
 <input aria-label="Search Seven-Eleven products" placeholder="Search Japanese product name" value={search} onChange={e=>setSearch(e.target.value)} style={{background:'#1d3b2b',color:'white',padding:12,borderRadius:10,width:'100%',boxSizing:'border-box'}}/>
 <div style={{display:'flex',gap:7,overflowX:'auto',margin:'12px 0'}}>{categories.map(c=><button key={c} onClick={()=>setCategory(c)} style={{padding:'8px 12px',borderRadius:20,color:category===c?'#132b1e':'white',background:category===c?'#efd89e':'#31543e',flexShrink:0}}>{c}</button>)}</div>
 <p style={{fontSize:12}}>{visible.length} of {items.length} sourced reference products · Official details and current package must be checked</p>
 <div style={{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:9}}>{visible.map((p,i)=><article key={p.name+i} style={{border:'1px solid #52715d',padding:12,borderRadius:12,minWidth:0}}>
 <strong style={{display:'block',fontSize:13,overflowWrap:'anywhere'}}>{p.name}</strong><small style={{display:'block',color:'#cebd81'}}>{p.category} · JAN not yet verified</small><small style={{display:'block',color:'#ffdf97',margin:'8px 0'}}>INGREDIENT DATA NEEDED</small>
 <a href={p.url} target="_blank" rel="noopener noreferrer" style={{fontSize:12,color:'#c9e8db'}}>Official 7-Eleven category ↗</a>
 <button onClick={()=>onChoose(p.name)} style={{display:'block',marginTop:10,padding:8,borderRadius:8,background:'#315543',color:'white'}}>Identify product / verify label</button>
 </article>)}</div>
 </section>
}
