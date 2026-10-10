/* Ingredient checker regression tests. Run: node tests/ingredient-regression.cjs */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
const start=html.indexOf('function halalAssessment('),end=html.indexOf('function halalBadge(',start);
assert.ok(start>=0&&end>start,'assessment function must exist');
const sandbox={};vm.createContext(sandbox);
vm.runInContext(html.slice(start,end)+';this.assess=halalAssessment;',sandbox);
const cases=[
 ['豚肉、しょうゆ','haram'],['ポークエキス','haram'],['pork fat','haram'],
 ['ゼラチン、砂糖','verify'],['乳化剤（大豆由来）','verify'],
 ['香料、食塩','verify'],['水、米、塩','verify'],['','verify'],
 ['HALAL', 'verify']
];
for(const [ingredients,expected] of cases){
 const actual=sandbox.assess(ingredients).status;
 assert.equal(actual,expected,ingredients);
}
assert.match(sandbox.assess('豚肉').reasons.join(' '),/Pork/);
assert.match(sandbox.assess('').reasons.join(' '),/unavailable/);
console.log('PASS: ingredient screening regression cases (not halal certification)');
