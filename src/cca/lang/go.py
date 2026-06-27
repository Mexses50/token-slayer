"""Go file analysis (regex-based)."""
from __future__ import annotations

import re
from pathlib import Path

from cca.parser import FileInfo

GO_EXTENSIONS = {".go"}

_FUNC_RE = re.compile(
    r"\bfunc\s+(?:\(\s*\w+\s+\*?\w+\s*\)\s+)?(\w+)\s*\("
)
_TYPE_RE = re.compile(r"\btype\s+(\w+)\s+(?:struct|interface)\b")
_IMPORT_BLOCK_RE = re.compile(r'import\s*\(([^)]*)\)', re.DOTALL)
_IMPORT_SINGLE_RE = re.compile(r'import\s+"([^"]+)"')
_IMPORT_PATH_RE = re.compile(r'"([^"]+)"')
_RETURN_TYPE_RE = re.compile(r"\bfunc\s+(?:\([^)]+\)\s+)?\w+\s*\([^)]*\)\s+\(?[\w\*\[\]]+")
_BRANCH_RE = re.compile(r"\bif\b|\bfor\b|\bswitch\b|\bcase\b|\bselect\b")


def analyze_go_file(path: Path) -> FileInfo:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return FileInfo(path=path, lines=0, language="go")

    lines = source.count("\n") + 1
    functions = [m.group(1) for m in _FUNC_RE.finditer(source)]
    classes = [m.group(1) for m in _TYPE_RE.finditer(source)]

    imports: list[str] = []
    for block_match in _IMPORT_BLOCK_RE.finditer(source):
        for path_match in _IMPORT_PATH_RE.finditer(block_match.group(1)):
            pkg = path_match.group(1).split("/")[-1]
            imports.append(pkg)
    for m in _IMPORT_SINGLE_RE.finditer(source):
        if not _IMPORT_BLOCK_RE.search(source):
            imports.append(m.group(1).split("/")[-1])

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
        language="go",
    )
