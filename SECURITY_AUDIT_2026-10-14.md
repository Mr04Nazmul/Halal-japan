# Japan Halal Checker: preliminary security audit (2026-10-14)

Scope reviewed: `api/free-product.js`, `api/research-products.js`, `api/yahoo-product.js`, `app-config.js`, `vercel.json`, selected frontend/research files. This was a source review, **not a penetration test** or a live Supabase configuration audit.

## Changes applied
- `vercel.json`: API-only security headers (nosniff, deny framing, no-referrer, restrictive Permissions-Policy). API-only scope avoids disabling the site's camera scanner.
- `api/research-products.js`: timing-safe comparison of the research admin token, and rejection of disallowed browser Origin values. CORS is **not** an authentication mechanism; non-browser clients can send arbitrary Origin headers, so admin token remains mandatory.
- Confirmed committed versions of both files via GitHub fetch.

## Observations and unfinished checks
- Public Supabase **anon** key in `app-config.js` is intended for public access. Do not confuse it with a service-role secret. Its safety depends on database RLS policies and function authorization; not verified.
- Research endpoint handles credentials via server environment variables; must confirm production variables and rotate any disclosed secrets.
- Yahoo throttling is in-memory/per-instance only. A shared/distributed rate limiter and quota monitoring are needed for dependable cost protection.
- No automated application dependency vulnerability scan or deployed behavior tests were performed here.
- Current image-upload implementation and storage policies have not been fully audited.
- GitHub Pages hosts a public static site; never put private keys in the repository or client-side files.
- Do not assume input validation, no-store responses or API CORS rules alone prevent abuse.
- HTTP response header changes apply when the Vercel endpoint is deployed; they do not automatically configure Supabase Edge Functions.

## Next steps
1. Confirm GitHub Actions/Vercel deployment and check headers with a live request.
2. Review exact Supabase table RLS grants and Edge Function JWT settings.
3. Run dependency scanning and browser test (camera, search, OCR/photo, language switching) after deployment.
4. Add shared rate limiting to server endpoints and audit uploaded file constraints.
