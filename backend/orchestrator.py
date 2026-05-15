import asyncio
import os
from typing import Awaitable, Callable, Literal

from agents.alpha import run_alpha
from agents.beta import run_beta
from agents.gamma import run_gamma
from agents.delta import run_delta
from agents.epsilon import run_epsilon
from journal import AttackJournal, LOGS_DIR
from tools.file_ops import write_log
from tools.http_exploit import summarize_response

BroadcastFn = Callable[[str, str, str], Awaitable[None]]
ScanOutcome = Literal["breached", "failed", "error"]

MAX_RETRIES = 4


async def run_scan(
    scan_id: str,
    target_url: str,
    vuln_type: str,
    broadcast_fn: BroadcastFn,
    journal: AttackJournal,
) -> ScanOutcome:
    journal.reset()
    target_url = target_url.rstrip("/")
    vuln_type = vuln_type.lower().strip()

    await broadcast_fn(
        f"Orchestrator: Red Swarm engaging {target_url} ({vuln_type})",
        "SYSTEM",
        "info",
    )

    try:
        alpha_data = await run_alpha(target_url, vuln_type, journal, broadcast_fn)
    except Exception as exc:
        await broadcast_fn(f"Alpha failed: {exc}", "ALPHA", "error")
        return "error"

    alpha_results = alpha_data.get("results", [])

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            beta_data = await run_beta(
                target_url,
                vuln_type,
                alpha_results,
                journal,
                broadcast_fn,
                attempt=attempt,
            )
        except Exception as exc:
            await broadcast_fn(f"Beta failed: {exc}", "BETA", "error")
            return "error"

        payload = beta_data.get("payload", "")
        response = beta_data.get("response", {})
        summary = summarize_response(response)

        if response.get("is_breach"):
            journal.add_entry(
                attempt_number=attempt,
                vuln_type=vuln_type,
                payload=payload,
                server_response_summary=summary,
                gamma_critique="",
                outcome="breached",
            )

            log_path = os.path.join(LOGS_DIR, f"{scan_id}.json")
            journal.to_file(log_path)
            write_log(
                scan_id,
                f"BREACH CONFIRMED\nPayload: {payload}\nResponse: {summary}\n",
            )

            await broadcast_fn(
                f"BREACH CONFIRMED — payload succeeded: {payload}",
                "SYSTEM",
                "breach",
            )
            
            # TRIGGER BLUE SWARM
            await broadcast_fn("SYSTEM: Activating Blue Swarm for remediation.", "SYSTEM", "info")
            patch_code = await run_delta(scan_id, target_url, vuln_type, payload, broadcast_fn)
            
            if not patch_code.startswith("Failed"):
                verify_result = await run_epsilon(scan_id, target_url, vuln_type, payload, broadcast_fn)
                # Send the final remediation status back
                await broadcast_fn(
                    f"REMEDIATION_DATA|{verify_result['patch_effective']}|{patch_code}",
                    "SYSTEM",
                    "info"
                )

            return "breached"

        try:
            critique = await run_gamma(
                payload, response, vuln_type, journal, broadcast_fn
            )
        except Exception as exc:
            critique = f"Gamma unavailable: {exc}"
            await broadcast_fn(critique, "GAMMA", "error")

        journal.add_entry(
            attempt_number=attempt,
            vuln_type=vuln_type,
            payload=payload,
            server_response_summary=summary,
            gamma_critique=critique,
            outcome="failed",
        )

        await asyncio.sleep(2)

    await broadcast_fn(
        "Red Swarm exhausted all attempts. Target hardened or scope exceeded.",
        "SYSTEM",
        "error",
    )

    log_path = os.path.join(LOGS_DIR, f"{scan_id}.json")
    journal.to_file(log_path)
    write_log(scan_id, journal.get_context_string())

    return "failed"
