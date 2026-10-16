/* Test manufacturer-source evidence links, not unlicensed copies of product data. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ts=require('typescript');
function loadTS(file){
 const m={exports:{}};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),
   {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,
  {exports:m.exports,module:m});
 return m.exports;
}
const {ingredientSources,janSourceLinks,validEAN13}=loadTS(path.join(__dirname,'../helpers/ingredientSourceLinks.ts'));
test('all advertised official sources link to distinct public manufacturer/reference destinations',()=>{
 assert.equal(ingredientSources.length,19);
 assert.equal(new Set(ingredientSources.map(s=>s.id)).size,ingredientSources.length);
 for(const s of ingredientSources){
  assert.match(s.url,/^https:\/\//);
  assert.ok(s.description.length>30);
 }
 for(const id of ['topvalu','sevenpremium','meiji','familymart','lawson','openfoodfacts','ksppos','caa','fooddb','mext','halallens','glico','morinaga','kagome','nissin','upcdatabase','nutritionix','openfda','publicapis'])
  assert.ok(ingredientSources.some(s=>s.id===id));
 assert.equal(ingredientSources.find(s=>s.id==='ksppos').evidence,'jan_or_name_only');
 assert.equal(ingredientSources.find(s=>s.id==='fooddb').evidence,'reference_only');
});
test('links only for valid 13 digit JAN barcode and never imply source verified',()=>{
 assert.equal(validEAN13('4549414087208'),true);
 assert.equal(validEAN13('4549414087209'),false);
 assert.equal(validEAN13('2044706200126'),true); // store code can pass checksum, still just a candidate
 assert.equal(validEAN13('4549414087208x'),false);
 const links=janSourceLinks('4549414087208');
 assert.equal(links.length,5);
 assert.ok(links[0].href.endsWith('/product/4549414087208'));
 assert.ok(links[1].href.endsWith('/4549414087208/'));
 assert.ok(links.some(s=>s.kind==='candidate'));
 assert.equal(janSourceLinks('4549414087209').length,0);
 assert.equal(janSourceLinks('https://evil.example/a').length,0);
});
test('scanner page includes source finder without changing the original barcode scanning and OCR components',()=>{
 const p=fs.readFileSync(path.join(__dirname,'../pages/_index.tsx'),'utf8');
 assert.match(p,/IngredientSourceFinder barcode=\{result\?\.code\|\|query\}/);
 assert.match(p,/BrowserMultiFormatReader/);
 assert.match(p,/IngredientOcr/);
 assert.match(p,/IngredientVerification/);
});
