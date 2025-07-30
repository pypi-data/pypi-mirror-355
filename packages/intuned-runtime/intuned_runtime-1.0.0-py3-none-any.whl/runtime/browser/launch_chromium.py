import json
import os
import tempfile
from contextlib import asynccontextmanager
from os.path import join
from typing import Any
from typing import Optional
from typing import Literal
import logging
import aiofiles
from playwright.async_api import async_playwright
from playwright.async_api import Browser
from playwright.async_api import ProxySettings

logger = logging.getLogger(__name__)


def get_proxy_env() -> Optional[ProxySettings]:
    server = os.getenv("PROXY_SERVER")
    username = os.getenv("PROXY_USERNAME")
    password = os.getenv("PROXY_PASSWORD")
    if server is None or username is None or password is None:
        return None
    return {
        "server": server,
        "username": username,
        "password": password,
    }


chromium_launch_args_to_ignore = [
    "--disable-field-trial-config",
    "--disable-background-networking",
    "--enable-features=NetworkService,NetworkServiceInProcess",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-back-forward-cache",
    "--disable-breakpad",
    "--disable-client-side-phishing-detection",
    "--disable-component-extensions-with-background-pages",
    "--disable-component-update",
    "--no-default-browser-check",
    "--disable-default-apps",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-features=ImprovedCookieControls,LazyFrameLoading,GlobalMediaControls,DestroyProfileOnBrowserClose,MediaRouter,DialMediaRouteProvider,AcceptCHFrame,AutoExpandDetailsElement,CertificateTransparencyComponentUpdater,AvoidUnnecessaryBeforeUnloadCheckSync,Translate,TranslateUI",
    "--allow-pre-commit-input",
    "--disable-hang-monitor",
    "--disable-ipc-flooding-protection",
    "--disable-prompt-on-repost",
    "--disable-renderer-backgrounding",
    "--force-color-profile=srgb",
    "--metrics-recording-only",
    "--no-first-run",
    "--enable-automation",
    "--password-store=basic",
    "--use-mock-keychain",
    "--no-service-autorun",
    "--export-tagged-pdf",
    "--enable-use-zoom-for-dsf=false",
    "--disable-popup-blocking",
]


async def create_user_dir_with_preferences():
    # Create a temporary directory
    playwright_temp_dir = tempfile.mkdtemp(prefix="pw-")
    user_dir = join(playwright_temp_dir, "userdir")
    default_dir = join(user_dir, "Default")

    # Create the default directory recursively
    os.makedirs(default_dir, exist_ok=True)

    # Preferences data
    preferences = {
        "plugins": {
            "always_open_pdf_externally": True,
        }
    }

    # Write preferences to file
    async with aiofiles.open(join(default_dir, "Preferences"), mode="w") as f:
        await f.write(json.dumps(preferences))

    return os.path.abspath(user_dir)


extra_args = [
    "--no-first-run",
    "--disable-sync",
    "--disable-translate",
    "--disable-features=TranslateUI",
    "--disable-features=NetworkService",
    "--lang=en",
    "--disable-blink-features=AutomationControlled",
]

default_user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"


@asynccontextmanager
async def launch_chromium(
    headless: bool = True,
    timeout: int = 10,
    cdp_address: str | None = None,
    **kwargs: Any,
):
    async with async_playwright() as playwright:
        if cdp_address is not None:
            browser: Browser = await playwright.chromium.connect_over_cdp(cdp_address)
            context = browser.contexts[0]
            dir = None
        else:
            dir = await create_user_dir_with_preferences()
            if kwargs.get("proxy") is None:
                proxy_env = get_proxy_env()
            else:
                proxy_env = kwargs.get("proxy")
            # Remove proxy from kwargs if it exists
            kwargs.pop("proxy", None)
            viewport = kwargs.get("viewport", {"width": 1280, "height": 800})
            kwargs.pop("viewport", None)

            if headless:
                chromium_launch_args_to_ignore.append("--headless")
                extra_args.append("--headless=new")

            context = await playwright.chromium.launch_persistent_context(
                dir,
                headless=headless,
                viewport=viewport,
                proxy=proxy_env,
                # ignore_default_args=chromium_launch_args_to_ignore,
                user_agent=os.environ.get("USER_AGENT", default_user_agent),
                # args=extra_args,
                **kwargs,
            )
        context.set_default_timeout(timeout * 1000)

        async def remove_dir_after_close(*_: Any, **__: Any) -> None:
            if not dir:
                return
            os.system(f"rm -rf {os.path.realpath(dir)}")

        context.once("close", remove_dir_after_close)
        yield context, context.pages[0]


async def dangerous_launch_chromium(
    headless: bool = True,
    timeout: int = 10,
    web_socket: str | None = None,
    cdp_url: str | None = None,
    connection_method: Literal["ws", "cdp"] | None = None,
    **kwargs: Any,
):
    playwright = await async_playwright().start()
    if web_socket is not None and connection_method == "ws":
        logging.info(f"Connecting to ws: {web_socket}")
        browser: Browser = await playwright.chromium.connect(web_socket)
        browser.on("disconnected", lambda: logging.info("Browser Session disconnected"))
        await browser.new_context(
            viewport={"width": 1280, "height": 800}, user_agent=default_user_agent
        )
        context = browser.contexts[0]
        dir = None
    elif cdp_url is not None and connection_method == "cdp":
        logging.info(f"Connecting to cdp: {cdp_url}")
        browser: Browser = await playwright.chromium.connect_over_cdp(cdp_url)
        browser.on("disconnected", lambda: logging.info("Browser Session disconnected"))
        context = browser.contexts[0]
        dir = None
    elif web_socket is None and cdp_url is None and connection_method is None:
        logging.info("Launching local browser")
        dir = await create_user_dir_with_preferences()
        logging.info(f"Using user data directory: {dir}")
        if kwargs.get("proxy") is None:
            proxy_env = get_proxy_env()
        else:
            proxy_env = kwargs.get("proxy")
        # Remove proxy from kwargs if it exists
        kwargs.pop("proxy", None)
        viewport = kwargs.get("viewport", {"width": 1280, "height": 800})
        kwargs.pop("viewport", None)

        if headless:
            chromium_launch_args_to_ignore.append("--headless")
            extra_args.append("--headless=new")

        context = await playwright.chromium.launch_persistent_context(
            dir,
            headless=headless,
            viewport=viewport,
            proxy=proxy_env,
            ignore_default_args=chromium_launch_args_to_ignore,
            user_agent=os.environ.get("USER_AGENT", default_user_agent),
            args=extra_args,
            **kwargs,
        )
    else:
        raise ValueError(
            "You have to provide method if you are launching a remote browser with ws or cdp"
        )
    context.set_default_timeout(timeout * 1000)

    async def remove_dir_after_close(*_: Any, **__: Any) -> None:
        if not dir:
            return
        os.system(f"rm -rf {os.path.realpath(dir)}")

    context.once("close", remove_dir_after_close)
    return playwright, context
