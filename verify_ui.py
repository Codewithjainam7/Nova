import time
import subprocess
from Desktop.ui_automation import UIAutomationController

def test_notepad():
    print("Testing Notepad automation...")
    controller = UIAutomationController()
    
    # 1. Launch Notepad
    print("Launching Notepad...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(1) # Give it a moment to spawn
    
    # 2. Find Window
    print("Finding window...")
    notepad_win = controller.find_window(class_name="Notepad", timeout=5)
    print(f"Found window: {notepad_win.Name}")
    
    # 3. Activate
    controller.activate_window(notepad_win)
    time.sleep(1)
    
    # 4. Find Edit control
    print("Finding text area...")
    try:
        edit_box = controller.find_element(notepad_win, control_type="Document")
    except:
        edit_box = controller.find_element(notepad_win, control_type="Edit")
        
    # 5. Type text
    print("Typing text...")
    time.sleep(1)
    controller.type_text(edit_box, "Hello! Nova UI Automation is working perfectly!")
    time.sleep(2)
    
    # 6. Verify text
    print("Verifying text...")
    controller.verifier.verify_text_changed(edit_box, "Hello! Nova UI Automation is working perfectly!", timeout=2)
    print("Text verified.")
    
    # 7. Close Window
    print("Closing Notepad...")
    controller.close_window(notepad_win)
    
    # It might prompt to save, let's look for the dialog
    try:
        dialog = controller.find_element(notepad_win, control_type="Window", timeout=2)
        # Find "Don't Save" button
        dont_save_btn = controller.find_element(dialog, name="Don't Save", control_type="Button")
        controller.click(dont_save_btn)
        print("Clicked Don't Save.")
    except:
        pass
        
    print("Test Complete.")

if __name__ == "__main__":
    test_notepad()
