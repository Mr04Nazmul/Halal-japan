import React,{useState,useEffect,useRef} from 'react';
import { BrowserMultiFormatReader, BrowserCodeReader } from '@zxing/browser';
import { BarcodeFormat, DecodeHintType } from '@zxing/library';
import {ScanLine,Search,ShieldCheck,MapPin,Languages,Info,Camera, X,CheckCircle2,AlertTriangle,PackageSearch,Heart,User,BookmarkPlus,ArrowRight,ChevronRight,ScanBarcode,FileText,Compass,Leaf,Clock3,Keyboard,ArrowUpRight,Store} from 'lucide-react';
import {Button} from '../components/Button';
import {Input} from '../components/Input';
import styles from './_index.module.css';
import IngredientOcr from '../components/IngredientOcr';
import IngredientVerification from '../components/IngredientVerification';
import ReviewedEcodeGuide from '../components/ReviewedEcodeGuide';
import ResearchSourcesSettings from '../components/ResearchSourcesSettings';
import IslamicTools from '../components/IslamicTools';
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
 const lookup=async(code:string)=>{setScanning(false);setView('home');setBusy(true);setError('');setResult(null);setQuery(code);try{
 const p=await postFoodLookup({query:code.trim()});
 if(!p.found){setResult({code:code.trim(),name:'Barcode evidence not yet available',verdict:'unknown',reasons:p.reasons?.length?p.reasons:['Verified ingredients are not yet linked to this barcode.'],source:'Automatic barcode lookup',coverageNote:'Official product records, the protected Japan catalogue and public product databases did not establish this barcode’s ingredients. No HALAL or HARAM verdict is invented.'});return;}
 setResult({code:p.barcode||code,name:p.name||'Unnamed product',brands:p.brand||undefined,ingredients_text:p.ingredients||undefined,image_front_small_url:p.image||undefined,verdict:p.verdict,reasons:p.reasons,source:p.source||'',productUrl:p.productUrl||null,coverageNote:p.coverageNote||'',confidence:p.confidence,findings:p.findings,manufacturerEvidence:p.manufacturerEvidence,certificate:p.certificate||null});
 }catch(e:any){setError(e.message||'Network error');}finally{setBusy(false)}};
 useEffect(()=>{if(!scanning)return;let cancelled=false;let scanner:BrowserMultiFormatReader|undefined;const init=async()=>{try{const hints=new Map();hints.set(DecodeHintType.POSSIBLE_FORMATS,[BarcodeFormat.EAN_13,BarcodeFormat.EAN_8,BarcodeFormat.UPC_A,BarcodeFormat.ITF]);hints.set(DecodeHintType.TRY_HARDER,true);scanner=new BrowserMultiFormatReader(hints,{delayBetweenScanAttempts:100,delayBetweenScanSuccess:300});if(!video.current)return;const c=await scanner.decodeFromConstraints({audio:false,video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}}},video.current,(r)=>{if(r&&!cancelled){cancelled=true;control.current?.stop();lookup(r.getText())}});control.current=c;if(cancelled)c.stop();const NativeDetector=(window as any).BarcodeDetector;if(NativeDetector&&!cancelled){try{const formats=await NativeDetector.getSupportedFormats();const available=['ean_13','ean_8','upc_a','itf'].filter(x=>formats.includes(x));if(available.length){const detector=new NativeDetector({formats:available});let pending=false;nativeTimer.current=setInterval(async()=>{if(cancelled||pending||!video.current||video.current.readyState<2)return;pending=true;try{const results=await detector.detect(video.current);const code=results?.[0]?.rawValue;if(code&&/^[0-9]{8,14}$/.test(code)){cancelled=true;control.current?.stop();lookup(code)}}catch{}finally{pending=false}},120)}}catch{}}}catch(e:any){setError('Camera unavailable: '+(e.message||'Check HTTPS and permissions'));setScanning(false);}};init();return()=>{cancelled=true;if(nativeTimer.current)clearInterval(nativeTimer.current);nativeTimer.current=null;control.current?.stop();control.current=null;};},[scanning]);
 // Camera scans, Favorites and product-directory choices always reveal their result.
 useEffect(()=>{if(result&&view==='home'){document.getElementById('scan-result')?.scrollIntoView({behavior:'smooth',block:'start'});}},[result,view]);
 const needsReview=result&&(/\b(gelatin|lard|pork|ethanol|alcohol|wine|rum|mirin)\b|ゼラチン|豚|酒精|みりん/i.test(result.ingredients_text||'')); 
 return <main className={styles.page}><div className={styles.shell}>
 <header className={styles.header}>
  <button type="button" className={styles.brandHome} onClick={()=>setView('home')} aria-label="Japan Halal Checker home">
   <span className={styles.logo}><Leaf size={23} strokeWidth={2.6}/></span>
   <span className={styles.brandTitle}><b>halal<span className={styles.accent}>japan.</span></b><small>SCAN · KNOW · CHOOSE</small></span>
  </button>
  <button type="button" className={styles.lang} onClick={()=>setView(view==='settings'?'home':'settings')} aria-label="Language and settings"><Languages size={19}/><span>{language.toUpperCase()}</span></button>
 </header>
 {view==='home'?<>
  <section className={styles.hero} aria-labelledby="barcode-hero-heading">
   <div className={styles.heroContent}>
    <div className={styles.eyebrow}><span className={styles.liveDot}/> YOUR FOOD, MADE CLEAR</div>
    <h1 id="barcode-hero-heading">Scan food.<br/><em>Know more.</em></h1>
    <p>{w.sub} Check Japanese ingredient labels and follow the original source.</p>
    <div className={styles.heroActions}>
     <Button size="lg" className={styles.cta} onClick={()=>{setError('');setScanning(true)}}><ScanBarcode size={22}/> {w.scan} <ArrowRight size={20}/></Button>
     <button type="button" className={styles.heroSecondary} onClick={()=>document.querySelector('#ingredient-photo-fallback')?.scrollIntoView({behavior:'smooth'})}><Camera size={18}/> Scan ingredients</button>
    </div>
   </div>
   <div className={styles.heroArtwork} aria-hidden="true">
    <div className={styles.scanOrbit}></div>
    <div className={styles.artPackage}><div className={styles.artLeaf}><Leaf size={40}/></div><div className={styles.artPackageText}>FOOD<br/>CHECK</div><div className={styles.artBarcode}><i/><i/><i/><i/><i/><i/><i/><i/><i/><i/><i/><i/><i/><i/></div></div>
    <div className={styles.artCornerTL}/><div className={styles.artCornerTR}/><div className={styles.artCornerBL}/><div className={styles.artCornerBR}/>
    <div className={styles.artScanLine}/>
    <div className={styles.artTag}><ShieldCheck size={15}/> Ingredient insights</div>
   </div>
   <div className={styles.heroFoot}><ShieldCheck size={15}/> Evidence-based screening <span>·</span> No sign-in required</div>
  </section>
  <section className={styles.section} id="product-lookup" aria-labelledby="product-search-heading">
   <div className={styles.sectionHeading}>
    <div><span className={styles.kicker}>01 / FIND YOUR PRODUCT</span><h2 id="product-search-heading"><Search size={21}/> {w.search}</h2></div>
    <span className={styles.sectionAside}>JAN / EAN / 名前</span>
   </div>
   <form className={styles.search} onSubmit={e=>{e.preventDefault();if(query.trim())lookup(query)}}>
    <Search size={21} className={styles.searchIcon} aria-hidden="true"/>
    <Input value={query} onChange={e=>setQuery(e.target.value)} placeholder={w.placeholder} aria-label={w.placeholder}/>
    <Button type="submit" disabled={busy||!query.trim()}>{busy?'Searching…':<>Check <ArrowRight size={18}/></>}</Button>
   </form>
   <div className={styles.searchFoot}><span><ShieldCheck size={14}/> JAN / EAN · Ingredient evidence</span><a href="#ingredient-photo-fallback">No label? Scan ingredients <ArrowUpRight size={14}/></a></div>
 {busy&&<p className={styles.note}>{w.checking}</p>}{error&&<div className={styles.alert}><AlertTriangle size={17}/><span>{error} <button type="button" onClick={()=>query.trim()&&lookup(query)} style={{display:'block',marginTop:10,padding:'9px 12px',borderRadius:9,background:'#e5c78e',color:'#172b20',fontWeight:700}}>Retry barcode lookup</button></span></div>}
 {result&&<article className={styles.detailCard} id="scan-result" aria-labelledby="scan-result-title">
  <div className={styles.resultEyebrow}><CheckCircle2 size={16}/> {result.verdict==='unknown'&&!result.ingredients_text?'BARCODE CHECKED':'PRODUCT FOUND'} <span>·</span> INGREDIENT REVIEW</div>
  <div className={styles.resultTop}>
   <div className={styles.detailPhoto}>{result.image_front_small_url?<img src={result.image_front_small_url} alt={result.name}/>:<PackageSearch size={53} strokeWidth={1.5}/>}</div>
   <div className={styles.resultIdentity}><h3 id="scan-result-title">{result.name}</h3><p>{result.brands||'Brand not provided'}</p><small>JAN: {/^[0-9]{8,14}$/.test(result.code)?result.code:'Not confirmed'}</small>
    <button type="button" className={styles.saveButton} onClick={()=>saveFavorite(result)}><Heart size={17} fill={isFavorite(result)?'currentColor':'none'}/> {isFavorite(result)?'Saved':'Save product'}</button>
   </div>
  </div>
  <div className={styles.verdictPanel} data-verdict={result.verdict} role="status">
   <div className={styles.verdictIcon}>{result.verdict==='haram_ingredient'?<AlertTriangle size={23}/>:result.verdict==='needs_review'||result.verdict==='unknown'?<Info size={23}/>:<ShieldCheck size={23}/>}</div>
   <div><span className={styles.verdictCaption}>INGREDIENT SCREENING RESULT</span>
    <div className={styles.statusLarge} data-verdict={result.verdict}>{result.verdict==='haram_ingredient'?'HARAM · Flagged ingredient':result.verdict==='certified'&&result.certificate&&isCertificateDisplayCurrent(result.certificate)?'HALAL · Certified':result.verdict==='ingredient_clear'?'HALAL · Ingredient Check':result.verdict==='needs_review'&&result.findings?.length?'CHECK · Ingredient origin':result.verdict==='needs_review'?'CHECK · Full label':'UNKNOWN · More evidence needed'}</div>
   </div>
  </div>
  <section className={styles.ingredientPanel} aria-label="Product ingredients">
   <div className={styles.ingredientHeading}><FileText size={20}/><h4>Ingredients <span>原材料名・添加物</span></h4></div>
   <p>{result.ingredients_text||'A verified full ingredient declaration is not yet linked to this barcode.'}</p>
   {result.findings?.length?<ul className={styles.findingList}>{result.findings.map((finding,i)=><li key={i} data-severity={finding.severity}><strong>{finding.ingredient}</strong><span>{finding.reason}</span></li>)}</ul>:null}
  </section>
  <div className={styles.detailGrid}>
   <div className={styles.detailRow}><strong>JAN / Barcode</strong><span>{/^[0-9]{8,14}$/.test(result.code)?result.code:'Not yet verified'}</span></div>
   <div className={styles.detailRow}><strong>Manufacturer</strong><span>{result.brands||'Not provided'}</span></div>
  </div>
  <details className={styles.resultDisclosure}><summary><Info size={17}/> Why this result? <ChevronRight size={18}/></summary>
   <p>{result.reasons?.join(' ')||'More information is needed.'}</p>
   {result.coverageNote?<p>{result.coverageNote}</p>:null}
   <p>Store availability has not been confirmed. Ingredient screening is not a halal certificate; compare the latest package label.</p>
  </details>
  <div className={styles.sourceBar}><div><span>DATA SOURCE</span><strong>{result.source||'Not available'}</strong></div>{result.productUrl?<a href={result.productUrl} target="_blank" rel="noopener noreferrer">View original <ArrowUpRight size={16}/></a>:null}</div>
  {result.manufacturerEvidence?.length?<details className={styles.resultDisclosure}>
   <summary><FileText size={17}/> Ingredient source evidence <ChevronRight size={18}/></summary>
   {result.manufacturerEvidence.map((e,i)=><div key={i}>
    <p>{e.type}{e.reviewedAt?' · Checked '+e.reviewedAt:''}</p>
    {e.url&&/^https:\/\//i.test(e.url)?<a href={e.url} target="_blank" rel="noopener noreferrer">Open manufacturer evidence ↗</a>:null}
   </div>)}
  </details>:null}
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
 <section className={styles.toolsSection} aria-label="Explore tools">
   <div className={styles.sectionHeading}><div><span className={styles.kicker}>02 / YOUR TOOLS</span><h2>Explore more</h2></div></div>
   <div className={styles.quickLinks}>
    <button type="button" onClick={()=>{setError('');setScanning(true)}}><span className={styles.toolIcon}><ScanBarcode size={25}/></span><strong>Barcode Scanner</strong><small>JAN · EAN codes</small><ChevronRight className={styles.toolArrow} size={16}/></button>
    <button type="button" onClick={()=>document.querySelector('#ingredient-photo-fallback')?.scrollIntoView({behavior:'smooth'})}><span className={styles.toolIcon}><FileText size={25}/></span><strong>Ingredient OCR</strong><small>Read Japanese labels</small><ChevronRight className={styles.toolArrow} size={16}/></button>
    <button type="button" onClick={()=>{setPlacesTab('restaurants');setView('places')}}><span className={styles.toolIcon}><Store size={25}/></span><strong>Restaurants</strong><small>Halal dining map</small><ChevronRight className={styles.toolArrow} size={16}/></button>
    <button type="button" onClick={()=>{setPlacesTab('mosques');setView('places')}}><span className={styles.toolIcon}><Compass size={25}/></span><strong>Prayer & Qibla</strong><small>Mosques · prayer times</small><ChevronRight className={styles.toolArrow} size={16}/></button>
   </div>
  </section>
  <button type="button" className={styles.discoverBanner} onClick={()=>{setPlacesTab('restaurants');setView('places')}}><span><strong>Find halal places in Japan</strong><small>Restaurants, mosques & nearby prayer spots</small></span><span className={styles.bannerArrow}><ArrowUpRight size={22}/></span></button>
 <details className={styles.ocrWorkflow}><summary>Optional manual ingredient tools</summary><section aria-labelledby="label-check-heading">
  <div className={styles.sectionHeading}>
   <div><span className={styles.kicker}>03 / INGREDIENT LABEL</span><h2 id="label-check-heading"><FileText size={21}/> Check the package</h2></div>
  </div>
  <div id="ingredient-photo-fallback"><IngredientOcr onDetected={setOcrText}/></div>
  <IngredientVerification initialText={ocrText}/>
 </section></details>
<div className={styles.hint}><ShieldCheck size={20}/><span>{w.sources}. No unverified halal certification claims.</span></div></section></>:view==='favorites'?<section className={styles.section}><h1>Favorites ({favorites.length})</h1><p className={styles.note}>Saved on this device</p><div className={styles.favGrid}>{favorites.map(p=><button key={p.code} className={styles.favCard} onClick={()=>{setView('home');lookup(p.code)}}>{p.image_front_small_url?<img src={p.image_front_small_url} alt=""/>:<PackageSearch size={40}/>}<strong>{p.name}</strong><span>{p.verdict==='haram_ingredient'?'HARAM':p.verdict==='certified'&&p.certificate&&isCertificateDisplayCurrent(p.certificate)?'HALAL · Certified':p.verdict==='ingredient_clear'?'HALAL · Ingredient Check':p.verdict==='needs_review'&&p.findings?.length?'CHECK · Origin':'CHECK'}</span></button>)}</div>{!favorites.length&&<p>Search a product and tap Add to Favorites to save it here.</p>}</section>:view==='profile'?<section className={styles.section}><h1>Profile & Settings</h1><div className={styles.detailCard}><div className={styles.detailRow}><strong>Product Status</strong><span>HALAL (Ingredient Check) · HARAM · CHECK · UNKNOWN</span></div><div className={styles.detailRow}><strong>Theme</strong><span>Barcode Pro · Mint & White</span></div><div className={styles.detailRow}><strong>Privacy</strong><span>Favorites stay on this device. No login needed.</span></div><div className={styles.detailRow}><strong>Help & Support</strong><span>Check package labels and manufacturer information before relying on a result.</span></div><div className={styles.detailRow}><strong>About</strong><span>Created by Najmul Hossain</span></div></div><button className={styles.profileButton} onClick={()=>setView('settings')}>Language & Research Sources →</button></section>:view==='settings'?<section className={styles.section}><h1>{w.settings}</h1><p>Select language</p><div className={styles.langGrid}>{Object.keys({en:1,bn:1,ja:1}).map(l=><Button key={l} variant={language===l?'primary':'outline'} onClick={()=>setLanguage(l)}>{({en:'English',bn:'বাংলা',ja:'日本語'} as any)[l]}</Button>)}</div><p className={styles.note}>Additional translations are planned and are not yet complete.</p><hr/><h2>About</h2><p>{w.about}</p><p>Results are informational only. Ingredient sources and certifications require verification.</p><ResearchSourcesSettings/><details className={styles.advancedResearch}><summary>Ingredient & E-number research guide</summary><ReviewedEcodeGuide/></details></section> :view==='places'?<section className={styles.section}><div className={styles.placesIntro}><small>DISCOVER JAPAN</small><h1>Places to explore.</h1><p>Find halal dining and nearby spaces for prayer.</p></div><div className={styles.placesTabs} role="tablist" aria-label="Places category"><button role="tab" aria-selected={placesTab==='restaurants'} className={placesTab==='restaurants'?styles.selectedTab:''} onClick={()=>setPlacesTab('restaurants')}>🍽️ Restaurants</button><button role="tab" aria-selected={placesTab==='mosques'} className={placesTab==='mosques'?styles.selectedTab:''} onClick={()=>setPlacesTab('mosques')}>🕌 Mosques · Prayer · Qibla</button></div>{placesTab==='restaurants'?<div className={styles.restaurantPanel}><h2>Live Restaurants & Mosque Map</h2><p>Explore community-mapped halal dining and mosques, plus prayer time and Qibla. Verify halal claims with the venue.</p><a className={styles.restaurantLink} href="./places-prayer.html">Open live restaurants · mosques · prayer map ↗</a><iframe title="Halal restaurant listings" src={'./places-prayer.html?lang='+language} loading="lazy" style={{width:'100%',height:640,border:0,borderRadius:18,background:'#f2f7f2'}}/></div>:<iframe title="Live mosques prayer times and Qibla" src={'./places-prayer.html?lang='+language} loading="lazy" style={{width:'100%',height:950,border:0,borderRadius:18,background:'#f2f7f2'}}/>}</section>:<section className={styles.section}><IslamicTools/></section>}
 <footer className={styles.nav} aria-label="Primary navigation">
  <button type="button" className={view==='home'?styles.activeNav:''} onClick={()=>setView('home')}><ScanLine size={22}/><span>{w.home}</span></button>
  <button type="button" className={view==='places'?styles.activeNav:''} onClick={()=>setView('places')}><MapPin size={22}/><span>{w.places}</span></button>
  <button type="button" className={styles.navScan} onClick={()=>{setError('');setScanning(true)}} aria-label="Open barcode scanner"><ScanBarcode size={26}/><span>Scan</span></button>
  <button type="button" className={view==='favorites'?styles.activeNav:''} onClick={()=>setView('favorites')}><Heart size={22}/><span>Saved</span></button>
  <button type="button" className={view==='profile'||view==='settings'?styles.activeNav:''} onClick={()=>setView('profile')}><User size={22}/><span>Profile</span></button>
 </footer>
 </div>
 {scanning&&<div className={styles.overlay}><div className={styles.scanner} role="dialog" aria-modal="true" aria-label="Scan JAN barcode">
  <div className={styles.scanHead}><div><span>SCAN MODE</span><b>Find your food</b></div><button type="button" aria-label="Close barcode scanner" onClick={()=>setScanning(false)}><X size={23}/></button></div>
  <div className={styles.videoWrap}><video ref={video} autoPlay playsInline muted/><div className={styles.frame}><div className={styles.scanBeam}/></div><div className={styles.scanViewHint}><ScanBarcode size={18}/> Position barcode inside frame</div></div>
  <p className={styles.scanHelp}>Hold the barcode steady in good light. Scanning starts automatically.</p>
  <label className={styles.photoUpload}><Camera size={20}/> Scan from a photo<input type="file" accept="image/*" onChange={scanFile}/></label>
  <form className={styles.scanManual} onSubmit={e=>{e.preventDefault();if(query.trim())lookup(query.trim())}}>
   <label htmlFor="manual-jan"><Keyboard size={16}/> Enter barcode manually</label>
   <div><input id="manual-jan" inputMode="numeric" pattern="[0-9]{8,14}" aria-label="Enter barcode number" placeholder="13-digit JAN code" value={query} onChange={e=>setQuery(e.target.value)}/><button type="submit" disabled={!/^[0-9]{8,14}$/.test(query.trim())}>Check <ArrowRight size={17}/></button></div>
  </form>
 </div></div>}
 </main>
}

