# Ingredient research pipeline

The Vercel serverless endpoint `/api/research-products` supports:
- `GET ?jan_code=...` or `?query=...`: Google Programmable Search discovery and Yahoo Shopping product metadata (no writes).
- `POST` with JSON `{"jan_code":"...", "query":""}`: searches and queues leads in Supabase `public.jhc_ingredient_research_queue`.
- Both endpoints require `X-Research-Token` set to the backend-only `RESEARCH_ADMIN_TOKEN`. **Do not put this token into a public frontend.** Trigger research from a trusted administrator tool only.

Configure these environment variables in the **Vercel backend project** (never GitHub or browser JavaScript):
- `GOOGLE_SEARCH_API_KEY`: Google Programmable Search API key; Google API availability, billing and quotas may apply.
- `GOOGLE_SEARCH_ENGINE_ID`: your search engine ID.
- `YAHOO_CLIENT_ID`: Yahoo! JAPAN Shopping API client ID with valid API access.
- `SUPABASE_URL`: Supabase project URL.
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role credential, server-side only.
- `RESEARCH_ADMIN_TOKEN`: long random private secret.
- `ALLOWED_ORIGINS`: comma-separated trusted frontend origins; CORS is **not** authorization.

The queue table was provisioned in Supabase with RLS on and without anonymous permissions. Search snippets and Yahoo retailer listings are **discovery leads**, not complete manufacturer ingredient evidence. Entries are queued as `needs_review` / `discovery_only`, not added directly to `halal_products`. A reviewer must check the manufacturer's label, exact JAN/pack variation, reuse rights and additive-origin proof before publication.

This workflow leaves the existing camera scanner, UI, Yahoo fallback, and 155 existing `halal_products` records unchanged. Before announcing the feature as live, configure the Vercel project, redeploy, and run a real integration check. No scheduled bulk import is enabled by default.
