const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx=vm.createContext({URL,AbortSignal,process:{env:{}},fetch:()=>{throw Error('unexpected network')},Date,Map});
vm.runInContext(fs.readFileSync('api/yahoo-product.js','utf8').replace('export default async function handler','async function handler'),ctx);
const handler=vm.runInContext('handler',ctx);
function res(){return {code:0,headers:{},setHeader(k,v){this.headers[k]=v},status(s){this.code=s;return this},json(x){this.data=x;return this},end(){return this}}}
async function call(query={},method='GET',origin='https://mr04nazmul.github.io'){const r=res();await handler({method,query,headers:{origin}},r);return r}
(async()=>{
 assert.equal((await call({health:'1'})).code,503);
 assert.equal((await call({jan_code:'bad'})).code,400);
 assert.equal((await call({jan_code:'4900000000000'})).code,503);
 assert.equal((await call({},'POST')).code,405);
 assert.equal((await call({},'OPTIONS')).code,204);
 assert.equal((await call({health:'1'},'GET','https://untrusted.example')).code,403);
 ctx.process.env.YAHOO_CLIENT_ID='test-only';assert.equal((await call({health:'1'})).code,200);
 let count=0;ctx.fetch=async url=>{count++;assert.equal(url.searchParams.get('jan_code'),'4900000000000');return {ok:true,json:async()=>({hits:[{janCode:'04900000000000',name:'Exact match',url:'https://shopping.yahoo.co.jp/item',image:{medium:'https://example.com/image.jpg'}},{janCode:'4900000000001',name:'Wrong product'}]})}};
 const found=await call({jan_code:'4900000000000'});assert.equal(found.code,200);assert.equal(found.data.products.length,1);assert.equal(found.data.products[0].ingredients_text,'');assert.equal(found.data.halalVerified,false);assert.equal(found.headers['Access-Control-Allow-Origin'],'https://mr04nazmul.github.io');
 assert.equal((await call({jan_code:'4900000000000'})).code,200);assert.equal(count,1,'Repeated lookups use cache');
 assert.equal((await call({query:'noodles'})).code,429);
 console.log('PASS: Yahoo configuration, CORS, validation, exact JAN matches, caching and rate guard');
})().catch(e=>{console.error(e);process.exitCode=1});
