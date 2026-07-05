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

class ObjectDetector:
    async def detect(self, image_data: bytes) -> VisionResult:
        app_logger.debug("Detecting objects in image")
        await asyncio.sleep(0.1)
        
        box = VisionBoundingBox(x=50, y=50, width=200, height=50, confidence=0.95, label="button")
        return VisionResult(boxes=[box])

class TextExtractor:
    def extract_from_boxes(self, boxes: list) -> str:
        return " ".join([b.text_content for b in boxes if b.text_content])

class LayoutAnalyzer:
    async def analyze(self, image_data: bytes) -> dict:
        app_logger.debug("Analyzing layout structure")
        await asyncio.sleep(0.05)
        return {"structure": "grid"}

class RegionSelector:
    def select(self, boxes: list, x: int, y: int) -> list:
        # Dummy selection logic
        return boxes

class UIAnalyzer:
    def __init__(self):
        self.detector = ObjectDetector()
        self.layout = LayoutAnalyzer()
        
    async def analyze_ui(self, image_data: bytes) -> VisionResult:
        app_logger.info("Starting UI Analysis")
        result = await self.detector.detect(image_data)
        layout = await self.layout.analyze(image_data)
        result.metadata["layout"] = layout
        return result

class ScreenAnalyzer:
    def __init__(self):
        self.ocr = OCRManager()
        self.ui = UIAnalyzer()
        
    async def analyze_screen(self, image_data: bytes) -> VisionResult:
        app_logger.info("Starting full screen analysis")
        
        ocr_result = await self.ocr.extract(image_data)
        ui_result = await self.ui.analyze_ui(image_data)
        
        # Merge results
        merged = VisionResult()
        merged.full_text = ocr_result.full_text
        merged.boxes = ocr_result.boxes + ui_result.boxes
        merged.metadata = ui_result.metadata
        return merged
