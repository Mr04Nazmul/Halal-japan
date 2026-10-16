/* Exact-source ingredient-label product tests across independent manufacturers.
 * All entries are un-certified, and source webpages can differ from packaging.
 */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ts=require('typescript');
const compile=file=>ts.transpileModule(fs.readFileSync(path.join(__dirname,'../helpers/'+file),'utf8'),
 {compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
const run=(file,requires={})=>{
 const context={exports:{},require:id=>{if(!(id in requires))throw Error('Unexpected '+id);return requires[id]}};
 vm.runInNewContext(compile(file),context);
 return context.exports;
};
const products=run('publicManufacturerFoods.ts').publicManufacturerFoods;
const ecode=run('reviewedEcodeGuide.ts');
const {ingredientDecision}=run('ingredientDecision.tsx',{'./reviewedEcodeGuide':ecode});
const eanOk=code=>{
 if(!/^\d{13}$/.test(code))return false;
 const sum=[...code.slice(0,12)].reverse().reduce((t,n,i)=>t+Number(n)*(i%2===0?3:1),0);
 return (10-sum%10)%10===Number(code[12]);
};
const lookup=code=>products.find(x=>x.code===code);
const decide=code=>{const p=lookup(code);return ingredientDecision(p.ingredients,false,p.ingredientDeclarationOnOfficialPage)};
test('34 unique exact JANs from four independent source domains with full source URL',()=>{
 assert.equal(products.length,34);
 assert.equal(new Set(products.map(x=>x.code)).size,34);
 assert.equal(new Set(products.map(x=>x.brand)).size,4);
 const domainCount=products.reduce((obj,p)=>{const d=new URL(p.sourceUrl).hostname;obj[d]=(obj[d]||0)+1;return obj},{});
 assert.equal(domainCount['www.kagome.co.jp'],11);
 assert.equal(domainCount['www.glico.com'],12);
 assert.equal(domainCount['www.morinaga.co.jp'],6);
 assert.equal(domainCount['www.nissin.com'],5);
 for(const product of products){
  assert.ok(eanOk(product.code),product.code);
  assert.ok(product.ingredients.length>=8,product.code);
  assert.equal(product.checkedAt,'2026-10-16');
  assert.equal(product.halalCertified,false);
  assert.equal(product.checkedCurrentPhysicalPackage,false);
  assert.equal(product.ingredientDeclarationOnOfficialPage,true);
 }
});
test('simple plant-food product web labels can be screened but never certified',()=>{
 for(const code of ['4901306026380','4901306083550','4902888272899']){
  const result=decide(code);
  assert.equal(result.verdict,'ingredient_clear',code+' '+JSON.stringify(result));
 }
});
test('nissin pork-containing foods are caught from the real source labels',()=>{
 for(const code of ['4902105242414','4902105271278','4548779731245','4548779731955','4902105288146']){
  const result=decide(code);
  assert.equal(result.verdict,'haram_ingredient',code+' '+JSON.stringify(result));
  assert.ok(lookup(code).ingredients.match(/(?:豚|ポーク)/),code);
 }
});
test('uncertain additive origins remain CHECK despite full online ingredient text',()=>{
 for(const code of ['4901005009134','4901005005228']){
  const result=decide(code);
  assert.equal(result.verdict,'needs_review',code+' '+JSON.stringify(result));
 }
});
test('main live barcode lookup imports the 34-product source without disturbing pre-existing data sources',()=>{
 const src=fs.readFileSync(path.join(__dirname,'../endpoints/food-lookup_POST.schema.ts'),'utf8');
 assert.ok(src.includes("publicManufacturerFoods.find"));
 assert.ok(src.includes("barcodeEquivalent(p.code,query)"));
 assert.ok(src.includes("ingredientDecision(sourceMatched.ingredients,false"));
 assert.ok(src.includes("topvaluProducts.find"));
 assert.ok(src.includes("yamayoProducts.find"));
 assert.ok(src.includes("lookupSaved(query,isBarcode)"));
});
