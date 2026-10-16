# Japanese ingredient collection target: 100,000

The `Crawl Japanese Ingredients to 100k` workflow starts on changes to its source and resumes at minute 17 of each hour. Each batch runs for at most 35 minutes / 1,500 pages. GitHub scheduling can be delayed; this is recurring work, not an uninterrupted forever process. Public source coverage may be insufficient for 100,000 products; the crawler never pads the target with worldwide foods or missing-ingredient records.

Source seeds contain previously observed official Japanese product URLs. The crawler follows eligible product/catalogue links and permitted sitemaps across its explicit manufacturer, brand and distributor allowlist. It respects robots.txt, slows requests per host, backs off on 403/429, and never bypasses authentication or anti-bot protection. Add reviewed sources to the allowlist and real observed URLs to the seed file as coverage grows.

## Persistent progress

Every hosted run restores the newest `japan-ingredients-state` artifact, validates the database, and continues its queue. It uploads the cumulative SQLite state, `products.json` and `summary.json`, including on an ordinary failed batch when state exists. The latest three cumulative artifacts are retained, each for 90 days. No ingredient research database or raw HTML is committed to the public repository or copied to the Pages artifact. Artifact access follows repository/Actions permissions; it is not a private-database security boundary. Restore failures stop the run rather than silently starting from zero. Platform outages, storage quotas and hard cancellations can interrupt a batch; the last uploaded checkpoint remains recoverable.

The earlier 721-record ChatGPT research checkpoint remains separate. Hosted counts start from actual revalidated pages; those 721 are never added to the counter without importing and deduplicating them. The old 100k worldwide catalogue is also excluded. Once 100,000 eligible products are reached, subsequent workflow wake-ups make no product requests.

## Count and decision contract

Only a named human food product with one unambiguous displayed Japanese ingredient declaration counts. Separately displayed additives are included in screening. JAN is retained only when explicitly displayed and checksum-valid. Missing JAN is never guessed from a URL or name. Identity is JAN when available, otherwise source publisher and normalized product name. Conflicting formulas for an identity are withheld from the goal count. Missing ingredients, allergen-only pages and placeholders never produce a HALAL result.

Each accepted record contains `rule_result`, `matched_terms`, `rule_version`, source URL, retrieval date and source-content hash. HALAL/HARAM is the user's configured ingredient rule result, not an independent religious ruling or a halal certificate (`halal_certified` stays false).

The user rule flags pork/pork extracts/lard, gelatin, emulsifier, flavouring, collagen, shortening, lecithin, processed fat, hydrolyzed protein, fermented seasoning and cooking/alcohol-related ingredients as HARAM. Explicit plant-sourced emulsifier is exempted locally; it cannot hide gelatin, pork, other emulsifiers or another prohibited term. A complete declaration without a user-prohibited term gets HALAL. Missing/incomplete declarations get UNKNOWN.

These research results are not automatically imported into the live website or Supabase. Existing scanner and application UI remain untouched. Source reuse permissions and actual product availability are not established by a successful crawl.

## Local execution

```sh
pip install beautifulsoup4==4.14.3
python -m unittest discover -s tests -p 'test_japan_ingredient_*.py' -v
python scripts/crawl_japanese_ingredients.py --state /path/outside/public/repo --target 100000 --minutes 35 --max-pages 1500
```

For another batch, run the same command with the same state directory. Do not publish the SQLite checkpoint or raw source pages through Pages.
