# Barcode-only automatic evidence lookup — 2026-10-24

Camera barcode recognition is unchanged. A scan now queries the protected catalogue and the existing manufacturer gateway, alongside the previously published Japan snapshots/barcode shards. Manufacturer ingredient results require an exact equivalent barcode and `ingredientsVerified=true`; provider verdicts are discarded and the ingredient decision is computed locally. Nonzero manufacturer-declared beverage alcohol stays prohibited.

The protected `jhc-catalog-lookup` Edge Function now looks up a narrowly filtered licensed Japan Open Food Facts staging row when the older catalogue has no ingredient-bearing record. The eligible dataset contains 2,588 distinct barcodes with ingredient text. This is an additional lookup source, not a claim of 2,588 new unique products beyond all other snapshots, and not halal certification. ODbL attribution remains attached to responses. Only Japan-market, non-obsolete, licensed records with exact source URL/JAN are eligible; other private manufacturer research remains inaccessible.

The existing persistent request limit, JWT gateway validation, origin restriction and narrow one-record response remain in place. No direct anonymous staging access or table export is enabled; no service key is shipped to browsers.

A missing barcode result does not require a photo. It displays UNKNOWN with evidence status instead of inventing a product identity or HALAL/HARAM result. Existing manual OCR tools remain optional and collapsed. Original scanner, maps, prayer and Qibla flows are preserved.

Validation: all 118 tests passed, including exact-JAN source priority, missing/mismatched/identity-only providers, declared alcohol, licensed-data scope and origin/rate protections. Production build passed. Two live barcodes absent from the previous private catalogue were tested against the deployed Edge Function. No claim of full coverage of every food in Japan is made.
