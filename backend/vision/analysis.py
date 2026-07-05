import asyncio
from backend.vision.schema import VisionResult, VisionBoundingBox
from backend.core.logger import app_logger

class OCRManager:
    async def extract(self, image_data: bytes) -> VisionResult:
        app_logger.debug("Extracting text via OCR")
        await asyncio.sleep(0.1)
        
        box = VisionBoundingBox(x=10, y=10, width=100, height=20, confidence=0.99, text_content="Mock OCR Text")
        return VisionResult(full_text="Mock OCR Text", boxes=[box])

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
