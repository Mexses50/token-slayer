"""Token counting using tiktoken as a Claude tokenizer approximation."""
from __future__ import annotations

from pathlib import Path

import tiktoken

# cl100k_base is the closest public approximation; real Claude counts may differ ±10%
_ENC = tiktoken.get_encoding("cl100k_base")

_IGNORE_DIRS = {
    ".venv", "venv", "__pycache__", ".git", "node_modules",
    "dist", "build", ".egg-info", ".pytest_cache", ".mypy_cache",
}
_IGNORE_SUFFIXES = {".pyc", ".pyo", ".exe", ".dll", ".so", ".dylib", ".png", ".jpg", ".gif"}


def count_tokens(text: str) -> int:
    return len(_ENC.encode(text))


def _should_skip(path: Path, extra_ignore: set[str]) -> bool:
    all_ignore = _IGNORE_DIRS | extra_ignore
    for part in path.parts:
        if part in all_ignore:
            return True
    return path.suffix in _IGNORE_SUFFIXES


def count_project_tokens(root: Path, extra_ignore: set[str] | None = None) -> dict:
    """Return {total: int, files: {rel_path: token_count}}."""
    ignore = extra_ignore or set()
    files: dict[str, int] = {}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if _should_skip(f, ignore):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
            files[str(f.relative_to(root))] = count_tokens(text)
        except Exception:
            pass
    return {"total": sum(files.values()), "files": files}
