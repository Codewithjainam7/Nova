import os
from typing import AsyncGenerator
from groq import AsyncGroq

from backend.providers.interface import ProviderInterface
from backend.providers.schema import GenerationRequest, GenerationResponse, StreamingToken, ProviderType, UsageMetrics

class GroqProvider(ProviderInterface):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")
        self.client = AsyncGroq(api_key=api_key)

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GROQ
        
    async def check_health(self) -> bool:
        return True

    def _convert_messages(self, messages):
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        messages = self._convert_messages(request.messages)
        model_name = request.model or os.getenv("GROQ_DEFAULT_MODEL", "openai/gpt-oss-20b")
        
        # Ensure json directive if json_mode requested
        if getattr(request, "json_mode", False):
            has_json = any("json" in str(m.get("content", "")).lower() for m in messages)
            if not has_json:
                messages.insert(0, {"role": "system", "content": "You are a JSON assistant. Output valid JSON only."})

        max_tokens = request.max_tokens or 1500
        kwargs = {
            "messages": messages,
            "model": model_name,
            "temperature": request.temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        if getattr(request, "json_mode", False):
            kwargs["response_format"] = {"type": "json_object"}
            
        try:
            response = await self.client.chat.completions.create(**kwargs)
        except Exception as e:
            if "json" in str(e).lower() and "response_format" in kwargs:
                del kwargs["response_format"]
                response = await self.client.chat.completions.create(**kwargs)
            else:
                raise e
        
        usage = UsageMetrics()
        if response.usage:
            usage.prompt_tokens = response.usage.prompt_tokens
            usage.completion_tokens = response.usage.completion_tokens
            usage.total_tokens = response.usage.total_tokens
            
        return GenerationResponse(
            content=response.choices[0].message.content or "",
            usage=usage,
            provider_used=self.provider_type,
            model_used=model_name
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[StreamingToken, None]:
        messages = self._convert_messages(request.messages)
        model_name = request.model or os.getenv("GROQ_DEFAULT_MODEL", "openai/gpt-oss-20b")
        
        stream = await self.client.chat.completions.create(
            messages=messages,
            model=model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            # Groq returns usage in a special chunk or we can just omit it if not available
            is_final = chunk.choices[0].finish_reason is not None
            
            yield StreamingToken(
                token=content,
                is_final=is_final,
                provider_used=self.provider_type,
                model_used=model_name
            )
