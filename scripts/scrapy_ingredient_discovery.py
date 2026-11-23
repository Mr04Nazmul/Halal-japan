import re
import unicodedata
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import scrapy
from scrapy.selector import Selector
from scrapy.http import TextResponse
from japan_ingredient_source_terms import is_terms_restricted_url


INGREDIENT_LABELS = {
    "原材料名",
    "原材料",
    "原材料名/添加物名",
    "原材料(一括表示ラベル)",
}

DETAIL_PATH_PATTERNS = (
    re.compile(r"/products/[^/]+/\d+\.html$"),
    re.compile(r"/products/detail/\d+$"),
    re.compile(r"/product/detail/\d+$"),
    re.compile(r"/products/\d+$"),
    re.compile(r"/products_search/[^/]+/item_\d+$"),
    re.compile(r"/product/item/\d+$"),
    re.compile(r"/item/\d+\.html$"),
    re.compile(r"/products/catalog/cd_[^/]+\.html$"),
    re.compile(r"/products/(?:carbonated|coffee)/[^/]+/[^/]+\.html$"),
)


def _compact(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or ""))


def is_product_detail_url(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    query = parse_qs(parsed.query)

    if path.endswith("/products/detail.php") and query.get("id"):
        return True
    if path.endswith("/product/search/detail") and query.get("id"):
        return True
    if path.endswith("/catalog/products/index.php") and query.get("id"):
        return True
    if (
        parsed.hostname == "shop.kyoritsu-foods.co.jp"
        and re.fullmatch(r"/item-detail/\\d+", path)
        and not parsed.query
    ):
        return True
    return any(pattern.search(path) for pattern in DETAIL_PATH_PATTERNS)


def has_declared_ingredient_field(selector):
    # Require an actual labelled field and a non-empty adjacent value. A
    # disclaimer that merely mentions 原材料 (for example, "ingredients may
    # change") is not ingredient evidence.
    for node in selector.css("th,dt,h2,h3,h4,strong,b,span,label,div,p"):
        label = _compact("".join(node.css("::text").getall())).strip(":：")
        if label not in INGREDIENT_LABELS:
            continue

        value = "".join(node.xpath("following-sibling::*[1]//text()").getall()).strip()
        if not value:
            value = "".join(node.xpath("following-sibling::text()[1]").getall()).strip()
        if len(_compact(value)) >= 2:
            return True

    # Some official pages render the complete labelled declaration in one
    # paragraph instead of a separate label/value pair.
    for text in selector.css("p::text,li::text").getall():
        compact = _compact(text)
        if re.match(r"^(?:原材料名|原材料)[:：]\S{2,}", compact):
            return True
    return False


def is_allowed_source_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or is_terms_restricted_url(url):
        return False

    # Kyoritsu's shop is a bounded discovery source: exact item details,
    # the root catalogue, and one numeric categoryId filter only.
    if parsed.hostname == "shop.kyoritsu-foods.co.jp":
        path = parsed.path.rstrip("/") or "/"
        if path == "/" and not parsed.query:
            return True
        if path == "/item-list":
            query = parse_qs(parsed.query, keep_blank_values=True)
            return (
                set(query) == {"categoryId"}
                and len(query["categoryId"]) == 1
                and query["categoryId"][0].isdigit()
            )
        if re.fullmatch(r"/item-detail/\\d+", path) and not parsed.query:
            return True
        return False

    return True


def response_text(response):
    """Return decoded HTML text, or None for binary/non-text responses."""
    if not isinstance(response, TextResponse):
        return None
    try:
        return response.text
    except (AttributeError, UnicodeError):
        return None


def is_ingredient_product_candidate(url, html):
    if not is_allowed_source_url(url) or not is_product_detail_url(url):
        return False
    return has_declared_ingredient_field(Selector(text=html))


class JapaneseProductLinks(scrapy.Spider):
    name = "japanese_product_links"
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DEPTH_LIMIT": 2,
        "CLOSESPIDER_PAGECOUNT": 300,
        "LOG_LEVEL": "INFO",
    }

    async def start(self):
        for request in self.start_requests():
            yield request

    def start_requests(self):
        seeds = Path("data/manufacturer_seed_urls.txt")
        seed_urls = [
            line.strip()
            for line in seeds.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("https://") and is_allowed_source_url(line.strip())
        ]
        # Put the bounded Kyoritsu category pages first; they were previously
        # excluded by the first-80 cap because they sit at the end of the seed file.
        kyoritsu_categories = [
            url for url in seed_urls
            if urlparse(url).hostname == "shop.kyoritsu-foods.co.jp"
            and urlparse(url).path.rstrip("/") == "/item-list"
            and is_allowed_source_url(url)
        ]
        ordered_seeds = kyoritsu_categories + [url for url in seed_urls if url not in kyoritsu_categories]
        for url in ordered_seeds[:120]:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={"origin_host": urlparse(url).hostname},
            )

    def parse(self, response):
        if not is_allowed_source_url(response.url):
            return
        if response.status != 200:
            return

        html = response_text(response)
        if html is None:
            self.crawler.stats.inc_value("jhc/non_text_responses_skipped")
            return

        if is_ingredient_product_candidate(response.url, html):
            yield {
                "url": response.url,
                "ingredient_page_candidate": True,
                "source": "scrapy",
            }

        for href in response.css("a::attr(href)").getall()[:200]:
            url = response.urljoin(href)
            if urlparse(url).hostname != response.meta["origin_host"]:
                continue
            if not is_allowed_source_url(url):
                continue
            path = urlparse(url).path
            if any(token in path for token in ("/product", "/item", "/goods")):
                yield response.follow(url, callback=self.parse, meta=response.meta)
