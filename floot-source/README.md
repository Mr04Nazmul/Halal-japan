# Japan Halal Checker — Editable GitHub Website

This folder is the independent React/Vite website built from the owner's **latest Floot source** (including the JAN/EAN camera scanner and Islamic emerald/gold layout). The source snapshot was synchronized on 2026-10-13 Japan time.

**Live address after a successful GitHub Pages deployment:** https://mr04nazmul.github.io/Halal-japan/floot/

## Keep editing for free after publishing

Edit `floot-source/pages/_index.tsx` for the layout, `floot-source/pages/_index.module.css` for the main theme, `floot-source/components/IslamicTools.tsx` and its CSS for Mosque/Prayer/Qibla, and `floot-source/components/IngredientVerification.tsx` for ingredient UI. Commit your changes to `main`. The repository's `.github/workflows/pages.yml` automatically builds the Vite app and publishes the new files to GitHub Pages. No paid site builder is required within GitHub's free-plan limits.

Alternatively clone the repo, run `cd floot-source && npm install && npm run dev`, then `npm run build` to test locally. Push the commits to publish.

## What was ported vs. the hosted original

The scanner UI, camera decoder, barcode-photo fallback, ingredient OCR, ingredient review screen, Islamic tools and theme come from Floot. The GitHub-specific product lookup code in `endpoints/food-lookup_POST.schema.ts` accesses the **610 migrated public Supabase records** and Open Food Facts directly. The catalogue accesses the Supabase public read-only table; it does not use Floot's private Postgres connection. Research sources also use the Supabase table.

**Important limitations:** Floot's private backend handlers and database cannot simply run inside static GitHub Pages. Historical Floot server endpoint implementations are preserved as source files, but production GitHub Pages cannot execute them. Ingredient/certificate evidence records from Floot were empty at migration time, so no certification is invented. Data and real-device scanner behavior must be tested separately. This is a web app, not an APK.

For safe updates: keep the `main` branch as the published version. Edit in a new branch and open a Pull Request when changing scanner/lookup behavior, then merge once checks pass.

**Current workflow:** `.github/workflows/pages.yml`. Check its latest successful run in the GitHub Actions tab; a commit alone does not prove the live website updated.
