"""Source-terms gate for ingredient-text collection and reuse.

Reviewed 2026-11-22. These publishers' published terms restrict copying,
redistribution, publication, or reuse of website content beyond private-use or
other legally permitted exceptions unless the rights holder grants permission.
Do not fetch, extract, or import their ingredient text until permission or a
compatible licence is established. Existing database rows are not modified.
"""
from urllib.parse import urlsplit

RESTRICTED_SOURCE_POLICIES = {
    # Ajinomoto AGF has a separate policy from the parent Ajinomoto site.
    "agf.ajinomoto.co.jp": {
        "policy_url": "https://agf.ajinomoto.co.jp/website.html",
        "reason": "AGF site terms allow copying for private use but prohibit unauthorized modification, reproduction, or reuse",
        "reviewed_on": "2026-11-22",
    },
    "ajinomoto.co.jp": {
        "policy_url": "https://www.ajinomoto.co.jp/terms/",
        "reason": "Ajinomoto terms prohibit unauthorized reproduction, modification, or distribution of site information beyond expressly permitted or legally allowed use",
        "reviewed_on": "2026-11-22",
    },
    "asahi-gf.co.jp": {
        "policy_url": "https://www.asahigroup-holdings.com/privacy_policy/terms.html",
        "reason": "Asahi group terms include Asahi Group Foods as a domestic subsidiary and restrict reuse beyond private or other legally permitted scope",
        "reviewed_on": "2026-11-22",
    },
    "asahiinryo.co.jp": {
        "policy_url": "https://www.asahigroup-holdings.com/privacy_policy/terms.html",
        "reason": "Asahi group terms include Asahi Beverage as a domestic subsidiary and restrict reuse beyond private or other legally permitted scope",
        "reviewed_on": "2026-11-22",
    },
    "fujiya-peko.co.jp": {
        "policy_url": "https://www.fujiya-peko.co.jp/copyright/",
        "reason": "site policy prohibits reproduction, alteration, transfer, distribution, and commercial use of site content without consent",
        "reviewed_on": "2026-11-22",
    },
    "maruchan.co.jp": {
        "policy_url": "https://www.maruchan.co.jp/customer/terms.html",
        "reason": "Toyo Suisan requires prior permission for reproduction, modification, adaptation, translation, or distribution except where copyright law permits",
        "reviewed_on": "2026-11-22",
    },
    "meiji.co.jp": {
        "policy_url": "https://www.meiji.co.jp/regulation/",
        "reason": "site terms limit copying and reuse to personal or household use and prohibit transfer to other websites or printed materials",
        "reviewed_on": "2026-11-22",
    },
    "meito-abc.co.jp": {
        "policy_url": "https://www.meito-abc.co.jp/terms/",
        "reason": "Meito terms restrict site information to private use and ask users not to copy, upload, publish, or quote it on other websites or printed matter",
        "reviewed_on": "2026-11-22",
    },
    "morinaga.co.jp": {
        "policy_url": "https://www.morinaga.co.jp/terms/",
        "reason": "Morinaga terms prohibit reuse, copying, distribution, or transfer of site data without consent; stated public product-site permission is limited to qualifying non-commercial personal websites",
        "reviewed_on": "2026-11-22",
    },
    "muso.co.jp": {
        "policy_url": "https://muso.co.jp/privacypolicy/",
        "reason": "MUSO terms prohibit use or publication of site content beyond personal private-use scope without permission",
        "reviewed_on": "2026-11-22",
    },
    "nipponham.co.jp": {
        "policy_url": "https://www.nipponham.co.jp/corporate/rules/",
        "reason": "Nippon Ham permits personal downloads and printing but prohibits transfer of website content to other websites or printed materials",
        "reviewed_on": "2026-11-22",
    },
    "tohato.jp": {
        "policy_url": "https://www.tohato.jp/about/",
        "reason": "Tohato site conditions explicitly prohibit secondary use of all or part of site content",
        "reviewed_on": "2026-11-22",
    },
    "topvalu.net": {
        "policy_url": "https://www.topvalu.net/terms/",
        "reason": "TOPVALU terms prohibit use, copying, sale, or publication beyond personal private-use scope without rights-holder consent",
        "reviewed_on": "2026-11-22",
    },
    "7premium.jp": {
        "policy_url": "https://7premium.jp/term",
        "reason": "Seven Premium terms prohibit use of site content, including text and product information, without rights-holder consent",
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
