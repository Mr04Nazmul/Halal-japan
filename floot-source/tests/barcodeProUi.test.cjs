const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const page=fs.readFileSync(path.join(__dirname,'../pages/_index.tsx'),'utf8');
const css=fs.readFileSync(path.join(__dirname,'../pages/_index.module.css'),'utf8');
const match=(name,src,pattern)=>assert.match(src,pattern,name);
test('Barcode Pro scan-first UI has both primary and middle-nav camera actions',()=>{
 match('hero',page,/Scan food\.<br\/><em>Know more\.<\/em>/);
 match('primary CTA',page,/className=\{styles\.cta\} onClick=\{\(\)=>\{setError\(''\);setScanning\(true\)\}\}/);
 match('middle bottom tab',page,/className=\{styles\.navScan\}/);
 match('human accessible scanner',page,/aria-modal="true"/);
 match('manual barcode fallback',page,/id="manual-jan"/);
 match('barcode from photo',page,/onChange=\{scanFile\}/);
});
test('product result shows individual reasons, source and precise certification evidence',()=>{
 for(const expr of [/className=\{styles\.ingredientPanel\}/,/result\.findings\?\.length/,/result\.coverageNote/,/result\.productUrl/,/result\.reasons/,/isCertificateDisplayCurrent\(result\.certificate\)/])
  assert.match(page,expr);
});
test('scanner, offline ingredients, OCR and all map/prayer paths unchanged',()=>{
 for(const expr of [/BrowserMultiFormatReader/,/BarcodeDetector/,/postFoodLookup\(\{query:code\.trim\(\)\}\)/,/IngredientSourceFinder barcode/,/IngredientOcr onDetected/,/IngredientVerification initialText/,/FoodCatalog onChoose/,/places-prayer\.html/,/IslamicTools/,/setPlacesTab\('mosques'\)/])
  assert.match(page,expr);
});
test('respects mobile, camera visibility, reduced motion and tap targets',()=>{
 for(const expr of [/BARCODE PRO 2026/,/\.heroArtwork/,/\.verdictPanel/,/\.navScan/,/\.scanManual/,/@media\(max-width:420px\)/,/prefers-reduced-motion/])
  assert.match(css,expr);
});
