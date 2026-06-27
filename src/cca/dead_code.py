"""Detect symbols that are defined but never used elsewhere in the project."""
from __future__ import annotations

from pathlib import Path

from cca.parser import FileInfo

_SKIP_NAMES = {
    "__init__", "__repr__", "__str__", "__eq__", "__hash__",
    "__len__", "__iter__", "__next__", "__enter__", "__exit__",
    "__call__", "__getitem__", "__setitem__", "__contains__",
    "main",
}


def find_unused_exports(file_infos: list[FileInfo], root: Path) -> dict[str, list[str]]:
    """
    Return {relative_path: [symbol, ...]} for functions/classes that appear
    to be defined but never referenced in any other file.

    Uses simple text search — dynamic access and __all__ are not detected.
    """
    source_texts: dict[str, str] = {}
    for info in file_infos:
        rel = str(info.path.relative_to(root))
        try:
            source_texts[rel] = info.path.read_text(encoding="utf-8")
        except Exception:
            source_texts[rel] = ""

    result: dict[str, list[str]] = {}
    for info in file_infos:
        rel = str(info.path.relative_to(root))
        symbols = [s for s in (info.functions + info.classes) if not s.startswith("_") and s not in _SKIP_NAMES]
        unused = [
            sym for sym in symbols
            if not any(sym in text for other_rel, text in source_texts.items() if other_rel != rel)
        ]
        if unused:
            result[rel] = unused

    return result
