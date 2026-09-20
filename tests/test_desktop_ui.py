import time
import subprocess
import unittest
from Desktop.ui_automation import UIAutomationController
from Desktop.ui_automation.exceptions import WindowNotFoundError

class TestUIAutomation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controller = UIAutomationController()
        # Ensure Notepad is running for testing
        cls.proc = subprocess.Popen(["notepad.exe"])
        time.sleep(1)
        cls.notepad_win = cls.controller.find_window(class_name="Notepad", process="notepad.exe", timeout=5)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.controller.close_window(cls.notepad_win)
            # handle 'dont save' dialog if it pops up
            dialog = cls.controller.find_element(cls.notepad_win, control_type="Window", timeout=1)
            dont_save = cls.controller.find_element(dialog, name="Don't Save", control_type="Button")
            cls.controller.click(dont_save)
        except Exception:
            cls.proc.kill()

    def test_window_activation(self):
        result = self.controller.activate_window(self.notepad_win)
        self.assertTrue(result)

    def test_type_and_verify_text(self):
        try:
            edit_box = self.controller.find_element(self.notepad_win, control_type="Document")
        except:
            edit_box = self.controller.find_element(self.notepad_win, control_type="Edit")
        
        text = "Hello Unit Test"
        self.controller.type_text(edit_box, text)
        result = self.controller.verifier.verify_text_changed(edit_box, text, timeout=2)
        self.assertTrue(result)
        
    def test_find_all_elements(self):
        # Find all buttons in Notepad
        items = self.controller.finder.find_all_elements(self.notepad_win, control_type="Button", search_depth=3)
        self.assertGreater(len(items), 0)
        
    def test_process_filtering(self):
        # Searching for Notepad but specifying a wrong process should fail
        with self.assertRaises(WindowNotFoundError):
            self.controller.find_window(class_name="Notepad", process="wrong_process.exe", timeout=1)

if __name__ == "__main__":
    unittest.main()
