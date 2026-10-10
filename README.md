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
## Version 2.2: requested language set and Yahoo lookup

The web app language picker now contains English, Japanese, Bengali (Bangladesh), Urdu (Pakistan), Uzbek (Uzbekistan), Arabic (Iraq), Persian (Iran), Indonesian and Malay. The seven requested languages have bundled translations for app navigation, settings, guides, result concerns, scanner messages and placeholders. Product names remain original. Ingredient translation uses MyMemory online and shows the original if translation fails; it is not used to establish religious certification.

Barcode lookup queries Open Food Facts and the configured Yahoo proxy in parallel, checks exact normalized barcodes, tries Open Food Facts v3 when ingredients are missing, then Wikidata if no product is available. Name search combines Open Food Facts and Yahoo and removes barcode duplicates. A missing ingredient list opens package-photo/manual review and manufacturer search. Coverage remains incomplete; this does not provide all Japanese products or a certified halal registry.

### Enable Yahoo in production

1. Import `Mr04Nazmul/Halal-japan` into Vercel using the included `vercel.json` (no framework/build command).
2. Set the server environment variable `YAHOO_CLIENT_ID` to your own Yahoo Developer Client ID, then deploy. Do not commit the ID.
3. Set `window.HALAL_API_BASE` in `app-config.js` to that deployment's HTTPS origin to enable Yahoo from GitHub Pages. If using the Vercel app itself, the empty value uses its own `/api/yahoo-product` route.
4. In Settings, use **Check connection**, then test a known JAN barcode. `health=1` reports only whether the secret is configured; a real barcode lookup is required to verify Yahoo access.

The proxy permits requests from `https://mr04nazmul.github.io`; add other trusted origins through comma-separated `ALLOWED_ORIGINS`. Its one-second guard is per server instance, not a shared distributed rate limiter. Retail names/images are never treated as verified ingredient data or certification. Without backend configuration the app explicitly says Yahoo is not connected.

Official API reference: https://developer.yahoo.co.jp/webapi/shopping/v3/itemsearch.html


## Connected backend and additional product sources (2026-10-10 UTC)

The GitHub Pages web app now calls the `halal-product-lookup` Edge Function in the existing Supabase project. Its JWT gateway stays enabled and uses only the public anon key in the client. The function has no account/database write operations. Yahoo configuration is retained privately in deployed backend code; the public repository contains only a placeholder/environment variable name, never the Yahoo Client ID.

- Backend health was live-tested with HTTP 200.
- Yahoo returned upstream HTTP 403 with the user-provided Client ID, from both a direct request and the deployed backend. Yahoo access is **not working** until that upstream authorization issue is resolved; health/configured does not prove Yahoo lookup works.
- UPCitemdb's free trial API is an additional exact-barcode metadata fallback (100 requests/day/IP; may return no record or quota errors). It supplies no verified ingredients or halal certification.
- The official Suntory JAN product catalogue adapter checks the page's exact `p_jan` and extracts its product name and ingredient list. Four official JAN records were retrieved and bundled with their source links and checked dates, so these records remain available when the manufacturer's server cannot be reached. They are labelled saved manufacturer records, and are not halal certificates. Names can also be searched locally.
- Links to official 7-Eleven, FamilyMart and Lawson ingredient/allergy guidance are available when data is missing. The category catalogue integration described below also makes selected store products searchable. Allergen lists are not complete ingredient lists.

The free sources do not cover every convenience-store food. Package-photo OCR/manual review remains necessary for unlisted products, local prepared meals, recipe changes and missing ingredient details.

Checks: `NODE_PATH=<directory-containing-linkedom> node tests/check-app.cjs` and `node tests/check-yahoo.cjs`. Browser/camera testing was not available in this environment.

## Convenience-store catalogue integration (2026-10-10 UTC)

Search → Convenience store foods → choose store/category → Browse foods. The bundled snapshot contains 357 distinct official catalogue records from 16 category pages across FamilyMart, 7-Eleven Japan and Lawson. Categories include bento, onigiri, sandwiches, noodles, fried food and FamilyMart pasta. Name searches also include these records. The backend refreshes the selected official category pages and falls back to their saved records individually when unavailable. Responses report livePages/savedPages; catalogue cache lasts ten minutes per backend instance.

Every record retains its source URL, store item ID, Japanese product name, image, category and checked date. Published regional/release notes are retained, including future releases. FamilyMart supplies published allergens and nutrition where available; some Lawson records include energy. Missing values are not invented. Store item IDs are **not JAN barcodes** and cannot match barcode scans. Distinct catalogue records retain independent scan-history entries.

These are selected catalogue pages, not an exhaustive database of every store, regional variant or Japanese food. Full ingredient lists and halal certificates are not supplied by these catalogue records. They receive VERIFY, even when product names mention pork or an allergen list contains gelatin; names/allergens alone are not a full ingredient assessment. Check the exact package, region and current recipe, or use package-photo/manual ingredient review. Japanese factual product text remains original; all new controls/instructions are bundled in the seven requested UI languages.

Additional checks: `NODE_PATH=<directory-containing-linkedom> node tests/check-stores.cjs` tests parser source IDs, factual allergen/nutrition extraction, deduplication, backend live parsing, saved fallback and invalid filters. UI tests cover offline store browsing, category filtering, seven-language result labels and separate history records.

## Halal shopping directory (2026-10-11 Asia/Tokyo)

Home → Halal shopping offers Gyomu Super halal foods and Convenience store options. Gyomu Super's explicit official halal category was paginated through all nine pages, yielding 211 distinct records. All 211 detail pages supplied full names, valid distinct JAN barcodes, pack sizes and countries of origin. Published storage instructions (197 products), nutrition including the stated serving basis (207), and allergens are included where available. No full ingredient lists or certification authority/expiry records were supplied or invented. Dates are saved-source dates; a fresh category fetch updates only the catalogue checked date, without pretending the saved JAN/details were rechecked. The backend refreshes these category pages with per-page snapshot fallback. Product-source and halal-category-source links are separate. English/Bengali search synonyms help locate original Japanese names.

Six additional exact retailer product listings provide simple-food shopping guidance: 7-Eleven fresh banana and plain mineral water; FamilyMart highland bananas and plain milk; Lawson plain milk in 500ml/1000ml sizes. Source regional caveats are retained (the saved 7-Eleven banana listing is Okinawa-specific). These options have no invented JAN codes or halal certificate. They are labelled as simple options to check, distinct from retailer halal catalogue evidence. Store finders and package-photo review are linked; branch stock is not available.

A retailer halal listing is source-attributed evidence, not independent verification of a certifier, current certificate or the package in the shopper's hand. Automated ingredient flags stay separate. Exact known Gyomu JAN lookups attach retailer evidence while preserving ingredient lists from exact Open Food Facts matches; a retailer listing does not suppress a conflicting ingredient flag. Changes to recipe, package, supplier or regional availability require comparison with the actual label/halal mark. The directory and all new UI guidance work offline; seven requested languages have bundled text.

Validation: parser tests cover the explicit halal-category boundary, all JAN check digits/unique codes, missing fields, catalogue-date separation, live refresh and nine-page saved fallback. UI tests cover both shopping views, all seven language labels, exact-JAN lookup and preservation of conflicting ingredient evidence.
