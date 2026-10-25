"""Fail-closed JAN-13 collision guard for isolated ingredient staging imports.

Existing source-researched records may have URL/hash identities but a JAN-13
that later appears as a crawler 'jan:<barcode>' identity. PostgREST's
on_conflict=identity_key does not ignore the separate unique JAN index.
"""
import json
import urllib.error
import urllib.request


def filter_existing_jan_conflicts(rows, base_url, key, opener=None):
    """Return (safe_rows, conflicting_jans); never modify existing records.

    Fetch only candidate JANs in bounded queries. A JAN already owned by the
    same identity is left for the existing identity-key upsert to ignore.
    A JAN owned by a different identity is skipped, not overwritten.
    Any failed/ambiguous lookup raises RuntimeError and blocks the import.
    """
    opener = opener or urllib.request.urlopen
    codes = sorted({r["jan_code"] for r in rows if r.get("jan_code")})
    owners = {}
    for start in range(0, len(codes), 100):
        batch = codes[start:start + 100]
        endpoint = (
            base_url.rstrip("/") +
            "/rest/v1/jhc_crawler_ingredient_staging"
            "?select=jan_code,identity_key&jan_code=in.(" +
            ",".join(batch) + ")&limit=1000"
        )
        req = urllib.request.Request(endpoint, headers={
            "apikey": key, "Authorization": "Bearer " + key,
        })
        try:
            with opener(req, timeout=30) as response:
                found = json.loads(response.read())
        except (urllib.error.URLError, ValueError, OSError) as exc:
            raise RuntimeError("JAN-13 dedup lookup failed; refusing unsafe import") from exc
        if not isinstance(found, list):
            raise RuntimeError("JAN-13 dedup lookup returned unexpected response")
        for item in found:
            if not isinstance(item, dict):
                raise RuntimeError("JAN-13 dedup lookup returned malformed row")
            code, owner = item.get("jan_code"), item.get("identity_key")
            if code not in batch or not isinstance(owner, str) or not owner:
                raise RuntimeError("JAN-13 dedup lookup returned inconsistent identity")
            if code in owners and owners[code] != owner:
                raise RuntimeError("JAN-13 dedup lookup returned conflicting owners")
            owners[code] = owner
    safe, conflicts = [], []
    for row in rows:
        code = row.get("jan_code")
        if code and code in owners and owners[code] != row["identity_key"]:
            conflicts.append(code)
        else:
            safe.append(row)
    return safe, conflicts
