import time
import hashlib
from typing import AsyncGenerator, Union
from backend.response.schema import ResponseInput, ResponseOutput, ResponseMetrics
from backend.response.parser import ResponseParser
from backend.response.normalizer import ResponseNormalizer
from backend.response.validator import ResponseValidator, ResponsePolicy
from backend.response.formatter import ResponseFormatter
from backend.response.streamer import ResponseStreamer
from backend.response.builder import ResponseAssembler
from backend.response.cache import ResponseCache
from backend.core.logger import app_logger

class ResponseAuditLogger:
    @staticmethod
    def log_response(output: ResponseOutput):
        app_logger.info(f"[RESPONSE GENERATED] ID: {output.response_id}, Type: {output.response_type}, Confidence: {output.confidence_score}, Provider: {output.provider}")

class ResponseManager:
    """Core class handling the response transformation pipeline."""
    def __init__(self):
        self.parser = ResponseParser()
        self.normalizer = ResponseNormalizer()
        self.policy = ResponsePolicy()
        self.validator = ResponseValidator(self.policy)
        self.formatter = ResponseFormatter()
        self.assembler = ResponseAssembler()
        self.cache = ResponseCache()
        
    def _generate_checksum(self, raw_content: str, request: ResponseInput) -> str:
        data = f"{request.provider}:{request.model}:{request.response_type}:{raw_content}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def process(self, request: ResponseInput) -> ResponseOutput:
        # Check cache
        req_hash = self._generate_checksum(request.raw_content, request)
        cached = self.cache.get(req_hash)
        if cached:
            return cached

        # 1. Normalize
        normalized = self.normalizer.normalize(request.raw_content)
        
        # 2. Parse (JSON, markdown extraction, etc)
        parsed_content, metadata = self.parser.parse(normalized, request.target_format)
        
        # 3. Validate
        if not self.validator.validate(parsed_content, metadata, request.target_format):
            # We don't necessarily raise, we just might pass along low confidence
            metadata["validation_failed"] = True
            
        # 4. Format
        formatted = self.formatter.format(parsed_content, request.target_format)
        
        # 5. Assemble
        output = self.assembler.assemble(formatted, metadata, request)
        
        # 6. Cache
        self.cache.set(req_hash, output)
        
        ResponseAuditLogger.log_response(output)
        return output

class ResponseGenerator:
    """Central entrypoint for transforming AI Provider outputs."""
    def __init__(self):
        self.manager = ResponseManager()
        self.streamer = ResponseStreamer()
        self.metrics = ResponseMetrics()

    async def generate(self, request: ResponseInput) -> ResponseOutput:
        start = time.time()
        try:
            output = await self.manager.process(request)
            
            # Update metrics
            self.metrics.total_responses += 1
            if output.metadata.get("validation_failed"):
                self.metrics.validation_failures += 1
                
            return output
        except Exception as e:
            app_logger.error(f"Response processing failed: {str(e)}")
            raise
        finally:
            elapsed = (time.time() - start) * 1000
            n = self.metrics.total_responses
            if n > 0:
                self.metrics.avg_processing_time_ms = ((self.metrics.avg_processing_time_ms * (n - 1)) + elapsed) / n

    async def generate_from_stream(self, stream: AsyncGenerator[str, None], request: ResponseInput) -> ResponseOutput:
        """Helper to aggregate a stream and process it fully."""
        try:
            aggregated_content = await self.streamer.aggregate(stream)
            self.metrics.total_streamed_chunks += 1 # simplistic metric tracking
            
            # Update input with the aggregated string
            request.raw_content = aggregated_content
            return await self.generate(request)
        except Exception as e:
            app_logger.error(f"Failed to generate from stream: {str(e)}")
            raise
