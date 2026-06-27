"""Parse Python source files using tree-sitter."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_python as tspython

_LANGUAGE = Language(tspython.language())
_PARSER = Parser(_LANGUAGE)

IGNORE_DIRS = {
    ".venv", "venv", "__pycache__", ".git", "node_modules",
    "dist", "build", ".egg-info", ".pytest_cache", ".mypy_cache",
}


@dataclass
class FileInfo:
    path: Path
    lines: int
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)

    @property
    def function_count(self) -> int:
        return len(self.functions)

    @property
    def class_count(self) -> int:
        return len(self.classes)


def _walk(node, visitor):
    visitor(node)
    for child in node.children:
        _walk(child, visitor)


def _extract_imports(root_node, source: bytes) -> list[str]:
    results: list[str] = []

    def visit(node):
        if node.type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    results.append(source[child.start_byte:child.end_byte].decode())
                elif child.type == "aliased_import":
                    for sub in child.children:
                        if sub.type == "dotted_name":
                            results.append(source[sub.start_byte:sub.end_byte].decode())
                            break
        elif node.type == "import_from_statement":
            for child in node.children:
                if child.type == "relative_import":
                    break
                if child.type == "dotted_name":
                    results.append(source[child.start_byte:child.end_byte].decode())
                    break

    _walk(root_node, visit)
    return results


def _extract_definitions(root_node, source: bytes) -> tuple[list[str], list[str]]:
    functions: list[str] = []
    classes: list[str] = []

    def visit(node):
        if node.type == "function_definition":
            for child in node.children:
                if child.type == "identifier":
                    functions.append(source[child.start_byte:child.end_byte].decode())
                    break
        elif node.type == "class_definition":
            for child in node.children:
                if child.type == "identifier":
                    classes.append(source[child.start_byte:child.end_byte].decode())
                    break

    _walk(root_node, visit)
    return functions, classes


def analyze_file(path: Path) -> FileInfo:
    source = path.read_bytes()
    tree = _PARSER.parse(source)
    lines = source.count(b"\n") + 1
    imports = _extract_imports(tree.root_node, source)
    functions, classes = _extract_definitions(tree.root_node, source)
    return FileInfo(path=path, lines=lines, imports=imports, functions=functions, classes=classes)


def analyze_project(root: Path) -> list[FileInfo]:
    results: list[FileInfo] = []
    for py_file in sorted(root.rglob("*.py")):
        if any(part in IGNORE_DIRS for part in py_file.parts):
            continue
        try:
            results.append(analyze_file(py_file))
        except Exception:
            pass
    return results
