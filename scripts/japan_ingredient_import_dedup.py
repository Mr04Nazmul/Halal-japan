"""Fail-closed JAN-8/JAN-13 collision guard for isolated ingredient staging imports.

Existing source-researched records may have URL/hash identities but a JAN-13
that later appears as a crawler 'jan:<barcode>' identity. PostgREST's
on_conflict=identity_key does not ignore the separate unique JAN index.
"""
import json
import re
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from japan_ingredient_barcodes import jan_valid


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
            raise RuntimeError("JAN dedup lookup failed; refusing unsafe import") from exc
        if not isinstance(found, list):
            raise RuntimeError("JAN dedup lookup returned unexpected response")
        for item in found:
            if not isinstance(item, dict):
                raise RuntimeError("JAN dedup lookup returned malformed row")
            code, owner = item.get("jan_code"), item.get("identity_key")
            if code not in batch or not isinstance(owner, str) or not owner:
                raise RuntimeError("JAN dedup lookup returned inconsistent identity")
            if code in owners and owners[code] != owner:
                raise RuntimeError("JAN dedup lookup returned conflicting owners")
            owners[code] = owner
    safe, conflicts = [], []
    for row in rows:
        code = row.get("jan_code")
        if code and code in owners and owners[code] != row["identity_key"]:
            conflicts.append(code)
        else:
            safe.append(row)
    return safe, conflicts


def filter_existing_source_conflicts(rows, base_url, key, opener=None):
    """Deduplicate source URLs without collapsing distinct JAN-coded products.

    One official release page can contain multiple products. Share a source URL
    only when every competing row has a different, checksum-valid JAN. A
    JAN-less row, an identical JAN, or an existing URL owner without a valid
    JAN remains a collision. Existing records are never modified.
    """
    opener = opener or urllib.request.urlopen
    headers = {"apikey": key, "Authorization": "Bearer " + key}
    base = base_url.rstrip("/") + "/rest/v1/jhc_crawler_ingredient_staging"
    existing = {}
    source_owners = {}
    formula_owners = {}
    page_size = 1000
    offset = 0

    def valid_jan(value):
        return isinstance(value, str) and jan_valid(value)

    while True:
        endpoint = (base + "?select=identity_key,source_url,product_name,ingredients_ja,jan_code"
                    "&order=identity_key.asc&limit=" + str(page_size)
                    + "&offset=" + str(offset))
        req = urllib.request.Request(endpoint, headers=headers)
        try:
            with opener(req, timeout=30) as response:
                found = json.loads(response.read())
        except (urllib.error.URLError, ValueError, OSError) as exc:
            raise RuntimeError("Source dedup staging index lookup failed; refusing unsafe import") from exc
        if not isinstance(found, list) or len(found) > page_size:
            raise RuntimeError("Source dedup staging index returned malformed page")
        for item in found:
            if (not isinstance(item, dict)
                    or not isinstance(item.get("identity_key"), str)
                    or not item["identity_key"]
                    or (item.get("source_url") is not None
                        and not isinstance(item["source_url"], str))
                    or (item.get("jan_code") is not None
                        and not isinstance(item.get("jan_code"), str))):
                raise RuntimeError("Source dedup staging index returned malformed row")
            ident = item["identity_key"]
            if ident in existing:
                raise RuntimeError("Source dedup staging index contains duplicate identity")
            source = item.get("source_url")
            existing[ident] = source
            owner_jan = item.get("jan_code")
            if not valid_jan(owner_jan):
                owner_jan = None
            if source:
                source_owners.setdefault(source, {})[ident] = owner_jan
            # JAN-less crawls can rediscover the same formula under a different
            # manufacturer product-page URL. Do not count those as new foods.
            name = item.get("product_name")
            ingredients = item.get("ingredients_ja")
            if (source and isinstance(name, str) and name.strip()
                    and isinstance(ingredients, str) and ingredients.strip()):
                formula = (urlsplit(source).hostname,
                           re.sub(r"\s+", "", name), ingredients.strip())
                formula_owners.setdefault(formula, set()).add(ident)
        if len(found) < page_size:
            break
        offset += page_size

    # A JAN-less page and a JAN-backed page can describe the identical
    # manufacturer formula in the same checkpoint. Prefer the JAN-backed row.
    batch_jan_formulas = set()
    batch_source_rows = {}
    for row in rows:
        src = row.get("source_url")
        if isinstance(src, str):
            batch_source_rows.setdefault(src, []).append(row)
        name, ingredients = row.get("product_name"), row.get("ingredients_ja")
        if (valid_jan(row.get("jan_code")) and isinstance(src, str)
                and isinstance(name, str) and name.strip()
                and isinstance(ingredients, str) and ingredients.strip()):
            batch_jan_formulas.add((urlsplit(src).hostname,
                                    re.sub(r"\s+", "", name), ingredients.strip()))

    safe, conflicts = [], []
    seen_formulas = {}
    for row in rows:
        ident = row["identity_key"]
        source = row.get("source_url")
        if ident in existing:
            safe.append(row)
            continue
        if not isinstance(source, str) or not source.startswith("https://"):
            raise RuntimeError("Source dedup requires a valid HTTPS source URL")

        candidate_jan = row.get("jan_code")
        candidate_has_jan = valid_jan(candidate_jan)

        existing_owners = [(owner, owner_jan)
                           for owner, owner_jan in source_owners.get(source, {}).items()
                           if owner != ident]
        if existing_owners and not (
                candidate_has_jan
                and all(valid_jan(owner_jan) and owner_jan != candidate_jan
                        for _, owner_jan in existing_owners)):
            conflicts.append({"identity_key": ident, "source_url": source,
                              "reason": "existing URL"})
            continue

        same_batch = [other for other in batch_source_rows.get(source, ())
                      if other.get("identity_key") != ident]
        if same_batch:
            if not candidate_has_jan:
                conflicts.append({"identity_key": ident, "source_url": source,
                                  "reason": "same-batch URL"})
                continue
            if any(valid_jan(other.get("jan_code"))
                   and other.get("jan_code") == candidate_jan for other in same_batch):
                conflicts.append({"identity_key": ident, "source_url": source,
                                  "reason": "same-batch URL same JAN"})
                continue
            # Distinct valid JANs may share a multi-product manufacturer page.
            # A competing JAN-less row is rejected when it is processed.

        # Only JAN-less/name identities are ambiguous: different valid JANs
        # may legitimately represent different package sizes or variants.
        if not candidate_has_jan:
            name = row.get("product_name")
            ingredients = row.get("ingredients_ja")
            if isinstance(name, str) and name.strip() and isinstance(ingredients, str) and ingredients.strip():
                formula = (urlsplit(source).hostname,
                           re.sub(r"\s+", "", name), ingredients.strip())
                if formula in batch_jan_formulas:
                    conflicts.append({"identity_key": ident, "source_url": source,
                                      "reason": "same-batch JAN-backed formula"})
                    continue
                if any(owner != ident for owner in formula_owners.get(formula, ())):
                    conflicts.append({"identity_key": ident, "source_url": source,
                                      "reason": "existing same-name same-ingredients"})
                    continue
                if formula in seen_formulas and seen_formulas[formula] != ident:
                    conflicts.append({"identity_key": ident, "source_url": source,
                                      "reason": "same-batch same-name same-ingredients"})
                    continue
                seen_formulas[formula] = ident
        safe.append(row)
    return safe, conflicts

def exceeds_invalid_rejection_limit(total_candidates, invalid_rejections):
    """Fail closed for malformed input, but do not treat safe dedup skips as invalid.

    Existing URL/JAN identity collisions are expected on cumulative reimports.
    They are excluded from this input-quality budget, and still never written.
    """
    if (not isinstance(total_candidates, int) or not isinstance(invalid_rejections, int)
            or total_candidates < 0 or invalid_rejections < 0
            or invalid_rejections > total_candidates):
        raise ValueError("Invalid candidate/rejection counts; refusing import")
    return invalid_rejections > max(10, int(total_candidates * 0.05))
