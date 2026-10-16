/* Keep the clean Barcode Pro home layout from turning back into a long
 * unrelated research listing. Original data/evidence stays inside lookup.
 */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..');
const page=fs.readFileSync(path.join(root,'pages/_index.tsx'),'utf8');
const css=fs.readFileSync(path.join(root,'pages/_index.module.css'),'utf8');
const lookup=fs.readFileSync(path.join(root,'endpoints/food-lookup_POST.schema.ts'),'utf8');
test('screenshot-identified research panels and endless product references do not render on Home',()=>{
 for(const marker of ['<IngredientSourceFinder','<SevenElevenIngredientResearch','<SevenPremiumIngredientLinks','<SevenElevenOfficialCatalog','<FoodCatalog','7-Eleven Japan · Halal / Haram Check','7-Eleven · Official food sources & product references','All manufacturer sources']){
  assert.ok(!page.includes(marker),'Unexpected noisy Home panel: '+marker);
 }
 assert.match(page,/Scan food\.<br\/><em>Know more\.<\/em>/);
 assert.match(page,/className=\{styles\.navScan\}/);
 assert.match(page,/className=\{styles\.ocrWorkflow\}/);
});
test('barcode camera, image fallback, manual JAN search and source-linked results survive',()=>{
 for(const marker of ['BrowserMultiFormatReader','BarcodeDetector','decodeFromConstraints','onChange={scanFile}','id="manual-jan"','postFoodLookup({query:code.trim()})','className={styles.ingredientPanel}','result.ingredients_text','result.productUrl','result.coverageNote','isCertificateDisplayCurrent(result.certificate)'])
  assert.ok(page.includes(marker),'Missing product check feature '+marker);
});
test('OCR, ingredient verification, restaurant map, prayer and Qibla survive',()=>{
 for(const marker of ['<IngredientOcr onDetected={setOcrText}/>','<IngredientVerification initialText={ocrText}/>','places-prayer.html','setPlacesTab(\'restaurants\')','setPlacesTab(\'mosques\')','Mosques · Prayer · Qibla','<IslamicTools/>'])
  assert.ok(page.includes(marker),'Missing preserved feature '+marker);
});
test('manufacturer-referenced ingredient lookup and underlying data stay present',()=>{
 for(const marker of ['publicManufacturerFoods.find','topvaluProducts.find','yamayoProducts.find','sevenOfficialItems','ingredientDecision('])
  assert.ok(lookup.includes(marker),'Unexpected missing original lookup '+marker);
 for(const filename of ['helpers/publicManufacturerFoods.ts','helpers/topvaluProducts.ts','helpers/ingredientSourceLinks.ts','components/SevenPremiumIngredientLinks.tsx','components/FoodCatalog.tsx'])
  assert.ok(fs.existsSync(path.join(root,filename)),'Underlying data/source deleted '+filename);
});
test('Barcode Pro light design also covers OCR and ingredient verification',()=>{
 for(const marker of ['BARCODE PRO 2026','.ocrWorkflow','.sourceBar','.verdictPanel','.scanManual'])
  assert.ok(css.includes(marker),'Missing responsive design '+marker);
});
