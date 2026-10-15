import React from 'react';

type Entry={barcode:string;name:string;sourceUrl:string;highlights:string;};
const items:Entry[]=[
 {barcode:'4901990380843',name:'海鮮ちゃんぽん',highlights:'ポークエキス・豚脂・魚介エキス',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-kaisen-chanpon'},
 {barcode:'4902881484398',name:'横浜家系豚骨醤油ラーメン',highlights:'豚脂・ポークエキス・チキンオイル',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-yokohama-iekei-tonkotsu-shoyu-ramen'},
 {barcode:'4902881480536',name:'京都背脂醤油ラーメン',highlights:'豚脂・ポーク調味料・背脂加工品',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-kyoto-seabura-shoyu-ramen'},
 {barcode:'4901071405120',name:'辛タンメン',highlights:'豚脂・ポーク調味料・鶏・豚味付肉そぼろ',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-kara-tanmen'},
 {barcode:'4902881483810',name:'黒マー油豚骨ラーメン',highlights:'ポークエキス・豚脂・チャーシュー',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-kuromayu-tonkotsu-ramen'},
 {barcode:'4902105290088',name:'すみれ 醤油',highlights:'豚脂・ポーク調味料・味付豚肉',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-sumire-shoyu'},
 {barcode:'4902105949375',name:'すみれメシ 味噌キムチ',highlights:'豚脂・ポーク調味料・魚醤',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-sumiremeshi-miso-kimchi'},
 {barcode:'4902105297018',name:'山頭火 カリーメン',highlights:'ポーク調味料・豚脂・豚肉加工品',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-santoka-currymen'},
 {barcode:'4902105949580',name:'一風堂メシ 赤丸新味',highlights:'ポーク調味料・豚脂・味付豚肉',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-ippudo-meshi-akamaru'},
 {barcode:'4901990379939',name:'すじ青のり使用 塩焼そば',highlights:'精製ラード・チキンエキス・昆布エキス',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-sujiaonori-sio-yakisoba'},
 {barcode:'4901990379915',name:'すじ青のり天ぷらうどん',highlights:'魚介エキス・レシチン・青のり天ぷら（要確認）',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-sujiaonori-tenpura-udon'},
 {barcode:'4902881478991',name:'とろろ昆布と梅のうどん',highlights:'かつおぶし・昆布エキス・乳化剤（由来要確認）',sourceUrl:'https://blog.webproduct-lab.com/entry/sevenpremium-tororokonbu-ume-udon'}
];
export default function SevenElevenIngredientResearch({onChoose}:{onChoose:(jan:string)=>void}){
 return <details style={{margin:'12px 0',padding:'10px 12px',border:'1px solid #c6ad7166',borderRadius:13,background:'#10291f',color:'#f0ebdb'}}>
  <summary style={{cursor:'pointer',fontSize:13,fontWeight:800}}>🔎 Seven Premium: 12 JAN + ingredient research records</summary>
  <p style={{fontSize:12,lineHeight:1.7}}>These are <b>selected ingredient excerpts reported from packages by third-party reviewers</b>, not manufacturer-verified full ingredient lists. Some reviews cover earlier product versions. Exact packaging, factory, additives and certification still require verification. 7-Eleven's official FAQ says to check the back of the current package.</p>
  <a href="https://faq.sej.co.jp/article/?knowledge_id=cihug2u49ras9ngq94kg" target="_blank" rel="noopener noreferrer" style={{fontSize:12,color:'#f4d68c'}}>7-Eleven's official ingredient-information FAQ ↗</a>
  <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(min(100%,260px),1fr))',gap:9,marginTop:13}}>
   {items.map(p=><article key={p.barcode} style={{padding:12,border:'1px solid #456350',borderRadius:12,minWidth:0}}>
    <strong style={{fontSize:13,display:'block',overflowWrap:'anywhere'}}>セブンプレミアム {p.name}</strong>
    <small style={{display:'block',color:'#c0d4be',margin:'5px 0'}}>JAN: {p.barcode}</small>
    <p style={{fontSize:12,margin:'5px 0',overflowWrap:'anywhere'}}>{'報告された原材料の抜粋：'+p.highlights}</p>
    <small style={{display:'block',color:'#e3c99c'}}>Information source: independent package review · full current label not confirmed</small>
    <button type="button" onClick={()=>onChoose(p.barcode)} style={{display:'inline-block',padding:'8px 10px',borderRadius:9,background:'#dcbd76',color:'#173225',fontSize:12,fontWeight:750,border:0,cursor:'pointer',marginTop:10,marginRight:9}}>Check JAN →</button>
    <a href={p.sourceUrl} target="_blank" rel="noopener noreferrer" style={{fontSize:12,color:'#e0cca0'}}>Label source ↗</a>
   </article>)}
  </div>
 </details>;
}
