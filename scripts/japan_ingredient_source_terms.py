"""Source-terms gate for ingredient-text collection and reuse.

Checked 2026-11-22. These two publishers explicitly restrict copying or
republishing website content without permission. Until written permission or
a compatible licence is established, do not fetch, extract, or import their
ingredient text into the product database.
"""
from urllib.parse import urlsplit

RESTRICTED_SOURCE_POLICIES = {
    "meiji.co.jp": {
        "policy_url": "https://www.meiji.co.jp/regulation/",
        "reason": "site terms limit copying and reuse to personal or household use and prohibit transfer to other websites or printed materials",
        "reviewed_on": "2026-11-22",
    },
    "fujiya-peko.co.jp": {
        "policy_url": "https://www.fujiya-peko.co.jp/copyright/",
        "reason": "site policy prohibits reproduction, alteration, transfer, distribution, and commercial use of site content without consent",
        "reviewed_on": "2026-11-22",
    },
}


def source_terms_restriction(url):
    try:
        host = (urlsplit(str(url)).hostname or "").lower().rstrip(".")
    except (TypeError, ValueError):
        return None
    if not host:
        return None
    for domain, policy in RESTRICTED_SOURCE_POLICIES.items():
        if host == domain or host.endswith("." + domain):
            return {"domain": domain, **policy}
    return None


def is_terms_restricted_url(url):
    return source_terms_restriction(url) is not None
