import React,{useState,useEffect,useRef} from 'react';
import { BrowserMultiFormatReader, BrowserCodeReader } from '@zxing/browser';
import { BarcodeFormat, DecodeHintType } from '@zxing/library';
import {ScanLine,Search,ShieldCheck,MapPin,Languages,Info,Camera, X,CheckCircle2,AlertTriangle,PackageSearch,Heart,User,BookmarkPlus} from 'lucide-react';
import {Button} from '../components/Button';
import {Input} from '../components/Input';
import styles from './_index.module.css';
import IngredientOcr from '../components/IngredientOcr';
import IngredientVerification from '../components/IngredientVerification';
import ReviewedEcodeGuide from '../components/ReviewedEcodeGuide';
import ResearchSourcesSettings from '../components/ResearchSourcesSettings';
import IslamicTools from '../components/IslamicTools';
import FoodCatalog from '../components/FoodCatalog';
import SevenElevenOfficialCatalog from '../components/SevenElevenOfficialCatalog';
import SevenElevenIngredientResearch from '../components/SevenElevenIngredientResearch';
import {postFoodLookup, type LookupResult} from '../endpoints/food-lookup_POST.schema';
import {isCertificateDisplayCurrent} from '../helpers/verifiedHalalCertificates';

type Product={code:string;name:string;brands?:string;ingredients_text?:string;image_front_small_url?:string;verdict?:LookupResult['verdict'];reasons?:string[];source?:string;productUrl?:string|null;coverageNote?:string;confidence?:'high'|'medium'|'low';findings?:LookupResult['findings'];manufacturerEvidence?:LookupResult['manufacturerEvidence'];certificate?:LookupResult['certificate'];};
const words:Record<string,Record<string,string>>={
 en:{sub:'Understand ingredients. Shop confidently.',scan:'Scan a barcode',search:'Search a Japanese product',placeholder:'Product name or JAN barcode',checking:'Looking up product…',unknown:'Not enough verified information',warning:'A barcode alone cannot establish halal certification.',sources:'Data from Open Food Facts · check the package',no:'No product found in the public database',about:'Created by Najmul Hossain',home:'Home',places:'Places',settings:'Settings'},
 bn:{sub:'উপাদান যাচাই করে সচেতনভাবে কেনাকাটা করুন',scan:'বারকোড স্ক্যান করুন',search:'জাপানি পণ্য খুঁজুন',placeholder:'পণ্যের নাম বা JAN বারকোড',checking:'পণ্য খোঁজা হচ্ছে…',unknown:'যাচাইযোগ্য তথ্য যথেষ্ট নেই',warning:'শুধু বারকোড দিয়ে হালাল সনদ নিশ্চিত করা যায় না।',sources:'Open Food Facts-এর তথ্য · প্যাকেটও যাচাই করুন',no:'পাবলিক ডেটাবেসে পণ্যটি পাওয়া যায়নি',about:'নির্মাতা: Najmul Hossain',home:'হোম',places:'স্থান',settings:'সেটিংস'},
 ja:{sub:'原材料を確認して、安心できるお買い物を。',scan:'バーコードを読み取る',search:'日本の商品を検索',placeholder:'商品名またはJANコード',checking:'商品を検索中…',unknown:'十分な確認情報がありません',warning:'バーコードだけではハラール認証を証明できません。',sources:'Open Food Factsの情報・商品ラベルをご確認ください',no:'公開データベースに商品が見つかりません',about:'制作：Najmul Hossain',home:'ホーム',places:'場所',settings:'設定'}
};
export default function Home(){
 const [language,setLanguage]=useState('en'); const w=words[language]||words.en;
 const [placesTab,setPlacesTab]=useState<'restaurants'|'mosques'>('restaurants');
 const [ocrText,setOcrText]=useState('');const [query,setQuery]=useState('');const [result,setResult]=useState<Product|null>(null);const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [scanning,setScanning]=useState(false);const [view,setView]=useState('home');
 const [favorites,setFavorites]=useState<Product[]>(()=>{try{return JSON.parse(localStorage.getItem('jhc-favorites')||'[]')}catch{return []}});
 const saveFavorite=(p:Product)=>setFavorites(old=>{const exists=old.some(x=>x.code===p.code);const next=exists?old.filter(x=>x.code!==p.code):[p,...old];localStorage.setItem('jhc-favorites',JSON.stringify(next));return next});
 const isFavorite=(p:Product)=>favorites.some(x=>x.code===p.code);
 const video=useRef<HTMLVideoElement>(null);const control=useRef<any>(null);const nativeTimer=useRef<ReturnType<typeof setInterval>|null>(null);
 const scanFile=async(e:React.ChangeEvent<HTMLInputElement>)=>{const file=e.target.files?.[0];if(!file)return;try{const url=URL.createObjectURL(file);try{const hints=new Map();hints.set(DecodeHintType.POSSIBLE_FORMATS,[BarcodeFormat.EAN_13,BarcodeFormat.EAN_8,BarcodeFormat.UPC_A,BarcodeFormat.ITF]);hints.set(DecodeHintType.TRY_HARDER,true);const reader=new BrowserMultiFormatReader(hints);const r=await reader.decodeFromImageUrl(url);lookup(r.getText());}finally{URL.revokeObjectURL(url)}}catch{setError('Could not read barcode from photo. Retake a clear, straight photo or enter the printed barcode number.');setScanning(false)}};
 const lookup=async(code:string)=>{setScanning(false);setBusy(true);setError('');setResult(null);setQuery(code);try{
 const p=await postFoodLookup({query:code.trim()});
 if(!p.found){setError('পণ্যটি পাওয়া যায়নি। প্যাকেটের পেছনে 原材料名 লেখা ingredient label-এর পরিষ্কার ছবি দিন। তাহলে pork extract, gelatin, emulsifier, flavouring ও অন্যান্য উপাদান যাচাই করা যাবে।');return;}
 setResult({code:p.barcode||code,name:p.name||'Unnamed product',brands:p.brand||undefined,ingredients_text:p.ingredients||undefined,image_front_small_url:p.image||undefined,verdict:p.verdict,reasons:p.reasons,source:p.source||'',productUrl:p.productUrl||null,coverageNote:p.coverageNote||'',confidence:p.confidence,findings:p.findings,manufacturerEvidence:p.manufacturerEvidence,certificate:p.certificate||null});
 }catch(e:any){setError(e.message||'Network error');}finally{setBusy(false)}};
 useEffect(()=>{if(!scanning)return;let cancelled=false;let scanner:BrowserMultiFormatReader|undefined;const init=async()=>{try{const hints=new Map();hints.set(DecodeHintType.POSSIBLE_FORMATS,[BarcodeFormat.EAN_13,BarcodeFormat.EAN_8,BarcodeFormat.UPC_A,BarcodeFormat.ITF]);hints.set(DecodeHintType.TRY_HARDER,true);scanner=new BrowserMultiFormatReader(hints,{delayBetweenScanAttempts:100,delayBetweenScanSuccess:300});if(!video.current)return;const c=await scanner.decodeFromConstraints({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}},video.current,(r)=>{if(r&&!cancelled){cancelled=true;control.current?.stop();lookup(r.getText())}});control.current=c;if(cancelled)c.stop();const NativeDetector=(window as any).BarcodeDetector;if(NativeDetector&&!cancelled){try{const formats=await NativeDetector.getSupportedFormats();const available=['ean_13','ean_8','upc_a','itf'].filter(x=>formats.includes(x));if(available.length){const detector=new NativeDetector({formats:available});let pending=false;nativeTimer.current=setInterval(async()=>{if(cancelled||pending||!video.current||video.current.readyState<2)return;pending=true;try{const results=await detector.detect(video.current);const code=results?.[0]?.rawValue;if(code&&/^[0-9]{8,14}$/.test(code)){cancelled=true;control.current?.stop();lookup(code)}}catch{}finally{pending=false}},120)}}catch{}}}catch(e:any){setError('Camera unavailable: '+(e.message||'Check HTTPS and permissions'));setScanning(false);}};init();return()=>{cancelled=true;if(nativeTimer.current)clearInterval(nativeTimer.current);nativeTimer.current=null;control.current?.stop();control.current=null;};},[scanning]);
 const needsReview=result&&(/\b(gelatin|lard|pork|ethanol|alcohol|wine|rum|mirin)\b|ゼラチン|豚|酒精|みりん/i.test(result.ingredients_text||'')); 
 return <main className={styles.page}><div className={styles.shell}>
 <header className={styles.header}><div className={styles.brand}><span className={styles.logo}>☪</span><div><b>HALAL<span className={styles.accent}>JAPAN</span></b><small>FOOD INTELLIGENCE</small></div></div><button className={styles.lang} onClick={()=>setView(view==='settings'?'home':'settings')}><Languages size={19}/>{language.toUpperCase()}</button></header>
 {view==='home'?<><section className={styles.hero}><div className={styles.eyebrow}>✦ JAPAN HALAL CHECKER</div><h1>Know what’s <em>inside.</em></h1><p>{w.sub}</p><div className={styles.graphic}><ScanLine size={78} strokeWidth={1.2}/><span>SCAN • CHECK • DISCOVER</span></div><Button size="lg" className={styles.cta} onClick={()=>{setError('');setScanning(true)}}><Camera size={19}/> {w.scan}</Button></section>
 <div className={styles.quickLinks}>
 <button onClick={()=>{setError('');setScanning(true)}}><span>▦</span><strong>Barcode Scanner</strong><small>JAN / EAN</small></button>
 <button onClick={()=>document.querySelector('#ingredient-photo-fallback')?.scrollIntoView({behavior:'smooth'})}><span>✧</span><strong>Ingredients</strong><small>Japanese OCR</small></button>
 <button onClick={()=>{setPlacesTab('restaurants');setView('places')}}><span>⌖</span><strong>Restaurants</strong><small>Halal food nearby</small></button>
 <button onClick={()=>{setPlacesTab('mosques');setView('places')}}><span>☪</span><strong>Mosques</strong><small>Prayer & Qibla</small></button>
 </div>
 <button className={styles.discoverBanner} onClick={()=>{setPlacesTab('restaurants');setView('places')}}><span><strong>Discover halal places</strong><small>Restaurants across Japan · Explore the directory</small></span><span aria-hidden="true">↗</span></button>
 <div className={styles.sectionLabel}><span>✦ SMART FOOD VERIFICATION</span><small>Identify · Verify · Decide carefully</small></div>
 <section className={styles.section}><h2><Search size={20}/> {w.search}</h2><form className={styles.search} onSubmit={e=>{e.preventDefault();if(query.trim())lookup(query)}}><Input value={query} onChange={e=>setQuery(e.target.value)} placeholder={w.placeholder}/><Button type="submit" disabled={busy}>{busy?'…':'Search'}</Button></form>
 {busy&&<p className={styles.note}>{w.checking}</p>}{error&&<div className={styles.alert}><AlertTriangle size={17}/><span>{error} <button type="button" onClick={()=>document.querySelector('#ingredient-photo-fallback')?.scrollIntoView({behavior:'smooth'})} style={{display:'block',marginTop:10,padding:'9px 12px',borderRadius:9,background:'#e5c78e',color:'#172b20',fontWeight:700}}>原材料名-এর ছবি দিন ↓</button></span></div>}
 {result&&<article className={styles.detailCard}>
 <div className={styles.detailPhoto}>{result.image_front_small_url?<img src={result.image_front_small_url} alt={result.name}/>:<PackageSearch size={60}/>}</div>
 <div className={styles.statusLarge} data-verdict={result.verdict}><span className={styles.statusDot}></span>{result.verdict==='haram_ingredient'?'HARAM':result.verdict==='certified'&&result.certificate&&isCertificateDisplayCurrent(result.certificate)?'HALAL · Certified':result.verdict==='naturally_halal'?'HALAL':result.verdict==='ingredient_clear'?'HALAL · Ingredient Check':result.verdict==='needs_review'&&result.findings?.length?'AVOID · Unverified':result.verdict==='needs_review'?'VERIFY':'UNKNOWN'}</div>
 <div className={styles.detailActions}><button onClick={()=>saveFavorite(result)}><Heart size={20} fill={isFavorite(result)?'currentColor':'none'}/> {isFavorite(result)?'Saved to Favorites':'Add to Favorites'}</button></div>
 <div className={styles.detailRow}><strong>Name</strong><span>{result.name}</span></div>
 <div className={styles.detailRow}><strong>Japanese Name / 商品名</strong><span>{result.name}</span></div>
 <div className={styles.detailRow}><strong>Company / Brand</strong><span>{result.brands||'Not provided'}</span></div>
 <div className={styles.detailRow}><strong>Barcode / JAN</strong><span>{/^\d{8,14}$/.test(result.code)?result.code:"Not yet verified — compare the code on the package"}</span></div>
 <div className={styles.detailRow}><strong>Ingredients / 原材料</strong><span>{result.ingredients_text||'Full ingredients unavailable'}</span></div>
 <div className={styles.detailRow}><strong>Verification details</strong><span>{result.reasons?.join(' ')||'More information needed'}</span></div>
 <div className={styles.detailRow}><strong>Information source</strong><span>{result.source||'Not available'}</span>{result.productUrl?<a href={result.productUrl} target="_blank" rel="noopener noreferrer" style={{color:'#efd699',fontSize:13}}>Open manufacturer / product source ↗</a>:null}</div>
 {result.coverageNote&&<div className={styles.detailRow}><strong>Coverage & verification</strong><span>{result.coverageNote}</span></div>}
 <div className={styles.detailRow}><strong>Available shops</strong><span>Store availability has not been confirmed for this product.</span></div>
 <p className={styles.note}>Ingredient screening is not a halal certificate. Gelatin and other source-dependent additives need verification.</p>
 <details className={styles.certificateDisclosure} key={result.code}>
  <summary className={styles.certificateToggle}><ShieldCheck size={15} aria-hidden="true"/> Halal Certificate <span aria-hidden="true" className={styles.certificateArrow}>⌄</span></summary>
  <div className={styles.certificateContent}>
   {result.certificate&&isCertificateDisplayCurrent(result.certificate)?<>
    <strong>HALAL · Certified</strong>
    <p>Issuer: {result.certificate.issuer}</p>
    <p>Certificate number: {result.certificate.certificateNumber}</p>
    <p>Certificate product: {result.certificate.productName}</p>
    <p>Valid: {result.certificate.validFrom} — {result.certificate.validUntil}</p>
    <p>Last verified: {result.certificate.verifiedAt}</p>
    <a href={result.certificate.officialVerificationUrl} target="_blank" rel="noopener noreferrer">Verify with official issuer ↗</a>
    {result.certificate.certificateDocumentUrl?<a href={result.certificate.certificateDocumentUrl} target="_blank" rel="noopener noreferrer">View official certificate ↗</a>:null}
   </>:<p>No verified product-specific Halal certificate is on file. This does not mean the food is Haram. Check ingredient details above.</p>}
  </div>
 </details>
 </article>}
 <div id="ingredient-photo-fallback"><IngredientOcr onDetected={setOcrText}/></div><IngredientVerification initialText={ocrText}/><ReviewedEcodeGuide/><FoodCatalog onChoose={lookup}/>
 <details style={{margin:'16px 0',border:'1px solid #a8a27566',borderRadius:14,padding:'10px 12px',background:'#143126',color:'#eff0df'}}>
  <summary style={{cursor:'pointer',fontSize:13,fontWeight:700}}>🏪 7-Eleven · Official food sources & product references</summary>
  <p style={{fontSize:12,lineHeight:1.6}}>Official sources only; allergen declarations are not full ingredient lists. Seven-Eleven keeps an internal raw-material and recipe database, but it is not publicly downloadable. No halal status is inferred from these sources alone.</p>
  <ul style={{fontSize:12,lineHeight:1.8,paddingLeft:20}}>
   <li><a href="https://www.7andi.com/en/sustainability/theme/theme2/traceability.html" target="_blank" rel="noopener noreferrer" style={{color:'#e8d298'}}>Food safety, ingredients & traceability — Seven & i ↗</a></li>
   <li><a href="https://www.7andi.com/en/sustainability/theme/theme2/health.html" target="_blank" rel="noopener noreferrer" style={{color:'#e8d298'}}>Health & nutrition policy — Seven & i ↗</a></li>
   <li><a href="https://www.sej.co.jp/products/info_allergy.html" target="_blank" rel="noopener noreferrer" style={{color:'#e8d298'}}>7-Eleven public allergen/nutrition listings ↗</a></li>
   <li><a href="https://7premium.jp/product?c=all" target="_blank" rel="noopener noreferrer" style={{color:'#e8d298'}}>Seven Premium official product catalogue ↗</a></li>
   <li><a href="https://www.sej.co.jp/products/a/bento/" target="_blank" rel="noopener noreferrer" style={{color:'#e8d298'}}>Official Bento category ↗</a></li>
   <li><a href="https://www.sej.co.jp/products/a/onigiri/" target="_blank" rel="noopener noreferrer" style={{color:'#e8d298'}}>Official Onigiri category ↗</a></li>
  </ul>
  <p style={{fontSize:12}}>To check halal suitability, compare the precise package/JAN and the complete <b>原材料名</b> declaration. Check uncertain ingredient origins with the manufacturer.</p>
  <SevenElevenIngredientResearch onChoose={lookup}/>
  <SevenElevenOfficialCatalog onChoose={lookup}/>
 </details><div className={styles.hint}><ShieldCheck size={20}/><span>{w.sources}. No unverified halal certification claims.</span></div></section></>:view==='favorites'?<section className={styles.section}><h1>Favorites ({favorites.length})</h1><p className={styles.note}>Saved on this device</p><div className={styles.favGrid}>{favorites.map(p=><button key={p.code} className={styles.favCard} onClick={()=>{setView('home');lookup(p.code)}}>{p.image_front_small_url?<img src={p.image_front_small_url} alt=""/>:<PackageSearch size={40}/>}<strong>{p.name}</strong><span>{p.verdict==='haram_ingredient'?'HARAM':p.verdict==='certified'&&p.certificate&&isCertificateDisplayCurrent(p.certificate)?'HALAL · Certified':p.verdict==='ingredient_clear'?'HALAL · Ingredient Check':p.verdict==='needs_review'&&p.findings?.length?'AVOID':'VERIFY'}</span></button>)}</div>{!favorites.length&&<p>Search a product and tap Add to Favorites to save it here.</p>}</section>:view==='profile'?<section className={styles.section}><h1>Profile & Settings</h1><div className={styles.detailCard}><div className={styles.detailRow}><strong>Product Status</strong><span>HALAL · HARAM · VERIFY · UNKNOWN</span></div><div className={styles.detailRow}><strong>Theme</strong><span>Emerald / Gold</span></div><div className={styles.detailRow}><strong>Privacy</strong><span>Favorites stay on this device. No login needed.</span></div><div className={styles.detailRow}><strong>Help & Support</strong><span>Check package labels and manufacturer information before relying on a result.</span></div><div className={styles.detailRow}><strong>About</strong><span>Created by Najmul Hossain</span></div></div><button className={styles.profileButton} onClick={()=>setView('settings')}>Language & Research Sources →</button></section>:view==='settings'?<section className={styles.section}><h1>{w.settings}</h1><p>Select language</p><div className={styles.langGrid}>{Object.keys({en:1,bn:1,ja:1}).map(l=><Button key={l} variant={language===l?'primary':'outline'} onClick={()=>setLanguage(l)}>{({en:'English',bn:'বাংলা',ja:'日本語'} as any)[l]}</Button>)}</div><p className={styles.note}>Additional translations are planned and are not yet complete.</p><hr/><h2>About</h2><p>{w.about}</p><p>Results are informational only. Ingredient sources and certifications require verification.</p><ResearchSourcesSettings/></section> :view==='places'?<section className={styles.section}><div className={styles.placesIntro}><small>DISCOVER JAPAN</small><h1>Places to explore.</h1><p>Find halal dining and nearby spaces for prayer.</p></div><div className={styles.placesTabs} role="tablist" aria-label="Places category"><button role="tab" aria-selected={placesTab==='restaurants'} className={placesTab==='restaurants'?styles.selectedTab:''} onClick={()=>setPlacesTab('restaurants')}>🍽️ Restaurants</button><button role="tab" aria-selected={placesTab==='mosques'} className={placesTab==='mosques'?styles.selectedTab:''} onClick={()=>setPlacesTab('mosques')}>🕌 Mosques · Prayer · Qibla</button></div>{placesTab==='restaurants'?<div className={styles.restaurantPanel}><h2>Live Restaurants & Mosque Map</h2><p>Explore community-mapped halal dining and mosques, plus prayer time and Qibla. Verify halal claims with the venue.</p><a className={styles.restaurantLink} href="./places-prayer.html">Open live restaurants · mosques · prayer map ↗</a><iframe title="Halal restaurant listings" src={'./places-prayer.html?lang='+language} loading="lazy" style={{width:'100%',height:640,border:0,borderRadius:18,background:'#f2f7f2'}}/></div>:<iframe title="Live mosques prayer times and Qibla" src={'./places-prayer.html?lang='+language} loading="lazy" style={{width:'100%',height:950,border:0,borderRadius:18,background:'#f2f7f2'}}/>}</section>:<section className={styles.section}><IslamicTools/></section>}
 <footer className={styles.nav}><button onClick={()=>setView('home')}><ScanLine size={23}/>{w.home}</button><button onClick={()=>setView('places')}><MapPin size={23}/>{w.places}</button><button onClick={()=>setView('favorites')}><Heart size={23}/>Favorites</button><button onClick={()=>setView('profile')}><User size={23}/>Profile</button></footer>
 </div>
 {scanning&&<div className={styles.overlay}><div className={styles.scanner}><div className={styles.scanHead}><b>Scan JAN / EAN Barcode</b><button onClick={()=>setScanning(false)}><X/></button></div><div className={styles.videoWrap}><video ref={video} autoPlay playsInline muted/><div className={styles.frame}></div></div><p>Keep the entire barcode and numbers visible. Hold 15–25 cm away, with good light.</p><label className={styles.photoUpload}>Scan barcode from photo<input type="file" accept="image/*" onChange={scanFile}/></label><Button variant="outline" onClick={()=>setScanning(false)}>Cancel</Button></div></div>}
 </main>
}
