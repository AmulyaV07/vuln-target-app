from typing import Awaitable, Callable

from journal import AttackJournal

BroadcastFn = Callable[[str, str, str], Awaitable[None]]


async def run_scan(
    target_url: str,
    vuln_type: str,
    broadcast_fn: BroadcastFn,
    journal: AttackJournal,
) -> None:
    """Phase 2 stub — full Red Swarm loop wired in Phase 3."""
    await broadcast_fn(
        f"Orchestrator: scan stub started for {target_url} ({vuln_type})",
        "SYSTEM",
        "info",
    )
    await broadcast_fn(
        "Orchestrator: Phase 2 test ping — backend is alive.",
        "SYSTEM",
        "success",
    )
