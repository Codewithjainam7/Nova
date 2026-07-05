import time
import asyncio
from typing import Optional
from backend.vision.schema import VisionSession, VisionResult, VisionPermissionLevel, VisionMetrics, VisionConfiguration
from backend.vision.processing import ImagePreprocessor
from backend.vision.analysis import ScreenAnalyzer, OCRManager, UIAnalyzer
from backend.core.logger import app_logger

class VisionLogger:
    @staticmethod
    def log_analysis(task_name: str, status: str):
        app_logger.info(f"[VISION ACTION - {status}] {task_name}")

class VisionCache:
    """Caches recent vision results for speed (e.g. static screen regions)."""
    def __init__(self):
        self._cache = {}
        
    def get(self, key: str) -> Optional[VisionResult]:
        return self._cache.get(key)
        
    def set(self, key: str, result: VisionResult):
        self._cache[key] = result

class VisionPermissionManager:
    def __init__(self, current_level: VisionPermissionLevel):
        self.level = current_level

    def check(self, requires_desktop: bool = False, requires_sensitive: bool = False) -> bool:
        if requires_sensitive and self.level != VisionPermissionLevel.SENSITIVE_REGIONS:
            return False
        if requires_desktop and self.level not in [VisionPermissionLevel.DESKTOP_ANALYSIS, VisionPermissionLevel.SENSITIVE_REGIONS]:
            return False
        return True

class VisionRecoveryManager:
    async def handle_failure(self, task_name: str, exception: Exception):
        app_logger.error(f"Vision task failed: {task_name} - {str(exception)}")
        app_logger.info("Attempting Vision fallback/recovery...")
        await asyncio.sleep(0.1)

class VisionPipeline:
    """Orchestrates the ordered flow: Preprocess -> OCR -> Object Detect -> Output"""
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.screen_analyzer = ScreenAnalyzer()
        
    async def run_pipeline(self, raw_image: bytes) -> VisionResult:
        processed = await self.preprocessor.process_for_ocr(raw_image)
        result = await self.screen_analyzer.analyze_screen(processed)
        return result

class VisionManager:
    def __init__(self, config: VisionConfiguration, permission_level: VisionPermissionLevel):
        self.config = config
        self.permissions = VisionPermissionManager(permission_level)
        self.recovery = VisionRecoveryManager()
        self.cache = VisionCache()
        self.pipeline = VisionPipeline()
        self.ocr = self.pipeline.screen_analyzer.ocr
        self.ui = self.pipeline.screen_analyzer.ui

class VisionExecutor:
    def __init__(self, manager: VisionManager, metrics: VisionMetrics):
        self.manager = manager
        self.metrics = metrics

    async def execute_full_screen(self, image_data: bytes) -> VisionResult:
        start = time.time()
        VisionLogger.log_analysis("FULL_SCREEN_ANALYSIS", "START")
        
        if not self.manager.permissions.check(requires_desktop=True):
            self.metrics.failed_images += 1
            raise PermissionError(f"Desktop analysis denied by permission level {self.manager.permissions.level}")
            
        try:
            # Simple caching simulation based on hash (just a mock for architecture)
            cache_key = str(hash(image_data))
            cached = self.manager.cache.get(cache_key)
            if cached:
                return cached
                
            result = await self.manager.pipeline.run_pipeline(image_data)
            self.manager.cache.set(cache_key, result)
            
            VisionLogger.log_analysis("FULL_SCREEN_ANALYSIS", "SUCCESS")
            self.metrics.total_images_processed += 1
            
            elapsed = (time.time() - start) * 1000
            self._update_metric("avg_total_latency_ms", elapsed)
            return result
        except Exception as e:
            await self.manager.recovery.handle_failure("FULL_SCREEN_ANALYSIS", e)
            self.metrics.failed_images += 1
            raise

    async def execute_ocr_only(self, image_data: bytes) -> VisionResult:
        start = time.time()
        VisionLogger.log_analysis("OCR_ONLY", "START")
        
        try:
            result = await self.manager.ocr.extract(image_data)
            self.metrics.total_images_processed += 1
            
            elapsed = (time.time() - start) * 1000
            self._update_metric("avg_ocr_latency_ms", elapsed)
            return result
        except Exception as e:
            await self.manager.recovery.handle_failure("OCR_ONLY", e)
            self.metrics.failed_images += 1
            raise

    def _update_metric(self, attr: str, elapsed: float):
        n = self.metrics.total_images_processed
        if n > 0:
            current = getattr(self.metrics, attr)
            new_val = ((current * (n - 1)) + elapsed) / n
            setattr(self.metrics, attr, new_val)

class VisionEngine:
    """Central entrypoint for Vision Analysis."""
    def __init__(self, permission_level: VisionPermissionLevel = VisionPermissionLevel.DESKTOP_ANALYSIS):
        self.metrics = VisionMetrics()
        self.config = VisionConfiguration()
        self.session = VisionSession(permissions=permission_level)
        self.manager = VisionManager(self.config, permission_level)
        self.executor = VisionExecutor(self.manager, self.metrics)

    async def analyze_screen(self, image_data: bytes) -> VisionResult:
        """Fully analyzes a screenshot (OCR + Objects + UI Layout)."""
        return await self.executor.execute_full_screen(image_data)
        
    async def extract_text(self, image_data: bytes) -> VisionResult:
        """Performs only OCR on an image region."""
        return await self.executor.execute_ocr_only(image_data)
