import asyncio
import cv2
import numpy as np
from typing import Any
from backend.core.logger import app_logger

class ImageResizer:
    def resize(self, image_data: bytes, width: int, height: int) -> bytes:
        app_logger.debug(f"Resizing image to {width}x{height}")
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return image_data
        resized = cv2.resize(img, (width, height), interpolation=cv2.INTER_CUBIC)
        _, buf = cv2.imencode('.png', resized)
        return buf.tobytes()

class ImageCropper:
    def crop(self, image_data: bytes, x: int, y: int, w: int, h: int) -> bytes:
        app_logger.debug(f"Cropping image at {x},{y} {w}x{h}")
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return image_data
        cropped = img[y:y+h, x:x+w]
        _, buf = cv2.imencode('.png', cropped)
        return buf.tobytes()

class ImageNormalizer:
    def normalize(self, image_data: bytes) -> bytes:
        app_logger.debug("Normalizing image (brightness/contrast/grayscale) for OCR")
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return image_data
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding to handle different lighting/backgrounds
        # OCR performs best on binary images (black text on white background)
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        _, buf = cv2.imencode('.png', binary)
        return buf.tobytes()

class ImageAnnotator:
    def annotate(self, image_data: bytes, boxes: list) -> bytes:
        app_logger.debug(f"Annotating image with {len(boxes)} boxes")
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return image_data
            
        for box in boxes:
            cv2.rectangle(img, (box.x, box.y), (box.x + box.width, box.y + box.height), (0, 255, 0), 2)
            if box.text_content:
                cv2.putText(img, box.text_content[:10], (box.x, box.y - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                            
        _, buf = cv2.imencode('.png', img)
        return buf.tobytes()

class ColorAnalyzer:
    def extract_dominant_colors(self, image_data: bytes) -> list:
        app_logger.debug("Extracting colors")
        return ["#FFFFFF", "#000000"]

class ImagePreprocessor:
    def __init__(self):
        self.resizer = ImageResizer()
        self.cropper = ImageCropper()
        self.normalizer = ImageNormalizer()
        self.annotator = ImageAnnotator()
        
    async def process_for_ocr(self, raw_image: bytes) -> bytes:
        app_logger.debug("Preprocessing image for OCR")
        # Run normalizer in a separate thread so we don't block the asyncio loop
        normalized = await asyncio.to_thread(self.normalizer.normalize, raw_image)
        return normalized
