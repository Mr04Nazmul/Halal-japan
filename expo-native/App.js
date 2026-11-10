import React, { useCallback, useRef, useState } from 'react';
import { ActivityIndicator, Linking, Pressable, SafeAreaView, ScrollView, StatusBar, StyleSheet, Text, TextInput, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { WebView } from 'react-native-webview';

const SITE = 'https://mr04nazmul.github.io/Halal-japan/';
const PAGE = { places: SITE + 'halal-restaurants.html', prayer: SITE + 'places-prayer.html', more: SITE };
const C = { bg:'#091b17', panel:'#102b24', panel2:'#15392f', green:'#b9f477', text:'#f2f8ef', subtle:'#aac4b6', border:'#305347', warning:'#ffd49a', red:'#ffb2a4' };
const I18N = {
  bn:{ scan:'স্ক্যান', search:'খুঁজুন', places:'রেস্টুরেন্ট', prayer:'নামাজ', more:'আরও', title:'জাপান হালাল চেকার', caption:'বারকোড দিয়ে খাবারের উপাদান যাচাই করুন', camera:'ক্যামেরা দিয়ে স্ক্যান', stop:'স্ক্যান বন্ধ', manual:'JAN / EAN বারকোড', submit:'পণ্য যাচাই', name:'পণ্যের নাম লিখুন', lookup:'পণ্য খুঁজুন', permission:'বারকোড স্ক্যান করতে ক্যামেরার অনুমতি দিন।', grant:'ক্যামেরা অনুমতি', ingredients:'উপাদান', uncertain:'নিষিদ্ধ উপাদান শনাক্ত হয়নি—তবু হালাল নিশ্চিত নয়।', check:'উৎস যাচাই প্রয়োজন', avoid:'সতর্কতা: নিষিদ্ধ উপাদানের সম্ভাবনা', missing:'সম্পূর্ণ পণ্যের তথ্য পাওয়া যায়নি। প্যাকেটের উপাদান পরীক্ষা করুন।', offline:'ইন্টারনেট বা তথ্যসেবা পাওয়া যাচ্ছে না। আবার চেষ্টা করুন।', disclaimer:'উপাদান বিশ্লেষণ কোনো হালাল সার্টিফিকেশন নয়। প্রস্তুতকারকের তথ্য ও প্যাকেট যাচাই করুন।', retry:'আবার চেষ্টা', open:'ব্রাউজারে খুলুন', loading:'খোঁজা হচ্ছে...', creator:'তৈরি করেছেন: Hossain Najmul', sources:'তথ্যের উৎস: Open Food Facts এবং বিদ্যমান ওয়েবসাইট', privacy:'কোনো স্ক্যান হিস্ট্রি সার্ভারে পাঠানো হয় না; পণ্যের কোড Open Food Facts-এ সার্চ করা হয়।'},
  en:{ scan:'Scan', search:'Search', places:'Restaurants', prayer:'Prayer', more:'More', title:'Japan Halal Checker', caption:'Check food ingredients by Japanese barcode', camera:'Scan with camera', stop:'Close scanner', manual:'JAN / EAN barcode', submit:'Check product', name:'Product name', lookup:'Search products', permission:'Camera access is needed to scan a barcode.', grant:'Allow camera', ingredients:'Ingredients', uncertain:'No flagged ingredients detected — halal status is still unconfirmed.', check:'Ingredient source needs verification', avoid:'Warning: potentially prohibited ingredients', missing:'No complete product record was found. Check the package.', offline:'Cannot reach the product service. Check your internet and retry.', disclaimer:'Ingredient analysis is NOT a halal certification. Verify packaging and manufacturer information.', retry:'Try again', open:'Open in browser', loading:'Looking up...', creator:'Created by Hossain Najmul', sources:'Data: Open Food Facts and the existing website', privacy:'No scan history is uploaded by this app; scanned product codes are queried on Open Food Facts.'},
  ja:{ scan:'スキャン', search:'商品検索', places:'レストラン', prayer:'礼拝', more:'その他', title:'日本ハラールチェッカー', caption:'JANコードで食品の原材料を確認', camera:'カメラでスキャン', stop:'カメラを閉じる', manual:'JAN / EANコード', submit:'商品を確認', name:'商品名を入力', lookup:'検索', permission:'バーコード読取にはカメラの許可が必要です。', grant:'カメラを許可', ingredients:'原材料', uncertain:'注意成分は見つかりませんでしたが、ハラールは未確認です。', check:'原料由来の確認が必要', avoid:'注意：禁止成分の可能性があります', missing:'十分な商品情報がありません。パッケージを確認してください。', offline:'通信に失敗しました。接続を確認して再試行してください。', disclaimer:'原材料判定はハラール認証ではありません。包装表示やメーカー情報を確認してください。', retry:'再試行', open:'ブラウザで開く', loading:'検索中...', creator:'開発者: Hossain Najmul', sources:'データ: Open Food Facts・既存Webサイト', privacy:'スキャン履歴は送信されません。JANコードをOpen Food Factsで検索します。'}
};
const flagRules = [
  { kind:'avoid', match:/pork|porcine|lard|bacon|ham extract|豚肉|豚脂|ラード|ポークエキス/i, reason:'Pork / 豚由来' },
  { kind:'check', match:/gelati[no]e?|collagen|ゼラチン|コラーゲン/i, reason:'Gelatin / collagen origin unknown' },
  { kind:'check', match:/alcohol|ethanol|wine|rum|sake|mirin|アルコール|酒精|みりん|料理酒/i, reason:'Alcohol-related ingredient needs review' },
  { kind:'check', match:/emulsifier|glycerin|enzyme|flavou?r|乳化剤|グリセリン|酵素|香料/i, reason:'Source-dependent additive' }
];
function assess(ingredients) {
  if (!ingredients || !ingredients.trim()) return {kind:'check', reasons:['Ingredient list missing']};
  const reasons = flagRules.filter(r=>r.match.test(ingredients));
  return {kind:reasons.some(r=>r.kind==='avoid')?'avoid':'check', reasons:reasons.map(r=>r.reason)};
}
function validBarcode(s) {
  if (!/^\d{8}$|^\d{12,14}$/.test(s)) return false;
  const digits = [...s].map(Number);
  const last = digits.pop();
  const sum = digits.reverse().reduce((n,d,i)=>n + d*(i%2===0?3:1),0);
  return (10-(sum%10))%10===last;
}
function Chip({children,onPress,selected}) {
  return <Pressable onPress={onPress} style={[styles.chip,selected&&styles.chipSelected]}><Text style={[styles.chipText,selected&&styles.chipTextSelected]}>{children}</Text></Pressable>;
}
function Primary({children,onPress,disabled,outline=false}) {
  return <Pressable onPress={onPress} disabled={disabled} style={[styles.button,outline&&styles.buttonOutline,disabled&&{opacity:.55}]}><Text style={[styles.buttonText,outline&&{color:C.green}]}>{children}</Text></Pressable>;
}
function InfoCard({children}) {return <View style={styles.card}>{children}</View>;}
export default function App() {
  const [tab,setTab] = useState('scan');
  const [lang,setLang] = useState('bn');
  const [barcode,setBarcode] = useState('');
  const [keyword,setKeyword] = useState('');
  const [busy,setBusy] = useState(false);
  const [scanner,setScanner] = useState(false);
  const [flash,setFlash] = useState(false);
  const [error,setError] = useState('');
  const [product,setProduct] = useState(null);
  const [matches,setMatches] = useState([]);
  const lock = useRef(false);
  const [permission,requestPermission] = useCameraPermissions();
  const t=I18N[lang];

  const lookup = useCallback(async value=>{
    const code = String(value || '').replace(/\s+/g,'');
    if(!validBarcode(code)){setScanner(false);lock.current=false;setError('Invalid JAN/EAN/UPC barcode or check digit.');return;}
    setBarcode(code);setBusy(true);setError('');setProduct(null);setScanner(false);
    try{
      const res=await fetch('https://world.openfoodfacts.org/api/v2/product/'+encodeURIComponent(code)+'.json?fields=code,product_name,product_name_ja,brands,ingredients_text,ingredients_text_ja,last_modified_t');
      if(!res.ok) throw new Error('HTTP '+res.status);
      const json=await res.json();
      const p=json.product;
      if(json.status===0 || !p || !(p.product_name||p.product_name_ja||p.ingredients_text||p.ingredients_text_ja)){
        setError(t.missing);return;
      }
      const ingredients=p.ingredients_text_ja||p.ingredients_text||'';
      setProduct({code,name:p.product_name_ja||p.product_name||'Unknown product',brand:p.brands||'',ingredients,source:'Open Food Facts',assessment:assess(ingredients)});
    }catch(e){setError(t.offline);}
    finally{setBusy(false);lock.current=false;}
  },[t]);

  const nameLookup = async()=>{
    if(keyword.trim().length<2){setError('Enter 2 or more characters.');return;}
    setBusy(true);setError('');setMatches([]);setProduct(null);
    try{
      const url='https://world.openfoodfacts.org/cgi/search.pl?search_terms='+encodeURIComponent(keyword.trim())+'&search_simple=1&action=process&json=1&page_size=20&fields=code,product_name,product_name_ja,brands';
      const r=await fetch(url);
      if(!r.ok) throw new Error('HTTP '+r.status);
      const d=await r.json();
      const items=(d.products||[]).filter(p=>p.code&&(p.product_name||p.product_name_ja)).slice(0,20);
      setMatches(items);
      if(!items.length)setError(t.missing);
    }catch(e){setError(t.offline);}
    finally{setBusy(false);}
  };
  const startScan=async()=>{
    setError('');setProduct(null);
    if(!permission?.granted){
      const response=await requestPermission();
      if(!response.granted){setError(t.permission);return;}
    }
    lock.current=false;setScanner(true);
  };
  const scanned=({data})=>{if(lock.current)return;lock.current=true;lookup(data);};
  const open=()=>Linking.openURL(PAGE[tab]||SITE).catch(()=>setError(t.offline));

  return <SafeAreaView style={styles.root}>
    <StatusBar barStyle="light-content" backgroundColor={C.bg}/>
    <View style={styles.header}>
      <Text style={styles.eyebrow}>JAPAN • FOOD SAFETY GUIDE</Text>
      <Text style={styles.title}>{t.title}</Text>
      <Text style={styles.subtitle}>{t.caption}</Text>
    </View>
    {tab==='scan'||tab==='search'?<ScrollView style={{flex:1}} contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
      <View style={styles.langRow}>{['bn','ja','en'].map(x=><Chip key={x} selected={lang===x} onPress={()=>setLang(x)}>{({bn:'বাংলা',ja:'日本語',en:'English'})[x]}</Chip>)}</View>
      {tab==='scan'?<>
        <InfoCard>
          <Text style={styles.cardTitle}>▦  JAN / EAN Barcode</Text>
          <Text style={styles.secondary}>EAN-8 • UPC-A • EAN-13 • GTIN-14</Text>
          {scanner?<View style={styles.scannerBox}>
            <CameraView style={styles.camera} facing="back" enableTorch={flash} barcodeScannerSettings={{barcodeTypes:['ean13','ean8','upc_a','upc_e','itf14']}} onBarcodeScanned={scanned}/>
            <View pointerEvents="none" style={styles.focusBox}/>
          </View>:null}
          {scanner?<View style={styles.row}><Chip selected={flash} onPress={()=>setFlash(x=>!x)}>⚡ Torch</Chip><Chip onPress={()=>setScanner(false)}>{t.stop}</Chip></View>:<Primary onPress={startScan}>{t.camera}</Primary>}
          <Text style={styles.label}>{t.manual}</Text>
          <TextInput style={styles.input} placeholder="4901234567894" placeholderTextColor="#80998d" keyboardType="number-pad" value={barcode} onChangeText={setBarcode} maxLength={14}/>
          <Primary onPress={()=>lookup(barcode)} disabled={busy}>{t.submit}</Primary>
        </InfoCard>
      </>:<InfoCard>
        <Text style={styles.cardTitle}>⌕  {t.search}</Text>
        <TextInput style={styles.input} placeholder={t.name} placeholderTextColor="#80998d" value={keyword} onChangeText={setKeyword} onSubmitEditing={nameLookup}/>
        <Primary disabled={busy} onPress={nameLookup}>{t.lookup}</Primary>
        {matches.map((p,i)=><Pressable key={p.code+'-'+i} onPress={()=>{setTab('scan');lookup(p.code);}} style={styles.resultRow}>
          <Text style={styles.resultName}>{p.product_name_ja||p.product_name}</Text>
          <Text style={styles.secondary}>{p.brands||'—'} • {p.code}</Text>
        </Pressable>)}
      </InfoCard>}
      {busy?<ActivityIndicator size="large" color={C.green} style={{marginTop:18}}/>:null}
      {!!error?<InfoCard><Text style={styles.warn}>⚠ {error}</Text><Primary outline onPress={()=>tab==='scan'?lookup(barcode):nameLookup()}>{t.retry}</Primary></InfoCard>:null}
      {product?<InfoCard>
        <Text style={styles.cardTitle}>{product.name}</Text>
        <Text style={styles.secondary}>{product.brand}  •  {product.code}</Text>
        <View style={styles.status}><Text style={styles.statusText}>{product.assessment.reasons.some(x=>x.includes('Pork'))?t.avoid:product.assessment.reasons.length?t.check:t.uncertain}</Text></View>
        <Text style={styles.sectionTitle}>{t.ingredients}</Text>
        <Text style={styles.body}>{product.ingredients||t.missing}</Text>
        {product.assessment.reasons.map(reason=><Text key={reason} style={styles.warn}>• {reason}</Text>)}
        <Text style={styles.secondary}>Source: {product.source} • Community-maintained; not manufacturer-verified</Text>
        <Primary outline onPress={()=>Linking.openURL('https://world.openfoodfacts.org/product/'+encodeURIComponent(product.code))}>Original record ↗</Primary>
      </InfoCard>:null}
      <InfoCard><Text style={styles.warn}>⚠ {t.disclaimer}</Text><Text style={styles.secondary}>Product not found? The existing web catalogue can be searched from the More tab. Absence of data does not establish halal status.</Text></InfoCard>
    </ScrollView>:<View style={{flex:1}}>
      <WebView key={tab} source={{uri:PAGE[tab]||SITE}} originWhitelist={['https://*']} startInLoadingState renderLoading={()=><ActivityIndicator size="large" color={C.green} style={{marginTop:40}}/>} renderError={()=><View style={styles.webError}><Text style={styles.warn}>{t.offline}</Text><Primary onPress={open}>{t.open}</Primary></View>}/>
      <View style={styles.webFooter}><Text style={styles.secondary}>{tab==='places'?'Restaurant directory (live website)':tab==='prayer'?'Prayer, mosque & Qibla (live website)':t.creator}</Text><Pressable onPress={open}><Text style={styles.webLink}>{t.open} ↗</Text></Pressable></View>
      {tab==='more'?<View style={styles.footerInfo}><Text style={styles.secondary}>{t.creator}</Text><Text style={styles.secondary}>{t.sources}</Text><Text style={styles.secondary}>{t.privacy}</Text></View>:null}
    </View>}
    <View style={styles.tabbar}>{['scan','search','places','prayer','more'].map((key,i)=><Pressable accessibilityRole="tab" accessibilityState={{selected:tab===key}} key={key} onPress={()=>{setTab(key);setError('');setScanner(false);}} style={[styles.tab,tab===key&&styles.activeTab]}><Text style={styles.tabIcon}>{['▦','⌕','♧','☾','☰'][i]}</Text><Text numberOfLines={1} style={[styles.tabLabel,tab===key&&styles.activeLabel]}>{t[key]}</Text></Pressable>)}</View>
  </SafeAreaView>;
}
const styles=StyleSheet.create({
  root:{flex:1,backgroundColor:C.bg},header:{paddingHorizontal:18,paddingTop:18,paddingBottom:13,borderBottomWidth:1,borderColor:C.border},
  eyebrow:{color:C.green,fontSize:10,fontWeight:'900',letterSpacing:1.8},title:{color:C.text,fontSize:25,fontWeight:'900',marginTop:5},subtitle:{color:C.subtle,fontSize:12,marginTop:3},
  scroll:{padding:16,paddingBottom:36},langRow:{flexDirection:'row',gap:9,marginBottom:16},chip:{borderWidth:1,borderColor:C.border,paddingVertical:8,paddingHorizontal:12,borderRadius:99,backgroundColor:C.panel},
  chipSelected:{backgroundColor:C.green,borderColor:C.green},chipText:{fontSize:12,color:C.text,fontWeight:'700'},chipTextSelected:{color:C.bg},
  card:{padding:18,backgroundColor:C.panel,borderWidth:1,borderColor:C.border,borderRadius:19,marginBottom:16},cardTitle:{fontSize:19,fontWeight:'900',color:C.text},
  secondary:{color:C.subtle,fontSize:12,lineHeight:18,marginTop:10},row:{flexDirection:'row',gap:9,marginTop:12},label:{color:C.text,fontSize:13,fontWeight:'800',marginTop:16,marginBottom:9},
  button:{backgroundColor:C.green,borderRadius:12,paddingVertical:13,paddingHorizontal:14,alignItems:'center',marginTop:13},
  buttonOutline:{backgroundColor:'transparent',borderWidth:1,borderColor:C.green},buttonText:{color:C.bg,fontWeight:'900',fontSize:15},
  input:{borderWidth:1,borderColor:C.border,borderRadius:10,color:C.text,paddingHorizontal:13,paddingVertical:12,backgroundColor:C.bg,fontSize:16},
  scannerBox:{height:320,borderRadius:15,overflow:'hidden',marginTop:15,position:'relative'},camera:{flex:1},focusBox:{position:'absolute',top:'20%',left:'9%',width:'82%',height:'60%',borderWidth:2,borderColor:C.green,borderRadius:13},
  resultRow:{borderBottomWidth:1,borderBottomColor:C.border,paddingVertical:13},resultName:{color:C.text,fontWeight:'800',fontSize:15},status:{padding:11,backgroundColor:'#403529',borderRadius:12,marginTop:16},statusText:{color:C.warning,fontWeight:'900'},sectionTitle:{color:C.green,fontWeight:'900',fontSize:15,marginTop:18},
  body:{color:C.text,lineHeight:23,fontSize:14,marginTop:8},warn:{color:C.warning,fontWeight:'700',fontSize:13,lineHeight:20,marginTop:10},
  tabbar:{flexDirection:'row',borderTopWidth:1,borderColor:C.border,backgroundColor:'#091c17',paddingBottom:6,paddingTop:8},tab:{flex:1,alignItems:'center',paddingVertical:7,borderRadius:10},
  activeTab:{backgroundColor:C.panel2},tabIcon:{color:C.green,fontWeight:'900',fontSize:19},tabLabel:{fontSize:10,color:C.subtle,marginTop:4},activeLabel:{color:C.text,fontWeight:'800'},
  webFooter:{backgroundColor:C.panel,paddingHorizontal:18,paddingVertical:8,flexDirection:'row',alignItems:'center',justifyContent:'space-between'},webLink:{color:C.green,fontSize:11,fontWeight:'800'},webError:{padding:20},
  footerInfo:{backgroundColor:C.bg,padding:12}
});
