# Product ingredient and gelatin origin review — 2026-10-24

The previous scanner treated every gelatin declaration as prohibited. It now separates an explicitly porcine source from fish, bovine and unresolved sources. Unknown gelatin and E441 require review. Bovine origin still requires slaughter/certification evidence. An exact current, complete ingredient declaration with fish gelatin may be ingredient-clear, while other uncertain ingredients continue to require review. Ingredient-clear is not certification.

Origin evidence is bound to the exact ingredient statement. The existing product-specific issuer certificate registry remains separate and unchanged. Pork overrides any claimed certificate. OCR and manual ingredient checks use the same decision helper.

## Data

- 105 distinct original ingredient records were saved to the existing private `jhc_crawler_ingredient_staging` table and verified by a database count.
- 1 record has a pork flag, 104 remain UNKNOWN pending full-product review, 0 were certified.
- This research batch includes 24 bovine-origin candidates and 3 fish-origin candidates; 2 fish entries are collagen-peptide products, not functional gelatin powder. It is not 100 halal-approved products.
- The public exact-name/JAN lookup gains 5 independently inspected public label records. Only 2 have independently validated JANs. Other records are exact-name only.
- Restricted manufacturer bulk declarations remain private; research staging is not a public product lookup API. No anonymous staging policy was added.
- Source links and review dates are displayed in the result’s Ingredient source evidence disclosure.

## Validation

106 tests passed with `node --test tests/*.test.cjs`; `npm run build` passed. Tests cover unknown gelatin, explicit fish and bovine declarations, pork conflicts, source evidence from a different/changed label, E441, unrelated additives, exact product/JAN lookups, and existing product/certificate regressions. Camera scanner code is unchanged.
