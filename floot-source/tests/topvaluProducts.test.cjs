const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const ts=require('typescript');
const load=(file,req)=>{const module={exports:{}};vm.runInNewContext(
 ts.transpileModule(fs.readFileSync(path.join(__dirname,'../helpers/'+file),'utf8'),
  {compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText,
 {exports:module.exports,module,require:req||(()=>{throw Error('unexpected require')})});return module.exports;};
const records=load('topvaluProducts.ts').topvaluProducts;
const ecodes=load('reviewedEcodeGuide.ts');
const {ingredientDecision}=load('ingredientDecision.tsx',name=>{
 if(name==='./reviewedEcodeGuide')return ecodes;
 throw Error(name);
});
const validJan=(code)=>{
 if(!/^\d{13}$/.test(code))return false;
 const digits=[...code].map(Number);
 const sum=digits.slice(0,12).reverse().reduce((a,b,i)=>a+b*(i%2===0?3:1),0);
 return (10-sum%10)%10===digits[12];
};
test('11 distinct published official TOPVALU JANs with recorded additive and label evidence',()=>{
 assert.equal(records.length,11);
 assert.equal(new Set(records.map(p=>p.code)).size,11);
 for(const p of records){
  assert.ok(validJan(p.code),'invalid JAN '+p.code);
  assert.equal(p.sourceUrl,'https://www.topvalu.net/items/detail/'+p.code+'/');
  assert.equal(p.brand,'AEON TOPVALU');
  assert.ok(p.ingredients.length>3);
  assert.equal(p.halalCertified,false);
  assert.equal(p.officialOnlineIngredientDeclaration,true);
  assert.equal(p.checkedAt,'2026-10-16');
 }
});
const find=code=>records.find(p=>p.code===code);
const judge=code=>{const p=find(code);return ingredientDecision(
 p.ingredients+(p.additives?'／'+p.additives:''),false,p.officialOnlineIngredientDeclaration);
};
test('pork-containing seasoned nori and gelatin pudding are flagged as prohibited',()=>{
 assert.ok(find('4549414695632').ingredients.includes('豚肉'));
 assert.equal(judge('4549414695632').verdict,'haram_ingredient');
 assert.ok(find('4549414546729').ingredients.includes('ゼラチン'));
 assert.equal(judge('4549414546729').verdict,'haram_ingredient');
});
test('full web-listed simple-source ingredients yield ingredient-only green, never certified',()=>{
 for(const code of ['4549414087208','4549414545142','4902121482184'])
  assert.equal(judge(code).verdict,'ingredient_clear',code);
});
test('unknown emulsifier origins remain CHECK, never automatic halal',()=>{
 assert.equal(judge('4549414662009').verdict,'needs_review');
});
