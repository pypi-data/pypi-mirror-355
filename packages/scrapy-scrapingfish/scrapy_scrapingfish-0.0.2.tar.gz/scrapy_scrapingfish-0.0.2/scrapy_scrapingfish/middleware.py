import asyncio

import aiohttp

from scrapy.http import HtmlResponse
from scrapy.exceptions import NotConfigured


class ScrapingFishProxyMiddleware:
    def __init__(self, api_key, timeout=90, settings=None):
        self.api_key = api_key
        self.timeout = timeout
        self.settings = settings

    @classmethod
    def from_crawler(cls, crawler):
        api_key = crawler.settings.get("SCRAPINGFISH_API_KEY")
        if not api_key:
            raise NotConfigured("SCRAPINGFISH_API_KEY is not set in settings.py")

        return cls(
            api_key=api_key,
            timeout=crawler.settings.get("SCRAPINGFISH_TIMEOUT", 90),
            settings=crawler.settings.get("SCRAPINGFISH_REQUEST_PARAMS", {}),
        )

    async def process_request(self, request, spider):
        payload = {
            "api_key": self.api_key,
            "url": request.url,
        }
        payload.update(self.settings)

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            try:
                async with session.get(
                    "https://scraping.narf.ai/api/v1/", params=payload
                ) as proxy_response:
                    if proxy_response.status == 401:
                        spider.logger.error("Bad API key or no more credits available")
                        return None

                    body = await proxy_response.read()
                    return HtmlResponse(
                        url=request.url,
                        status=proxy_response.status,
                        body=body,
                        encoding="utf-8",
                        request=request,
                    )
            except asyncio.TimeoutError:
                spider.logger.error("ScrapingFish request timed out")
                return None
            except aiohttp.ClientError as e:
                spider.logger.error(f"ScrapingFish request failed: {e}")
                return None
