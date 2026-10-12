# Japan Halal Checker — Android WebView APK

This is a minimal Android Java WebView wrapper for **https://japan-halal-checker-najmul.floot.app/**. All food/scanner/UI logic is on the live Floot website; updating the Floot site automatically updates the content shown inside this APK. Internet connection required.

## Build for free with GitHub Actions
1. Open [Build Halal Checker WebView APK](../../actions/workflows/halal-webview-apk.yml).
2. Choose **Run workflow** if no run exists, or wait for the automatic run from a commit touching android-webview.
3. Open the **successful** run, scroll to **Artifacts**, download `Japan-Halal-Checker-WebView-APK`, unzip, and install `app-debug.apk`.

Debug APK is for private testing, not a release-signed Play Store submission. No binary download link exists until the workflow succeeds.

## Access
App prompts for camera access when the website scanner asks. It prompts for location when Islamic tools request GPS. File picker lets you select ingredient/product photos. HTTPS and the exact Floot host are required for privileged WebView permissions; external links open through Android. No unrelated Android permissions.

## Editing
`app/src/main/java/com/najmul/japanhalalchecker/MainActivity.java` contains the fixed home URL, WebView permissions and navigation. Modify through GitHub and commit to trigger a new APK. To modify the website rather than the wrapper, edit and republish the Floot project.

## Limitations
Camera/geolocation behavior depends on Android System WebView version, site behavior and phone permissions; real-device tests are still necessary. A native Kotlin/React Native rebuild would be required for offline support or fully native camera processing.
