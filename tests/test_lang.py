"""Tests for cca.lang — TypeScript and Go analysis."""
from __future__ import annotations

from pathlib import Path

import pytest

from cca.lang.typescript import analyze_ts_file
from cca.lang.go import analyze_go_file
from cca.lang import detect_extra_languages


class TestTypeScriptAnalyzer:
    def test_detects_functions(self, tmp_path: Path):
        f = tmp_path / "app.ts"
        f.write_text(
            "function greet(name: string): string { return name; }\n"
            "const add = (a: number, b: number) => a + b;\n",
            encoding="utf-8",
        )
        info = analyze_ts_file(f)
        assert info.function_count >= 1

    def test_detects_classes(self, tmp_path: Path):
        f = tmp_path / "service.ts"
        f.write_text("class UserService { }\nclass AuthService { }\n", encoding="utf-8")
        info = analyze_ts_file(f)
        assert "UserService" in info.classes
        assert "AuthService" in info.classes

    def test_detects_imports(self, tmp_path: Path):
        f = tmp_path / "mod.ts"
        f.write_text(
            'import { useState } from "react";\nimport axios from "axios";\n',
            encoding="utf-8",
        )
        info = analyze_ts_file(f)
        assert "react" in info.imports
        assert "axios" in info.imports

    def test_counts_lines(self, tmp_path: Path):
        f = tmp_path / "lines.ts"
        content = "\n".join([f"const x{i} = {i};" for i in range(20)])
        f.write_text(content, encoding="utf-8")
        info = analyze_ts_file(f)
        assert info.lines == 20

    def test_complexity_from_branches(self, tmp_path: Path):
        f = tmp_path / "branchy.ts"
        f.write_text(
            "function check(x: number) {\n"
            "  if (x > 0) { return true; }\n"
            "  for (let i = 0; i < x; i++) { }\n"
            "  return false;\n"
            "}\n",
            encoding="utf-8",
        )
        info = analyze_ts_file(f)
        assert info.complexity >= 2

    def test_language_field(self, tmp_path: Path):
        f = tmp_path / "a.ts"
        f.write_text("const x = 1;\n", encoding="utf-8")
        info = analyze_ts_file(f)
        assert info.language == "typescript"

    def test_missing_file_returns_empty_info(self, tmp_path: Path):
        f = tmp_path / "missing.ts"
        f.write_text("", encoding="utf-8")
        info = analyze_ts_file(f)
        assert info.lines == 1  # empty file has 1 line (count("\n")+1)


class TestGoAnalyzer:
    def test_detects_functions(self, tmp_path: Path):
        f = tmp_path / "main.go"
        f.write_text(
            "package main\n\nfunc main() {}\nfunc helper(x int) int { return x }\n",
            encoding="utf-8",
        )
        info = analyze_go_file(f)
        assert "main" in info.functions
        assert "helper" in info.functions

    def test_detects_struct_as_class(self, tmp_path: Path):
        f = tmp_path / "types.go"
        f.write_text("package p\ntype User struct { Name string }\n", encoding="utf-8")
        info = analyze_go_file(f)
        assert "User" in info.classes

    def test_detects_interface(self, tmp_path: Path):
        f = tmp_path / "iface.go"
        f.write_text(
            "package p\ntype Repository interface { Find(id int) User }\n",
            encoding="utf-8",
        )
        info = analyze_go_file(f)
        assert "Repository" in info.classes

    def test_detects_imports(self, tmp_path: Path):
        f = tmp_path / "imports.go"
        f.write_text(
            'package main\nimport (\n\t"fmt"\n\t"net/http"\n)\n',
            encoding="utf-8",
        )
        info = analyze_go_file(f)
        assert "fmt" in info.imports
        assert "http" in info.imports

    def test_language_field(self, tmp_path: Path):
        f = tmp_path / "a.go"
        f.write_text("package main\n", encoding="utf-8")
        info = analyze_go_file(f)
        assert info.language == "go"

    def test_complexity_from_branches(self, tmp_path: Path):
        f = tmp_path / "branchy.go"
        f.write_text(
            "package main\nfunc f(x int) int {\n"
            "  if x > 0 { return x }\n"
            "  for i := 0; i < x; i++ { }\n"
            "  return 0\n}\n",
            encoding="utf-8",
        )
        info = analyze_go_file(f)
        assert info.complexity >= 2


class TestDetectExtraLanguages:
    def test_detects_typescript(self, tmp_path: Path):
        (tmp_path / "app.ts").write_text("const x = 1;\n", encoding="utf-8")
        langs = detect_extra_languages(tmp_path)
        assert "typescript" in langs

    def test_detects_go(self, tmp_path: Path):
        (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
        langs = detect_extra_languages(tmp_path)
        assert "go" in langs

    def test_python_only_returns_empty(self, tmp_path: Path):
        (tmp_path / "mod.py").write_text("x = 1\n", encoding="utf-8")
        langs = detect_extra_languages(tmp_path)
        assert langs == set()

    def test_empty_dir_returns_empty(self, tmp_path: Path):
        assert detect_extra_languages(tmp_path) == set()
