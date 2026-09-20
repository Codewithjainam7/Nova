import time
import subprocess
from Desktop.ui_automation import UIAutomationController

def run_stress_test(iterations=10):
    print(f"Starting UI Stress Test ({iterations} iterations)...")
    controller = UIAutomationController()
    
    successes = 0
    failures = 0
    start_total = time.time()
    
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}...")
        try:
            proc = subprocess.Popen(["notepad.exe"])
            time.sleep(1)
            
            win = controller.find_window(class_name="Notepad", process="notepad.exe", timeout=3)
            
            controller.activate_window(win)
            controller.close_window(win)
            successes += 1
        except Exception as e:
            print(f"Failed iteration {i+1}: {e}")
            failures += 1
            # Cleanup
            try:
                proc.kill()
            except:
                pass
                
    total_time = time.time() - start_total
    print("\n--- Stress Test Results ---")
    print(f"Total Iterations: {iterations}")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Avg Time per Iteration: {total_time/iterations:.2f}s")

if __name__ == "__main__":
    run_stress_test(5) # Running 5 iterations for quick validation
