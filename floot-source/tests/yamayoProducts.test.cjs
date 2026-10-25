/* Real producer-supplied JAN / original label checks, no fake halal certificates. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ts=require('typescript');
const compile=file=>{
 const source=fs.readFileSync(path.join(__dirname,'../helpers/'+file),'utf8');
 return ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
};
const food={exports:{}};
vm.runInNewContext(compile('yamayoProducts.ts'),food);
const products=food.exports.yamayoProducts;
const ecode={exports:{}};
vm.runInNewContext(compile('reviewedEcodeGuide.ts'),ecode);
const decision={exports:{},require:n=>{if(n==='./reviewedEcodeGuide')return ecode.exports;throw Error(n)}};
vm.runInNewContext(compile('ingredientDecision.tsx'),decision);
const scan=decision.exports.ingredientDecision;
const checksum=code=>{
 const sum=[...code.slice(0,-1)].reverse().reduce((s,c,i)=>s+Number(c)*(i%2===0?3:1),0);
 return (10-sum%10)%10===Number(code.at(-1));
};
test('exactly five unique manufacturer-supplied valid retail JANs',()=>{
 assert.equal(products.length,5);
 assert.equal(new Set(products.map(x=>x.code)).size,5);
 assert.ok(products.every(p=>/^\d{13}$/.test(p.code)&&checksum(p.code)));
 assert.ok(products.every(p=>p.brand==='株式会社ヤマヨ'&&p.ingredientListComplete&&!p.halalCertified));
});
test('four complete original bottled juice labels have ingredient-only clear status',()=>{
 const juices=products.filter(p=>p.code!=='4571310560806');
 assert.equal(juices.length,4);
 for(const p of juices){
  assert.equal(scan(p.ingredients,false,true).verdict,'ingredient_clear',p.code);
  assert.ok(p.sourceUrl?.startsWith('https://'));
 }
});
test('Yamayo Le Lectier gummy gelatin is prohibited under app policy',()=>{
 const g=products.find(x=>x.code==='4571310560806');
 assert.ok(g.ingredients.includes('ゼラチン'));
 assert.equal(scan(g.ingredients,false,true).verdict,'haram_ingredient');
 assert.ok(g.sourceUrl?.includes('product.smts-online.jp'));
});

