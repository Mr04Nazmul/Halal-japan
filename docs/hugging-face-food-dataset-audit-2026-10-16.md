# Hugging Face food and Japanese ingredient data audit — 2026-10-16

## Decision
**Do not import Open Food Facts from Hugging Face a second time.** The existing food catalogue already uses the same source; a second bulk import would duplicate JAN/GTIN values without establishing any new ingredient evidence. The Hugging Face repository is an alternate format/distribution for the upstream Open Food Facts database, **not a distinct Japanese manufacturer database**.

| Dataset | Role | Fields / applicability | Conditions |
|---|---|---|---|
| [openfoodfacts/product-database](https://huggingface.co/datasets/openfoodfacts/product-database) | Packaged food records | Product barcode `code`, multilingual ingredient text, product name, allergen and country tags; filter exact barcodes and `countries_tags` | Approx. 4.8 million worldwide records at check date, **not** that many Japanese records. ODbL 1.0 source database; check image licensing separately. Community-supplied labels do not prove complete ingredient lists or manufacturer confirmation |
| [openfoodfacts/ingredient-detection](https://huggingface.co/datasets/openfoodfacts/ingredient-detection) | Training/evaluating extraction of ingredients from OCR text | `text`, `marked_text`, `tokens`, `ner_tags`, image barcode metadata | 5,065 training + 556 test samples. CC-BY-SA-4.0. NOT a product catalogue; language distribution does not establish Japanese label performance |
| [recruit-jp/japanese-image-classification-evaluation-dataset](https://huggingface.co/datasets/recruit-jp/japanese-image-classification-evaluation-dataset) | Food image type classification | 101 Japanese food/dish categories | Not packaged product 原材料名 or JAN mapping; **do not use for ingredient screening** |
| [allergen-lab/off-allergenqa-jp8](https://huggingface.co/datasets/allergen-lab/off-allergenqa-jp8) | Allergen QA evaluation | Eight priority allergens in Japan, US-labelled English-language food examples | Not a Japanese foods/barcodes source; no certification |

## Actual current repository inventory (from 2026-10-16 GitHub manifest and enrichment report)

- **120,000 stored entries across tiers**, but **100,000 distinct barcode strings**.
- **30,000 Japan-country-tagged records** in the main Japan file and **90,000 supplemental records**. The groups overlap by **20,000 duplicate barcode entries**.
- **32,158 entries with some ingredient text** across stored groups: 1,828 in main Japan tier and 30,330 in supplemental tier; this is **entry count, not deduplicated unique full label count**.
- The latest official OFF TSV enrichment scanned **4,532,767 upstream rows** but recovered **0** additional missing ingredient texts via safe exact-barcode matching; duplicated barcodes were quarantined.
- More product names do not mean more verified Japanese ingredients. Country tags, prefix 45/49 and Japanese-looking names are separate, imperfect evidence of Japanese store availability.

Grounding: `data/food-catalog-manifest.json` and `docs/ingredient-enrichment-report.json` as checked 2026-10-16; the values may change after subsequent data jobs.

## Recommended data pipeline

1. Treat actual Japanese producer/certification records as highest-priority when the same physical product, current packaging and JAN are independently matched.
2. Keep Open Food Facts as a **community research source**, not manufacturer verification. Deduplicate existing entries carefully and do not infer current Japanese retail availability.
3. Add manufacturer-authorized full 原材料名 / additives and exact barcodes when available, with evidence and a revision date.
4. For missing labels, use package-image capture + Japanese OCR, then user correction and further review before storing product-specific facts; evaluate extraction software against representative **Japanese package photographs** rather than relying on English/French test performance.
5. Distinguish clear prohibited indicators, full-source-reviewed no-prohibited-ingredient screens, ambiguous origins and actual certificate records. Do not make up an ingredient's origin, a barcode or a certificate.

## Sources and terms

- Official product data source: https://world.openfoodfacts.org/
- Official Hugging Face product archive: https://huggingface.co/datasets/openfoodfacts/product-database
- Open Food Facts ingredient extraction corpus: https://huggingface.co/datasets/openfoodfacts/ingredient-detection
- Open Database License: https://opendatacommons.org/licenses/odbl/1-0/
- OFF data policies: https://world.openfoodfacts.org/terms-of-use

**Audit finding:** No independently licensed, comprehensive, Japan-specific packaged-food dataset supplying all three of **JAN + full current ingredients + halal evidence** was found among the checked Hugging Face candidates. Do not claim the market has no such data; this search only verified the sources listed above.
