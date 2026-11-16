import os
import json
import base64
from typing import AsyncGenerator
import httpx

from backend.providers.interface import ProviderInterface
from backend.providers.schema import (
    GenerationRequest, GenerationResponse, StreamingToken, ProviderType, UsageMetrics
)
from backend.core.logger import app_logger

class OpenRouterProvider(ProviderInterface):
    """
    OpenRouter API provider adapter.
    Powers ADA with elite reasoning models like nvidia/nemotron-3.5-super-vl:free.
    Supports unary generation, streaming, JSON mode, and multimodal Vision.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment.")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = os.getenv("OPENROUTER_DEFAULT_MODEL", "nvidia/nemotron-3.5-super-vl:free")

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENROUTER

    async def check_health(self) -> bool:
        return bool(self.api_key)

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "ADA AI",
            "Content-Type": "application/json"
        }

    def _convert_messages(self, messages):
        converted = []
        for msg in messages:
            role = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            images = getattr(msg, "images", None)
            
            if images:
                content_parts = [{"type": "text", "text": msg.content}]
                for img in images:
                    if isinstance(img, bytes):
                        b64 = base64.b64encode(img).decode("utf-8")
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"}
                        })
                converted.append({"role": role, "content": content_parts})
            else:
                converted.append({"role": role, "content": msg.content})
        return converted

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        messages = self._convert_messages(request.messages)
        model_name = request.model or self.default_model

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or 2048,
            "stream": False
        }

        if getattr(request, "json_mode", False):
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=request.timeout or 35.0) as client:
            resp = await client.post(self.base_url, headers=self._get_headers(), json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text}")

            data = resp.json()
            choice = data["choices"][0]
            content = choice["message"]["content"] or ""

            usage = UsageMetrics()
            if "usage" in data and data["usage"]:
                usage.prompt_tokens = data["usage"].get("prompt_tokens", 0)
                usage.completion_tokens = data["usage"].get("completion_tokens", 0)
                usage.total_tokens = data["usage"].get("total_tokens", 0)

            return GenerationResponse(
                content=content,
                usage=usage,
                provider_used=self.provider_type,
                model_used=model_name
            )

    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[StreamingToken, None]:
        messages = self._convert_messages(request.messages)
        model_name = request.model or self.default_model

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens or 2048,
            "stream": True
        }

        if getattr(request, "json_mode", False):
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=request.timeout or 45.0) as client:
            async with client.stream("POST", self.base_url, headers=self._get_headers(), json=payload) as resp:
                if resp.status_code != 200:
                    error_text = await resp.aread()
                    raise RuntimeError(f"OpenRouter streaming error {resp.status_code}: {error_text.decode('utf-8', errors='ignore')}")

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        raw_data = line[6:].strip()
                        if raw_data == "[DONE]":
                            yield StreamingToken(token="", is_final=True)
                            break
                        try:
                            chunk = json.loads(raw_data)
                            choices = chunk.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                text = delta.get("content", "")
                                if text:
                                    yield StreamingToken(token=text, is_final=False)
                        except Exception:
                            continue
