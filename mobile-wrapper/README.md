# Japan Halal Checker — Web + Android foundation

This is a **separate experimental Capacitor wrapper** on branch `floot-webview-migration`. The original website and existing Expo Android app stay unchanged.

## What works now
The build script packages the existing GitHub website's HTML, JavaScript, icon, translations and local product records for a Capacitor Android WebView. It is **not yet a clone of Floot**: the Floot source/export is required to replace the existing website with the newer Floot UI and services.

## Build on a development machine

```bash
cd mobile-wrapper
npm install
npm run build:web
npx cap add android
npm run sync:android
npx cap open android
```

Build APK/AAB in Android Studio or configured CI after the Android project is generated. Android camera scanning requires explicit tests of permission, HTTPS security and WebView support on real phones. No APK has been generated or verified by this scaffold.

## Migration checklist
- Export Floot source, assets, API routes and DB schema through authorized Floot export/tools.
- Compare page UI, routes, product data and functions with the current website before replacement.
- Keep all server secrets in backend environment variables; **never** put service-role keys or Yahoo client secrets in the bundled frontend.
- Implement and test camera permissions / barcode decoder on Android (native Capacitor plugin if web camera support is unreliable).
- Confirm halal judgments are evidence-based and represent uncertain products as needing verification.
- Run Android launch, scanner, API and Play Store compliance checks before publishing.

Website GitHub repo: https://github.com/Mr04Nazmul/Halal-japan
