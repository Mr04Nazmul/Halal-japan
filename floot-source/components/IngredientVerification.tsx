import React, { useMemo, useState } from 'react';
import { ingredientDecision } from '../helpers/ingredientDecision';

/** Independent label verification panel. Does not control barcode camera or scan flow. */
export default function IngredientVerification({ initialText = '' }: { initialText?: string }) {
  const [label, setLabel] = useState(initialText);
  React.useEffect(() => { if (initialText) setLabel(initialText); }, [initialText]);
  const [evidenceUrl, setEvidenceUrl] = useState('');
  const decision = useMemo(() => ingredientDecision(label, false), [label]);
  const strictAvoid = decision.verdict === 'haram_ingredient' || decision.findings.length > 0;
  const verdict = decision.verdict === 'haram_ingredient' ? '⛔ HARAM — prohibited ingredient detected' : strictAvoid ? '⛔ HARAM / AVOID — strict precautionary screening' : decision.verdict === 'needs_review' ? '⚠️ No prohibited keyword found — not halal certified' : '⚠️ Unknown — ingredients unavailable';

  return <section style={{ border: '1px solid #344054', borderRadius: 16, padding: 16, marginTop: 20 }}>
    <h3>Ingredient verification / 原材料チェック</h3>
    <p>Paste or correct Japanese ingredient text from the package. Ingredient matching alone cannot certify a product as halal.</p>
    <label htmlFor="ingredient-verification-label">Ingredient label</label>
    <textarea id="ingredient-verification-label" value={label} onChange={e => setLabel(e.target.value)} rows={4} style={{ display: 'block', width: '100%', boxSizing: 'border-box', marginTop: 8, marginBottom: 12 }} placeholder="例：原材料名：小麦粉、乳化剤、ゼラチン…" />
    <div role="status" style={{padding:16,borderRadius:14,background:strictAvoid?'#681c26':'#3c321d',border:strictAvoid?'2px solid #ff7482':'1px solid #cfb370',color:'#fff7ed',fontWeight:800,fontSize:18,margin:'14px 0'}}>{verdict}<div style={{fontSize:12,fontWeight:400,marginTop:8}}>Evidence confidence: {decision.confidence}. Gelatin, emulsifiers and alcohol-related terms are flagged for avoidance under this app's strict screening. Some sources may be permissible; this is not a universal religious ruling.</div></div>
    <small>Confidence means strength of available evidence, not probability of halal status.</small>
    {decision.findings.length > 0 ? <ul>{decision.findings.map((f, i) => <li key={i}><strong>{f.ingredient}</strong> — {f.reason}</li>)}</ul> : null}
    <p>{decision.reasons.join(' ')}</p>
    <label htmlFor="manufacturer-evidence-link">Manufacturer / certification source URL (optional, for reference only)</label>
    <input id="manufacturer-evidence-link" value={evidenceUrl} onChange={e => setEvidenceUrl(e.target.value)} placeholder="https://…" type="url" style={{ display: 'block', width: '100%', boxSizing: 'border-box', marginTop: 8 }} />
    {/^https:\/\//i.test(evidenceUrl) ? <p><a href={evidenceUrl} target="_blank" rel="noopener noreferrer">Open source for manual verification</a> — not automatically verified</p> : null}
    <p><small>Unknown origin, insufficient details, or no reviewed certificate must not be treated as halal certification.</small></p>
  </section>;
}

