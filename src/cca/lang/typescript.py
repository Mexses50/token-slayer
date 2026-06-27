"""TypeScript / JavaScript file analysis (regex-based)."""
from __future__ import annotations

import re
from pathlib import Path

from cca.parser import FileInfo

TS_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}

_FUNC_RE = re.compile(
    r"(?:function\s+(\w+))|(?:(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\()"
)
_CLASS_RE = re.compile(r"\bclass\s+(\w+)")
_IMPORT_RE = re.compile(
    r"""(?:import|from)\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
)
_RETURN_TYPE_RE = re.compile(r"\)\s*:\s*\w")  # ): SomeType  →  explicit return type

_BRANCH_RE = re.compile(
    r"\bif\s*\(|\bfor\s*\(|\bwhile\s*\(|\bswitch\s*\(|\bcatch\s*\(|\?(?!=)"
)


def analyze_ts_file(path: Path) -> FileInfo:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return FileInfo(path=path, lines=0, language="typescript")

    lines = source.count("\n") + 1

    functions = [
        m.group(1) or m.group(2)
        for m in _FUNC_RE.finditer(source)
        if m.group(1) or m.group(2)
    ]
    classes = [m.group(1) for m in _CLASS_RE.finditer(source)]
    imports_raw = [
        m.group(1) or m.group(2)
        for m in _IMPORT_RE.finditer(source)
        if m.group(1) or m.group(2)
    ]
    # Keep only the package root (strip relative paths)
    imports = [
        imp.lstrip("./").split("/")[0]
        for imp in imports_raw
        if not imp.startswith(".")
    ]

    complexity = len(_BRANCH_RE.findall(source))
    typed_funcs = min(len(_RETURN_TYPE_RE.findall(source)), len(functions))

    return FileInfo(
        path=path,
        lines=lines,
        functions=functions,
        classes=classes,
        imports=imports,
        complexity=complexity,
        typed_functions=typed_funcs,
        language="typescript",
    )
