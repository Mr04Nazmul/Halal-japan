import React,{useState} from 'react';
/** Official Seven Premium external ingredient-label references.
 * No manufacturer texts/images/data mirrored. Product page IDs are NOT JANs.
 * Some formulations or selling regions may change without notice.
 * The maker's terms permit direct links but require permission to reuse content.
 */
const pages=[
  {
    "name": "マロンあんパイ 1個",
    "url": "https://7premium.jp/product/search/detail?id=8998",
    "note": "乳化剤・香料などの由来確認が必要"
  },
  {
    "name": "いちごヨーグルト 4個入",
    "url": "https://7premium.jp/product/search/detail?id=986",
    "note": "香料・添加物の由来確認が必要"
  },
  {
    "name": "海鮮ごのみ 57g",
    "url": "https://7premium.jp/product/search/detail?id=5054",
    "note": "ポークエキス・ゼラチン分解物の記載あり"
  },
  {
    "name": "カレーヌードル 87g",
    "url": "https://7premium.jp/product/search/detail?id=376",
    "note": "豚脂・豚肉加工品の記載あり"
  },
  {
    "name": "ナポリタン 1食入",
    "url": "https://7premium.jp/product/search/detail?id=7220",
    "note": "ソーセージ・豚肉アレルゲンなど確認"
  },
  {
    "name": "玉ねぎサラダ 90g",
    "url": "https://7premium.jp/product/search/detail?id=8875",
    "note": "玉ねぎ・レタス等。現物確認が必要"
  },
  {
    "name": "ぬれせんべい 4枚入",
    "url": "https://7premium.jp/product/search/detail?id=8960",
    "note": "発酵調味液の由来確認が必要"
  },
  {
    "name": "おつまみカニカマ 100g",
    "url": "https://7premium.jp/product/search/detail?id=5442",
    "note": "魚肉・マヨネーズ等。現物確認が必要"
  },
  {
    "name": "銘店紀行 六角家 家系豚骨醤油 99g",
    "url": "https://7premium.jp/product/search/detail?id=11720",
    "note": "豚脂・ポークエキス・味付豚肉の記載あり"
  }
] as const;
export default function SevenPremiumIngredientLinks(){
 const [filter,setFilter]=useState('');
 const visible=pages.filter(p=>(p.name+' '+p.note).toLocaleLowerCase().includes(filter.toLocaleLowerCase().trim()));
 return <section style={{margin:'12px 0',padding:'13px',border:'1px solid #466e58',borderRadius:14,background:'#173629',color:'#f1f3e5'}}>
 <h3 style={{fontSize:16,margin:'0 0 8px'}}>7 Premium — Official 原材料 sources</h3>
 <p style={{fontSize:12,lineHeight:1.6}}>These links open real ingredient disclosures on the official Seven Premium website. Links are references only, not copied ingredient lists or confirmed barcode matches. No Halal certification is implied. Packages and recipes may change.</p>
 <input aria-label="Filter Seven Premium official ingredient sources" value={filter} onChange={e=>setFilter(e.target.value)} placeholder="Product name / 7 Premium…" style={{width:'100%',boxSizing:'border-box',padding:10,borderRadius:9,background:'#244836',border:'1px solid #567b62',color:'#fff'}}/>
 <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(min(100%,240px),1fr))',gap:8,marginTop:10}}>
  {visible.map(p=><article key={p.url} style={{padding:12,border:'1px solid #4d705b',borderRadius:11}}>
   <b style={{display:'block',fontSize:13}}>{p.name}</b>
   <span style={{display:'block',fontSize:12,margin:'5px 0',color:'#e9d4a2'}}>{p.note}</span>
   <a href={p.url} target="_blank" rel="noopener noreferrer" style={{fontSize:12,color:'#9cd9ff',textDecoration:'underline'}}>7 Premium の公式原材料を見る ↗</a>
   <small style={{display:'block',marginTop:5,color:'#d4d6c7'}}>JAN not confirmed · check current package</small>
  </article>)}
 </div>
 <small style={{display:'block',marginTop:10}}>External pages belong to Seven & i. This tool is independent; no data partnership is claimed.</small>
 </section>;
}
