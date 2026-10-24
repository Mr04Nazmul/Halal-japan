const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),ts=require('typescript'),{webcrypto}=require('node:crypto');
const raw=fs.readFileSync(path.resolve(__dirname,'../../supabase/functions/jhc-catalog-lookup/index.ts'),'utf8');
const code=ts.transpileModule(raw,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
const jan='4902777329338',licensed={jan_code:jan,product_name:'Japanese curry',ingredients_ja:'米、食塩',source_url:'https://world.openfoodfacts.org/product/'+jan,evidence:{brand:'Example',source_license:'ODbL-1.0 / DbCL-1.0',market_country:'Japan',obsolete:false}};
const json=x=>new Response(JSON.stringify(x),{headers:{'Content-Type':'application/json'}});
function server(item=licensed,catalogue=null,gate=true){let handler;const calls=[];vm.runInNewContext(code,{Deno:{env:{get:k=>k==='SUPABASE_URL'?'https://example.supabase.co':'TEST-SERVICE-SECRET'},serve:f=>{handler=f}},URL,URLSearchParams,Request,Response,TextEncoder,AbortSignal,crypto:webcrypto,fetch:async(input,options)=>{calls.push([String(input),options]);const u=String(input);if(u.includes('/rpc/'))return json(gate);if(u.includes('/jhc_floot_products'))return json(catalogue?[catalogue]:[]);if(u.includes('/jhc_crawler_ingredient_staging'))return json(item?[item]:[]);throw Error(u);}});return {handler,calls};}
const request=(origin='https://mr04nazmul.github.io')=>new Request('https://edge.example?jan_code='+jan,{headers:{origin}});
test('private licensed Japan data supplies one exact barcode record with attribution',async()=>{const {handler,calls}=server();const r=await handler(request());assert.equal(r.status,200);const body=await r.json();assert.equal(body.record.barcode,jan);assert.match(body.record.evidence_source,/ODbL/);assert.equal(body.bulk_export,false);const url=new URL(calls.find(([u])=>u.includes('jhc_crawler_ingredient_staging'))[0]);assert.equal(url.searchParams.get('evidence->>market_country'),'eq.Japan');assert.equal(url.searchParams.get('limit'),'1');assert.ok(!JSON.stringify(body).includes('TEST-SERVICE-SECRET'));assert.ok(!('evidence' in body.record));});
test('unlicensed or non-Japan rows cannot escape staging',async()=>{for(const evidence of [{...licensed.evidence,source_license:'permission not established'},{...licensed.evidence,market_country:'US'},{...licensed.evidence,obsolete:true}]){const {handler}=server({...licensed,evidence});assert.equal((await (await handler(request())).json()).record,null);}});
test('wrong exact JAN or untrusted source URL is discarded',async()=>{for(const item of [{...licensed,jan_code:'4901777193369'},{...licensed,source_url:'https://example.org/unrelated'}]){const {handler}=server(item);assert.equal((await (await handler(request())).json()).record,null);}});
test('existing ingredient-bearing private catalogue remains preferred',async()=>{const {handler,calls}=server(licensed,{barcode:jan,name:'Existing',ingredients:'砂糖'});const body=await (await handler(request())).json();assert.equal(body.record.name,'Existing');assert.ok(!calls.some(([u])=>u.includes('jhc_crawler_ingredient_staging')));});
test('foreign origins are rejected and persisted rate gate stays in force',async()=>{const a=server();assert.equal((await a.handler(request('https://evil.example'))).status,403);assert.equal(a.calls.length,0);const b=server(licensed,null,false);assert.equal((await b.handler(request())).status,429);assert.equal(b.calls.length,1);});
const parserSandbox={Deno:{env:{get:()=>''},serve:()=>{}},URL,URLSearchParams,Response,TextEncoder,AbortSignal,crypto:webcrypto};
vm.runInNewContext(code,parserSandbox);
const parse=parserSandbox.parseTopvaluDeclaration;
const page=(id,ing='米、食塩',add='')=>'<h1 class="item-detail__name">Example food</h1><dl><dt>JAN：</dt><dd>'+id+'</dd></dl><div class="item-spec"><dl><dt>原材料名</dt><dd>'+ing+'</dd></dl>'+(add?'<dl><dt>添加物</dt><dd>'+add+'</dd></dl>':'')+'<dl><dt>栄養成分</dt><dd>エネルギー 100kcal</dd></dl></div>';
test('official-page parser requires matching on-page JAN and labelled declaration',()=>{
 assert.equal(parse(page(jan),jan).ingredients,'米、食塩');
 assert.equal(parse(page('4901777193369'),jan),null);
 assert.equal(parse('<h1>Marketing</h1>'+page(jan).replace('原材料名','おすすめ'),jan),null);
});
test('unrelated allergy dictionaries and scripts cannot become the ingredient result',()=>{
 const r=parse(page(jan)+'<script>"<dt>原材料名</dt><dd>豚肉</dd>"</script><div>豚肉・ゼラチン</div>',jan);
 assert.equal(r.ingredients,'米、食塩');
});
test('separate additives are included and conflicting label variants rejected',()=>{
 assert.equal(parse(page(jan,'じゃがいも','香料、乳化剤'),jan).ingredients,'じゃがいも／香料、乳化剤');
 assert.equal(parse(page(jan)+'<dl><dt>原材料名</dt><dd>豚肉</dd></dl>',jan),null);
});

test('non-food material declarations are not assessed as food ingredients',()=>{assert.equal(parse(page(jan).replace('エネルギー 100kcal','素材情報'),jan),null);});

const meijiJan='4902705125308',meijiUrl='https://www.meiji.co.jp/products/icecream/'+meijiJan+'.html';
const meijiHtml='<meta property="og:url" content="'+meijiUrl+'"><h1>明治 エッセル スーパーカップ 超バニラ 200ml</h1><table><tr><th scope="row">原材料名</th><td>乳製品、植物油脂、砂糖、卵黄、食塩／香料、アナトー色素</td></tr></table><h2>栄養成分表示</h2><div>アレルギー関連情報 豚肉 ゼラチン</div>';
test('Meiji exact-JAN official label excludes unrelated allergy dictionary',()=>{
 const r=parserSandbox.parseMeijiDeclaration(meijiHtml,meijiJan,meijiUrl);
 assert.equal(r.barcode,meijiJan);assert.equal(r.ingredient_declaration_reviewed,true);
 assert.match(r.ingredients,/香料/);assert.doesNotMatch(r.ingredients,/豚肉|ゼラチン/);
});
test('Meiji rejects wrong identity, maintenance and conflicting ingredient variants',()=>{
 const parse=parserSandbox.parseMeijiDeclaration;
 assert.equal(parse(meijiHtml,jan,meijiUrl),null);
 assert.equal(parse(meijiHtml.replace(meijiUrl,'https://example.org/'),meijiJan,meijiUrl),null);
 assert.equal(parse('<h1>Maintenance</h1>',meijiJan,meijiUrl),null);
 assert.equal(parse(meijiHtml+'<th>原材料名</th><td>豚肉</td>',meijiJan,meijiUrl),null);
});
test('Meiji research fetches official label without any database discovery record',async()=>{
 const calls=[];parserSandbox.fetch=async(u)=>{calls.push(u);return u===meijiUrl?new Response(meijiHtml,{headers:{'content-type':'text/html'}}):new Response('',{status:404});};
 const r=await parserSandbox.researchMeijiBarcode(meijiJan);
 assert.equal(r.evidence_url,meijiUrl);assert.equal(calls.length,2);
 calls.length=0;assert.equal(await parserSandbox.researchMeijiBarcode('https://evil.example/'),null);assert.equal(calls.length,0);
});
