"""Source-terms gate for ingredient-text collection and reuse.

Reviewed 2026-11-23. This gate blocks sources with express reuse restrictions and sources whose site policy asserts copyright ownership while bulk reuse permission remains unestablished. Do not fetch, extract, or import ingredient text from blocked sources until permission or a compatible licence is established. Existing database rows are not modified.
"""
from urllib.parse import urlsplit

SOURCE_TERMS_POLICY_VERSION = "2026-11-23-v14"

RESTRICTED_SOURCE_POLICIES = {
    "sokensha.co.jp": {
        "policy_url": "https://sokensha.co.jp/",
        "reason": "Sokensha corporate pages display a copyright notice; no compatible licence or bulk ingredient-data reuse permission is established, so automated collection/import is paused pending rights-holder clarification.",
        "reviewed_on": "2026-11-23",
    },
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
    "askul.co.jp": {
        "policy_url": "https://www.askul.co.jp/etc/disclaimer.html",
        "reason": "ASKUL states product-information content belongs to ASKUL or rights holders and prohibits copying, adaptation, reuse, distribution, public transmission, or third-party provision without prior consent beyond legally permitted scope",
        "reviewed_on": "2026-11-23",
    },
    "fujiya-peko.co.jp": {
        "policy_url": "https://www.fujiya-peko.co.jp/copyright/",
        "reason": "site policy prohibits reproduction, alteration, transfer, distribution, and commercial use of site content without consent",
        "reviewed_on": "2026-11-22",
    },
    "bourbon.co.jp": {
        "policy_url": "https://www.bourbon.co.jp/terms.html",
        "reason": "Bourbon terms permit only personal private use; downloading, copying, modifying, distributing, transmitting, reusing on other websites or printed materials, or commercial use without consent is prohibited",
        "reviewed_on": "2026-11-22",
    },
    "dydo.co.jp": {
        "policy_url": "https://holdings.dydo.co.jp/terms/",
        "reason": "DyDo terms allow personal use but prohibit reprinting website content on other websites or printed materials and prohibit unauthorized copying, secondary use, or sale",
        "reviewed_on": "2026-11-22",
    },
    "fujicco.co.jp": {
        "policy_url": "https://www.fujicco.co.jp/about.html",
        "reason": "Fujicco permits private use but prohibits reuse or transfer of site content to other websites or printed materials",
        "reviewed_on": "2026-11-22",
    },
    "kamedaseika.co.jp": {
        "policy_url": "https://www.kamedaseika.co.jp/guide/",
        "reason": "Kameda terms limit website content to personal or legally permitted use and prohibit unauthorized reproduction, modification, distribution, transmission, or commercial use beyond that scope",
        "reviewed_on": "2026-11-22",
    },
    "sanko-seika.co.jp": {
        "policy_url": "https://www.sanko-seika.co.jp/terms/",
        "reason": "Sanko Seika terms prohibit using, reproducing, altering, or distributing website content without authorization, including commercial reuse",
        "reviewed_on": "2026-11-22",
    },
    "myojofoods.co.jp": {
        "policy_url": "https://www.nissin.com/jp/docs/terms/",
        "reason": "Myojo Foods is included in the Nissin Group's stated group definition; the group terms prohibit use beyond private or other legally permitted scope without authorization",
        "reviewed_on": "2026-11-22",
    },
    "natori.co.jp": {
        "policy_url": "https://www.natori.co.jp/policy.html",
        "reason": "Natori limits use of site content to private or other legally permitted scope and prohibits reuse on other websites or printed materials",
        "reviewed_on": "2026-11-22",
    },
    "nissin.com": {
        "policy_url": "https://www.nissin.com/jp/docs/terms/",
        "reason": "Nissin Group terms prohibit use, copying, alteration or distribution beyond private or other legally permitted scope without authorization",
        "reviewed_on": "2026-11-22",
    },
    "sbfoods.co.jp": {
        "policy_url": "https://www.sbfoods.co.jp/terms/",
        "reason": "S&B terms prohibit use of website content beyond private or other legally permitted scope without prior permission",
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
    "nagatanien.co.jp": {
        "policy_url": "https://www.nagatanien.co.jp/sitepolicy/",
        "reason": "Nagatanien site policy states that website text, images, video and programs are copyrighted by Nagatanien; bulk ingredient-data reuse permission or a compatible licence is not established, so collection/import is paused pending rights-holder clarification.",
        "reviewed_on": "2026-11-23",
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
    "hikarimiso.co.jp": {
        "policy_url": "https://www.hikarimiso.co.jp/siteguide/",
        "reason": "Hikari Miso permits private use but prohibits reuse of site content on other websites or printed matter without permission",
        "reviewed_on": "2026-11-22",
    },
    "hanamaruki.co.jp": {
        "policy_url": "https://www.hanamaruki.co.jp/sitepolicy/",
        "reason": "Hanamaruki site policy permits content use only for private purposes and requires company permission for reproduction, republication, transmission, distribution, or other secondary use",
        "reviewed_on": "2026-11-23",
    },
    "calbee.co.jp": {
        "policy_url": "https://www.calbee.co.jp/policy/",
        "reason": "Calbee site policy prohibits unauthorized use or reproduction of site intellectual property, including text.",
        "reviewed_on": "2026-11-23",
    },
    "ebarafoods.com": {
        "policy_url": "https://www.ebarafoods.com/guide/",
        "reason": "Ebara website terms prohibit unauthorized use, reproduction, adaptation, distribution, or public transmission of site works except as allowed by copyright law.",
        "reviewed_on": "2026-11-23",
    },
    "imuraya.co.jp": {
        "policy_url": "https://www.imuraya.co.jp/site-policy/",
        "reason": "Imuraya site policy states that site works may not be used without prior company permission.",
        "reviewed_on": "2026-11-23",
    },
    "kikkoman.co.jp": {
        "policy_url": "https://www.kikkoman.co.jp/kiyaku/kiyaku.html",
        "reason": "Kikkoman website terms restrict use of site content to private use and other copyright-law exceptions; unauthorized use is not allowed.",
        "reviewed_on": "2026-11-23",
    },
    "morinagamilk.co.jp": {
        "policy_url": "https://www.morinagamilk.co.jp/terms_of_use/",
        "reason": "Morinaga Milk terms prohibit unauthorized use, reproduction, modification, distribution, or publication beyond private use and require prior permission.",
        "reviewed_on": "2026-11-23",
    },
    "housefoods.jp": {
        "policy_url": "https://housefoods.jp/term_of_use.html",
        "reason": "House Foods terms state that site text and other information are copyright-protected and cannot be used without authorization beyond legally permitted exceptions.",
        "reviewed_on": "2026-11-23",
    },
    "tajimaya-cc.net": {
        "policy_url": "https://www.tajimaya-cc.net/service",
        "reason": "Tajimaya site footer asserts copyright for site content; bulk ingredient-data reuse permission is not established, so automated collection/import is paused pending rights-holder clarification.",
        "reviewed_on": "2026-11-23",
    },
    "tablemark.co.jp": {
        "policy_url": "https://www.tablemark.co.jp/content/terms.html",
        "reason": "Tablemark terms restrict unauthorized use of site content beyond uses permitted by copyright law.",
        "reviewed_on": "2026-11-23",
    },
    "lotte.co.jp": {
        "policy_url": "https://www.lotte.co.jp/agreement/index.html",
        "reason": "Lotte terms prohibit copying, modifying, distributing, or publicly transmitting site information beyond private-use copyright exceptions without company consent.",
        "reviewed_on": "2026-11-23",
    },
    "marusanai.co.jp": {
        "policy_url": "https://www.marusanai.co.jp/privacy/",
        "reason": "Marusan-Ai prohibits unauthorized use or copying of site content for purposes other than noncommercial private use",
        "reviewed_on": "2026-11-22",
    },
    "itoen.jp": {
        "policy_url": "https://www.itoen.co.jp/agreement/",
        "reason": "Ito En terms restrict use, reproduction, distribution, alteration, or republication of site information beyond private use without prior consent",
        "reviewed_on": "2026-11-22",
    },
    "kewpie.co.jp": {
        "policy_url": "https://www.kewpie.com/policy/",
        "reason": "Kewpie prohibits unauthorized use of website content beyond private or legally permitted scope, including reuse on other websites or printed materials",
        "reviewed_on": "2026-11-22",
    },
    "meg-snow.com": {
        "policy_url": "https://www.meg-snow.com/rule/",
        "reason": "Megmilk Snow Brand limits content use to private or legally permitted scope and prohibits reuse on other websites or printed media without consent",
        "reviewed_on": "2026-11-22",
    },
    "yotsuba.co.jp": {
        "policy_url": "https://www.yotsuba.co.jp/guide/rule/",
        "reason": "Yotsuba prohibits unauthorized use of copyrighted website content beyond personal or legally permitted use",
        "reviewed_on": "2026-11-22",
    },
    "yamamori.co.jp": {
        "policy_url": "https://www.yamamori.co.jp/policy-site",
        "reason": "Yamamori site policy states that site text, graphics, photos, and data are owned by Yamamori or their rights holders and may not be used, copied, reprinted, transmitted, or modified without consent or a legal exception; bulk ingredient-data reuse permission is not established.",
        "reviewed_on": "2026-11-23",
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
