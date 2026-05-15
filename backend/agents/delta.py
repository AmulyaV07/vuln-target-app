import os
from typing import Awaitable, Callable

from llm import groq_complete
from tools.file_ops import write_patch

BroadcastFn = Callable[[str, str, str], Awaitable[None]]

async def run_delta(
    scan_id: str,
    target_url: str,
    vuln_type: str,
    winning_payload: str,
    broadcast_fn: BroadcastFn,
) -> str:
    await broadcast_fn(
        "Delta: Analyzing target source code to design a patch...",
        "DELTA",
        "info",
    )

    try:
        app_path = os.path.join(os.path.dirname(__file__), "..", "..", "target", "app.py")
        with open(app_path, "r", encoding="utf-8") as f:
            source_code = f.read()
    except Exception as exc:
        err = f"Failed to read target source code: {exc}"
        await broadcast_fn(err, "DELTA", "error")
        return err

    system_prompt = (
        "You are Delta, an elite security architect. "
        "You have been given the source code of a vulnerable application and the exact payload that breached it. "
        "Your task is to write a patched version of the specific vulnerable function only. "
        "For SQLi: replace raw string concatenation with parameterized queries using sqlite3's ? placeholder syntax. "
        "For CMDi: add input validation that only allows alphanumeric characters and dots for the host. "
        "CRITICAL: You must also modify the app.run() call at the bottom of the file to use port=5002 instead of 5000. "
        "Output ONLY the complete patched Python code (the full app.py file content, so it can run standalone). "
        "Do not use markdown formatting like ```python, do not explain anything, output raw python code ONLY."
    )

    user_prompt = (
        f"Vulnerability Type: {vuln_type}\n"
        f"Winning Payload that breached the system: {winning_payload}\n\n"
        f"--- CURRENT SOURCE CODE (app.py) ---\n{source_code}\n------------------------------------"
    )

    await broadcast_fn("Delta: Designing and applying patch logic...", "DELTA", "thinking")
    
    try:
        patch_code = await groq_complete(system_prompt, user_prompt)
        
        # Clean up possible markdown if LLM misbehaves
        if patch_code.startswith("```python"):
            patch_code = patch_code[9:]
        if patch_code.startswith("```"):
            patch_code = patch_code[3:]
        if patch_code.endswith("```"):
            patch_code = patch_code[:-3]
            
        patch_code = patch_code.strip()

        patch_filename = f"patch_{scan_id}.py"
        write_patch(patch_filename, patch_code)
        
        await broadcast_fn(
            f"Delta: Patch designed. Source code patched and saved to {patch_filename}.",
            "DELTA",
            "success",
        )
        return patch_code
    except Exception as exc:
        err = f"Failed to generate patch: {exc}"
        await broadcast_fn(err, "DELTA", "error")
        return err
