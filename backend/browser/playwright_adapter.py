import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from backend.browser.schema import BrowserAction, BrowserActionType
from backend.core.logger import app_logger
import os
import urllib.parse

class PlaywrightState:
    """Singleton to hold active playwright instances."""
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        # Headed by default so user can visually witness the automation
        self.headless = os.getenv("NOVA_BROWSER_HEADLESS", "false").lower() == "true"
        self.downloads_path = os.getenv("NOVA_DOWNLOADS_PATH", "downloads")

playwright_state = PlaywrightState()

async def ensure_browser_ready():
    """Guarantees that a playwright browser and page are ready before executing actions."""
    if not playwright_state.playwright or not playwright_state.page or playwright_state.page.is_closed():
        launcher = PlaywrightBrowserLauncher()
        await launcher.execute(BrowserAction(action_type=BrowserActionType.LAUNCH))

class PlaywrightBrowserLauncher:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.playwright:
            playwright_state.playwright = await async_playwright().start()
            
        if not playwright_state.browser or not playwright_state.browser.is_connected():
            playwright_state.browser = await playwright_state.playwright.chromium.launch(
                headless=playwright_state.headless,
                downloads_path=playwright_state.downloads_path,
                args=["--no-sandbox", "--disable-gpu", "--start-maximized"]
            )
            playwright_state.context = await playwright_state.browser.new_context(
                accept_downloads=True,
                no_viewport=True
            )
            playwright_state.page = await playwright_state.context.new_page()
            app_logger.info("Playwright Chromium Launched Successfully")
        elif not playwright_state.page or playwright_state.page.is_closed():
            playwright_state.page = await playwright_state.context.new_page()
            
        return True

class PlaywrightTabManager:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.context:
            return False
            
        if action.action_type == BrowserActionType.NEW_TAB:
            playwright_state.page = await playwright_state.context.new_page()
            
        elif action.action_type == BrowserActionType.CLOSE_TAB:
            if playwright_state.page:
                await playwright_state.page.close()
                pages = playwright_state.context.pages
                if pages:
                    playwright_state.page = pages[-1]
                else:
                    playwright_state.page = None
                    
        elif action.action_type == BrowserActionType.SWITCH_TAB:
            index = action.payload.get("index", 0)
            pages = playwright_state.context.pages
            if 0 <= index < len(pages):
                playwright_state.page = pages[index]
                await playwright_state.page.bring_to_front()
                
        return True

class PlaywrightNavigationManager:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.page:
            return False
            
        if action.action_type == BrowserActionType.NAVIGATE:
            url = action.payload.get("url", "")
            query = action.payload.get("query", "")
            
            if not url and query:
                url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
                
            if url:
                if not url.startswith("http"):
                    url = "https://" + url
                app_logger.info(f"Playwright: Navigating to {url}")
                await playwright_state.page.goto(url, wait_until="domcontentloaded", timeout=20000)
                
                # If a query was searched, attempt to extract the top answer or organic snippet
                if query:
                    try:
                        # Check Google quick answer boxes
                        loc = playwright_state.page.locator("div.VwiC3b, span.hgKElc, div.BNeawe, div.kno-rdesc").first
                        if await loc.count() > 0:
                            snippet = await loc.inner_text()
                            action.payload["output"] = snippet
                            app_logger.info(f"Playwright: Extracted search snippet: {snippet[:100]}...")
                    except Exception as e:
                        app_logger.warning(f"Could not extract search snippet: {e}")
                        
        elif action.action_type == BrowserActionType.RELOAD:
            await playwright_state.page.reload(wait_until="domcontentloaded")
            
        elif action.action_type == BrowserActionType.BACK:
            await playwright_state.page.go_back()
            
        elif action.action_type == BrowserActionType.FORWARD:
            await playwright_state.page.go_forward()
            
        return True

class PlaywrightDOMManager:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.page:
            return False
            
        selector = action.payload.get("selector", "")
        
        if action.action_type == BrowserActionType.CLICK:
            if not selector:
                return False
            await playwright_state.page.click(selector, timeout=10000)
            
        elif action.action_type == BrowserActionType.DOUBLE_CLICK:
            if not selector:
                return False
            await playwright_state.page.dblclick(selector, timeout=10000)
            
        elif action.action_type == BrowserActionType.RIGHT_CLICK:
            if not selector:
                return False
            await playwright_state.page.click(selector, button="right", timeout=10000)
            
        elif action.action_type == BrowserActionType.HOVER:
            if not selector:
                return False
            await playwright_state.page.hover(selector, timeout=10000)
            
        elif action.action_type == BrowserActionType.TYPE:
            text = action.payload.get("text", "")
            if selector:
                await playwright_state.page.type(selector, text)
            else:
                await playwright_state.page.keyboard.type(text)
            
        elif action.action_type == BrowserActionType.FILL:
            text = action.payload.get("text", "")
            if not selector:
                return False
            await playwright_state.page.fill(selector, text)
            
        elif action.action_type == BrowserActionType.EXTRACT_TEXT:
            if selector:
                loc = playwright_state.page.locator(selector).first
                text = await loc.inner_text()
            else:
                text = await playwright_state.page.inner_text("body")
            action.payload["output"] = text
            
        elif action.action_type == BrowserActionType.EXTRACT_HTML:
            if selector:
                html = await playwright_state.page.locator(selector).first.inner_html()
            else:
                html = await playwright_state.page.content()
            action.payload["output"] = html
            
        elif action.action_type == BrowserActionType.SCROLL:
            delta_y = action.payload.get("delta_y", 500)
            await playwright_state.page.mouse.wheel(0, delta_y)
            
        elif action.action_type == BrowserActionType.WAIT_FOR_ELEMENT:
            if not selector:
                return False
            timeout = action.payload.get("timeout_ms", 10000)
            await playwright_state.page.wait_for_selector(selector, timeout=timeout)
            
        return True

class PlaywrightScreenshotManager:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.page:
            return False
            
        path = action.payload.get("path", "screenshot.png")
        full_page = action.payload.get("full_page", False)
        await playwright_state.page.screenshot(path=path, full_page=full_page)
        return True

class PlaywrightPDFExporter:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.page:
            return False
            
        path = action.payload.get("path", "page.pdf")
        await playwright_state.page.pdf(path=path)
        return True

class PlaywrightJavaScriptExecutor:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.page:
            return False
            
        script = action.payload.get("script", "")
        if script:
            res = await playwright_state.page.evaluate(script)
            action.payload["output"] = str(res)
        return True

class PlaywrightDownloadManager:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.page:
            return False
            
        selector = action.payload.get("selector")
        if selector:
            async with playwright_state.page.expect_download() as download_info:
                await playwright_state.page.click(selector)
            download = await download_info.value
            path = os.path.join(playwright_state.downloads_path, download.suggested_filename)
            await download.save_as(path)
            action.payload["output"] = path
        return True

class PlaywrightCookieManager:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        return True

class PlaywrightNetworkMonitor:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.page:
            return False
        if action.action_type == BrowserActionType.WAIT_FOR_NETWORK:
            await playwright_state.page.wait_for_load_state("networkidle")
        return True

class PlaywrightUploadManager:
    async def execute(self, action: BrowserAction) -> bool:
        await ensure_browser_ready()
        if not playwright_state.page:
            return False
            
        selector = action.payload.get("selector")
        file_path = action.payload.get("file_path")
        if selector and file_path:
            await playwright_state.page.set_input_files(selector, file_path)
        return True
