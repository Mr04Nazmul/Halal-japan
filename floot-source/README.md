# Japan Halal Checker — GitHub React edition

The original React / TypeScript source was exported from the owner's Floot app, including its camera JAN/EAN scanner, product screen, ingredient OCR, ingredient screening, mosque map, prayer times, Qibla, and settings.

## GitHub Pages

The repository's `.github/workflows/pages.yml` builds the Vite frontend and stages it at `/floot/`, keeping the pre-existing website at the repository root intact.

Expected website after a **successful** Pages build:
https://mr04nazmul.github.io/Halal-japan/floot/

Track actual deployment status in the repository Actions tab; a source commit is not proof of successful deployment.

## What works without the Floot backend

* Browser-based rear-camera JAN/EAN scanner via ZXing with native BarcodeDetector supplement where supported.
* Photo barcode scan fallback.
* Public product/barcode lookup via Open Food Facts, with product and ingredient details when supplied.
* On-device OCR of Japanese ingredient labels via Tesseract.
* Evidence-conservative ingredient keyword screening; absence of flagged ingredients is **not** proof of halal.
* Nearby mosque search (OpenStreetMap / Overpass), calculated prayer times (AlAdhan), and Qibla bearing.

Browser camera functionality requires HTTPS, user camera permission, and testing on real devices.

## Still requiring migration

The Floot `foodProducts` database and its retailer catalogue, product verification evidence, and private Yahoo credentials have **not** been moved to GitHub. As a result, the GitHub edition cannot yet show the same retailer database or authoritative certificate records. The React catalogue UI indicates that retailer entries are unavailable rather than inventing them.

The `endpoints/*GET.ts` and `*POST.ts` server handlers are preserved as source/reference, but static Pages does not run those handlers. This edition uses a separate browser-based product lookup adapter in `endpoints/food-lookup_POST.schema.ts`.

This is a **web app**, not an Android APK or Play Store build. A successful Vite build verifies compilation only, not actual camera scanning on the user's phone.
