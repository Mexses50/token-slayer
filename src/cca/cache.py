"""Incremental parse cache — skip unchanged files on repeated runs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CACHE_FILE = ".cca_cache.json"


def _file_sig(path: Path) -> str:
    stat = path.stat()
    return f"{stat.st_mtime_ns}:{stat.st_size}"


def load_cache(root: Path) -> dict[str, Any]:
    cache_path = root / _CACHE_FILE
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(root: Path, cache: dict[str, Any]) -> None:
    try:
        (root / _CACHE_FILE).write_text(
            json.dumps(cache, indent=2), encoding="utf-8"
        )
    except Exception:
        pass  # cache is best-effort; never block normal operation


def get_cached(cache: dict[str, Any], path: Path, root: Path) -> dict | None:
    rel = str(path.relative_to(root))
    entry = cache.get(rel)
    if entry and entry.get("sig") == _file_sig(path):
        return entry.get("data")
    return None


def set_cached(cache: dict[str, Any], path: Path, root: Path, data: dict) -> None:
    rel = str(path.relative_to(root))
    cache[rel] = {"sig": _file_sig(path), "data": data}


def invalidate(cache: dict[str, Any], path: Path, root: Path) -> None:
    rel = str(path.relative_to(root))
    cache.pop(rel, None)
