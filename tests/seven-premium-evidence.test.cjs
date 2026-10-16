const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../data/seven-premium-ingredient-signals-20261016.json'),'utf8'));
const records=data.records;
test('exact online source evidence and no invented JAN',()=>{
 assert.equal(records.length,14);
 assert.equal(new Set(records.map(x=>x.product_page_id)).size,14);
 assert.equal(records.filter(x=>x.official_full_ingredient_list_on_source_page).length,14);
 assert.equal(data.published_online_full_ingredient_lists,14);
 assert.equal(data.package_and_JAN_confirmed_count,0);
 assert.ok(records.every(x=>x.jan===null && x.full_list_in_this_database===false));
 assert.ok(records.every(x=>x.halal_certification==='not_verified'));
 assert.ok(records.every(x=>x.source_url==='https://7premium.jp/product/search/detail?id='+x.product_page_id));
});
test('four explicit pork ingredients and one pork allergen declaration',()=>{
 const explicit=records.filter(x=>x.screening_status==='explicit_pork_ingredient');
 const allergy=records.filter(x=>x.screening_status==='declared_pork_allergen');
 assert.deepEqual(explicit.map(x=>x.product_page_id).sort(),['1088','4757','5053','6054']);
 assert.deepEqual(allergy.map(x=>x.product_page_id),['7220']);
 assert.ok(allergy[0].ingredient_signals_ja.some(s=>s.includes('豚肉')));
 assert.equal(data.explicit_pork_ingredient_count,4);
 assert.equal(data.pork_allergen_declaration_count,1);
 assert.equal(records.filter(x=>x.screening_status==='needs_origin_or_processing_evidence').length,7);
});
test('no claimed halal status or full reprinted labels',()=>{
 assert.ok(records.every(x=>x.ingredient_data_status==='official_full_label_on_linked_page;only_key_facts_stored'));
 assert.ok(records.every(x=>x.verification_scope==='source_online_declaration_only'));
 assert.ok(records.every(x=>typeof x.screening_reason_bn==='string'&&x.screening_reason_bn.length>15));
 assert.equal(data.no_certification_count,14);
});

test('ingredient-based compatible wording does not imply certification',()=>{
 const chips=records.filter(x=>['11641','3096'].includes(x.product_page_id));
 assert.equal(chips.length,2);
 assert.ok(chips.every(x=>x.screening_status==='no_explicit_prohibited_ingredient_on_label'));
 assert.ok(chips.every(x=>x.ingredient_screening_summary_bn.includes('হালাল-সঙ্গত')));
 assert.ok(chips.every(x=>x.halal_certification==='not_verified'));
});
test('additive source questions not invented as manufacturer confirmations',()=>{
 for(const id of ['3331','986']){
  const r=records.find(x=>x.product_page_id===id);
  assert.ok(r.origin_research_status.includes('not_public'));
  assert.ok(r.origin_check_questions_ja.length>=2);
  assert.ok(r.official_pack_image_numeric_candidate_note.includes('NOT independently validated'));
 }
 assert.ok(records.find(x=>x.product_page_id==='3331').related_brand_research.relationship.includes('not established'));
});
