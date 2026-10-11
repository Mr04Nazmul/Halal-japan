import React, { useState, useRef } from 'react';
import { SafeAreaView, View, Text, TextInput, Pressable, ScrollView, ActivityIndicator, StyleSheet, StatusBar, Linking } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import TextRecognition from '@react-native-ml-kit/text-recognition';
import Constants from 'expo-constants';
import { InterstitialAd, AdEventType, TestIds } from 'react-native-google-mobile-ads';

const API = 'https://world.openfoodfacts.org/api/v2/product/';
const ADS_ENABLED = Constants.expoConfig?.extra?.buildVariant === 'ads-test';
const BACKEND_URL = String(Constants.expoConfig?.extra?.productApiBaseUrl || '').replace(/\/$/, '');
const BACKEND_ANON_KEY = String(Constants.expoConfig?.extra?.backendAnonKey || '');
const yahooLookup = async (params) => {
  if (!BACKEND_URL) return [];
  const isSupabase = BACKEND_URL.includes('/functions/v1/halal-product-lookup');
  const url = BACKEND_URL + (isSupabase ? '' : '/api/yahoo-product') + '?' + Object.entries(params).map(([key,value])=>encodeURIComponent(key)+'='+encodeURIComponent(String(value))).join('&');
  const response = await fetch(url, {headers: isSupabase && BACKEND_ANON_KEY ? {apikey:BACKEND_ANON_KEY,Authorization:'Bearer '+BACKEND_ANON_KEY} : {}});
  if (!response.ok) throw new Error('Product backend HTTP ' + response.status);
  const data = await response.json();
  return Array.isArray(data.products) ? data.products : [];
};

// Google test interstitial only until a production ad configuration is verified.
const interstitial = ADS_ENABLED ? InterstitialAd.createForAdRequest(TestIds.INTERSTITIAL) : null;
const CACHE_PREFIX = 'halalchecker:product:';
// Online-first: always request current data. A previous record is never treated as live.
const CACHE_AGE_MS = 0;
const risky = [
  { pattern: /pork|porcine|lard|bacon|豚肉|豚脂|ラード|ポーク|猪肉/i, label: 'Pork / porcine ingredient' },
  { pattern: /gelatin|gelatine|ゼラチン|collagen|コラーゲン/i, label: 'Gelatin or collagen: check source' },
  { pattern: /alcohol|ethanol|wine|rum|mirin|sake|アルコール|みりん|酒精|料理酒/i, label: 'Alcohol-related ingredient: verify details' },
  { pattern: /emulsifier|glycerin|enzymes|flavou?r|乳化剤|グリセリン|酵素|香料/i, label: 'Source-dependent ingredient: verify with manufacturer' },
];
const strings = {
  en: { title:'Japan Halal Checker', intro:'Scan a Japanese barcode to review ingredients.', scan:'Scan barcode', manual:'Enter barcode', check:'Check product', back:'Back', camera:'Camera permission is needed to scan barcodes.', grant:'Allow camera', loading:'Looking up product…', missing:'No reliable product record found. Check the package and manufacturer.', warning:'Ingredient guidance only — not halal certification.', concerns:'Ingredients to verify', none:'No flagged terms found. This does not confirm halal status.', ingredients:'Ingredients', retry:'Try again', error:'Could not fetch product. Check your connection.' },
  bn: { title:'জাপান হালাল চেকার', intro:'জাপানের খাবারের বারকোড স্ক্যান করে উপাদান যাচাই করো।', scan:'বারকোড স্ক্যান', manual:'বারকোড নম্বর', check:'পণ্য দেখো', back:'ফিরে যাও', camera:'স্ক্যান করতে ক্যামেরার অনুমতি দরকার।', grant:'ক্যামেরা অনুমতি', loading:'পণ্যের তথ্য খোঁজা হচ্ছে…', missing:'পণ্যের নির্ভরযোগ্য তথ্য নেই। প্যাকেট ও প্রস্তুতকারকের কাছে যাচাই করো।', warning:'শুধু উপাদান যাচাই — হালাল সার্টিফিকেট নয়।', concerns:'যা যাচাই করতে হবে', none:'চিহ্নিত শব্দ পাওয়া যায়নি। এতে হালাল নিশ্চিত হয় না।', ingredients:'উপাদান', retry:'আবার চেষ্টা', error:'তথ্য পাওয়া যায়নি। ইন্টারনেট পরীক্ষা করো।' },
  ja: { title:'日本ハラールチェッカー', intro:'バーコードを読み取り、原材料を確認します。', scan:'バーコードをスキャン', manual:'バーコード番号', check:'商品を確認', back:'戻る', camera:'スキャンにはカメラの許可が必要です。', grant:'カメラを許可', loading:'商品を検索中…', missing:'信頼できる商品情報がありません。表示やメーカーに確認してください。', warning:'原材料の参考情報です。ハラール認証ではありません。', concerns:'確認が必要な原材料', none:'注意キーワードは見つかりませんでした。ハラールを保証しません。', ingredients:'原材料', retry:'再試行', error:'商品情報を取得できません。通信状態を確認してください。' }
,
  ur: { title:'جاپان حلال چیکر', intro:'بارکوڈ اسکین کر کے اجزاء دیکھیں۔', scan:'بارکوڈ اسکین کریں', manual:'بارکوڈ درج کریں', check:'مصنوعات چیک کریں', back:'واپس', camera:'کیمرے کی اجازت درکار ہے۔', grant:'کیمرے کی اجازت دیں', loading:'مصنوعات تلاش ہو رہی ہیں…', missing:'قابل اعتماد معلومات نہیں ملیں۔', warning:'یہ حلال سرٹیفیکیشن نہیں ہے۔', concerns:'جانچنے والے اجزاء', none:'کوئی مشتبہ لفظ نہیں ملا؛ حلال ہونے کی تصدیق نہیں۔', ingredients:'اجزاء', retry:'دوبارہ کوشش کریں', error:'معلومات حاصل نہیں ہو سکیں۔' },
  id: { title:'Pemeriksa Halal Jepang', intro:'Pindai kode batang untuk memeriksa bahan.', scan:'Pindai kode batang', manual:'Masukkan kode batang', check:'Periksa produk', back:'Kembali', camera:'Izin kamera diperlukan.', grant:'Izinkan kamera', loading:'Mencari produk…', missing:'Data produk tepercaya tidak ditemukan.', warning:'Panduan bahan saja, bukan sertifikasi halal.', concerns:'Bahan yang perlu diperiksa', none:'Tidak ada bahan yang ditandai; bukan jaminan halal.', ingredients:'Bahan', retry:'Coba lagi', error:'Gagal mengambil data produk.' },
  ms: { title:'Pemeriksa Halal Jepun', intro:'Imbas kod bar untuk menyemak ramuan.', scan:'Imbas kod bar', manual:'Masukkan kod bar', check:'Semak produk', back:'Kembali', camera:'Kebenaran kamera diperlukan.', grant:'Benarkan kamera', loading:'Mencari produk…', missing:'Maklumat produk yang dipercayai tidak ditemui.', warning:'Panduan ramuan sahaja, bukan pensijilan halal.', concerns:'Ramuan untuk disemak', none:'Tiada istilah dikesan; status halal belum disahkan.', ingredients:'Ramuan', retry:'Cuba lagi', error:'Gagal mendapatkan maklumat.' },
  fa: { title:'بررسی حلال ژاپن', intro:'برای بررسی مواد تشکیل‌دهنده بارکد را اسکن کنید.', scan:'اسکن بارکد', manual:'ورود بارکد', check:'بررسی محصول', back:'بازگشت', camera:'اجازه دوربین لازم است.', grant:'اجازه دوربین', loading:'در حال جستجوی محصول…', missing:'اطلاعات معتبر محصول پیدا نشد.', warning:'فقط راهنمای مواد؛ گواهی حلال نیست.', concerns:'مواد نیازمند بررسی', none:'موردی شناسایی نشد؛ حلال بودن تأیید نشده است.', ingredients:'مواد تشکیل‌دهنده', retry:'تلاش مجدد', error:'دریافت اطلاعات ناموفق بود.' },
  ar: { title:'فاحص الحلال في اليابان', intro:'امسح الرمز الشريطي لمراجعة المكونات.', scan:'مسح الرمز الشريطي', manual:'أدخل الرمز الشريطي', check:'فحص المنتج', back:'رجوع', camera:'يلزم إذن الكاميرا.', grant:'السماح بالكاميرا', loading:'جار البحث عن المنتج…', missing:'لم يتم العثور على بيانات موثوقة.', warning:'إرشادات المكونات فقط وليست شهادة حلال.', concerns:'مكونات تحتاج إلى التحقق', none:'لم يتم رصد مكونات محددة؛ هذا لا يؤكد الحلال.', ingredients:'المكونات', retry:'حاول مجددًا', error:'تعذر جلب بيانات المنتج.' },
  uz: { title:'Yaponiya Halol Tekshiruv', intro:'Tarkibni tekshirish uchun shtrix-kodni skanerlang.', scan:'Shtrix-kodni skanerlash', manual:'Shtrix-kodni kiriting', check:'Mahsulotni tekshirish', back:'Orqaga', camera:'Kamera ruxsati kerak.', grant:'Kameraga ruxsat', loading:'Mahsulot qidirilmoqda…', missing:'Ishonchli mahsulot maʼlumoti topilmadi.', warning:'Faqat tarkib bo‘yicha yo‘riqnoma, halol sertifikati emas.', concerns:'Tekshirilishi kerak bo‘lgan tarkib', none:'Belgilangan modda topilmadi; bu halollikni tasdiqlamaydi.', ingredients:'Tarkibi', retry:'Qayta urinish', error:'Maʼlumotni olib bo‘lmadi.' },
};

// Standard JAN/EAN product barcodes do not encode a package-specific expiry date.
// Only accept a visible date read from the actual package, never infer it from a barcode.
const expiryFromLabel=(value)=>{
  const text=String(value||'');
  const labelled=text.match(/(?:賞味期限|消費期限|best\s*before|use\s*by|expiry|exp\.?)[^\d]{0,12}(20\d{2})[\/.\-年](\d{1,2})[\/.\-月](\d{1,2})/i);
  if(!labelled)return null;
  const year=Number(labelled[1]),month=Number(labelled[2]),day=Number(labelled[3]);
  const date=new Date(year,month-1,day);
  if(date.getFullYear()!==year||date.getMonth()!==month-1||date.getDate()!==day)return null;
  const today=new Date();today.setHours(0,0,0,0);
  const days=Math.round((date.getTime()-today.getTime())/86400000);
  return {date:`${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`,days,type:/消費期限|use\s*by/i.test(labelled[0])?'Use by / 消費期限':'Best before / 賞味期限'};
};

export default function App() {
  const [lang,setLang]=useState('bn');
  const [barcode,setBarcode]=useState('');
  const [query,setQuery]=useState('');
  const [store,setStore]=useState('all');
  const [results,setResults]=useState([]);
  const [searching,setSearching]=useState(false);
  const adReady=useRef(false);
  React.useEffect(()=>{
    if(!interstitial)return;
    const unsubLoaded=interstitial.addAdEventListener(AdEventType.LOADED,()=>{adReady.current=true;});
    const unsubClosed=interstitial.addAdEventListener(AdEventType.CLOSED,()=>{adReady.current=false;interstitial.load();});
    const unsubError=interstitial.addAdEventListener(AdEventType.ERROR,()=>{adReady.current=false;});
    interstitial.load();
    return ()=>{unsubLoaded();unsubClosed();unsubError();};
  },[]);
  const showTestAd=()=>{if(interstitial&&adReady.current){adReady.current=false;interstitial.show().catch(()=>{});}};
  const searchProducts=async()=>{
    const term=query.trim();if(term.length<2){setError('Enter at least 2 characters.');return;}
    setSearching(true);setResults([]);setError('');
    try{
      // Store names are search hints, not evidence of a product's actual retailer.
      const hint=store==='gyomu'?'業務スーパー ':store==='seven'?'セブンイレブン ':store==='family'?'ファミリーマート ':store==='lawson'?'ローソン ':'';
      const url='https://world.openfoodfacts.org/cgi/search.pl?search_terms='+encodeURIComponent(hint+term)+'&search_simple=1&action=process&json=1&page_size=30&fields=code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja';
      const response=await fetch(url);
      if(!response.ok)throw Error('HTTP '+response.status);
      const data=await response.json();
      let items=(data.products||[]).filter(p=>p.product_name||p.product_name_ja).map(p=>({code:p.code,name:p.product_name_ja||p.product_name,brand:p.brands||'',ingredients:p.ingredients_text_ja||p.ingredients_text||'',source:'Open Food Facts',storeVerified:false}));
      if(BACKEND_URL){try{const yahoo=await yahooLookup(store==='all'?{query:term}:{query:term,source:'stores',store});const known=new Set(items.map(p=>p.code));items=[...items,...yahoo.filter(p=>(p.product_name||p.name)&&(!p.code||!known.has(p.code))).map(p=>({code:p.code||'',name:p.product_name||p.name,brand:p.brands||'',ingredients:p.ingredients_text||'',source:p._source||'Store / Yahoo product metadata',storeVerified:false,sourceUrl:p._sourceUrl||'',savedRecord:!!p._savedRecord}))];}catch(_){/* OFF results remain usable if backend unavailable */}}
      setResults(items);
      if(!items.length)setError('No matching product found in Open Food Facts. This does not mean the store does not sell it. Try searching without a store filter.');
      else showTestAd();
    }catch(e){setError('Search unavailable. Check internet and try again.');}
    finally{setSearching(false);}
  };
  const [scanning,setScanning]=useState(false);
  const [loading,setLoading]=useState(false);
  const [product,setProduct]=useState(null);
  const [fromCache,setFromCache]=useState(false);
  const [photoText,setPhotoText]=useState('');
  const [photoBusy,setPhotoBusy]=useState(false);
  const [error,setError]=useState('');
  const [permission,requestPermission]=useCameraPermissions();
  const lock=useRef(false);
  const t=strings[lang];
  const lookup=async (raw)=>{
    const code=String(raw||'').replace(/\s/g,'');
    if(!/^(\d{8}|\d{12,14})$/.test(code)){lock.current=false;setError('Enter a valid EAN-8, UPC or JAN/EAN-13 barcode.');return;}
    lock.current=true;setScanning(false);setBarcode(code);setLoading(true);setError('');setProduct(null);setFromCache(false);
    try{
      const cached = await AsyncStorage.getItem(CACHE_PREFIX+code);
      // Cached records are intentionally not returned as current product data.
      const response=await fetch(API+encodeURIComponent(code)+'.json?fields=code,product_name,product_name_en,product_name_ja,brands,ingredients_text,ingredients_text_en,ingredients_text_ja,last_modified_t,labels_tags,countries_tags',{headers:{'User-Agent':'JapanHalalChecker/1.1 (https://github.com/Mr04Nazmul/Halal-japan)'}});
      if(!response.ok)throw Error('HTTP '+response.status);
      const data=await response.json();
      const p=data.product;
      if(!p || data.status===0 || !(p.product_name||p.product_name_en||p.product_name_ja||p.ingredients_text||p.ingredients_text_ja)){if(BACKEND_URL){try{let matches=[];if(code.startsWith('490177')){try{matches=await yahooLookup({jan_code:code,source:'suntory'});}catch(_){}}if(!matches.length)matches=await yahooLookup({jan_code:code});const y=matches.find(x=>x.code===code);if(y){const ing=y.ingredients_text||'';setProduct({name:y.product_name||'Product',brand:y.brands||'',ingredients:ing,code,source:y._source||'Manufacturer / Yahoo product metadata',sourceUrl:y._sourceUrl||'',updated:null,flags:risky.filter(x=>x.pattern.test(ing)).map(x=>x.label)});return;}}catch(_){}}setError(t.missing);return;}
      const ingredients=p.ingredients_text_ja||p.ingredients_text||p.ingredients_text_en||'';
      const found={name:p.product_name_ja||p.product_name||p.product_name_en||'Product',brand:p.brands||'',ingredients,code,source:'Open Food Facts',updated:p.last_modified_t||null,flags:risky.filter(x=>x.pattern.test(ingredients)).map(x=>x.label)};
      setProduct(found);
      showTestAd();
      // Online-only: do not persist product lookup results as current information.
    }catch(e){setError(t.error);}finally{setLoading(false);lock.current=false;}
  };
  const captureIngredients=async()=>{
    setError('');
    try{
      const perm=await ImagePicker.requestCameraPermissionsAsync();
      if(!perm.granted){setError(t.camera);return;}
      const photo=await ImagePicker.launchCameraAsync({mediaTypes:['images'],quality:0.9,allowsEditing:false});
      if(photo.canceled||!photo.assets?.[0]?.uri)return;
      setPhotoBusy(true);
      const recognized=await TextRecognition.recognize(photo.assets[0].uri);
      const extracted=(recognized.text||'').trim();
      if(!extracted){setError('No readable text found. Retake the photo in good light.');return;}
      setPhotoText(extracted);
    }catch(_){setError('Photo text recognition failed. Please retry or type the ingredients manually.');}
    finally{setPhotoBusy(false);}
  };
  const expiry=expiryFromLabel(photoText);
  const photoFlags=risky.filter(x=>x.pattern.test(photoText)).map(x=>x.label);
  const onScan=({data})=>{if(!lock.current){lock.current=true;lookup(data);}};
  const openScanner=async()=>{
    setError('');setProduct(null);
    if(!permission?.granted){const p=await requestPermission();if(!p.granted){setError(t.camera);return;}}
    lock.current=false;setScanning(true);
  };
  return <SafeAreaView style={s.root}><StatusBar barStyle="light-content" backgroundColor="#0c382b"/><ScrollView contentContainerStyle={s.container} keyboardShouldPersistTaps="handled">
    <Text style={s.brand}>☪  {t.title}</Text>
    <View style={s.languages}>{['bn','ja','en','ur','ar','fa','uz','id','ms'].map(l=><Pressable key={l} onPress={()=>setLang(l)} style={[s.lang,lang===l&&s.selected]}><Text style={{color:lang===l?'#0c382b':'#e2f0e5',fontWeight:'700'}}>{({bn:'বাংলা',ja:'日本語',en:'English',ur:'اردو',ar:'العربية',fa:'فارسی',uz:'O‘zbek',id:'Indonesia',ms:'Melayu'})[l]}</Text></Pressable>)}</View>
    <Text style={s.intro}>{t.intro}</Text>
    {scanning ? <View><View style={s.cameraFrame}><CameraView style={s.camera} facing="back" barcodeScannerSettings={{barcodeTypes:['ean13','ean8','upc_a','upc_e']}} onBarcodeScanned={onScan}/></View><Pressable style={s.button} onPress={()=>setScanning(false)}><Text style={s.buttonText}>{t.back}</Text></Pressable></View> : <Pressable style={s.button} onPress={openScanner}><Text style={s.buttonText}>▦  {t.scan}</Text></Pressable>}
    <View style={s.card}>
      <Text style={s.heading}>🔎 Product search / 商品検索</Text>
      <Text style={s.muted}>Search Japanese product names. Store names are search hints only. No store stock, ingredients, or halal certification is verified by these results.</Text>
      <View style={{flexDirection:'row',flexWrap:'wrap',gap:6,marginVertical:12}}>{[['all','All'],['seven','7-Eleven'],['family','FamilyMart'],['lawson','Lawson'],['gyomu','業務スーパー']].map(([id,name])=><Pressable key={id} onPress={()=>setStore(id)} style={[s.lang,{backgroundColor:store===id?'#c9f36a':'#0c382b'}]}><Text style={{color:store===id?'#0c382b':'white'}}>{name}</Text></Pressable>)}</View>
      <TextInput value={query} onChangeText={setQuery} placeholder="商品名 / Product name" style={s.input}/>
      <Pressable style={s.button} onPress={searchProducts} disabled={searching}><Text style={s.buttonText}>{searching?'Searching…':'Search products'}</Text></Pressable>
      {results.map((p,i)=><Pressable key={p.code||i} onPress={()=>{if(p.code)lookup(p.code);else{setProduct({name:p.name,brand:p.brand,code:'',ingredients:p.ingredients,source:p.source,flags:risky.filter(x=>x.pattern.test(p.ingredients)).map(x=>x.label),sourceUrl:p.sourceUrl});setError('Catalogue listing only: no barcode to confirm this specific package.');}}} style={{paddingVertical:12,borderBottomWidth:1,borderColor:'#dfe8de'}}><Text style={s.heading}>{p.name}</Text><Text style={s.muted}>{p.brand} · {p.code||'No barcode'}</Text><Text style={s.link}>{p.code?'Check barcode details →':'View catalogue details (barcode unavailable) →'}</Text></Pressable>)}
    </View>
    <Text style={s.label}>{t.manual}</Text>
    <TextInput value={barcode} onChangeText={setBarcode} keyboardType="number-pad" placeholder="4901234567894" style={s.input} accessibilityLabel={t.manual}/>
    <Pressable style={s.button} onPress={()=>lookup(barcode)} disabled={loading}><Text style={s.buttonText}>{t.check}</Text></Pressable>
    <View style={s.card}>
      <Text style={s.heading}>📷 Ingredient label photo / 原材料名</Text>
      <Text style={s.muted}>On-device OCR reads packaging text. Confirm the recognized text against the original label; OCR can make mistakes.</Text>
      <Pressable style={s.button} onPress={captureIngredients} disabled={photoBusy}><Text style={s.buttonText}>{photoBusy?'Reading text…':'Photograph ingredients'}</Text></Pressable>
      <TextInput multiline value={photoText} onChangeText={setPhotoText} placeholder="Recognized ingredients / 原材料名 (editable)" style={[s.input,{minHeight:100,marginTop:12,textAlignVertical:'top'}]}/>
      {!!photoText&&<><Text style={s.heading}>📅 Expiry label check / 期限確認</Text>{expiry?<Text style={expiry.days<0?s.flag:s.body}>{expiry.type}: {expiry.date} · {expiry.days<0?'Date passed':expiry.days===0?'Date is today':expiry.days+' days remaining'} (verify printed label)</Text>:<Text style={s.muted}>No full labelled expiry date detected. Photograph the printed 賞味期限 / 消費期限 and check manually; barcode alone cannot reveal it.</Text>}<Text style={s.heading}>Ingredient review — not certification</Text>{photoFlags.length?photoFlags.map(f=><Text style={s.flag} key={f}>⚠ {f}</Text>):<Text style={s.body}>{t.none}</Text>}</>}
    </View>
    {loading&&<ActivityIndicator style={{marginTop:20}} color="#0c382b" size="large"/>}
    {!!error&&<View style={s.card}><Text style={s.error}>{error}</Text><Pressable onPress={()=>lookup(barcode)}><Text style={s.link}>{t.retry}</Text></Pressable></View>}
    {product&&<View style={s.card}><Text style={s.heading}>{product.name}</Text><Text style={s.muted}>{product.brand} · {product.code}</Text>{fromCache&&<Text style={s.muted}>Saved product record (up to 7 days old) · Open Food Facts</Text>}<Text style={s.muted}>Source: {product.source||'Open Food Facts'}{product.updated?' · Updated: '+new Date(product.updated*1000).toLocaleDateString():''}</Text><Text style={s.heading}>{t.ingredients}</Text><Text style={s.body}>{product.ingredients||t.missing}</Text><Text style={s.heading}>{t.concerns}</Text>{!product.ingredients?<Text style={s.flag}>⚠ Ingredients not available — verification required.</Text>:product.flags.length?product.flags.map(f=><Text key={f} style={s.flag}>⚠ {f}</Text>):<Text style={s.body}>{t.none}</Text>}{/suntory|サントリー/i.test((product.brand||'')+' '+(product.name||''))&&<Pressable onPress={()=>Linking.openURL('https://products.suntory.co.jp/d/'+encodeURIComponent(product.code)+'/')}><Text style={s.link}>Suntory official product ingredients ↗ (check barcode and current label)</Text></Pressable>}{!!product.sourceUrl&&<Pressable onPress={()=>Linking.openURL(product.sourceUrl)}><Text style={s.link}>Original product source ↗</Text></Pressable>}{!!product.code&&<Pressable onPress={()=>Linking.openURL('https://world.openfoodfacts.org/product/'+encodeURIComponent(product.code))}><Text style={s.link}>Open Food Facts ↗</Text></Pressable></View>}
    <View style={s.notice}><Text style={s.noticeText}>⚠ {t.warning}</Text><Text style={s.muted}>Open Food Facts data is voluntarily contributed and may be inaccurate, incomplete or unreliable. Store catalogues and manufacturer pages can also change. Check the actual package, ingredient origins and halal certification before deciding.</Text><Pressable onPress={()=>Linking.openURL('https://opendatacommons.org/licenses/odbl/1-0/')}><Text style={s.link}>Open Database License (ODbL) ↗</Text></Pressable></View>
  </ScrollView></SafeAreaView>;
}
const s=StyleSheet.create({root:{flex:1,backgroundColor:'#f4f8f3'},container:{padding:18,paddingBottom:45},brand:{backgroundColor:'#0c382b',color:'white',fontSize:23,fontWeight:'800',padding:20,borderTopLeftRadius:18,borderTopRightRadius:18},languages:{flexDirection:'row',flexWrap:'wrap',backgroundColor:'#0c382b',padding:12,borderBottomLeftRadius:18,borderBottomRightRadius:18,gap:8},lang:{padding:9,borderRadius:9,borderWidth:1,borderColor:'#527362'},selected:{backgroundColor:'#c9f36a'},intro:{fontSize:17,color:'#243b2c',marginVertical:19},button:{backgroundColor:'#0c382b',padding:15,borderRadius:12,marginTop:12,alignItems:'center'},buttonText:{color:'white',fontWeight:'800',fontSize:16},label:{fontWeight:'700',color:'#0c382b',marginTop:22,marginBottom:8},input:{borderWidth:1,borderColor:'#bfd2c2',backgroundColor:'white',borderRadius:12,padding:14,fontSize:17},cameraFrame:{height:290,overflow:'hidden',borderRadius:16},camera:{flex:1},card:{backgroundColor:'white',borderRadius:15,padding:17,marginTop:18,borderWidth:1,borderColor:'#dfe8de'},heading:{fontSize:18,fontWeight:'800',marginTop:12,marginBottom:8,color:'#0c382b'},muted:{color:'#63756c',marginTop:7},body:{fontSize:15,lineHeight:23},error:{color:'#a33020'},flag:{color:'#953b16',paddingVertical:4},link:{color:'#12673e',fontWeight:'700',marginTop:15},notice:{padding:17,backgroundColor:'#fff5d8',borderRadius:13,marginTop:18},noticeText:{fontWeight:'800',color:'#775b19'}});
