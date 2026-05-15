import asyncio
import os
import shutil
import subprocess
import time
from typing import Awaitable, Callable

from tools.http_exploit import fire_payload

BroadcastFn = Callable[[str, str, str], Awaitable[None]]

async def run_epsilon(
    scan_id: str,
    target_url: str,
    vuln_type: str,
    winning_payload: str,
    broadcast_fn: BroadcastFn,
) -> dict:
    await broadcast_fn("Epsilon: Initializing verification environment...", "EPSILON", "info")
    
    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    patch_path = os.path.join(root_dir, "logs", "patches", f"patch_{scan_id}.py")
    target_dir = os.path.join(root_dir, "target")
    test_patch_path = os.path.join(target_dir, f"test_patch_{scan_id}.py")
    
    if not os.path.exists(patch_path):
        err = "Patch file not found for verification."
        await broadcast_fn(err, "EPSILON", "error")
        return {"patch_effective": False}

    # Copy the patch to the target dir so it can resolve database.py
    shutil.copy2(patch_path, test_patch_path)
    
    await broadcast_fn("Epsilon: Starting patched target on test port 5002...", "EPSILON", "thinking")
    
    proc = None
    try:
        proc = subprocess.Popen(
            ["python", f"test_patch_{scan_id}.py"],
            cwd=target_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Give Flask time to boot
        await asyncio.sleep(2)
        
        await broadcast_fn("Epsilon: Re-firing winning payload against patched code...", "EPSILON", "info")
        
        # Hit the new port 5002
        test_url = "http://localhost:5002"
        response = await fire_payload(test_url, vuln_type, winning_payload, broadcast_fn)
        
        is_breach = response.get("is_breach", False)
        
        if is_breach:
            await broadcast_fn("Epsilon: PATCH INSUFFICIENT — exploit still works", "EPSILON", "error")
            effective = False
        else:
            await broadcast_fn("Epsilon: PATCH VERIFIED — exploit neutralized", "EPSILON", "success")
            effective = True
            
        return {"patch_effective": effective}
        
    finally:
        if proc:
            proc.terminate()
            proc.wait(timeout=2)
        
        if os.path.exists(test_patch_path):
            try:
                os.remove(test_patch_path)
            except OSError:
                pass
