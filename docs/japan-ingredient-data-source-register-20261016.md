# Japan Halal Checker: actual public ingredient and JAN sources — checked 2026-10-16

This register separates **product barcode identities**, **full Japanese 原材料名 / 添加物 declarations**, **ingredient reference vocabulary**, and **religious certification**. One does not prove the others.

## Highest-priority product-ingredient sources

| Source | Real information seen | What we can use | Limits and next action |
|---|---|---|---|
| [AEON TOPVALU official product catalogue](https://www.topvalu.net/items/category/100000000/1000/) | Food section indexed at around **4,149 item listings**; individual URLs `https://www.topvalu.net/items/detail/{JAN}/` provide a **literal 13-digit JAN, 原材料名, separate 添加物, allergens and source-linked identity** | Eleven specifically checked non-bulk records added to `floot-source/helpers/topvaluProducts.ts` and used by the main barcode lookup | This listing count is **not 4,149 verified full labels**. No automatic crawling/bulk republication authorization was established. Before large-scale collection, seek reuse rights / data feed permission, honor site rules, and verify product freshness. Package prevails |
| [Seven Premium public product pages](https://7premium.jp/product/search/) | Detailed product pages contain official 原材料 and allergens | Product-level ingredient research, source page links; existing `data/seven-premium-ingredient-signals-20261016.json` | The URL `id` is **not a JAN**. Never insert a guessed JAN or attach one product's list to another |
| [Open Food Facts](https://world.openfoodfacts.org/) | Millions of world food products and some Japanese barcode/ingredient text | ODbL data export and exact barcode lookup already integrated | Existing project's audit has **100,000 unique barcodes / 120,000 stored entries / 32,158 entries with any ingredient text**, with **20,000 duplicate entries**; 2026-10-16 licensed bulk exact-barcode ingredient recovery found **zero** new missing labels. Community labels ≠ official verification; no guarantees of Japanese store availability |

## Complementary resources — not a substitute for product ingredients

| Source | What is actually supplied | Restrictions |
|---|---|---|
| [KSP-POS free API](https://www.ksp-sp.com/open_data/API/) | Japanese food-supermarket top rankings **with JAN and product name / sales info** | Limited ranking scope; **does not supply full 原材料名**. Check service's data use terms before republishing |
| [Japanese fooddb-jp open-source dataset](https://github.com/takakix2/fooddb-jp) | **2,541** Japanese food categories and nutrition by ingredient; 353 nutrients | Basic foods/nutrition, **not packaged item JANs nor complete ingredients**; API free plan may have daily request limit |
| [Japanese Consumer Affairs Agency additive lists](https://www.caa.go.jp/policies/policy/standards_evaluation/food_additives/) | Official Japanese food additive names, additive use standards and published list downloads | Additive legal approval or chemical safety **does not prove halal ingredient origin or certification** |
| [HalalLens open-source ingredient lookup client](https://github.com/halallens-no/halal-scanner) | Project claims a **10,000+ ingredient** halal-status community/AI-supported *API*, client library MIT | Not a free bulk packaged product database, no Japanese JAN list demonstrated. Confirm actual API quality, request policy and public display rights separately |
| [Japanese Food Labeling Checker](https://github.com/yabuuchi-hiroaki/japanese-food-labeling-checker) | Japanese label syntax/format checking samples | No licence verified for the data source files; avoid copying without authorization. Does not offer a complete JAN-product ingredient database |
| [MEXT public food composition database](https://fooddb.mext.go.jp/) | Government food nutrient composition reference | **Not** a barcode/packaged-food ingredient declaration |
| [halalcheck LINE bot GAS](https://github.com/ahmadradi11/halalcheck_LINE_bot_GAS) | Public Japanese ingredient-image screening source code | No verified licensed bulk manufacturer product JAN+ingredient dataset established |

## Repository update performed

- Added **eleven** exact TOPVALU JAN records with source URLs, web-published ingredient declarations, separate additive fields and a research date.
- Main React barcode lookup prioritizes these **exact manufacturer-page JAN matches** over unverified source results, retaining existing scanner and product database.
- Existing ingredient rules classify explicitly flagged components, ambiguous-source additives and apparently clear online lists distinctly. Nothing is automatically assigned halal certification.
- Regression tests verify JAN check digits, strictly matched source URLs and no fabricated halal certificates.
- Research record is **not** evidence that TOPVALU granted a licence for bulk product-data distribution. Contact the data owner for automated/large-scale reuse.

## Non-negotiable data quality gates

1. No guessing JAN from page IDs, image filenames, names or 45/49 prefixes.
2. Do not scrape or access private Supabase/Firebase repositories or protected endpoints of third-party apps, even if a public anon key appears in their source. Public source code is not a licence to copy user/product database contents.
3. Preserve source URL, retrieval date and ingredient/additive separation for every product; don't conflate allergen manufacturing-cross-contact warnings with used ingredients.
4. Match current barcode and packaging revision before reliable current-product conclusions.
5. Treat ambiguous additive origin as unconfirmed. Halal certification is a separate exact-product evidence step.

## High-return next step
Obtain an **approved TOPVALU bulk product feed or reuse permission for published JAN + ingredient label data**. It is one of the clearest sources with real barcode-plus-formula information. Prioritize the most scanned convenience-store products and manufacturers who explicitly authorize reuse, and supplement with product label photos for missing entries.
