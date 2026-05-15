import os

LOGS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
PATCHES_DIR = os.path.join(LOGS_DIR, "patches")


def _ensure_logs_dir() -> None:
    os.makedirs(LOGS_DIR, exist_ok=True)


def write_log(scan_id: str, content: str) -> str:
    _ensure_logs_dir()
    path = os.path.join(LOGS_DIR, f"{scan_id}.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path


def write_patch(filename: str, content: str) -> str:
    os.makedirs(PATCHES_DIR, exist_ok=True)
    path = os.path.join(PATCHES_DIR, filename)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return path
