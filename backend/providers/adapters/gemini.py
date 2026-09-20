import os
import asyncio
from typing import AsyncGenerator
from google import genai
from google.genai import types

from backend.providers.interface import ProviderInterface
from backend.providers.schema import GenerationRequest, GenerationResponse, StreamingToken, ProviderType, UsageMetrics

class GeminiProvider(ProviderInterface):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")
        self.client = genai.Client(api_key=api_key)

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GEMINI
        
    async def check_health(self) -> bool:
        return True

    def _convert_messages(self, messages):
        # Gemini handles system instructions separately
        contents = []
        system_instruction = None
        for msg in messages:
            if msg.role.value == "system":
                system_instruction = msg.content
            else:
                parts = [types.Part.from_text(text=msg.content)]
                if getattr(msg, "images", None):
                    for img_bytes in msg.images:
                        parts.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
                
                contents.append(
                    types.Content(
                        role="user" if msg.role.value == "user" else "model",
                        parts=parts
                    )
                )
        return contents, system_instruction

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        contents, system_instruction = self._convert_messages(request.messages)
        
        config_kwargs = {
            "temperature": request.temperature,
            "max_output_tokens": request.max_tokens,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
            
        if getattr(request, "json_mode", False):
            config_kwargs["response_mime_type"] = "application/json"
            
        config = types.GenerateContentConfig(**config_kwargs)
        
        # We use asyncio.to_thread because the google.genai sdk is mostly sync, 
        # but it supports async client. Let's use the async client if available or wrap it.
        # Actually, genai.Client provides aio support.
        response = await self.client.aio.models.generate_content(
            model=request.model or os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash"),
            contents=contents,
            config=config
        )
        
        usage = UsageMetrics()
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage.prompt_tokens = response.usage_metadata.prompt_token_count
            usage.completion_tokens = response.usage_metadata.candidates_token_count
            usage.total_tokens = response.usage_metadata.total_token_count
            
        return GenerationResponse(
            content=response.text,
            usage=usage,
            provider_used=self.provider_type,
            model_used=request.model or os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash")
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[StreamingToken, None]:
        contents, system_instruction = self._convert_messages(request.messages)
        
        config_kwargs = {
            "temperature": request.temperature,
            "max_output_tokens": request.max_tokens,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
            
        config = types.GenerateContentConfig(**config_kwargs)
        model_name = request.model or os.getenv("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash")
        
        async for chunk in await self.client.aio.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=config
        ):
            usage = None
            if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                usage = UsageMetrics(
                    prompt_tokens=chunk.usage_metadata.prompt_token_count,
                    completion_tokens=chunk.usage_metadata.candidates_token_count,
                    total_tokens=chunk.usage_metadata.total_token_count
                )
            
            is_final = False # we determine final by catching the end of stream, or if usage is present
            if usage:
                is_final = True
                
            yield StreamingToken(
                token=chunk.text,
                is_final=is_final,
                usage=usage,
                provider_used=self.provider_type,
                model_used=model_name
            )
