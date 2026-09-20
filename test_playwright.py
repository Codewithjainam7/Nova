import asyncio
from playwright.async_api import async_playwright

async def test():
    pw = await async_playwright().start()
    try:
        b = await pw.chromium.launch(headless=True)
        print("Browser launched OK")
        page = await b.new_page()
        await page.goto("https://www.google.com", wait_until="domcontentloaded")
        print(f"Page title: {await page.title()}")
        await b.close()
    except Exception as e:
        print(f"Launch failed: {e}")
    await pw.stop()

asyncio.run(test())
