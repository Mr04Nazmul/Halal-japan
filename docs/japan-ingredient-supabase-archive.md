# Crawler → Supabase staging archive
The GitHub crawler artifact remains the source of truth; this is a separate, additive backup/import.
Staging table: `public.jhc_crawler_ingredient_staging` (RLS enabled, no anon/auth grants).
No changes to the scanner, UI, production product tables, or user-configured ingredient policy.
HALAL/HARAM are the user's *ingredient screening rules*, not certification.

Configure GitHub Actions **repository secrets** (not variables or committed files):
- `JHC_SUPABASE_URL`: `https://vjygltfnrmyghlwyjtwu.supabase.co`
- `JHC_SUPABASE_SERVICE_ROLE_KEY`: Supabase project server-side service-role key. This must never be exposed to the browser or pasted in chat.

Go to Actions → 'Archive Japanese Ingredients to Supabase' → Run workflow.
Afterward, successful crawler runs can trigger the archival workflow automatically.
The archive validates the *highest* of the three recent cumulative checkpoints against SQLite and JSON,
refuses partial snapshots, and inserts in chunks with duplicate-safe conflict handling.
This keeps existing data unchanged and does not claim new products were added without a successful run.
