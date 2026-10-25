import React, {useState} from 'react';
export default function PriceHistory({code}:{code:string}) {
 const [open,setOpen]=useState(false);
 if(!/^\d{8,14}$/.test(code)) return null;
 const src=`./price-tools.html?code=${encodeURIComponent(code)}`;
 return <section style={{margin:'20px 0',padding:16,border:'1px solid #65856d',borderRadius:16}} aria-label="Product price history">
  <h3>Price Time Machine · দাম তুলনা</h3>
  <p>Community price records with date, currency and store. Japan coverage varies.</p>
  <button type="button" onClick={()=>setOpen(!open)}>{open?'Close prices':'Compare prices for this barcode'}</button>
  {' '}<a href="./price-tools.html#basket">Basket cost tracker</a>
  {open&&<iframe key={code} src={src} title="Open Prices lookup" style={{width:'100%',height:620,border:0,marginTop:16,borderRadius:12}}/>}
 </section>;
}
