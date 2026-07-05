import asyncio
import os
import time
import pytesseract
from backend.vision.capture import ScreenCaptureManager
from backend.vision.core import VisionEngine
from backend.vision.schema import VisionPermissionLevel
from backend.vision.processing import ImageAnnotator

# Ensure tesseract path is set for the test session if needed
if os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
elif os.path.exists(r"F:\Tesseract\tesseract.exe"):
    pytesseract.pytesseract.tesseract_cmd = r"F:\Tesseract\tesseract.exe"

async def run_verification():
    print("Starting Vision UI Engine Verification...")
    
    # Initialize engines
    engine = VisionEngine(permission_level=VisionPermissionLevel.DESKTOP_ANALYSIS)
    screen_cap = ScreenCaptureManager()
    annotator = ImageAnnotator()
    
    results = []
    errors = []
    latencies = {}

    def record(name, condition, err=None):
        status = "PASS" if condition else "FAIL"
        results.append(f"{name}: {status}")
        if err:
            errors.append(f"{name} Error: {err}")
        print(f"[{status}] {name}")

    try:
        # 1. Capture Screen
        start_time = time.time()
        screen_bytes = screen_cap.capture_full_screen()
        latencies["Capture Screen"] = time.time() - start_time
        record("Capture screen", screen_bytes is not None and len(screen_bytes) > 0)
        
        # 2. Analyze Screen (OCR + UI)
        start_time = time.time()
        result = await engine.analyze_screen(screen_bytes)
        latencies["UI Analysis (OCR + OpenCV)"] = time.time() - start_time
        
        # 3. Validation
        record("VisionResult returned", result is not None)
        record("Boxes detected", len(result.boxes) > 0)
        
        has_button = any(b.element_type == "button" for b in result.boxes)
        has_checkbox = any(b.element_type == "checkbox" for b in result.boxes)
        has_textbox = any(b.element_type == "textbox" for b in result.boxes)
        has_label = any(b.element_type == "label" for b in result.boxes)
        has_panel = any(b.element_type == "panel" for b in result.boxes)
        
        record("Detected: Buttons", has_button)
        record("Detected: Text fields", has_textbox)
        record("Detected: Labels", has_label)
        
        # Validate properties
        if result.boxes:
            box = result.boxes[0]
            record("Properties: element_id", hasattr(box, 'element_id'))
            record("Properties: element_type", hasattr(box, 'element_type'))
            record("Properties: clickable", hasattr(box, 'clickable'))
            record("Properties: editable", hasattr(box, 'editable'))
        
        # 4. Generate Annotated Output
        try:
            annotated_bytes = annotator.annotate(screen_bytes, result.boxes)
            output_path = os.path.join(os.getcwd(), "docs", "annotated_ui.png")
            with open(output_path, "wb") as f:
                f.write(annotated_bytes)
            record("Saved Annotated Image", os.path.exists(output_path))
        except Exception as annotate_err:
            record("Saved Annotated Image", False, str(annotate_err))

        print(f"\n--- Discovered {len(result.boxes)} elements ---")
        types = {}
        for b in result.boxes:
            t = b.element_type or "unknown"
            types[t] = types.get(t, 0) + 1
        for k, v in types.items():
            print(f"- {k}: {v}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        errors.append(str(e))
        
    print("\n--- Latencies ---")
    for k, v in latencies.items():
        print(f"{k}: {v:.2f}s")
        
    with open("docs/VISION_UI_VERIFICATION.md", "w", encoding="utf-8") as f:
        f.write("# Vision UI Implementation Verification\n\n")
        f.write("## Tests\n")
        for res in results:
            f.write(f"- {res}\n")
        f.write("\n## Element Summary\n")
        if 'result' in locals() and result:
            for k, v in types.items():
                f.write(f"- {k}: {v}\n")
        f.write("\n## Latencies\n")
        for k, v in latencies.items():
            f.write(f"- {k}: {v:.2f}s\n")
        f.write("\n## Errors\n")
        if not errors:
            f.write("None\n")
        else:
            for err in errors:
                f.write(f"- {err}\n")

if __name__ == "__main__":
    asyncio.run(run_verification())
