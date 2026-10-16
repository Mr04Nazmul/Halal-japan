import React,{useMemo,useState,useEffect} from 'react';
import {ingredientSources,janSourceLinks,validEAN13} from '../helpers/ingredientSourceLinks';

/** Gives users a safe path to the ORIGINAL source when a scanned JAN is missing.
 * Upstream sites are linked, not copied. Never claims a product is found until
 * its exact barcode and ingredient evidence has been independently checked.
 */
export default function IngredientSourceFinder({barcode='',onLookup}:{barcode?:string,onLookup?:(code:string)=>void}){
 const [current,setCurrent]=useState(barcode);
 const [showAll,setShowAll]=useState(false);
 useEffect(()=>setCurrent(barcode),[barcode]);
 const code=current.trim();
 const valid=validEAN13(code);
 const sourceLinks=useMemo(()=>janSourceLinks(code),[code]);
 const fieldStyle:React.CSSProperties={width:'100%',minWidth:0,padding:'12px',borderRadius:10,boxSizing:'border-box',background:'#081a14',border:'1px solid #698977',color:'#f6f5e7',fontSize:16};
 const buttonStyle:React.CSSProperties={background:'#e7cb8f',color:'#16261d',border:'none',borderRadius:10,fontWeight:800,padding:'11px 14px',cursor:'pointer'};
 const linkStyle:React.CSSProperties={color:'#f5db9d',fontWeight:700,fontSize:13,lineHeight:1.6};
 return <section id="japan-ingredient-sources" aria-label="Japanese ingredient evidence sources"
   style={{margin:'18px 0',padding:'18px',borderRadius:18,border:'1px solid #59826b',background:'#11281e',color:'#f4f4e9'}}>
  <h2 style={{fontSize:20,margin:'0 0 8px'}}>🔎 Japanese Ingredient Source Finder</h2>
  <p style={{fontSize:13,lineHeight:1.65,marginBottom:14}}>
   JAN barcode দিয়ে manufacturer-এর আসল 原材料名 ও 添加物 খুঁজুন।
   Official websites, public APIs and research databases একই জায়গা থেকে খুলুন।
   এগুলো উৎস খোঁজার লিংক—কোনো পণ্যের HALAL certificate নয়।
  </p>
  <form onSubmit={e=>{e.preventDefault();if(code&&onLookup)onLookup(code)}} style={{display:'flex',gap:8,flexWrap:'wrap',margin:'0 0 10px'}}>
   <label htmlFor="ingredient-source-jan" style={{width:'100%',fontSize:13,fontWeight:700}}>Barcode / JAN (13 digits) অথবা Product name</label>
   <div style={{flex:'1 1 185px',minWidth:0}}><input id="ingredient-source-jan" value={current} onChange={e=>setCurrent(e.target.value)}
    placeholder="例: 4549414087208" autoComplete="off" style={fieldStyle}/></div>
   {onLookup?<button type="submit" disabled={code.length<2} style={{...buttonStyle,opacity:code.length<2?.5:1}}>Search in our app</button>:null}
  </form>
  {code&&/^\\d+$/.test(code)&&!valid?<p style={{fontSize:12,color:'#f6d4a7'}}>13-digit JAN-এর checksum মিলছে না, অথবা এটি অন্য ধরনের in-store code। তাই manufacturer link দিয়ে exact match দাবি করছি না।</p>:null}
  {valid?<div style={{padding:12,background:'#0b1c16',borderRadius:12,margin:'12px 0'}}>
    <b style={{fontSize:13}}>Exact JAN: {code}</b>
    <p style={{fontSize:12,lineHeight:1.6,margin:'6px 0 10px'}}>Manufacturer result পাওয়ার নিশ্চয়তা নেই। Official page খুলে একই JAN ও complete package label মিলিয়ে দেখুন।</p>
    <div style={{display:'flex',flexWrap:'wrap',gap:12}}>
     {sourceLinks.map(source=><a key={source.href} href={source.href} target="_blank" rel="noopener noreferrer" style={linkStyle}>{source.name} ↗</a>)}
    </div>
   </div>:null}
  {code&&!valid&&!/^\\d+$/.test(code)?<p style={{fontSize:13,margin:'8px 0'}}>
   <a href={'https://www.google.com/search?q='+encodeURIComponent(code+' 原材料名')} target="_blank" rel="noopener noreferrer" style={linkStyle}>Search Japanese manufacturer ingredient pages for “{code.slice(0,50)}” ↗</a>
  </p>:null}
  <button type="button" onClick={()=>setShowAll(x=>!x)} aria-expanded={showAll} style={{...buttonStyle,background:'transparent',border:'1px solid #809c88',color:'#f3e4c4',width:'100%',textAlign:'left',marginTop:6}}>
   {showAll?'▾ Hide':'▸ Show'} all Japanese product databases & ingredient references ({ingredientSources.length})
  </button>
  {showAll?<div style={{marginTop:12,display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(210px,1fr))',gap:10}}>
   {ingredientSources.map(source=><article key={source.id} style={{border:'1px solid #415d4e',borderRadius:12,padding:12,background:'#0b1f16'}}>
    <a href={source.url} target="_blank" rel="noopener noreferrer" style={linkStyle}>{source.title} ↗</a>
    <div style={{fontSize:11,marginTop:5,color:'#b9c9c0'}}>{source.evidence.replace(/_/g,' ')}</div>
    <p style={{fontSize:12,lineHeight:1.55,margin:'7px 0 0',color:'#e5e9dc'}}>{source.description}</p>
   </article>)}
  </div>:null}
  <p style={{fontSize:12,color:'#d3e1d4',margin:'12px 0 0',lineHeight:1.6}}>
   TOPVALU-এর হাজার হাজার public product listing এখন source search দিয়ে দেখা যায়; পুরো তালিকা বা ingredient text আমাদের database-এ কপি করা হয়নি।
   অন্যের database ব্যবহার-অনুমতি ছাড়া republish করি না। প্যাকেটের ছবি থাকলে নিচের Japanese OCR দিয়ে যাচাই করুন।
  </p>
 </section>;
}
