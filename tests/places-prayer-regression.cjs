const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const js=fs.readFileSync('places-prayer.js','utf8');
const html=fs.readFileSync('places-prayer.html','utf8');
const app=fs.readFileSync('index.html','utf8');
const product=fs.readFileSync('product-data.js','utf8');
for(const [name,code] of [['Places/prayer',js],['Product data',product]]){
 new vm.Script(code,{filename:name});
 console.log('PASS JavaScript parses:',name);
}
assert.match(app,/href="\.\/places-prayer\.html"/,'Main site must link to the map');
for(const id of ['map','places','prayerGrid','qiblaDegrees','lang','gps','method','asr','city','radius']){
 assert.match(html,new RegExp('id="'+id+'"'),'Missing element '+id);
}
for(const locale of ['en','bn','ja'])assert.match(js,new RegExp('\\b'+locale+':\\{'),'Missing '+locale+' dictionary');
const start=js.indexOf('function qiblaBearing('),end=js.indexOf('function translate()',start);
assert.ok(start>0&&end>start,'Qibla bearing helper absent');
const context={};vm.createContext(context);
vm.runInContext(js.slice(start,end)+';this.calc=qiblaBearing;',context);
for(const [city,lat,lon] of [['Kobe',34.6901,135.1955],['Osaka',34.6937,135.5023],['Tokyo',35.6762,139.6503]]){
 const value=context.calc(lat,lon);
 assert.ok(Number.isFinite(value)&&value>280&&value<310,'Unexpected Qibla bearing for '+city+': '+value);
 console.log('PASS Qibla',city,value.toFixed(1)+'°');
}
assert.match(js,/timeZone:'Asia\/Tokyo'/,'Prayer times must display JST');
assert.match(js,/status|notCertified|osmDisclaimer/,'Missing certification disclaimer');
assert.match(js,/overpass-api\.de\/api\/interpreter/,'Real map provider absent');
assert.match(product,/offJapanProducts/,'Attributed food research is not connected to product search');
console.log('PASS layout, languages, map, prayer/Qibla and product source wiring');
