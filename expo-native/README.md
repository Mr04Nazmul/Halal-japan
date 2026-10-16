# Japan Halal Checker — Expo native Android edition

New, isolated React Native application derived from the maintained **Expo create-expo-app blank-template layout**. The historical \`expo/create-react-native-app\` repository is deprecated. Use \`npx create-expo-app@latest\` for future projects.

## What is implemented

- Native Expo Camera scanner for JAN/EAN-8, EAN-13, UPC-A and GTIN-14 with check-digit validation and torch.
- Manual barcode input, food-name search, Open Food Facts product lookup, ingredient flags and clear unverified/unknown treatment.
- Bangla / Japanese / English interface.
- In-app live restaurant, prayer, mosque and Qibla pages from the existing Japan Halal Checker website using a WebView; their accuracy and live geolocation require device testing.
- No embedded private API credentials, Google Mobile Ads, background tracking or invented halal certifications.
- Source and attribution links; graceful missing/offline messages.

This edition does **not** yet have working on-device OCR, an offline ingredient database, or verified full-store coverage. The older \`android-app/\` experiment remains untouched.

## Build

On a computer with Node.js 22:

\`\`\`sh
cd expo-native
npm install
npx expo install --check
npx expo start
\`\`\`

Create a free installable DEBUG APK using the \`Expo Native Android APK\` GitHub Actions workflow on this branch; download \`japan-halal-checker-expo-debug-apk\` from the run's artifacts.

For a properly signed internal APK and later Play Store AAB, configure Expo EAS credentials and use:

\`\`\`sh
npx eas-cli build --platform android --profile preview
npx eas-cli build --platform android --profile production
\`\`\`

The DEBUG APK is **not** production-signed, may have inconsistent upgrade certificates across runners, and must not be uploaded to Google Play. On-device scanning, WebView location, startup stability, Android compatibility and source permissions are **not yet verified**. Product information is independently maintained by providers and not automatically halal certified.

Original web pages and product data remain unchanged on \`main\`.

## New project from Expo's supported creator

For a future separate app: \`npx create-expo-app@latest my-app --template blank\`; then install modules with \`npx expo install expo-camera react-native-webview\`.
