import asyncio
import unittest
import sys
import os

# Set path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.desktop.core import DesktopEngine
from backend.browser.core import BrowserEngine
from backend.kernel.capability_router import CapabilityRouter
from backend.planner.schema import Task

class TestDesktopBrowserAutomation(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.desktop = DesktopEngine()
        self.browser = BrowserEngine()
        self.router = CapabilityRouter(api_manager=None, browser_engine=self.browser, desktop_engine=self.desktop)

    async def test_01_desktop_calculator_math(self):
        """Test Desktop Automation: Launch Calculator, calculate 50 * 6, verify result."""
        task = Task(
            task_id="test_calc",
            description="Calculate 50 * 6 on Calculator",
            required_tools=["desktop"],
            action_metadata={
                "app": "calculator",
                "intent": "calculate",
                "entity": "50 * 6",
                "desktop_action": "APP_INTENT_EXECUTE"
            }
        )
        success = await self.router.route_task(task)
        self.assertTrue(success, "Calculator task routing failed")
        output = task.action_metadata.get("execution_output", "")
        print(f"Calculator computation result: {output}")
        self.assertIn("300", output.replace(",", ""), "Result did not contain 300")

        # Cleanup calculator
        close_task = Task(
            task_id="close_calc",
            description="Close Calculator",
            required_tools=["desktop"],
            action_metadata={"app": "calculator", "intent": "close_app", "desktop_action": "APP_INTENT_EXECUTE"}
        )
        await self.router.route_task(close_task)

    async def test_02_browser_navigation_and_search(self):
        """Test Browser Automation: Search for Python documentation on Google, verify execution output."""
        task = Task(
            task_id="test_search",
            description="Search Python official documentation",
            required_tools=["browser"],
            action_metadata={
                "intent": "search",
                "query": "Python official documentation python.org"
            }
        )
        success = await self.router.route_task(task)
        self.assertTrue(success, "Browser search task routing failed")
        output = task.action_metadata.get("execution_output", "")
        print(f"Browser search output: {output[:100]}...")
        self.assertTrue(len(output) > 0, "Execution output is empty")

    async def asyncTearDown(self):
        await self.browser.close()

if __name__ == "__main__":
    unittest.main()
