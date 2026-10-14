# Japan halal apps — public data access research
Checked 2026-10-14. Based on Replica Recon's clean-room/public-only method.

| App | Public URL | Finding | Import status |
|---|---|---|---|
| Halal Japan (NOLIMIT INTERNATIONAL) | https://play.google.com/store/apps/details?id=com.conceptuale.productivity.halaljapan | Barcode and search advertised, no documented public export found | Do not import proprietary data without written permission |
| HALAL SCAN JAPAN | https://play.google.com/store/apps/details?id=com.mycompany.halalcheck | Calls its dataset proprietary/unique; no published API/export found | Permission required |
| Halal Japan (K-UBE) | https://halaljapan.app/about/ | Public website promises forthcoming product pages, no published bulk export found | No import |
| Halal & Healthy | https://www.halalapp.app/data | Open Food Facts-derived product packs; ODbL attribution/share alike | Eligible for import with license compliance |
| Open Food Facts | https://world.openfoodfacts.org/ | Original public contributor database | Already the source for repository's collector |

Conclusions: Replica skills do not grant permission to copy private servers, copyrighted images or independently produced halal verdicts. Public descriptions alone do not constitute product data. No external app's private product rows have been downloaded in this research. Existing collection workflow `.github/workflows/collect-japan-products.yml` targets the legally reusable Open Food Facts source and requires a successful run to confirm any new imported rows.

For owner permission:
- NOLIMIT: info@halaljapanofficial.com
- HALAL SCAN JAPAN: info@halal-check.jp
- K-UBE: support@k-ube.com

Suggested next step: Request explicit bulk data licensing/export terms from each owner; separately inspect collector results and validate Japan-tagged JANs, provenance, deduplication, ingredient completeness and copyright/licensing before publishing.
