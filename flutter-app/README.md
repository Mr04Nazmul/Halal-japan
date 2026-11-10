# Japan Halal Checker — Flutter Android

This is a **new native Flutter Android starting point**. The existing website, Expo Android app, product records and Supabase functions remain untouched on the main branch.

## Implemented in this starter
- Android camera barcode scanning using mobile_scanner.
- Real Open Food Facts HTTPS product lookup by barcode and product name.
- English, Bangla and Japanese UI language selection, persisted on device.
- Ingredient keyword warnings and clear **NOT VERIFIED** status. Keyword matches are NOT religious rulings, and missing matches do NOT mean certified halal.
- Creator credit: Hossain Najmul.
- GitHub Actions workflow to generate Android scaffolding and build APK.

## Not yet implemented / verified
- Offline Japanese catalogue imports and Supabase live lookup.
- OCR ingredient photos, evidence-backed certification, stores & mosque map, prayer times, qibla, all requested languages, advertisements.
- Hardware camera verification and app installation testing on real Android devices.
- Play Store release signing and production AAB.

## Build
From this directory run `flutter create --platforms=android --project-name japan_halal_checker --no-overwrite .`, `flutter pub get`, `flutter build apk --release`.
The workflow generates Android scaffolding during CI; the result is downloadable from its Actions artifacts after successful completion.
