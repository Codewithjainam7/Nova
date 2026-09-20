import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from backend.browser.schema import BrowserAction, BrowserActionType
from backend.core.logger import app_logger
import os

class PlaywrightState:
    """Singleton-like object to hold the active playwright instances."""
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.headless = os.getenv("NOVA_BROWSER_HEADLESS", "false").lower() == "true"
        self.downloads_path = os.getenv("NOVA_DOWNLOADS_PATH", "downloads")

playwright_state = PlaywrightState()

class PlaywrightBrowserLauncher:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.playwright:
            playwright_state.playwright = await async_playwright().start()
            playwright_state.browser = await playwright_state.playwright.chromium.launch(
                headless=playwright_state.headless,
                downloads_path=playwright_state.downloads_path,
                args=["--no-sandbox", "--disable-gpu"]
            )
            # Create persistent context equivalent
            playwright_state.context = await playwright_state.browser.new_context(
                accept_downloads=True
            )
            playwright_state.page = await playwright_state.context.new_page()
            app_logger.info("Playwright Browser Launched Successfully")
        return True

class PlaywrightTabManager:
    async def execute(self, action: BrowserAction) -> bool:
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
        return True

class PlaywrightNavigationManager:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.page:
            return False
            
        if action.action_type == BrowserActionType.NAVIGATE:
            url = action.payload.get("url")
            if url:
                if not url.startswith("http"):
                    url = "https://" + url
                await playwright_state.page.goto(url, wait_until="domcontentloaded")
                
        elif action.action_type == BrowserActionType.RELOAD:
            await playwright_state.page.reload(wait_until="domcontentloaded")
            
        elif action.action_type == BrowserActionType.BACK:
            await playwright_state.page.go_back()
            
        elif action.action_type == BrowserActionType.FORWARD:
            await playwright_state.page.go_forward()
            
        return True

class PlaywrightDOMManager:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.page:
            return False
            
        selector = action.payload.get("selector")
        if not selector:
            return False
            
        if action.action_type == BrowserActionType.CLICK:
            await playwright_state.page.click(selector)
            
        elif action.action_type == BrowserActionType.DOUBLE_CLICK:
            await playwright_state.page.dblclick(selector)
            
        elif action.action_type == BrowserActionType.RIGHT_CLICK:
            await playwright_state.page.click(selector, button="right")
            
        elif action.action_type == BrowserActionType.HOVER:
            await playwright_state.page.hover(selector)
            
        elif action.action_type == BrowserActionType.TYPE:
            text = action.payload.get("text", "")
            await playwright_state.page.type(selector, text)
            
        elif action.action_type == BrowserActionType.FILL:
            text = action.payload.get("text", "")
            await playwright_state.page.fill(selector, text)
            
        return True

class PlaywrightScreenshotManager:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.page:
            return False
            
        path = action.payload.get("path", "screenshot.png")
        full_page = action.payload.get("full_page", False)
        
        await playwright_state.page.screenshot(path=path, full_page=full_page)
        return True

class PlaywrightPDFExporter:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.page:
            return False
            
        path = action.payload.get("path", "page.pdf")
        await playwright_state.page.pdf(path=path)
        return True

class PlaywrightJavaScriptExecutor:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.page:
            return False
            
        script = action.payload.get("script", "")
        if script:
            await playwright_state.page.evaluate(script)
        return True

class PlaywrightDownloadManager:
    async def execute(self, action: BrowserAction) -> bool:
        # Note: Playwright handles downloads via an event listener.
        # This wrapper expects a direct click that triggers a download.
        if not playwright_state.page:
            return False
            
        selector = action.payload.get("selector")
        if selector:
            async with playwright_state.page.expect_download() as download_info:
                await playwright_state.page.click(selector)
            download = await download_info.value
            path = os.path.join(playwright_state.downloads_path, download.suggested_filename)
            await download.save_as(path)
        return True

class PlaywrightCookieManager:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.context:
            return False
        # Implementation depends on action.payload, for now just a stub to return True
        return True

class PlaywrightNetworkMonitor:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.page:
            return False
        if action.action_type == BrowserActionType.WAIT_FOR_NETWORK:
            await playwright_state.page.wait_for_load_state("networkidle")
        return True

class PlaywrightUploadManager:
    async def execute(self, action: BrowserAction) -> bool:
        if not playwright_state.page:
            return False
            
        selector = action.payload.get("selector")
        file_path = action.payload.get("file_path")
        if selector and file_path:
            await playwright_state.page.set_input_files(selector, file_path)
        return True
