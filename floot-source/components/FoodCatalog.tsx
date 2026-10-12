import React,{useEffect,useState} from 'react';
import {getFoodCatalog,type CatalogProduct} from '../endpoints/food-catalog_GET.schema';
import {Button} from './Button';
import styles from './FoodCatalog.module.css';
export default function FoodCatalog({onChoose}:{onChoose:(q:string)=>void}){
 const [store,setStore]=useState('gyomu'),[page,setPage]=useState(1),[items,setItems]=useState<CatalogProduct[]>([]),[total,setTotal]=useState(0),[error,setError]=useState(''),[loading,setLoading]=useState(false);
 useEffect(()=>{let active=true;setLoading(true);getFoodCatalog(store,page).then(r=>{if(active){setItems(r.items);setTotal(r.total);setError('')}}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[store,page]);
 return <section className={styles.wrap}><h2>Explore Japanese Food Products</h2><p>Photos and listings from retailer/manufacturer catalogues. <b>Listed here does not mean halal certified.</b></p>
 <div className={styles.stores}>{[['gyomu','業務スーパー'],['family','FamilyMart'],['seven','7-Eleven'],['lawson','Lawson'],['suntory','Suntory']].map(([value,label])=><button key={value} className={store===value?styles.active:''} onClick={()=>{setStore(value);setPage(1)}}>{label}</button>)}</div>
 <p className={styles.count}>{loading?'Loading products…':total+' catalog products'} · Tap a product to check details</p>
 {error&&<p className={styles.error}>{error}</p>}
 <div className={styles.grid}>{items.map(x=><button className={styles.item} key={x.id} onClick={()=>onChoose(x.barcode||x.name)}>{x.image?<img loading="lazy" src={x.image} alt={x.name}/>:<div className={styles.noImage}>No photo</div>}<b>{x.name}</b><small>{x.brand} {x.category?' · '+x.category:''}</small><span>Check ingredients →</span></button>)}</div>
 <div className={styles.pages}><Button variant="outline" disabled={page<=1||loading} onClick={()=>setPage(x=>x-1)}>Previous</Button><span>{page} / {Math.max(1,Math.ceil(total/24))}</span><Button variant="outline" disabled={page*24>=total||loading} onClick={()=>setPage(x=>x+1)}>Next</Button></div>
 </section>;
}
