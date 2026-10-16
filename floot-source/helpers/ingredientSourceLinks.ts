/** Ingredient evidence source directory, linking to upstream pages without copying
 * entire commercial product databases or assuming third-party API credentials.
 * A search URL is ONLY a way to find evidence; it does not verify a product.
 */
export type IngredientSource={
 id:string;title:string;region:'products'|'references';
 description:string; evidence:'jan_and_ingredients'|'ingredients_only'|'jan_or_name_only'|'reference_only';
 url:string; publicBrowse:boolean;
};
export const ingredientSources:IngredientSource[]=[
 {id:'topvalu',title:'AEON TOPVALU',region:'products',description:'Official Japanese food catalogue; individual product pages may list JAN, 原材料名 and additives. External site; entire catalogue is not imported.',evidence:'jan_and_ingredients',url:'https://www.topvalu.net/items/category/100000000/1000/',publicBrowse:true},
 {id:'sevenpremium',title:'Seven Premium',region:'products',description:'Official product and ingredient pages. Page IDs are not JAN barcodes.',evidence:'ingredients_only',url:'https://7premium.jp/product/search/',publicBrowse:true},
 {id:'meiji',title:'Meiji',region:'products',description:'Manufacturer product listings and JAN-specific pages for selected products.',evidence:'jan_and_ingredients',url:'https://www.meiji.co.jp/products/',publicBrowse:true},
 {id:'familymart',title:'FamilyMart',region:'products',description:'Official product information; complete ingredients are not guaranteed online.',evidence:'jan_or_name_only',url:'https://www.family.co.jp/goods.html',publicBrowse:true},
 {id:'lawson',title:'Lawson',region:'products',description:'Official product information; many full labels require checking the package.',evidence:'jan_or_name_only',url:'https://www.lawson.co.jp/recommend/original/',publicBrowse:true},
 {id:'openfoodfacts',title:'Open Food Facts',region:'products',description:'Open community food database: barcode plus ingredient text when available, ODbL 1.0.',evidence:'jan_and_ingredients',url:'https://world.openfoodfacts.org/',publicBrowse:true},
 {id:'glico',title:'Glico / グリコ',region:'products',description:'Official Pocky, Bisco and other product pages display exact JAN and Japanese 原材料名. Individual recipes can change.',evidence:'jan_and_ingredients',url:'https://www.glico.com/jp/product/',publicBrowse:true},
 {id:'morinaga',title:'Morinaga / 森永製菓',region:'products',description:'Official biscuits and food product pages include JAN, ingredients and allergen declarations; compare current package.',evidence:'jan_and_ingredients',url:'https://www.morinaga.co.jp/products/',publicBrowse:true},
 {id:'kagome',title:'Kagome / カゴメ',region:'products',description:'Official foodservice and grocery sauces: specific JAN, food ingredients and additive lists. Bulk reuse requires rights.',evidence:'jan_and_ingredients',url:'https://www.kagome.co.jp/foodservice/',publicBrowse:true},
 {id:'nissin',title:'Nissin / 日清食品',region:'products',description:'Official instant noodle and frozen foods product pages list exact JAN and full 原材料名. Verify current packaging.',evidence:'jan_and_ingredients',url:'https://www.nissin.com/jp/product/',publicBrowse:true},
 {id:'ksppos',title:'KSP-POS open rankings',region:'products',description:'Free Japanese food supermarket rankings with JAN/product identity, not full ingredients. Separate use restrictions apply.',evidence:'jan_or_name_only',url:'https://www.ksp-sp.com/open_data/API/',publicBrowse:true},
 {id:'caa',title:'Consumer Affairs Agency',region:'references',description:'Government Japanese food additive identities and standards; not product-specific halal certification.',evidence:'reference_only',url:'https://www.caa.go.jp/policies/policy/standards_evaluation/food_additives/',publicBrowse:true},
 {id:'fooddb',title:'Japanese basic-food database',region:'references',description:'Basic food/nutrition reference, not retail JAN ingredients.',evidence:'reference_only',url:'https://github.com/takakix2/fooddb-jp',publicBrowse:true},
 {id:'mext',title:'MEXT Food Composition',region:'references',description:'Official Japanese food composition database; not a packaged product catalogue.',evidence:'reference_only',url:'https://fooddb.mext.go.jp/',publicBrowse:true},
 {id:'halallens',title:'HalalLens research client',region:'references',description:'Third-party ingredient-rule research project, not independently certified manufacturer facts.',evidence:'reference_only',url:'https://github.com/halallens-no/halal-scanner',publicBrowse:true}
];
export function validEAN13(input:string):boolean{
 if(!/^\d{13}$/.test(input))return false;
 const v=Array.from(input,Number);
 const sum=v.slice(0,12).reverse().reduce((s,x,i)=>s+x*(i%2===0?3:1),0);
 return (10-sum%10)%10===v[12];
}
/** Exact barcode links are leads only; target may be missing or changed. */
export function janSourceLinks(raw:string){
 const code=raw.trim();
 if(!validEAN13(code))return [];
 return [
  {name:'Open Food Facts · exact barcode',href:'https://world.openfoodfacts.org/product/'+encodeURIComponent(code),kind:'database'},
  {name:'TOPVALU · possible product page',href:'https://www.topvalu.net/items/detail/'+encodeURIComponent(code)+'/',kind:'candidate'},
  {name:'Search Japanese manufacturer 原材料名',href:'https://www.google.com/search?q='+encodeURIComponent('"'+code+'" 原材料名'),kind:'search'},
  {name:'Search TOPVALU official pages',href:'https://www.google.com/search?q='+encodeURIComponent('site:topvalu.net/items/detail/ "'+code+'"'),kind:'search'},
  {name:'Search Seven Premium ingredient pages',href:'https://www.google.com/search?q='+encodeURIComponent('site:7premium.jp "'+code+'" 原材料名'),kind:'search'}
 ];
}
