import React from 'react';

// Only these generic, independently public citations are shipped to browsers.
// The internal source registry and manufacturer research stay on the server.
const publicReferences = [
  {
    label: 'MEXT — 日本食品標準成分表',
    url: 'https://fooddb.mext.go.jp/',
    note: 'Japanese food composition data. Not a product-specific ingredient label.'
  },
  {
    label: 'Open Food Facts',
    url: 'https://world.openfoodfacts.org/',
    note: 'Community-maintained product information; check exact JAN and label.'
  },
  {
    label: 'Consumer Affairs Agency — 食品表示',
    url: 'https://www.caa.go.jp/policies/policy/food_labeling/',
    note: 'Official guidance for interpreting Japanese food labels.'
  }
] as const;

export default function FoodReferenceSources() {
  return (
    <section style={{padding:16, marginTop:24, border:'1px solid #475467', borderRadius:16}}>
      <h3>Japanese food research sources / 食品情報の参考資料</h3>
      <p>Public reference materials only. Our private manufacturer research is not downloadable here.</p>
      <ul>
        {publicReferences.map(source => (
          <li key={source.url} style={{marginBottom:12}}>
            <a href={source.url} target="_blank" rel="noopener noreferrer">{source.label}</a>
            <div><small>{source.note}</small></div>
          </li>
        ))}
      </ul>
      <small>These references do not establish product-specific halal certification. Check the exact ingredient label and certificate evidence.</small>
    </section>
  );
}
