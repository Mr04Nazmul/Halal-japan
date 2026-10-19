import scrapy
from urllib.parse import urlparse
from pathlib import Path

class JapaneseProductLinks(scrapy.Spider):
    name="japanese_product_links"
    custom_settings={"ROBOTSTXT_OBEY":True,"DOWNLOAD_DELAY":2,"CONCURRENT_REQUESTS_PER_DOMAIN":1,"DEPTH_LIMIT":2,"CLOSESPIDER_PAGECOUNT":300,"LOG_LEVEL":"INFO"}
    async def start(self):
        for request in self.start_requests():
            yield request

    def start_requests(self):
        seeds=Path("data/manufacturer_seed_urls.txt")
        for u in seeds.read_text(encoding="utf-8").splitlines()[:80]:
            u=u.strip()
            if u.startswith("https://"):yield scrapy.Request(u,callback=self.parse,meta={"origin_host":urlparse(u).hostname})
    def parse(self,response):
        if response.status!=200:return
        text=response.css("body ::text").getall()
        if any("原材料" in t for t in text):
            yield {"url":response.url,"ingredient_page_candidate":True,"source":"scrapy"}
        for href in response.css("a::attr(href)").getall()[:200]:
            u=response.urljoin(href)
            if urlparse(u).hostname != response.meta["origin_host"]:continue
            if any(k in u for k in ("/product","/item","/goods")):
                yield response.follow(u,callback=self.parse,meta=response.meta)
