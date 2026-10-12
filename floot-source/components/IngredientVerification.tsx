import React, { useMemo, useState } from 'react';
import { ingredientDecision } from '../helpers/ingredientDecision';

/** Independent label verification panel. Does not control barcode camera or scan flow. */
export default function IngredientVerification({ initialText = '' }: { initialText?: string }) {
  const [label, setLabel] = useState(initialText);
  React.useEffect(() => { if (initialText) setLabel(initialText); }, [initialText]);
  const [evidenceUrl, setEvidenceUrl] = useState('');
  const decision = useMemo(() => ingredientDecision(label, false), [label]);
  const verdict = decision.verdict === 'haram_ingredient' ? 'Haram ingredient detected' : decision.verdict === 'needs_review' ? 'Mushbooh — source verification needed' : 'Unknown — insufficient information';

  return <section style={{ border: '1px solid #344054', borderRadius: 16, padding: 16, marginTop: 20 }}>
    <h3>Ingredient verification / 原材料チェック</h3>
    <p>Paste or correct Japanese ingredient text from the package. Ingredient matching alone cannot certify a product as halal.</p>
    <label htmlFor="ingredient-verification-label">Ingredient label</label>
    <textarea id="ingredient-verification-label" value={label} onChange={e => setLabel(e.target.value)} rows={4} style={{ display: 'block', width: '100%', boxSizing: 'border-box', marginTop: 8, marginBottom: 12 }} placeholder="例：原材料名：小麦粉、乳化剤、ゼラチン…" />
    <p role="status"><strong>{verdict}</strong> · Evidence confidence: {decision.confidence}</p>
    <small>Confidence means strength of available evidence, not probability of halal status.</small>
    {decision.findings.length > 0 ? <ul>{decision.findings.map((f, i) => <li key={i}><strong>{f.ingredient}</strong> — {f.reason}</li>)}</ul> : null}
    <p>{decision.reasons.join(' ')}</p>
    <label htmlFor="manufacturer-evidence-link">Manufacturer / certification source URL (optional, for reference only)</label>
    <input id="manufacturer-evidence-link" value={evidenceUrl} onChange={e => setEvidenceUrl(e.target.value)} placeholder="https://…" type="url" style={{ display: 'block', width: '100%', boxSizing: 'border-box', marginTop: 8 }} />
    {/^https:\/\//i.test(evidenceUrl) ? <p><a href={evidenceUrl} target="_blank" rel="noopener noreferrer">Open source for manual verification</a> — not automatically verified</p> : null}
    <p><small>Unknown origin, insufficient details, or no reviewed certificate must not be treated as halal certification.</small></p>
  </section>;
}

