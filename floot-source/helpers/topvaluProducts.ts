/** Carefully checked factual product JANs and Japanese ingredient declarations
 * from individual AEON TOPVALU official product pages.
 *
 * Online declarations can lag packaging or differ across factories.
 * This is not halal certification, a bulk-licensed manufacturer feed, or
 * permission to spider/republish their entire catalogue.
 * Screen only the specific original JAN and include additives separately.
 * Reviewed 2026-10-16; confirm on the physical current package.
 */
export type TopvaluProduct={
  code:string;
  name:string;
  ingredients:string;
  additives:string;
  sourceUrl:string;
  checkedAt:'2026-10-16';
  brand:'AEON TOPVALU';
  officialOnlineIngredientDeclaration:true;
  halalCertified:false;
};
const official=(code:string)=>'https://www.topvalu.net/items/detail/'+code+'/';
export const topvaluProducts:TopvaluProduct[]=[
 {code:'4549414087208',name:'チャック付き強力小麦粉 1kg',
  ingredients:'小麦(カナダ産又はアメリカ産)',additives:'',
  sourceUrl:official('4549414087208'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549414730470',name:'おでんの素',
  ingredients:'食塩(国内製造)、砂糖、かつおぶし粉末、粉末しょうゆ(小麦・大豆を含む)、酵母エキス、いわし煮干粉末、焼きあご・あじ煮干粉末、さばぶし粉末',
  additives:'調味料(アミノ酸等)',
  sourceUrl:official('4549414730470'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549414546729',name:'ミルクプリン 北海道産クリーム使用',
  ingredients:'砂糖(国内製造)、植物油脂、脱脂粉乳、クリーム(乳成分を含む)、寒天、ゼラチン、液卵',
  additives:'糊料(加工でん粉、増粘多糖類)、香料(乳成分を含む)、乳化剤',
  sourceUrl:official('4549414546729'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549414662009',name:'北海道産小麦使用 たこ焼粉',
  ingredients:'小麦粉(国内製造)、でん粉、粉末水あめ、粉末油脂、食塩、かつおぶし粉末、卵黄粉(卵を含む)',
  additives:'調味料(アミノ酸等)、ベーキングパウダー、乳化剤、増粘多糖類',
  sourceUrl:official('4549414662009'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549414545142',name:'国産はるさめ 100g',
  ingredients:'かんしょでん粉(かんしょ(九州産))、ばれいしょでん粉(ばれいしょ(北海道産))',
  additives:'みょうばん',
  sourceUrl:official('4549414545142'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4902121482184',name:'国産しお 5kg',
  ingredients:'海水(瀬戸内)',additives:'',
  sourceUrl:official('4902121482184'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549414695632',name:'卓上味付けのり',
  ingredients:'乾のり(韓国産)、調味液[砂糖、しょうゆ(小麦・大豆を含む)、魚介エキス(小麦・えび・大豆を含む)、たん白酵素分解物(豚肉・小麦を含む)、魚醤(魚介類)、食塩、酵母エキス]',
  additives:'香辛料抽出物',
  sourceUrl:official('4549414695632'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549741557498',name:'瀬戸内の減塩しお',
  ingredients:'海水(45%、瀬戸内)',
  additives:'粗製海水塩化カリウム(48%)、粗製海水塩化マグネシウム(にがり)(4%)、グルコン酸ナトリウム(3%)、微粒二酸化ケイ素',
  sourceUrl:official('4549741557498'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549414622485',name:'和風だし',
  ingredients:'砂糖類(乳糖、グラニュー糖)、食塩(国内製造、韓国製造)、風味原料(かつお節粉末、かつおエキス、昆布エキス)、酵母エキス',
  additives:'調味料(アミノ酸等)',
  sourceUrl:official('4549414622485'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549414734645',name:'たこ飯の素 175g',
  ingredients:'たこ(ベトナム産)、たれ(しょうゆ(小麦・大豆を含む)、砂糖、おろし生姜、食塩、昆布エキス、かつおエキス(さばを含む)、かつお節粉末、酵母エキス、かきエキス、米発酵調味料、かつお節、乾しいたけ、昆布)、ごぼう、人参',
  additives:'調味料(アミノ酸等)、カラメル色素、増粘剤(キサンタン)',
  sourceUrl:official('4549414734645'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false},
 {code:'4549414734638',name:'ベビーホタテ飯の素 195g',
  ingredients:'ボイルアズマニシキ貝(アズマニシキ貝(中国産))、たれ(しょうゆ(小麦・大豆を含む)、砂糖、おろし生姜、食塩、昆布エキス、かつおエキス(さばを含む)、かつお節粉末、酵母エキス、かきエキス、米発酵調味料、かつお節、乾しいたけ、昆布)、ごぼう、人参',
  additives:'調味料(アミノ酸等)、カラメル色素、増粘剤(キサンタン)',
  sourceUrl:official('4549414734638'),checkedAt:'2026-10-16',brand:'AEON TOPVALU',
  officialOnlineIngredientDeclaration:true,halalCertified:false}
];
