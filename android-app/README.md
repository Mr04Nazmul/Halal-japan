# Japan Halal Checker — Android starter

This is an **Expo React Native WebView shell** for the existing Japan Halal Checker website. It is not yet a fully native scanner or a verified APK.

## Build

1. Install dependencies: `npm install`
2. Validate versions: `npx expo-doctor`
3. Configure an Expo account: `npx eas-cli login`
4. Build an APK: `npx eas-cli build --platform android --profile preview`

## Required verification

- Confirm the GitHub Pages URL in App.js is live.
- Test launch, navigation, internet failures, camera permissions, barcode scanning and photo upload on real Android devices. Android WebView camera permissions may require extra native handling.
- Do not assume successful build means scanner works or that the app is crash-free.
- Product assessments are ingredient guidance, not halal certification.

The original website files in the repository root remain unchanged.
