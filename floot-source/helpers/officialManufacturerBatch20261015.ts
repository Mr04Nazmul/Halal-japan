/** Official Japanese manufacturer JAN + full ingredient label research, 2026-10-15.
 * Records are keyed by exact JAN, not name. Not halal certificates.
 * Duplicate-checked against curated edge-function records and 2026-10-14 research.
 * Packaging may change; manufacturer pages are the source of truth for the snapshot.
 */
export type OfficialManufacturerProduct = {
 code:string;product_name:string;brands:string;ingredients_text:string;
 _source:string;_sourceUrl:string;_ingredientEvidence:string;_halalVerified:boolean;
 _verificationStatus:string;_snapshotDate:string;_note:string;
};
export const OFFICIAL_MANUFACTURER_BATCH_20261015: OfficialManufacturerProduct[] = [
  {
    "code": "4902888256912",
    "product_name": "パックンチョ＜チョコ＞ 43g",
    "brands": "Morinaga Seika",
    "ingredients_text": "チョコクリーム（植物油脂、砂糖、乳糖、全粉乳、ココアパウダー、カカオマス）（国内製造）、小麦粉、砂糖、ショートニング、デキストリン、食塩、イースト／膨脹剤、炭酸カルシウム、乳化剤（大豆由来）、香料、カラメル色素",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.morinaga.co.jp/products/detail.php?id=PRD2009-08-0170",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4902888256929",
    "product_name": "パックンチョ＜イチゴ＞ 41g",
    "brands": "Morinaga Seika",
    "ingredients_text": "イチゴ風味クリーム（砂糖、植物油脂、乳糖、全粉乳）（国内製造）、小麦粉、砂糖、ショートニング、デキストリン、食塩、イースト／膨脹剤、炭酸カルシウム、乳化剤（大豆由来）、アカビート色素、香料、酸味料、カラメル色素",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.morinaga.co.jp/products/detail.php?id=PRD2011-05-0015",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4902888270611",
    "product_name": "パックンチョ＜チョコ＞大袋 101g",
    "brands": "Morinaga Seika",
    "ingredients_text": "チョコクリーム（植物油脂、砂糖、乳糖、全粉乳、ココアパウダー、カカオマス）（国内製造）、小麦粉、砂糖、ショートニング、デキストリン、食塩、イースト／膨脹剤、炭酸カルシウム、乳化剤（大豆由来）、香料、カラメル色素",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.morinaga.co.jp/products/detail.php?id=PRD2014-08-0015",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4901005555006",
    "product_name": "アーモンドグリコ＜袋入り＞ 76g",
    "brands": "Glico",
    "ingredients_text": "水あめ（国内製造）、乳等を主要原料とする食品、砂糖、アーモンド、植物油脂、クリーム、ホエイパウダー、大豆たんぱく、食塩／加工デンプン、炭酸Ca、乳化剤、（一部に乳成分・小麦・大豆・アーモンドを含む）",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.glico.com/jp/product/gum_candy/almondglico/40953/",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4901005001411",
    "product_name": "ジャイアントコーン 生キャラメル 140ml",
    "brands": "Glico",
    "ingredients_text": "乳製品（外国製造、国内製造）、砂糖、キャラメルソース、チョコレート、コーン、チョコレートコーチング、植物油脂、キャラメルクッキー、水あめ、アーモンドプラリネ／香料、乳化剤、安定剤（増粘多糖類、寒天）、着色料（カラメル色素、アナトー）、乳酸カルシウム、（一部に乳成分・小麦・大豆・アーモンドを含む）",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.glico.com/jp/product/ice/giantcone/47169/",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4901005312548",
    "product_name": "ジャイアントコーン 大人のアーモンドショコラ 130ml",
    "brands": "Glico",
    "ingredients_text": "チョコレート(国内製造)、コーン、乳製品、砂糖、チョコレートコーチング、キャンデーコートアーモンド、ココア、植物油脂、アーモンドプラリネ／乳化剤、カラメル色素、安定剤（増粘多糖類）、香料、ビタミンＥ、シェラック、（一部に乳成分・小麦・大豆・アーモンドを含む）",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.glico.com/jp/product/ice/giantcone/46685/",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4901360368457",
    "product_name": "ショコロ 6個",
    "brands": "Bourbon",
    "ingredients_text": "小麦粉（国内製造）、砂糖、植物油脂、全粉乳、乳糖、マーガリン（乳成分を含む）、カカオマス、ココアパウダー、液全卵、マルトース、食塩、水飴／乳化剤（大豆由来）、香料（乳由来）、膨脹剤、着色料（カロテン）",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.bourbon.co.jp/product/detail/36845.html",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4901360364084",
    "product_name": "７２ｇセピアート生クリーム",
    "brands": "Bourbon",
    "ingredients_text": "砂糖（国内製造、タイ製造）、植物油脂、カカオマス、全粉乳、ココアバター、乳糖、脱脂粉乳、クリーム（乳成分を含む）、バターオイル／乳化剤（大豆由来）、香料（アーモンド由来）",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.bourbon.co.jp/product/detail/36408.html",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4901360364602",
    "product_name": "キュービィロップ 100g",
    "brands": "Bourbon",
    "ingredients_text": "砂糖（国内製造）、水飴、植物油脂、ぶどう濃縮果汁、もも濃縮果汁、レモン濃縮果汁、オレンジ濃縮果汁、いちご濃縮果汁／酸味料、ビタミンＣ、香料、重曹、着色料（アントシアニン、カロテノイド、ウコン、クチナシ、紅花黄）、乳化剤（大豆由来）",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.bourbon.co.jp/product/detail/36460.html",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4901360360864",
    "product_name": "ブランチュール 9個",
    "brands": "Bourbon",
    "ingredients_text": "砂糖（国内製造、タイ製造）、小麦粉、全粉乳、植物油脂、ショートニング、マーガリン、液卵白（卵を含む）、ココアバター、ホエイパウダー（乳成分を含む）、乳糖、乾燥卵白（卵を含む）、バター、水飴、食塩／トレハロース、乳化剤（大豆由来）、着色料（カラメル）、香料（乳由来）、膨脹剤",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.bourbon.co.jp/product/detail/36086.html",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  },
  {
    "code": "4901360362820",
    "product_name": "プチココア 47g",
    "brands": "Bourbon",
    "ingredients_text": "小麦粉（国内製造）、砂糖、ショートニング、ココアパウダー、小麦全粒粉、乳糖、異性化液糖、ホエイパウダー（乳成分を含む）、食塩、デキストリン／膨脹剤、乳化剤（大豆由来）、香料",
    "_source": "Official manufacturer product page",
    "_sourceUrl": "https://www.bourbon.co.jp/product/detail/36282.html",
    "_ingredientEvidence": "manufacturer_published",
    "_halalVerified": false,
    "_verificationStatus": "needs_review",
    "_snapshotDate": "2026-10-15",
    "_note": "Not halal-certified; review processing and additive origins. Packaging may differ from web listing."
  }
];
