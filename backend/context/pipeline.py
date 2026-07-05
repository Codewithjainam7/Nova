from typing import List
from backend.context.schema import ContextItem, ContextPackage
from backend.context.collector import ContextCollector
from backend.context.ranker import ContextRanker
from backend.context.filter import ContextFilter
from backend.context.compressor import ContextCompressor
from backend.context.assembler import ContextAssembler

class ContextPipeline:
    def __init__(self, collector: ContextCollector, max_tokens: int = 4000):
        self.collector = collector
        self.filter = ContextFilter()
        self.compressor = ContextCompressor(max_tokens=max_tokens)

    async def build_context(self) -> ContextPackage:
        # 1. Collect
        items = await self.collector.collect_all()
        
        # 2. Deduplicate & Filter
        items = self.filter.deduplicate(items)
        items = self.filter.filter_by_threshold(items)
        
        # 3. Rank
        items = ContextRanker.rank(items)
        
        # 4. Compress (enforce token limits)
        items = self.compressor.compress(items)
        
        # 5. Assemble
        package = ContextAssembler.assemble(items)
        return package
