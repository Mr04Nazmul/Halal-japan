/* Source-of-truth tests for the live Floot scanner ingredient decision helper.
   Run after: cd floot-source && npm install && node --test tests/ingredientDecision.test.cjs */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const ts=require('typescript');
const source=fs.readFileSync(path.join(__dirname,'../helpers/ingredientDecision.tsx'),'utf8');
const js=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
const sandbox={exports:{}};
vm.runInNewContext(js,sandbox);
const decide=sandbox.exports.ingredientDecision;
assert.equal(typeof decide,'function');

const checks=[
 ['豚肉、しょうゆ','haram_ingredient'],
 ['ポークエキス、食塩','haram_ingredient'],
 ['豚骨スープ、小麦','haram_ingredient'],
 ['pork fat, rice','haram_ingredient'],
 ['lard, wheat flour','haram_ingredient'],
 ['ゼラチン、砂糖','haram_ingredient'],
 ['gelatin, sugar','haram_ingredient'],
 ['本みりん、醤油','haram_ingredient'],
 ['料理酒、砂糖','haram_ingredient'],
 ['米、豚肉不使用','needs_review'],
 ['小麦粉、ポークエキス不使用','needs_review'],
 ['小麦粉、ゼラチン不使用','needs_review'],
 ['no pork, rice and wheat','needs_review'],
 ['rice, gelatin-free','needs_review'],
 ['アルコールフリー、砂糖','needs_review'],
 ['ノンアルコール、ぶどう果汁','needs_review'],
 ['豚肉不使用、豚脂','haram_ingredient'],
 ['乳化剤、砂糖','needs_review'],
 ['香料、食塩','needs_review'],
 ['鶏肉、食塩','needs_review'],
 ['チキンエキス、砂糖','needs_review'],
 ['酒精、砂糖','needs_review'],
 ['大豆由来乳化剤、砂糖','needs_review'],
 ['乳化剤(大豆由来)、砂糖','needs_review'],
 ['無添加、豚肉不使用','unknown'],
 ['', 'unknown'],
 ['HALAL','unknown'],
 ['serum powder, salt','needs_review'],
 ['本製品の製造工場では豚肉を使用する製品を製造しています。 原材料名:米、塩','needs_review']
];
for(const [label,expected] of checks)test(label,()=>{const actual=decide(label).verdict;assert.equal(actual,expected);});

test('verified manufacturer complete, no flagged ingredient is ingredient-only clear',()=>{
 const r=decide('米粉、砂糖、食塩',false,true);
 assert.equal(r.verdict,'ingredient_clear');
 assert.ok(r.reasons.join(' ').includes('Not certified'));
});
test('unverified community ingredient list never implies HALAL',()=>{
 assert.equal(decide('米粉、砂糖、食塩',false,false).verdict,'needs_review');
});
test('declared pork overrides claimed certification boolean',()=>{
 assert.equal(decide('豚肉',true,true).verdict,'haram_ingredient');
});
test('confirmed plant emulsifier in an otherwise complete manufacturer label is not uncertain',()=>{
 const r=decide('小麦粉、乳化剤(大豆由来)、食塩',false,true);
 assert.equal(r.verdict,'ingredient_clear');
});
test('unknown flavoring in manufacturer declaration requires verification',()=>{
 assert.equal(decide('米粉、香料',false,true).verdict,'needs_review');
});
test('origin uncertainty does not become a religious certificate',()=>{
 const r=decide('砂糖、乳化剤',false,false);
 assert.equal(r.findings[0].severity,'uncertain');
});
