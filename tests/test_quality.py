"""Tests for complexity and type coverage in parser, and find_cycles in graph."""
from __future__ import annotations

from pathlib import Path

import pytest

from cca.parser import analyze_file, analyze_project
from cca.graph import build_graph, find_cycles


class TestComplexity:
    def test_simple_function_zero_complexity(self, tmp_path: Path):
        (tmp_path / "simple.py").write_text(
            "def greet(name: str) -> str:\n    return f'hello {name}'\n",
            encoding="utf-8",
        )
        info = analyze_file(tmp_path / "simple.py")
        assert info.complexity == 0

    def test_if_adds_complexity(self, tmp_path: Path):
        (tmp_path / "cond.py").write_text(
            "def check(x):\n    if x > 0:\n        return True\n    return False\n",
            encoding="utf-8",
        )
        info = analyze_file(tmp_path / "cond.py")
        assert info.complexity >= 1

    def test_for_loop_adds_complexity(self, tmp_path: Path):
        (tmp_path / "loop.py").write_text(
            "def process(items):\n    for item in items:\n        print(item)\n",
            encoding="utf-8",
        )
        info = analyze_file(tmp_path / "loop.py")
        assert info.complexity >= 1

    def test_nested_conditions_accumulate(self, tmp_path: Path):
        code = (
            "def complex(x, y):\n"
            "    if x > 0:\n"
            "        if y > 0:\n"
            "            for i in range(x):\n"
            "                if i % 2 == 0:\n"
            "                    pass\n"
        )
        (tmp_path / "nested.py").write_text(code, encoding="utf-8")
        info = analyze_file(tmp_path / "nested.py")
        assert info.complexity >= 3

    def test_complexity_field_exists(self, sample_project: Path):
        from cca.parser import analyze_file
        info = analyze_file(sample_project / "main.py")
        assert hasattr(info, "complexity")
        assert isinstance(info.complexity, int)


class TestTypeCoverage:
    def test_annotated_function_counted(self, tmp_path: Path):
        (tmp_path / "typed.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n",
            encoding="utf-8",
        )
        info = analyze_file(tmp_path / "typed.py")
        assert info.typed_functions == 1
        assert info.type_coverage == 100.0

    def test_unannotated_function_not_counted(self, tmp_path: Path):
        (tmp_path / "untyped.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )
        info = analyze_file(tmp_path / "untyped.py")
        assert info.typed_functions == 0
        assert info.type_coverage == 0.0

    def test_mixed_coverage(self, tmp_path: Path):
        code = (
            "def typed() -> None:\n    pass\n\n"
            "def untyped():\n    pass\n"
        )
        (tmp_path / "mixed.py").write_text(code, encoding="utf-8")
        info = analyze_file(tmp_path / "mixed.py")
        assert info.typed_functions == 1
        assert info.type_coverage == 50.0

    def test_no_functions_coverage_zero(self, tmp_path: Path):
        (tmp_path / "empty.py").write_text("X = 1\n", encoding="utf-8")
        info = analyze_file(tmp_path / "empty.py")
        assert info.type_coverage == 0.0


class TestFindCycles:
    def test_no_cycles_returns_empty(self, sample_project: Path):
        from cca.parser import analyze_project
        infos = analyze_project(sample_project)
        graph = build_graph(infos, sample_project)
        cycles = find_cycles(graph)
        assert cycles == []

    def test_detects_simple_cycle(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("from b import x\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("from a import y\n", encoding="utf-8")
        from cca.parser import analyze_file
        infos = [analyze_file(tmp_path / "a.py"), analyze_file(tmp_path / "b.py")]
        graph = build_graph(infos, tmp_path)
        cycles = find_cycles(graph)
        assert len(cycles) >= 1

    def test_returns_list(self, sample_project: Path):
        from cca.parser import analyze_project
        infos = analyze_project(sample_project)
        graph = build_graph(infos, sample_project)
        result = find_cycles(graph)
        assert isinstance(result, list)
