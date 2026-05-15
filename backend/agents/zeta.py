import json
import os
from typing import Any, Awaitable, Callable

from llm import groq_complete

BroadcastFn = Callable[[str, str, str], Awaitable[None]]

async def run_zeta(
    target_file: str,
    vuln_type: str,
    broadcast_fn: BroadcastFn,
) -> dict[str, Any]:
    await broadcast_fn("Zeta: Reading local file for static analysis...", "ZETA", "info")

    with open(target_file, "r", encoding="utf-8") as f:
        source_code = f.read()

    system_prompt = (
        "You are Zeta, an elite static code analysis AI agent.\n"
        f"Analyze the following source code for '{vuln_type}' vulnerabilities.\n"
        "Return your analysis using exactly these two XML tags:\n"
        "<is_vulnerable>true</is_vulnerable> (or false)\n"
        "<code>the exact vulnerable line of code or explanation here</code>\n"
        "Output ONLY the tags, no other text."
    )

    user_prompt = f"--- SOURCE CODE ---\n{source_code}\n-------------------"

    await broadcast_fn("Zeta: Analyzing code via LLM...", "ZETA", "thinking")

    try:
        response_text = await groq_complete(system_prompt, user_prompt)
        
        import re
        is_vuln_match = re.search(r'<is_vulnerable>(.*?)</is_vulnerable>', response_text, re.IGNORECASE | re.DOTALL)
        code_match = re.search(r'<code>(.*?)</code>', response_text, re.IGNORECASE | re.DOTALL)
        
        is_vuln = False
        if is_vuln_match:
            val = is_vuln_match.group(1).strip().lower()
            is_vuln = val == 'true' or val == 'yes'
            
        code = code_match.group(1).strip() if code_match else ""

        
        if is_vuln:
            await broadcast_fn(f"Zeta: Vulnerability found: {code}", "ZETA", "success")
        else:
            await broadcast_fn("Zeta: Code appears secure.", "ZETA", "info")
            
        return {"is_vulnerable": is_vuln, "vulnerable_code": code}
    except Exception as exc:
        await broadcast_fn(f"Zeta JSON parsing or LLM error: {exc}", "ZETA", "error")
        return {"is_vulnerable": False, "vulnerable_code": ""}
