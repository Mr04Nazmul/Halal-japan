import React, {useEffect,useState} from 'react';
import superjson from 'superjson';
type Source={sourceKey:string;sourceName:string;sourceUrl:string;sourceKind:string;usageNote:string;halalCertificationSource:boolean};
export default function FoodReferenceSources(){
 const [sources,setSources]=useState<Source[]>([]);
 useEffect(()=>{let cancelled=false;fetch('/_api/reference-sources').then(r=>{if(!r.ok)throw Error('Unavailable');return r.text()}).then(t=>{if(!cancelled)setSources(superjson.parse<{sources:Source[]}>(t).sources)}).catch(()=>{});return()=>{cancelled=true}},[]);
 return <section style={{padding:16,marginTop:24,border:'1px solid #475467',borderRadius:16}}>
 <h3>Japanese food research sources / 食品情報の参考資料</h3>
 <p>These are research references, not product-specific halal certificates or barcode databases.</p>
 <ul>{sources.map(s=><li key={s.sourceKey} style={{marginBottom:12}}><a href={s.sourceUrl} target="_blank" rel="noopener noreferrer">{s.sourceName}</a><div><small>{s.usageNote}</small></div></li>)}</ul>
 {!sources.length&&<p>Reference directory is temporarily unavailable.</p>}
 <small>For halal decisions, check exact product ingredients and reviewed manufacturer/certificate evidence.</small>
 </section>;
}

