"""Multi-language analysis: TypeScript, JavaScript, Go (regex-based)."""
from __future__ import annotations

from pathlib import Path

from cca.parser import FileInfo, IGNORE_DIRS
from cca.lang.typescript import analyze_ts_file, TS_EXTENSIONS
from cca.lang.go import analyze_go_file, GO_EXTENSIONS

ALL_EXTRA_EXTENSIONS = TS_EXTENSIONS | GO_EXTENSIONS


def analyze_extra_files(root: Path) -> list[FileInfo]:
    """Return FileInfo list for all TS/JS/Go files in the project."""
    results: list[FileInfo] = []
    for ext in sorted(ALL_EXTRA_EXTENSIONS):
        for f in sorted(root.rglob(f"*{ext}")):
            if any(part in IGNORE_DIRS for part in f.parts):
                continue
            try:
                if ext in TS_EXTENSIONS:
                    results.append(analyze_ts_file(f))
                else:
                    results.append(analyze_go_file(f))
            except Exception:
                pass
    return results


def detect_extra_languages(root: Path) -> set[str]:
    """Return set of extra language names found in the project."""
    found: set[str] = set()
    for ext in TS_EXTENSIONS:
        if next(root.rglob(f"*{ext}"), None):
            found.add("typescript")
            break
    for ext in GO_EXTENSIONS:
        if next(root.rglob(f"*{ext}"), None):
            found.add("go")
            break
    return found
