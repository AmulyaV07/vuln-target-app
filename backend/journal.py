import json
import os
from typing import Any, Optional

LOGS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "logs"))


class AttackJournal:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def add_entry(
        self,
        attempt_number: int,
        vuln_type: str,
        payload: str,
        server_response_summary: str,
        gamma_critique: str,
        outcome: str,
    ) -> None:
        self._entries.append(
            {
                "attempt_number": attempt_number,
                "vuln_type": vuln_type,
                "payload": payload,
                "server_response_summary": server_response_summary,
                "gamma_critique": gamma_critique,
                "outcome": outcome,
            }
        )

    def get_entries(self) -> list[dict[str, Any]]:
        return list(self._entries)

    def get_context_string(self) -> str:
        if not self._entries:
            return "No previous attempts yet."

        parts = []
        for entry in self._entries:
            crit = entry['gamma_critique']
            if len(crit) > 300:
                crit = crit[:300] + "...(truncated)"
            parts.append(
                f"ATTEMPT {entry['attempt_number']}: "
                f"Payload=`{entry['payload']}`, "
                f"Response=`{entry['server_response_summary']}`, "
                f"Critique=`{crit}`, "
                f"Outcome={entry['outcome']}."
            )
        return " ".join(parts)

    def get_winning_payload(self) -> Optional[str]:
        for entry in self._entries:
            if entry.get("outcome") == "breached":
                return entry.get("payload")
        return None

    def reset(self) -> None:
        self._entries.clear()

    def to_file(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or LOGS_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self._entries, handle, indent=2)


journal = AttackJournal()
