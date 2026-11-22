# Japan Halal Checker — licensed product-data expansion

Reviewed: 2026-11-23.

## Competitor data availability
- Halal Japan by NOLIMIT INTERNATIONAL: https://play.google.com/store/apps/details?id=com.conceptuale.productivity.halaljapan
- The public Play listing documents barcode lookup and product categories, but does NOT grant rights to copy its complete catalogue or provide an identified public database export.
- Rights holder contact listed publicly: info@halaljapanofficial.com. Request written terms for bulk reuse or licensing before importing its records. Do not call private endpoints, scrape behind accounts, copy its assets, or infer permission from an app displaying a product.

## Authorized sources and constraints
1. Open Food Facts API: https://openfoodfacts.github.io/openfoodfacts-server/api/ — publicly accessible product data, ODbL database license. Attribute Open Food Facts; maintain appropriate share-alike obligations and separate sources when license compatibility is uncertain. Images have separate CC BY-SA conditions and product artwork may have additional rights. Community records are unverified, so no automatic 'halal certified' classification.
2. Official manufacturers: use product name/JAN/ingredients when permission or lawful quotation/reuse conditions are met. Store source URL, observation date, and permission/rights status. Ingredient lists may change.
3. Retail catalogues: existing cached data may include product titles, store IDs and allergens, NOT verified full ingredient lists or certification. Store IDs are not JANs.
4. Manufacturer email responses: private correspondence should not be published verbatim; get permission before publishing proprietary product materials. General claims cannot certify individual products.

## Recommended database fields
`jan`, `product_name_ja`, `brand`, `ingredients_ja`, `ingredient_data_status`, `source_name`, `source_url`, `source_license`, `rights_status`, `checked_at`, `manufacturer_confirmation`, `halal_certificate_issuer`, `halal_certificate_expiry`, `decision`, `reviewed_at`.

## Required ingestion guards
- Exact JAN match and barcode checksum validation; deduplicate while preserving provenance.
- Never label unknown origin or missing ingredients as halal automatically.
- Keep raw source data segregated by license; record license, attribution and provenance on every imported item.
- Respect API rate limits, request identification/User-Agent, and cache policies. Do not mix protected/unlicensed databases into an Open Food Facts derivative.
- Each batch must report attempted, accepted, duplicates, rejected, published, and ingredient-verified counts separately.

Status: research/licensing plan only. No competitor records have been copied, and no new product records were imported in this commit.


## Additional source-policy review — 2026-11-23
- Kato Sangyo: its site policy limits reproduction to private use and restricts other copying, uploading, publication, or reuse without authorization. Automated collection is blocked pending permission.
- Ohyama Foods: its online-shop terms section 10 states that website text and images belong to the company and unauthorized reprinting/use is prohibited. Automated collection is blocked pending permission.
- Kurakon: product pages carry a company copyright notice; no compatible licence or bulk ingredient-data reuse permission is established. Automated collection is blocked pending permission.
- These restrictions affect future collection only. Existing Supabase rows are not deleted or modified.

## Source-discovery workflow status
The former Agent Reach scheduled job did not have a configured search provider and was fetching an unrelated third-party halal-guide site. That access and the hourly schedule have been removed. The status workflow is manual/on-change only and reports zero candidates until an approved search provider is configured. The main Japanese ingredient crawler remains scheduled and continues to enforce its source registry, robots checks, source-terms restrictions, and deduplication.
