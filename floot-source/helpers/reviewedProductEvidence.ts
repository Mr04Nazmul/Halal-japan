/** Narrow, exact-barcode evidence records; positive prohibited ingredients
 * can establish a concern even when a full current declaration is unavailable.
 * Do not transfer a product-name-only match to another barcode/flavour. */
export const reviewedProductEvidence=[{
 code:'4901330581985',name:'ピザポテト 64g / Calbee Pizza Potato',brand:'Calbee / カルビー',
 ingredientEvidence:'サラミ風チップ（豚肉を含む）',
 ingredientSourceUrl:'https://www.calbee.co.jp/products/detail/?p=20210513141859',
 barcodeSourceUrl:'https://www.sugoimart.com/products/pizza-potato',
 checkedAt:'2026-10-24',fullIngredientList:false,
 note:'Positive pork ingredient excerpt from the indexed official Pizza Potato declaration. The manufacturer page lists the 64g convenience-store version in this product family. Exact JAN/product identity is independently listed by the retailer. The live Calbee site showed maintenance during review; this is a dated reviewed declaration, not a live current-package check. No unsupported alcohol claim is made.'
}] as const;
