// Run: node scripts/audit-catalog.mjs
// Audits existing records without inventing halal certifications or barcode values.
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
const files=[
 ['stores','supabase/functions/halal-product-lookup/store-records.js','STORE_RECORDS'],
 ['gyomu','supabase/functions/halal-product-lookup/gyomu-records.js','GYOMU_RECORDS'],
 ['manufacturer','floot-source/helpers/manufacturerDrinks.tsx','manufacturerDrinks'],
 ['extra_manufacturer','floot-source/helpers/extraManufacturerDrinks.tsx','extraManufacturerDrinks'],
 ['verified_excerpts','floot-source/helpers/verifiedFoodRecords.tsx','verifiedFoodRecords'],
 ['suntory','supabase/functions/halal-product-lookup/manufacturer-records.js','MANUFACTURER_RECORDS']
];
function checksum(s){if(!/^\\d{8}$|^\\d{13}$/.test(s))return null;const nums=[...s].map(Number),body=nums.slice(0,-1);const total=body.reduce((acc,n,i)=>acc+n*(body.length%2===i%2?1:3),0);return (10-total%10)%10===nums.at(-1)}
const items=[],summary=[];
for(const [kind,path,key] of files){
 const source=readFileSync(path,'utf8');
 const at=source.indexOf('=',source.indexOf(key))+1;
 const begin=source.indexOf('[',at);let depth=0,inString=false,escaped=false,quote='';
 let end=-1;
 for(let i=begin;i<source.length;i++){const ch=source[i];if(inString){if(escaped)escaped=false;else if(ch==='\\\\')escaped=true;else if(ch===quote)inString=false;continue;}if(ch==='"'||ch==="'"){inString=true;quote=ch;continue;}if(ch==='[')depth++;if(ch===']'&&--depth===0){end=i+1;break;}}
 if(end<0)throw Error('Unterminated '+path);
 const rows=JSON.parse(source.slice(begin,end));
 summary.push({dataset:kind,rows:rows.length});
 for(const row of rows){const barcode=String(row.code||row.barcode||'').trim();
 const name=row.product_name||row.name||'';
 const ingredients=row.ingredients_text||row.ingredients||null;
 items.push({dataset:kind,barcode,name,manufacturer:row.brands||row.manufacturer||null,ingredients,partial_ingredients:Boolean(row.ingredientsPartial),source_url:row._sourceUrl||row.url||null,barcode_valid:barcode?checksum(barcode):null,classification:'not_assessed'});
 }
}
const seen=new Map();
for(const item of items){if(!item.barcode)continue;const group=seen.get(item.barcode)||[];group.push(item);seen.set(item.barcode,group)}
const duplicates=[...seen.entries()].filter(([_,v])=>v.length>1).map(([barcode,v])=>({barcode,records:v.map(r=>({dataset:r.dataset,name:r.name}))}));
const report={generated_at:new Date().toISOString(),summary,total_rows:items.length,distinct_nonempty_barcodes:seen.size,missing_barcode:items.filter(x=>!x.barcode).length,invalid_barcode:items.filter(x=>x.barcode&&x.barcode_valid===false).length,missing_ingredients:items.filter(x=>!x.ingredients).length,duplicate_barcode_groups:duplicates.length,duplicates,notes:['This is a file inventory, not a count of independently verified halal products.','Store catalogue IDs are not JAN codes.','Barcode checksum is a format check only; it does not establish product identity.']};
mkdirSync('research',{recursive:true});
writeFileSync('research/catalog-audit.json',JSON.stringify(report,null,2)+'\\n');
writeFileSync('research/catalog-index.json',JSON.stringify({generated_at:report.generated_at,records:items},null,2)+'\\n');
console.log(JSON.stringify({total_rows:report.total_rows,distinct_barcodes:report.distinct_nonempty_barcodes,missing_barcode:report.missing_barcode,invalid_barcode:report.invalid_barcode,duplicate_groups:report.duplicate_barcode_groups},null,2));
