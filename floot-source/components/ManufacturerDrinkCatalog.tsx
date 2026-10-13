import React,{useState} from 'react';
import {manufacturerDrinks} from '../helpers/manufacturerDrinks';
import {extraManufacturerDrinks} from '../helpers/extraManufacturerDrinks';
const allDrinks=[...manufacturerDrinks,...extraManufacturerDrinks];
import {ingredientDecision} from '../helpers/ingredientDecision';
export default function ManufacturerDrinkCatalog({onChoose}:{onChoose:(barcode:string)=>void}){
 const [term,setTerm]=useState(''),[category,setCategory]=useState('All');
 const items=allDrinks.filter(p=>(category==='All'||p.category===category)&&
  (p.name+' '+p.barcode+' '+p.ingredients).toLocaleLowerCase().includes(term.toLocaleLowerCase()));
 return <section style={{margin:'25px 0',padding:16,border:'1px solid #6d765568',borderRadius:18,background:'#11291f'}}>
 <h2 style={{margin:'4px 0 8px',color:'#f2db9f'}}>Manufacturer Drinks Database</h2>
 <p style={{fontSize:12,color:'#b4cbbc'}}>{allDrinks.length} Sangaria, Kirin & ITO EN JAN records • Official product ingredient links • No assumed halal certificates</p>
 <input aria-label="Search manufacturer drinks" placeholder="Search coffee, tea, juice, soda or JAN" value={term} onChange={e=>setTerm(e.target.value)} style={{width:'100%',padding:13,borderRadius:12,border:'1px solid #57725d',background:'#102018',color:'white',boxSizing:'border-box'}}/>
 <div style={{display:'flex',gap:8,overflowX:'auto',padding:'12px 0'}}>{['All','Coffee','Tea','Juice','Soda','Other Drinks'].map(c=><button key={c} onClick={()=>setCategory(c)} style={{padding:'8px 11px',borderRadius:20,whiteSpace:'nowrap',border:'1px solid #63795f',background:category===c?'#dab879':'#203e2e',color:category===c?'#0c241b':'#e6e9d8'}}>{c}</button>)}</div>
 <div style={{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:9}}>
 {items.map(p=>{const d=ingredientDecision(p.ingredients,false,true);return <button key={p.barcode} onClick={()=>onChoose(p.barcode)} style={{textAlign:'left',background:'#1a3428',border:'1px solid #49674c',borderRadius:13,padding:12,color:'#ebf2e4',minWidth:0}}>
 <strong style={{fontSize:12,display:'block',lineHeight:1.45,overflowWrap:'anywhere'}}>{p.name}</strong>
 <small style={{display:'block',marginTop:8,color:'#a1b9a9'}}>{p.barcode}</small>
 <span style={{fontSize:11,color:d.verdict==='haram_ingredient'?'#ff9494':d.verdict==='needs_review'?'#f3d099':'#b6dfab',fontWeight:700}}>{d.verdict==='haram_ingredient'?'HARAM':d.verdict==='needs_review'?'AVOID':'HALAL · INGREDIENT CHECK'}</span>
 </button>})}
 </div><p style={{fontSize:11,color:'#9fbbaa',marginTop:12}}>Source links and full ingredient information appear after selecting a product. Some additives require manufacturer origin confirmation.</p>
 </section>;
}