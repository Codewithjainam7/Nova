"""
ADA Silent Backend Web Research & Intelligence Engine
Executes web searches silently in the background without opening visible desktop browsers,
avoiding CAPTCHAs and screen disruption. Synthesizes findings using LLM into concise intel.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from backend.core.logger import app_logger

class WebResearchEngine:
    def __init__(self, provider_manager=None):
        self.provider_manager = provider_manager
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

    def search_ddgs(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Fetches web search results silently using ddgs library.
        Zero API keys required, zero browser windows, zero CAPTCHAs.
        """
        results = []
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                for item in raw_results:
                    title = item.get("title", "").strip()
                    snippet = item.get("body", "").strip()
                    url = item.get("href", "").strip()
                    if title:
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": url
                        })
            app_logger.info(f"[WebResearchEngine] ddgs returned {len(results)} results for '{query}'")
        except Exception as e:
            app_logger.warning(f"[WebResearchEngine] ddgs search notice: {e}")
        return results

    def search_duckduckgo_instant(self, query: str) -> List[Dict[str, str]]:
        """Fallback to DuckDuckGo Instant Answer API"""
        results = []
        try:
            api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            req = urllib.request.Request(api_url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            abstract = data.get("AbstractText", "")
            heading = data.get("Heading", query)
            source_url = data.get("AbstractURL", "")
            
            if abstract:
                results.append({
                    "title": heading,
                    "snippet": abstract,
                    "url": source_url or "https://duckduckgo.com"
                })
                
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:60] + "...",
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", "")
                    })
        except Exception as e:
            app_logger.warning(f"[WebResearchEngine] Instant Answer API notice: {e}")
        return results

    def search_tavily(self, query: str, api_key: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Optional Tavily search if user configured TAVILY_API_KEY in .env"""
        results = []
        try:
            url = "https://api.tavily.com/search"
            payload = json.dumps({
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results
            }).encode('utf-8')
            
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "url": item.get("url", "")
                })
        except Exception as e:
            app_logger.error(f"[WebResearchEngine] Tavily error: {e}")
        return results

    async def execute_search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Unified search runner:
        1. Normalizes search query by removing conversational stop words.
        2. Checks for dedicated Tavily key if configured.
        3. Primary engine: Silent ddgs on backend (0 API keys, 0 CAPTCHAs, no browser window).
        4. Fallback: DuckDuckGo Instant Answer API.
        """
        # Clean leading stop words for optimal search index hit rate
        norm_q = re.sub(r'^(?:the|a|an|about|regarding|information\s+on|details\s+on)\s+', '', query.strip(), flags=re.IGNORECASE).strip()
        search_query = norm_q if norm_q else query

        tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        if tavily_key:
            results = self.search_tavily(search_query, tavily_key, max_results)
            if results:
                return results

        results = self.search_ddgs(search_query, max_results)
        if results:
            return results

        # Try original query if normalized yielded nothing
        if search_query != query:
            results = self.search_ddgs(query, max_results)
            if results:
                return results

        return self.search_duckduckgo_instant(search_query)

    async def research_and_synthesize(self, query: str, conversation_history: Optional[str] = None) -> str:
        """
        Executes silent backend web search and synthesizes findings into an executive report,
        incorporating multi-turn conversation history for context.
        """
        app_logger.info(f"[WebResearchEngine] Initiating silent backend research for query: '{query}'")
        
        # If query refers to context (pronouns/short query) and history exists, enrich the search query
        effective_query = query
        ref_words = ["that", "it", "this", "they", "them", "he", "she", "in that", "about it", "more details"]
        if conversation_history and any(w in query.lower() for w in ref_words):
            # Extract last user query or topic from history to augment search
            lines = [l.strip() for l in conversation_history.strip().splitlines() if l.strip()]
            if lines:
                effective_query = f"{lines[-1][:60]} {query}"

        search_results = await self.execute_search(effective_query, max_results=5)
        if not search_results and effective_query != query:
            search_results = await self.execute_search(query, max_results=5)
        
        if not search_results:
            app_logger.info(f"[WebResearchEngine] No live search hits found; synthesizing from cognitive knowledge base.")
            return await self._synthesize_fallback(query)
            
        context_lines = []
        for i, item in enumerate(search_results, 1):
            context_lines.append(f"[{i}] {item['title']}\nSource: {item['url']}\nSummary: {item['snippet']}\n")
            
        research_context = "\n".join(context_lines)
        
        system_instruction = (
            "You are ADA (Autonomous Digital Assistant), an advanced Jarvis-style cognitive operating system with a female persona. "
            "You have direct real-time access to live web intelligence on your backend. "
            "Be articulate, confident, clear, and executive. "
            "Highlight key facts, context, timeline, and current status. "
            "Answer thoroughly incorporating the user's conversation context and the live web intelligence. "
            "Keep the response structured and impactful so it can be comfortably read or spoken aloud via voice TTS."
        )
        
        history_block = f"Recent Conversation Context:\n{conversation_history}\n\n" if conversation_history else ""
        prompt = (
            f"{history_block}"
            f"User Query: '{query}'\n\n"
            f"Live Web Intelligence retrieved from background search:\n"
            f"{research_context}\n\n"
            f"Deliver an executive briefing directly answering the query based on this intelligence and the conversation context."
        )

        # 1. Try Groq directly with qwen3.8-27b or openai/gpt-oss-120b for ultra-fast, high-quality synthesis
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_key:
            try:
                import requests
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                body = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.4
                }
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=12)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    if content:
                        return content
            except Exception as ge:
                app_logger.warning(f"[WebResearchEngine] Groq synthesis warning: {ge}")

        # 2. Try ProviderManager
        if self.provider_manager:
            try:
                from backend.providers.schema import GenerationRequest, Message, Role, CognitiveDomain
                req = GenerationRequest(
                    messages=[
                        Message(role=Role.SYSTEM, content=system_instruction),
                        Message(role=Role.USER, content=prompt)
                    ],
                    cognitive_domain=CognitiveDomain.REASONING,
                    max_tokens=400,
                    stream=False
                )
                resp = await self.provider_manager.generate(req)
                if resp and resp.content and resp.content.strip():
                    return resp.content.strip()
            except Exception as pe:
                app_logger.warning(f"[WebResearchEngine] ProviderManager synthesis warning: {pe}")
                
        # 3. Direct bullet fallback
        bullets = [f"• **{r['title']}**: {r['snippet'][:140]}..." for r in search_results[:3]]
        return f"Regarding '{query}', here are the key findings:\n\n" + "\n".join(bullets)

    async def _synthesize_fallback(self, query: str) -> str:
        """Fallback synthesis when search yields 0 live hits."""
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if groq_key:
            try:
                import requests
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                body = {
                    "model": "qwen/qwen3.8-27b",
                    "messages": [
                        {"role": "system", "content": "You are ADA, an executive AI operating system. Provide a concise, accurate 2-sentence briefing answering the user's inquiry."},
                        {"role": "user", "content": f"Provide an accurate summary regarding: '{query}'."}
                    ],
                    "max_tokens": 300
                }
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body, timeout=10)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                pass
        return f"I have reviewed my intelligence records for '{query}', but could not find live updates at this moment."
