from backend.core.logger import app_logger

class PromptCompressor:
    def compress(self, content: str) -> str:
        # Removes double spaces, duplicate newlines
        import re
        compressed = re.sub(r'\n{3,}', '\n\n', content)
        compressed = re.sub(r' {3,}', '  ', compressed)
        return compressed.strip()

class PromptOptimizer:
    def __init__(self, compressor: PromptCompressor):
        self.compressor = compressor

    def optimize(self, rendered_content: str, provider_target: str) -> str:
        # Provider specific tweaks could go here
        optimized = self.compressor.compress(rendered_content)
        return optimized
