# Japan Halal Checker — Floot source export

Original project: https://japan-halal-checker-najmul.floot.app

This folder contains the Floot React/TypeScript application screens, JAN/EAN barcode scanner, OCR, ingredient review, mosque map, prayer time, qibla, styles, API endpoint handlers, schemas, data helpers, and UI components copied from the Floot project on 2026-10-12.

**Important:** This is a source snapshot, not yet a standalone deployed clone. Floot-specific server endpoints (`/_api/food-lookup`, `/_api/food-catalog`) and managed database/runtime cannot be served directly from GitHub Pages. Do not replace the existing working Pages site until backend replacement, configuration, and browser tests are completed.

## Scanner
The scanner is in `pages/_index.tsx`; it uses `@zxing/browser` and `@zxing/library`, the rear camera, optional native `BarcodeDetector`, and a photo fallback. Phone HTTPS + camera permission are required.

## What GitHub Actions builds
The workflow `floot-source-archive.yml` checks scanner and API source files and creates a downloadable ZIP of the exported Floot source. This verifies packaging, **not** an Android APK or complete standalone web runtime.
