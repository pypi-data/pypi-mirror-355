from contextlib import asynccontextmanager

from playwright.async_api import ProxySettings

from ..browser import launch_chromium


@asynccontextmanager
async def get_production_playwright_constructs(
    proxy: ProxySettings | None = None,
    headless: bool = False,
    *,
    cdp_address: str | None = None,
):
    async with launch_chromium(headless=headless, cdp_address=cdp_address, proxy=proxy) as (context, page):
        try:
            yield context, page
        finally:
            await context.close()
