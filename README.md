# Japan Halal Checker 🇯🇵☪️

A mobile-friendly web app for people checking packaged food in Japan. It supports barcode lookup, product-name search, and a manual ingredient keyword review in English, Bangla, and Japanese.

## Live deployment

A GitHub Actions deployment workflow is included. Open **Settings → Pages** and select **GitHub Actions** as the build/deployment source. After the first successful run in the **Actions** tab, the site should be available at:

https://mr04nazmul.github.io/Halal-japan/

If the page does not load yet, check the Pages deployment status in the repository's **Actions** tab and the Pages settings.

## Features in the current version

- Responsive layout for phones and desktop
- English / বাংলা / 日本語 interface
- Barcode number lookup
- Rear-camera barcode scanning for common retail formats including JAN/EAN-13, EAN-8, UPC-A/UPC-E, Code 128, Code 39 and ITF
- Faster continuous scan loop, scan-success beep/vibration where supported, optional camera flash control where the browser exposes it, and photo-of-barcode fallback
- Camera barcode scanner (browser camera permission required; HTTPS required)
- Product search using Open Food Facts
- Manual ingredient keyword review
- Displays available product name, brand, barcode, ingredient text, product image and source record
- Cautions that a keyword match is not a halal ruling or certification

## Data and limitations

Product information is fetched from the community-maintained Open Food Facts API. Coverage and ingredient information can be missing, outdated, or incorrect, and not every Japanese product will be listed. Keyword screening is a basic helper, not a complete ingredient analysis: ingredient names, translations, processing aids, source materials and manufacturing processes can be missed or misunderstood.

**A result labelled “Needs verification” is not a halal approval.** The app does not currently connect to an authoritative halal-certification registry and does not independently verify certification. When uncertain, check the original package, contact the manufacturer, or consult a trusted halal certifying authority.

## Scanner expectations

This uses a phone camera, not the dedicated high-speed laser/imager hardware found at Japanese convenience-store checkouts. It can scan common product barcodes, but speed depends on the phone camera, focus, lighting, glare, browser and barcode condition. For best results, open the HTTPS site in Safari/Chrome, allow camera access, use the rear camera, keep the whole JAN barcode visible, and try the photo/manual barcode input if live scanning misses it. Flash control is not available on every phone/browser.

## Technology

- Static HTML, CSS and JavaScript
- Open Food Facts API
- html5-qrcode browser library for barcode scanning

No account or user database is required for the current version. The page sends product search requests to Open Food Facts when you search or scan a barcode. Camera access is only requested when you start the scanner.

## Automatic deployment

A GitHub Actions workflow is included to publish the repository root to GitHub Pages on each push to `main`. In the repository, open **Settings → Pages** and select **GitHub Actions** as the build/deployment source once. Then check **Actions** for the first deployment. The live URL is only ready after that deployment succeeds.

## Development notes

The app is currently a prototype. Features such as a verified certification directory, restaurant and mosque map, prayer times, Qibla, and a dedicated Japanese-product data source are not implemented yet.