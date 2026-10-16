/* Barcode Pro design-only regression: user-selected UI cannot delete core features. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..');
const page=fs.readFileSync(path.join(root,'pages/_index.tsx'),'utf8');
const style=fs.readFileSync(path.join(root,'pages/_index.module.css'),'utf8');
test('Barcode Pro scan-first UI has top-level camera action, manual search and product result evidence',()=>{
 for(const marker of [
  'Scan food.<br/><em>Know more.</em>',
  'onClick={()=>{setError(\'\');setScanning(true)}',
  'id="product-lookup"',
  'id="scan-result"',
  "setScanning(false);setView('home');setBusy(true)",
  "getElementById('scan-result')?.scrollIntoView",
  'INGREDIENT SCREENING RESULT',
  'Ingredients <span>原材料名・添加物</span>',
  'DATA SOURCE',
  'Save product',
  'role="dialog" aria-modal="true"',
  'Enter barcode manually',
  'styles.navScan'
 ])assert.ok(page.includes(marker),'Missing '+marker);
});
test('existing scanner, ingredient engine, source evidence and Places remain wired',()=>{
 for(const marker of [
  'BrowserMultiFormatReader',
  'decodeFromConstraints(',
  'BarcodeDetector',
  'decodeFromImageUrl(',
  'postFoodLookup({query:code.trim()})',
  'result.findings',
  'isCertificateDisplayCurrent(',
  '<IngredientOcr onDetected={setOcrText}/>',
  '<IngredientVerification initialText={ocrText}/>',
  '<ReviewedEcodeGuide/>' ,
  'places-prayer.html',
  '<IslamicTools/>',
  'setPlacesTab(\'mosques\')',
  'ResearchSourcesSettings'
 ])assert.ok(page.includes(marker),'Missing '+marker);
 for(const file of ['helpers/ingredientSourceLinks.ts','components/FoodCatalog.tsx','components/SevenElevenIngredientResearch.tsx'])assert.ok(fs.existsSync(path.join(root,file)),'Source preserved '+file);
});
test('mobile layout, visual scan frame and reduced motion accessibility available',()=>{
 for(const marker of ['BARCODE PRO 2026','.heroArtwork','.resultTop','.verdictPanel','.scanBeam','@media(max-width:420px)','@media(prefers-reduced-motion:reduce)','env(safe-area-inset-bottom)'])
  assert.ok(style.includes(marker),'Missing style '+marker);
});
