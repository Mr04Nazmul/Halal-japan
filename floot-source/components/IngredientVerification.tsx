import React, { useMemo, useState } from 'react';
import { ingredientDecision } from '../helpers/ingredientDecision';

/**
 * Independent ingredient-label assessment. This never declares certification.
 * Users must confirm the CURRENT package's full 原材料名/添加物 text before a
 * clean-label screening can be displayed as HALAL · Ingredient Check.
 */
export default function IngredientVerification({ initialText = '' }: { initialText?: string }) {
  const [label, setLabel] = useState(initialText);
  const [fullLabelChecked,setFullLabelChecked]=useState(false);
  React.useEffect(() => { setLabel(initialText);setFullLabelChecked(false); }, [initialText]);
  const [evidenceUrl, setEvidenceUrl] = useState('');
  const decision = useMemo(() => ingredientDecision(label, false, fullLabelChecked), [label,fullLabelChecked]);
  const haram=decision.verdict==='haram_ingredient';
  const clear=decision.verdict==='ingredient_clear';
  const title=haram ? '⛔ HARAM · prohibited ingredient listed'
    :clear ? '✅ HALAL · Ingredient Check'
    :decision.verdict==='unknown'?'❔ UNKNOWN · full ingredient list missing'
    :'⚠️ CHECK · ingredient origin or label incomplete';
  const theme=haram?{background:'#681c26',border:'2px solid #ff7482'}
    :clear?{background:'#125b3c',border:'2px solid #72dc9e'}
    :{background:'#3c321d',border:'1px solid #cfb370'};
  return <section style={{border:'1px solid #344054',borderRadius:16,padding:16,marginTop:20}}>
    <h3>Ingredient verification / 原材料チェック</h3>
    <p>Paste or correct the Japanese ingredient list. The app checks for prohibited ingredients, uncertain additives and missing evidence. No halal certificate is claimed.</p>
    <label htmlFor="ingredient-verification-label">原材料名 + 添加物 / Complete ingredient label</label>
    <textarea id="ingredient-verification-label" value={label}
      onChange={e=>{setLabel(e.target.value);setFullLabelChecked(false)}}
      rows={5} style={{display:'block',width:'100%',boxSizing:'border-box',marginTop:8,marginBottom:12}}
      placeholder="例：原材料名：米、食塩、砂糖…" />
    <label style={{display:'flex',alignItems:'flex-start',gap:10,fontSize:13,lineHeight:1.6,padding:'11px',border:'1px solid #769b82',borderRadius:10}}>
      <input type="checkbox" checked={fullLabelChecked}
        onChange={e=>setFullLabelChecked(e.target.checked&&Boolean(label.trim()))}
        style={{width:18,height:18,flexShrink:0,marginTop:3}}/>
      <span><b>I checked the complete label on the current package</b> (原材料名 + 添加物).
      OCR errors were corrected; this is not just a shortened ingredient excerpt.
      <br/>প্যাকেটের সম্পূর্ণ ingredient list মিলিয়ে দেখেছি—শুধু OCR-এর অসম্পূর্ণ লেখা নয়।</span>
    </label>
    <div role="status" style={{...theme,padding:16,borderRadius:14,color:'#fff7ed',fontWeight:800,fontSize:18,margin:'14px 0'}}>
      {title}
      <div style={{fontSize:12,fontWeight:400,marginTop:8}}>
        {clear?'No prohibited or unresolved ingredient detected in the full reviewed label. Ingredient-only assessment; NOT halal-certified.':
        haram?'A prohibited ingredient was detected in the supplied declaration. Check the exact package.':
        'Green HALAL is shown only for a complete reviewed label with no prohibited or source-uncertain ingredients.'}
      </div>
    </div>
    {decision.findings.length>0?<ul>{decision.findings.map((f,i)=>
      <li key={i}><strong>{f.ingredient}</strong> — {f.reason}</li>)}</ul>:null}
    <p style={{fontSize:13}}>{decision.reasons.join(' ')}</p>
    <label htmlFor="manufacturer-evidence-link">Manufacturer / source URL (reference only)</label>
    <input id="manufacturer-evidence-link" value={evidenceUrl} onChange={e=>setEvidenceUrl(e.target.value)}
      placeholder="https://…" type="url"
      style={{display:'block',width:'100%',boxSizing:'border-box',marginTop:8}}/>
    {/^https:\/\//i.test(evidenceUrl) ? <p><a href={evidenceUrl} target="_blank" rel="noopener noreferrer">
      Open source for manual verification</a> — source is not independently verified</p>:null}
    <p><small>Classification is based only on the supplied text. Missing additive origins, OCR mistakes and recipe changes can change the result. Certification is a separate question.</small></p>
  </section>;
}
