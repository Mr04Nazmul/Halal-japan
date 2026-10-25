const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
const root=path.resolve(__dirname,'..');
function load(file,fetcher,cache=new Map()){
 if(cache.has(file))return cache.get(file);
 if(file.endsWith('.json'))return JSON.parse(fs.readFileSync(file,'utf8'));
 const module={exports:{}};cache.set(file,module.exports);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
 const req=id=>{if(!id.startsWith('.'))return require(id);const b=path.resolve(path.dirname(file),id);const f=[b,b+'.ts',b+'.tsx',b+'.json'].find(f=>fs.existsSync(f)&&fs.statSync(f).isFile());return load(f,fetcher,cache);};
 vm.runInNewContext(code,{exports:module.exports,module,require:req,fetch:fetcher,URL,AbortSignal,Date,console,setTimeout,clearTimeout},{filename:file});
 return module.exports;
}
const json=(x,status=200)=>new Response(JSON.stringify(x),{status,headers:{'content-type':'application/json'}});
const CODE='4902777329338';
function fixtures(official=null,catalog=true){return async input=>{const u=String(input);if(u.includes('halal-product-lookup'))return json(official||{products:[],ingredientsVerified:false});if(u.includes('jhc-catalog-lookup'))return json({record:catalog?{barcode:CODE,name:'Community Japanese curry',ingredients:'米、砂糖、食塩',evidence_source:'Open Food Facts Japan (ODbL-1.0 / DbCL-1.0; community-contributed)',evidence_url:'https://world.openfoodfacts.org/product/'+CODE}:null});if(u.includes('openfoodfacts.org/api'))return json({status:0});return json({},404);};}
function lookup(fetcher){return load(path.join(root,'endpoints/food-lookup_POST.schema.ts'),fetcher).postFoodLookup;}
test('barcode-only community ingredients remain un-certified and attributed',async()=>{const r=await lookup(fixtures())({query:CODE});assert.equal(r.found,true);assert.equal(r.barcode,CODE);assert.equal(r.verdict,'needs_review');assert.match(r.coverageNote,/ODbL/);assert.equal(r.certificate,null);});
test('exact-JAN official ingredients win over community snapshot',async()=>{const r=await lookup(fixtures({ingredientsVerified:true,products:[{code:CODE,product_name:'Official item',ingredients_text:'米、食塩',_sourceUrl:'https://example.org/official'}]}))({query:CODE});assert.equal(r.name,'Official item');assert.equal(r.verdict,'ingredient_clear');assert.equal(r.certificate,null);});
test('manufacturer mismatch cannot supply a verdict for the scanned barcode',async()=>{const r=await lookup(fixtures({ingredientsVerified:true,products:[{code:'4901777193369',product_name:'Other item',ingredients_text:'米'}]}))({query:CODE});assert.equal(r.name,'Community Japanese curry');});
test('identity-only manufacturer response is not a verified label',async()=>{const r=await lookup(fixtures({ingredientsVerified:false,products:[{code:CODE,ingredients_text:'米'}]}))({query:CODE});assert.equal(r.verdict,'needs_review');});
test('declared non-zero official beverage alcohol stays HARAM',async()=>{const r=await lookup(fixtures({ingredientsVerified:true,products:[{code:CODE,product_name:'Alcoholic drink',ingredients_text:'水、砂糖',_alcoholPercent:3}]}))({query:CODE});assert.equal(r.verdict,'haram_ingredient');});
test('zero alcohol metadata does not produce a prohibited ingredient',async()=>{const r=await lookup(fixtures({ingredientsVerified:true,products:[{code:CODE,ingredients_text:'水、砂糖',_alcoholPercent:0}]}))({query:CODE});assert.equal(r.verdict,'ingredient_clear');});
test('unknown barcode has no invented halal/haram claim or required photo',async()=>{const r=await lookup(fixtures(null,false))({query:CODE});assert.equal(r.found,false);assert.equal(r.verdict,'unknown');const p=fs.readFileSync(path.join(root,'pages/_index.tsx'),'utf8');assert.ok(p.includes('Barcode evidence not yet available'));assert.ok(!p.includes('原材料名-এর ছবি দিন'));assert.ok(p.includes('Optional manual ingredient tools'));});
test('reported Calbee Pizza Potato JAN uses official positive pork evidence before empty metadata',async()=>{
 const r=await lookup(async()=>{throw Error('Curated exact evidence must resolve without a third-party call');})({query:'4901330581985'});
 assert.equal(r.verdict,'haram_ingredient');assert.equal(r.barcode,'4901330581985');
 assert.ok(r.ingredients.includes('豚肉'));assert.match(r.coverageNote,/EXCERPT ONLY/);
 assert.ok(r.manufacturerEvidence.some(x=>x.url.startsWith('https://www.calbee.co.jp/')));
 assert.ok(!r.reasons.join(' ').includes('alcohol'));
});
test('retail fallback identifies exact barcode but never treats title as ingredients',async()=>{
 const base=fixtures(null,false);const calls=[];
 const r=await lookup(async input=>{const u=String(input);calls.push(u);if(u.includes('source=yahoo'))return json({source:'Yahoo! Shopping Japan',products:[{code:CODE,product_name:'Rice gelatin free snack',brands:'Example',ingredients_text:'砂糖',image_url:'https://example.org/a.jpg'}]});return base(input);})({query:CODE});
 assert.equal(r.found,true);assert.equal(r.name,'Rice gelatin free snack');assert.equal(r.ingredients,null);assert.equal(r.verdict,'unknown');assert.equal(r.certificate,null);assert.ok(calls.some(u=>u.includes('source=upcitemdb')));
});
test('wrong retail barcode is rejected even with matching-looking title',async()=>{
 const base=fixtures(null,false);
 const r=await lookup(async input=>String(input).includes('source=yahoo')?json({products:[{code:'4901777193369',product_name:'Wrong food'}]}):base(input))({query:CODE});
 assert.equal(r.found,false);assert.equal(r.verdict,'unknown');
});
test('UPC fallback survives unavailable Yahoo and community APIs',async()=>{
 const base=fixtures(null,false);
 const r=await lookup(async input=>{const u=String(input);if(u.includes('source=upcitemdb'))return json({source:'UPCitemdb',products:[{code:CODE,product_name:'Identified snack'}]});if(u.includes('source=yahoo')||u.includes('openfoodfacts.org/api'))throw Error('Offline');return base(input);})({query:CODE});
 assert.equal(r.found,true);assert.equal(r.name,'Identified snack');assert.equal(r.verdict,'unknown');
});
