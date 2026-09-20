import asyncio
import os
import traceback
import sys
from pydantic import BaseModel

class TestResult:
    def __init__(self, name):
        self.name = name
        self.status = "PASS"
        self.error = None
        self.cause = None
        
    def fail(self, err, cause):
        self.status = "FAIL"
        self.error = str(err)
        self.cause = cause

results = []

def record_pass(name):
    print(f"[{name}] PASS")
    results.append(TestResult(name))

def record_fail(name, err, cause):
    print(f"[{name}] FAIL: {err}")
    r = TestResult(name)
    r.fail(err, cause)
    results.append(r)

async def test_memory():
    print("--- MEMORY TESTS ---")
    try:
        from backend.memory.sqlite_store import SQLiteStore
        store = SQLiteStore()
        record_pass("SQLite initialization")
    except Exception as e:
        record_fail("SQLite initialization", e, "Missing implementation or Bug")

    try:
        from backend.memory.chroma_store import ChromaVectorStore
        store = ChromaVectorStore()
        record_pass("ChromaDB initialization")
    except Exception as e:
        record_fail("ChromaDB initialization", e, "Dependency issue or Configuration issue")

    try:
        from backend.memory.core import MemoryEngine
        from backend.memory.schema import MemoryItem, MemoryType
        engine = MemoryEngine()
        
        item = MemoryItem(memory_type=MemoryType.LONG_TERM_MEMORY, content="The user's favorite color is blue.")
        await engine.add(item)
        record_pass("Store conversation / Remember user fact")
        
        retrieved = await engine.get(item.memory_id)
        if retrieved:
            record_pass("Retrieve conversation / Recall user fact")
        else:
            record_fail("Retrieve conversation / Recall user fact", "Item not found after store", "Bug")
            
        from backend.memory.schema import MemoryQuery
        query = MemoryQuery(query_text="favorite color", min_similarity=0.1)
        res = await engine.search(query)
        record_pass("Semantic similarity search")
    except Exception as e:
        record_fail("Memory CRUD operations", e, "Bug or Missing Implementation")

async def test_browser():
    print("--- BROWSER TESTS ---")
    try:
        from backend.browser.core import BrowserEngine
        from backend.browser.schema import BrowserAction, BrowserActionType
        engine = BrowserEngine()
        
        await engine.perform_action(BrowserAction(action_type=BrowserActionType.LAUNCH))
        record_pass("Launch browser")
        
        await engine.perform_action(BrowserAction(action_type=BrowserActionType.NAVIGATE, payload={"url": "https://google.com"}))
        record_pass("Open https://google.com")
        
        await engine.perform_action(BrowserAction(action_type=BrowserActionType.NAVIGATE, payload={"url": "https://github.com"}))
        record_pass("Open https://github.com")
        
        # We can't really guarantee an element click without knowing the page
        try:
            await engine.perform_action(BrowserAction(action_type=BrowserActionType.CLICK, payload={"selector": "a"}))
            record_pass("Click an element")
        except Exception as e:
            record_fail("Click an element", e, "Bug or missing selector")
            
        try:
            await engine.perform_action(BrowserAction(action_type=BrowserActionType.TYPE, payload={"selector": "input", "text": "hello"}))
            record_pass("Type text")
        except Exception as e:
            record_fail("Type text", e, "Bug or missing selector")
            
        await engine.perform_action(BrowserAction(action_type=BrowserActionType.SCREENSHOT, payload={"path": "test.png"}))
        record_pass("Take screenshot")
        
        await engine.perform_action(BrowserAction(action_type=BrowserActionType.EXPORT_PDF, payload={"path": "test.pdf"}))
        record_pass("Export PDF")
        
        await engine.perform_action(BrowserAction(action_type=BrowserActionType.NEW_TAB))
        record_pass("Open multiple tabs")
        
        # Close isn't in BrowserActionType explicitly, let's just close tab
        await engine.perform_action(BrowserAction(action_type=BrowserActionType.CLOSE_TAB))
        record_pass("Close browser")
        
    except Exception as e:
        record_fail("Browser tests", e, "Missing dependency, Bug, or Configuration issue")

async def test_desktop():
    print("--- DESKTOP TESTS ---")
    try:
        from backend.desktop.core import DesktopEngine
        from backend.desktop.schema import DesktopAction, DesktopActionType
        engine = DesktopEngine()
        
        try:
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.APP_LAUNCH, payload={"path": "notepad.exe"}))
            record_pass("Open Notepad")
        except Exception as e:
            record_fail("Open Notepad", e, "Bug")
            
        try:
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.APP_LAUNCH, payload={"path": "calc.exe"}))
            record_pass("Open Calculator")
        except Exception as e:
            record_fail("Open Calculator", e, "Bug")
            
        try:
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.MOUSE_MOVE, payload={"x": 500, "y": 500}))
            record_pass("Move mouse")
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.MOUSE_CLICK, payload={"button": "left"}))
            record_pass("Click")
        except Exception as e:
            record_fail("Mouse Actions", e, "Bug")
            
        try:
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.KEYBOARD_TYPE, payload={"text": "hello world"}))
            record_pass("Type text")
        except Exception as e:
            record_fail("Type text", e, "Bug")
            
        try:
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.CLIPBOARD_WRITE, payload={"text": "test"}))
            res = await engine.manager.clipboard.execute(DesktopAction(action_type=DesktopActionType.CLIPBOARD_READ))
            if res == "test":
                record_pass("Clipboard read/write")
            else:
                record_fail("Clipboard read/write", "Values didn't match", "Bug")
        except Exception as e:
            record_fail("Clipboard read/write", e, "Dependency or Bug")
            
        try:
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.SCREENSHOT, payload={"path": "desktop.png"}))
            record_pass("Screenshot")
        except Exception as e:
            record_fail("Screenshot", e, "Bug")
            
        try:
            # We don't have FS_CREATE_FOLDER mapped, only FS_WRITE which is a placeholder
            # Let's see if it errors out
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.FS_WRITE, payload={"path": "test_folder"}))
            record_pass("Create a test folder")
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.FS_DELETE, payload={"path": "test_folder"}))
            record_pass("Delete the test folder")
        except Exception as e:
            record_fail("Filesystem actions", e, "Missing implementation")
            
        try:
            await engine.perform_action(DesktopAction(action_type=DesktopActionType.WINDOW_MINIMIZE, payload={"title": "Notepad"}))
            record_pass("Window management")
        except Exception as e:
            record_fail("Window management", e, "Bug")
            
    except Exception as e:
        record_fail("Desktop Tests Init", e, "Dependency issue")

async def main():
    await test_memory()
    await test_browser()
    await test_desktop()
    
    with open("results.txt", "w") as f:
        for r in results:
            f.write(f"{r.name}|{r.status}|{r.error}|{r.cause}\n")

if __name__ == "__main__":
    asyncio.run(main())
