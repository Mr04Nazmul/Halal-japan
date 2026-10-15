import React,{useMemo,useState} from 'react';
import {REVIEWED_ECODES} from '../helpers/reviewedEcodeGuide';

/**
 * Only show source/identity-reviewed additive reference cards. All upstream
 * classifications live in private staging until independently reviewed.
 */
export default function ReviewedEcodeGuide(){
 const [q,setQ]=useState('');
 const filtered=useMemo(()=>REVIEWED_ECODES.filter(x=>
  [x.code,x.name,x.japanese,x.evidence,x.note].join(' ').normalize('NFKC').toLocaleLowerCase()
  .includes(q.normalize('NFKC').trim().toLocaleLowerCase())),[q]);
 return <details style={{border:'1px solid #aa95645d',borderRadius:16,padding:12,margin:'15px 0',background:'#153028',color:'#e9eddf'}}>
  <summary style={{cursor:'pointer',fontWeight:800,fontSize:14}}>🔬 Ingredient &amp; E-number guide · 7 reviewed references</summary>
  <p style={{fontSize:12,lineHeight:1.7}}>A separate private review database contains 577 imported entries (225 ingredients + 352 E-number rows) from <a href="https://github.com/cahyadsn/halal" target="_blank" rel="noopener noreferrer" style={{color:'#e8d6a3'}}>Cahya DSN's MIT-licensed dataset</a>. Its original Halal/Haram labels are <b>unverified</b> and are NOT automatically used for product verdicts. Only these 7 additive identities were independently cross-checked against EFSA or FAO/JECFA; even they are NOT product-specific halal certificates.</p>
  <input aria-label="Search reviewed E-numbers or Japanese ingredient names" placeholder="Search E471, E406, ゼラチン…" value={q} onChange={e=>setQ(e.target.value)} style={{width:'100%',boxSizing:'border-box',background:'#0e251d',color:'#fff5db',padding:12,border:'1px solid #718b76',borderRadius:11,outlineOffset:2,fontSize:14}}/>
  <p style={{fontSize:12,margin:'9px 0',color:'#cbd2c0'}}>{filtered.length} of {REVIEWED_ECODES.length} source-checked codes · Identity checked ≠ whole product Halal</p>
  <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(min(100%,250px),1fr))',gap:10}}>
   {filtered.map(x=><article key={x.code} style={{minWidth:0,padding:12,background:'#0f281f',border:'1px solid #4f6852',borderRadius:12}}>
    <div style={{display:'flex',alignItems:'baseline',gap:8,justifyContent:'space-between',flexWrap:'wrap'}}>
     <strong style={{fontSize:15,color:'#f1d796'}}>{x.code}</strong>
     <small style={{fontSize:10,color:'#f2d8aa'}}>{x.action==='identity_only'?'SOURCE IDENTITY CHECKED':x.action==='precaution'?'PRECAUTION / VERIFY':'VERIFY SOURCE'}</small>
    </div>
    <strong style={{display:'block',fontSize:13,marginTop:6}}>{x.name}</strong>
    <span style={{display:'block',fontSize:12,marginTop:4}}>{x.japanese}</span>
    <p style={{fontSize:12,lineHeight:1.55,margin:'7px 0'}}>{x.note}</p>
    <small style={{fontSize:11,color:'#c8d9cb'}}>{x.evidence}</small>
    <a href={x.sourceUrl} target="_blank" rel="noopener noreferrer" style={{fontSize:12,display:'block',marginTop:9,color:'#eacb7d',overflowWrap:'anywhere'}}>Read original scientific source ↗</a>
   </article>)}
  </div>
  {!filtered.length?<p style={{fontSize:12}}>No reviewed match yet. An E-number not in this list is NOT necessarily Halal or Haram.</p>:null}
  <p style={{fontSize:11,marginBottom:0,color:'#b8cfc1'}}>Attribution: Cahya DSN, <a href="https://github.com/cahyadsn/halal/blob/master/LICENSE" target="_blank" rel="noopener noreferrer" style={{color:'#dbc68e'}}>MIT License</a>. Original classifications are research leads only; this guide uses independent source notes. Japan may use Japanese additive names rather than E-numbers.</p>
 </details>;
}
