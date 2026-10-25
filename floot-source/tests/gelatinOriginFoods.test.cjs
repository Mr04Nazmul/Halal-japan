const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript');
const root=path.resolve(__dirname,'..'),cache=new Map();
function load(file){
 if(cache.has(file))return cache.get(file);
 if(file.endsWith('.json'))return JSON.parse(fs.readFileSync(file,'utf8'));
 const module={exports:{}};cache.set(file,module.exports);
 const js=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
 const req=id=>{if(!id.startsWith('.'))return require(id);const base=path.resolve(path.dirname(file),id);const found=[base,base+'.ts',base+'.tsx',base+'.json'].find(f=>fs.existsSync(f)&&fs.statSync(f).isFile());if(!found)throw Error(id);return load(found);};
 vm.runInNewContext(js,{exports:module.exports,module,require:req,URL,Date,AbortSignal,console,fetch:()=>{throw Error('Reviewed lookup must not use network');}},{filename:file});
 cache.set(file,module.exports);return module.exports;
}
const {gelatinOriginFoods:records}=load(path.join(root,'helpers/gelatinOriginFoods.ts'));
const {postFoodLookup:lookup}=load(path.join(root,'endpoints/food-lookup_POST.schema.ts'));
test('five distinct origin records, two known JANs',()=>{assert.equal(records.length,5);assert.equal(new Set(records.map(p=>p.sourceUrl)).size,5);assert.equal(records.filter(p=>p.code).length,2);});
test('bovine JAN is blocked under app gelatin policy',async()=>{const r=await lookup({query:'4901325301994'});assert.equal(r.verdict,'haram_ingredient');assert.equal(r.certificate,null);assert.ok(r.manufacturerEvidence[0].type.includes('bovine'));});
test('fish JAN is ingredient-clear without invented certificate',async()=>{const r=await lookup({query:'4562385320327'});assert.equal(r.verdict,'ingredient_clear');assert.equal(r.certificate,null);assert.ok(r.manufacturerEvidence[0].type.includes('fish'));});
test('fish collagen jelly still needs additive checks and has no invented JAN',async()=>{const p=records.find(x=>x.ingredientForm==='collagen_peptide_with_gelatin_allergen');const r=await lookup({query:p.name});assert.equal(r.verdict,'needs_review');assert.equal(r.barcode,null);assert.ok(r.findings.some(f=>f.ingredient==='Flavoring origin'));});
test('source evidence is visible in UI',()=>{const s=fs.readFileSync(path.join(root,'pages/_index.tsx'),'utf8');assert.ok(s.includes('Ingredient source evidence'));assert.ok(s.includes('result.manufacturerEvidence.map'));});
