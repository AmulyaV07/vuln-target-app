import asyncio
import os
from typing import Awaitable, Callable, Optional

BroadcastFn = Optional[Callable[[str, str, str], Awaitable[None]]]


async def search_exploits(
    query: str,
    broadcast_fn: BroadcastFn = None,
) -> list[str]:
    if broadcast_fn:
        await broadcast_fn(f"Alpha: Searching for — {query}", "ALPHA", "thinking")

    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return []

        def _search() -> list[str]:
            client = TavilyClient(api_key=api_key)
            result = client.search(query=query, max_results=5)
            snippets: list[str] = []
            for item in result.get("results", [])[:5]:
                content = item.get("content") or item.get("snippet") or ""
                title = item.get("title", "")
                if content:
                    snippets.append(f"{title}: {content}".strip())
            return snippets

        return await asyncio.to_thread(_search)
    except Exception:
        return []
