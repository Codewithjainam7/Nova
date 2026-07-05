import asyncio
import io
import pytesseract
from PIL import Image
from backend.vision.schema import VisionResult, VisionBoundingBox
from backend.core.logger import app_logger

class OCRManager:
    async def extract(self, image_data: bytes) -> VisionResult:
        app_logger.debug("Extracting text via OCR (Tesseract)")
        
        def _run_tesseract():
            try:
                img = Image.open(io.BytesIO(image_data))
                
                # Get structured data (bounding boxes & confidence)
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                
                boxes = []
                full_text_parts = []
                
                n_boxes = len(data['level'])
                for i in range(n_boxes):
                    text = data['text'][i].strip()
                    conf = float(data['conf'][i])
                    if text and conf > 0:
                        box = VisionBoundingBox(
                            x=data['left'][i],
                            y=data['top'][i],
                            width=data['width'][i],
                            height=data['height'][i],
                            confidence=conf / 100.0,  # Normalize to 0-1
                            text_content=text,
                            label="text"
                        )
                        boxes.append(box)
                        full_text_parts.append(text)
                        
                full_text = " ".join(full_text_parts)
                return VisionResult(full_text=full_text, boxes=boxes)
            except Exception as e:
                app_logger.error(f"Tesseract OCR failed: {e}")
                raise

        return await asyncio.to_thread(_run_tesseract)

import cv2
import numpy as np

class ElementDetector:
    async def detect(self, image_data: bytes) -> VisionResult:
        app_logger.debug("Detecting UI elements with OpenCV heuristics")
        
        def _run_cv():
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return VisionResult()
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Use Canny edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Dilate edges slightly to close gaps
            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=1)
            
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            boxes = []
            img_h, img_w = img.shape[:2]
            
            for cnt in contours:
                approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
                x, y, w, h = cv2.boundingRect(approx)
                area = w * h
                
                # Filter out noise or full screen
                if area < 100 or area > (img_w * img_h * 0.95):
                    continue
                    
                aspect_ratio = float(w) / h
                element_type = "container"
                clickable = False
                editable = False
                
                if len(approx) == 4 or True:  # Mostly rects in UI
                    if 0.8 <= aspect_ratio <= 1.2 and 100 <= area <= 600:
                        element_type = "checkbox"
                        clickable = True
                    elif 1.5 <= aspect_ratio <= 8 and 800 <= area <= 25000:
                        element_type = "button"
                        clickable = True
                    elif aspect_ratio > 4 and 2000 <= area <= 30000:
                        element_type = "textbox"
                        clickable = True
                        editable = True
                    elif area > 40000 and aspect_ratio > 0.5:
                        element_type = "dialog"
                    else:
                        element_type = "panel"
                        
                # Only add if it's reasonably classified
                if element_type != "panel" or area > 10000:
                    box = VisionBoundingBox(
                        x=x, y=y, width=w, height=h,
                        confidence=0.85,
                        element_type=element_type,
                        clickable=clickable,
                        editable=editable,
                        visible=True,
                        enabled=True
                    )
                    boxes.append(box)
                    
            # Basic Non-Maximum Suppression to remove overlapping identical boxes
            filtered_boxes = []
            for b in sorted(boxes, key=lambda x: x.width * x.height, reverse=True):
                duplicate = False
                for fb in filtered_boxes:
                    # Check if heavily overlaps
                    if (abs(b.x - fb.x) < 10 and abs(b.y - fb.y) < 10 and
                        abs(b.width - fb.width) < 10 and abs(b.height - fb.height) < 10):
                        duplicate = True
                        break
                if not duplicate:
                    filtered_boxes.append(b)
                    
            return VisionResult(boxes=filtered_boxes)
            
        return await asyncio.to_thread(_run_cv)

class TextExtractor:
    def extract_from_boxes(self, boxes: list) -> str:
        return " ".join([b.text_content for b in boxes if b.text_content])

class LayoutAnalyzer:
    async def analyze(self, boxes: list) -> dict:
        app_logger.debug("Building UI Tree")
        # Very simple containment hierarchy
        tree = []
        # Sort by area ascending so smaller elements are processed first
        sorted_boxes = sorted(boxes, key=lambda b: b.width * b.height)
        
        # We can map parent relationships. For simplicity, just return a flat structure indicator
        return {"structure": "hierarchy_calculated", "element_count": len(boxes)}

class RegionSelector:
    def select(self, boxes: list, x: int, y: int) -> list:
        selected = []
        for b in boxes:
            if b.x <= x <= b.x + b.width and b.y <= y <= b.y + b.height:
                selected.append(b)
        return selected

class UIAnalyzer:
    def __init__(self):
        self.detector = ElementDetector()
        self.layout = LayoutAnalyzer()
        
    async def analyze_ui(self, image_data: bytes) -> VisionResult:
        app_logger.info("Starting UI Analysis")
        result = await self.detector.detect(image_data)
        layout = await self.layout.analyze(result.boxes)
        result.metadata["layout"] = layout
        return result

class ScreenAnalyzer:
    def __init__(self):
        self.ocr = OCRManager()
        self.ui = UIAnalyzer()
        
    async def analyze_screen(self, image_data: bytes) -> VisionResult:
        app_logger.info("Starting full screen analysis (OCR + UI)")
        
        ocr_task = self.ocr.extract(image_data)
        ui_task = self.ui.analyze_ui(image_data)
        
        ocr_result, ui_result = await asyncio.gather(ocr_task, ui_task)
        
        # Merge results: If an OCR text box is inside a UI box, assign text to UI box.
        merged_boxes = []
        
        for ui_box in ui_result.boxes:
            contained_texts = []
            for text_box in ocr_result.boxes:
                # Calculate center of text box
                tx_c = text_box.x + text_box.width / 2
                ty_c = text_box.y + text_box.height / 2
                
                # Check if center falls inside ui_box
                if (ui_box.x <= tx_c <= ui_box.x + ui_box.width and 
                    ui_box.y <= ty_c <= ui_box.y + ui_box.height):
                    if text_box.text_content:
                        contained_texts.append(text_box.text_content)
            
            if contained_texts:
                ui_box.text_content = " ".join(contained_texts)
            merged_boxes.append(ui_box)
            
        # Also include standalone text boxes that didn't fall into a UI element
        for text_box in ocr_result.boxes:
            tx_c = text_box.x + text_box.width / 2
            ty_c = text_box.y + text_box.height / 2
            inside_any = False
            for ui_box in ui_result.boxes:
                if (ui_box.x <= tx_c <= ui_box.x + ui_box.width and 
                    ui_box.y <= ty_c <= ui_box.y + ui_box.height):
                    inside_any = True
                    break
            if not inside_any:
                text_box.element_type = "label"
                text_box.clickable = False
                text_box.visible = True
                merged_boxes.append(text_box)
        
        merged = VisionResult()
        merged.full_text = ocr_result.full_text
        merged.boxes = merged_boxes
        merged.metadata = ui_result.metadata
        return merged
