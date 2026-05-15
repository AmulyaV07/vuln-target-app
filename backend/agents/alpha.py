import asyncio
import json
import re
from typing import Any, Awaitable, Callable

from journal import AttackJournal
from llm import groq_complete
from target_intel import get_attack_surface
from tools.web_search import search_exploits

BroadcastFn = Callable[[str, str, str], Awaitable[None]]


def _parse_queries(raw: str) -> list[str]:
    raw = raw.strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(q).strip() for q in parsed[:3] if str(q).strip()]
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                return [str(q).strip() for q in parsed[:3] if str(q).strip()]
        except json.JSONDecodeError:
            pass

    lines = [line.strip(" \"'-") for line in raw.splitlines() if line.strip()]
    return lines[:3] if lines else [raw[:120]]


async def run_alpha(
    target_url: str,
    vuln_type: str,
    journal: AttackJournal,
    broadcast_fn: BroadcastFn,
) -> dict[str, Any]:
    await broadcast_fn(
        f"Alpha: Starting recon on {target_url} for {vuln_type}",
        "ALPHA",
        "info",
    )

    system_prompt = (
        "You are Alpha, an elite reconnaissance agent. Given a target URL and "
        "vulnerability type, generate 3 specific, targeted web search queries to "
        "find real PoC payloads and bypass techniques for this exact environment. "
        "Output ONLY a JSON array of 3 search query strings, nothing else."
    )
    surface = get_attack_surface(vuln_type, target_url)
    user_prompt = (
        f"Target URL: {target_url}\nVulnerability type: {vuln_type}\n\n{surface}\n"
        "Search for payloads that match this exact JSON POST injection point."
    )

    raw = await groq_complete(system_prompt, user_prompt)
    queries = _parse_queries(raw)

    all_snippets: list[str] = []
    for query in queries:
        snippets = await search_exploits(query, broadcast_fn)
        all_snippets.extend(snippets)
        await asyncio.sleep(2)

    await broadcast_fn(
        f"Alpha: Recon complete. Found {len(all_snippets)} intelligence sources.",
        "ALPHA",
        "success",
    )

    return {"queries": queries, "results": all_snippets}
