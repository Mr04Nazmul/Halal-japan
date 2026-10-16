# Apify research integration — Japan Halal Checker
This workflow is **manual-run and research-only**. It does not modify the live scanner, Supabase or halal status.
1. Make an Apify account and copy an API token. Never paste it in chat or commit it to GitHub.
2. GitHub repository → Settings → Secrets and variables → Actions → New repository secret; name: `APIFY_TOKEN`.
3. Check actor `bgGC9uvqqfOkeeVjY` supports `{ queries: string, countryCode: 'jp' }`. It may be a search-result Actor, **not** a manufacturer-page extractor. Check prices/usage in Apify first.
4. Actions → **Apify Japanese Food Research** → Run workflow.
5. Download the `apify-official-food-candidates` artifact, if successful.
6. Before importing any record: check manufacturer's original page, exact JAN, checksum, full Japanese ingredients, duplicate JAN, packaging/date, and origin/certification evidence. Only then import separately.
No automatic halal/haram approvals. A found URL is not a complete product record.
