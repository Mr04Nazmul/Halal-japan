/* Verifies certificate evidence matching; fixtures below are fictional, never published. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ts=require('typescript');
const path=require('node:path');
const raw=fs.readFileSync(path.join(__dirname,'../helpers/verifiedHalalCertificates.tsx'),'utf8');
const js=ts.transpileModule(raw,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.CommonJS}}).outputText;
const sandbox={exports:{},Date,Number,RegExp,Set,String};
vm.runInNewContext(js,sandbox);
const {findVerifiedHalalCertificate:find,isCertificateDisplayCurrent:isCurrent,VERIFIED_HALAL_CERTIFICATES:list}=sandbox.exports;
const now=new Date('2026-10-15T13:00:00Z');
const f={
 barcode:'4902705133099',productNames:['FICTIONAL TEST YOGURT'],brand:'Fictional Example',
 issuer:'Example Test Certification Agency',certificateNumber:'TEST-ONLY-0001',
 validFrom:'2026-07-01',validUntil:'2027-07-01',verifiedAt:'2026-10-01',
 officialVerificationUrl:'https://example.org/fictional-cert',
 scope:'exact_product',reviewStatus:'approved'
};
const get=(changes={},barcode=f.barcode,name=f.productNames[0],brand=f.brand,date=now)=>
 find(barcode,name,brand,date,[{...f,...changes}]);
test('production registry starts empty, no imaginary halal-certified food',()=>{
 assert.equal(list.length,0);
 assert.equal(find(f.barcode,f.productNames[0],f.brand,now),null);
});
test('approved, in-date, issuer checked exact product barcode may qualify',()=>{
 const x=get();
 assert.ok(x);
 assert.equal(x.status,'verified');
 assert.equal(x.certificateNumber,f.certificateNumber);
 assert.ok(isCurrent(x,now));
});
test('pending application is not certified',()=>assert.equal(get({reviewStatus:'pending'}),null));
test('rejected certificate is not certified',()=>assert.equal(get({reviewStatus:'rejected'}),null));
test('wrong brand is not certified',()=>assert.equal(get({},f.barcode,f.productNames[0],'Other Brand'),null));
test('wrong product name is not certified',()=>assert.equal(get({},f.barcode,'Other Food',f.brand),null));
test('wrong barcode is not certified',()=>assert.equal(get({},'4902705131279'),null));
test('invalid GTIN checksum is not certified',()=>assert.equal(get({},'4902705133090'),null));
test('expired document is not certified',()=>assert.equal(get({validUntil:'2026-10-14'}),null));
test('future start is not certified',()=>assert.equal(get({validFrom:'2026-10-16'}),null));
test('stale issuer status recheck >180 days is not certified',()=>assert.equal(get({verifiedAt:'2026-02-01'}),null));
test('future recheck is not certified',()=>assert.equal(get({verifiedAt:'2026-11-01'}),null));
test('invalid issue date is not certified',()=>assert.equal(get({validFrom:'2026-02-31'}),null));
test('no official registry URL is not certified',()=>assert.equal(get({officialVerificationUrl:''}),null));
test('non-HTTPS issuer link is not certified',()=>assert.equal(get({officialVerificationUrl:'http://example.org/fixture'}),null));
test('non-exact certificate scope is not certified',()=>assert.equal(get({scope:'factory'}),null));
test('missing certificate number is not certified',()=>assert.equal(get({certificateNumber:''}),null));
test('missing issuer is not certified',()=>assert.equal(get({issuer:''}),null));
test('only exact manufacturer-reviewed alias is accepted',()=>{
 const x=get({productNames:['TEST A','TEST B']},f.barcode,'TEST B');
 assert.ok(x);assert.equal(x.productName,'TEST B');
 assert.equal(get({productNames:['TEST A','TEST B']},f.barcode,'TEST'),null);
});
test('expired once stored is not displayed as certified',()=>{
 const x=get();assert.ok(x);
 assert.equal(isCurrent(x,new Date('2027-07-02T00:00:00Z')),false);
});
