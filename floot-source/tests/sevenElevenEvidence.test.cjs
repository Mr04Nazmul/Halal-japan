const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const ts=require('typescript');
const vm=require('node:vm');
const src=fs.readFileSync(require('node:path').join(__dirname,'../helpers/sevenElevenEvidence.ts'),'utf8');
const js=ts.transpileModule(src,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
const sandbox={exports:{}};vm.runInNewContext(js,sandbox);
const guard=sandbox.exports.guardSevenElevenVerdict;
function item(overrides={}) {
 return {found:true,name:'セブンプレミアム ポーク風味',brand:'Seven Premium / セブンプレミアム',
  barcode:'4901990380843',ingredients:'ポークエキス',
  source:'Third-party product-package ingredient transcription; selected excerpts only; NOT manufacturer-confirmed',
  verdict:'haram_ingredient',reasons:['Pork-derived ingredient detected'],confidence:'high',
  findings:[{ingredient:'Pork',severity:'prohibited',reason:'pork'}],certificate:null,...overrides};
}
test('third party reported pork is AVOID/VERIFY, not verified HARAM',()=>{
 const r=guard(item());
 assert.equal(r.verdict,'needs_review');
 assert.equal(r.confidence,'low');
 assert.match(r.reasons.join(' '),/manufacturer\/full-package/);
});
test('absence of forbidden keywords cannot declare Seven food halal',()=>{
 const r=guard(item({ingredients:'米、塩',verdict:'ingredient_clear',source:'7-Eleven Japan official product listing'}));
 assert.equal(r.verdict,'needs_review');
});
test('Seven shop listing without ingredients remains unknown',()=>{
 const r=guard(item({ingredients:null,verdict:'unknown',reasons:['Missing 原材料名']}));
 assert.equal(r.verdict,'unknown');
});
test('issuer-verified exact product certificate remains certified',()=>{
 const r=guard(item({verdict:'certified',certificate:{status:'verified'}}));
 assert.equal(r.verdict,'certified');
});
test('manufacturer-reviewed current complete product label can establish explicit prohibited content',()=>{
 const today=new Date().toISOString().slice(0,10);
 const r=guard(item({source:'7-Eleven Japan label review',manufacturerEvidence:[{
  type:'reviewed_current_complete_package_label',url:'https://www.sej.co.jp/products/example',
  issuer:'Seven-Eleven Japan',reviewedAt:today}]}));
 assert.equal(r.verdict,'haram_ingredient');
});
test('a different brand is unaffected',()=>{
 const r=guard(item({brand:'Meiji',source:'Meiji official',verdict:'ingredient_clear'}));
 assert.equal(r.verdict,'ingredient_clear');
});
