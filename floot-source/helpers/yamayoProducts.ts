/** Manufacturer-supplied product records, permission explicitly granted on 2026-10-15.
 * Source: Yamayo's supplied JAN Excel sheets and actual 原材料名 label images;
 * gummy ingredient declaration independently cross-checked on producer's SMTS listing.
 * NO halal certification is implied. Do not conflate gift-set JAN with bottle JAN.
 */
export type YamayoProduct={
 code:string; name:string; brand:'株式会社ヤマヨ';
 ingredients:string; sourceUrl:string|null;
 evidence:'manufacturer_label_and_jan_sheet'|'manufacturer_confirmation_and_trade_catalog';
 ingredientListComplete:boolean; halalCertified:false; checkedAt:'2026-10-16';
};
const pear='西洋梨（新潟県産ルレクチェ）／酸化防止剤（ビタミンC）、pH調整剤';
const grape='ぶどう（新潟県産巨峰）';
export const yamayoProducts:YamayoProduct[]=[
 {code:'4571310560066',name:'ルレクチェジュース 180ml',brand:'株式会社ヤマヨ',
  ingredients:pear,sourceUrl:'https://the-niigata.jp/product/3673/',
  evidence:'manufacturer_label_and_jan_sheet',ingredientListComplete:true,halalCertified:false,checkedAt:'2026-10-16'},
 {code:'4571310560011',name:'ルレクチェジュース 500ml',brand:'株式会社ヤマヨ',
  ingredients:pear,sourceUrl:'https://www.mistore.jp/shopping/product/900000000000000001997799.html',
  evidence:'manufacturer_label_and_jan_sheet',ingredientListComplete:true,halalCertified:false,checkedAt:'2026-10-16'},
 {code:'4571310560103',name:'巨峰ジュース 180ml',brand:'株式会社ヤマヨ',
  ingredients:grape,sourceUrl:'https://www.mistore.jp/shopping/product/900000000000000001997799.html',
  evidence:'manufacturer_label_and_jan_sheet',ingredientListComplete:true,halalCertified:false,checkedAt:'2026-10-16'},
 {code:'4571310560073',name:'巨峰ジュース 500ml',brand:'株式会社ヤマヨ',
  ingredients:grape,sourceUrl:'https://www.mistore.jp/shopping/product/900000000000000001997799.html',
  evidence:'manufacturer_label_and_jan_sheet',ingredientListComplete:true,halalCertified:false,checkedAt:'2026-10-16'},
 {code:'4571310560806',name:'ルレクチェグミ 40g（4g×10粒）',brand:'株式会社ヤマヨ',
  ingredients:'水飴（国内製造）、砂糖、ゼラチン、洋なし果汁（新潟県産ルレクチェ）、粉末オブラート／セルロース、酸味料、ゲル化剤（ペクチン）、香料、乳化剤、ベニバナ黄色素、光沢剤、酸化防止剤（ビタミンC）、pH調整剤',
  sourceUrl:'https://product.smts-online.jp/Search/Product/tucues8O-mw/rrrIW76pyj0',
  evidence:'manufacturer_confirmation_and_trade_catalog',ingredientListComplete:true,halalCertified:false,checkedAt:'2026-10-16'}
];
