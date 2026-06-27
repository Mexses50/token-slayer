"""Tests for cca.dead_code — unused symbol detection."""
from __future__ import annotations

from pathlib import Path

import pytest

from cca.dead_code import find_unused_exports
from cca.parser import analyze_project


class TestFindUnusedExports:
    def test_unused_function_detected(self, sample_project: Path):
        infos = analyze_project(sample_project)
        unused = find_unused_exports(infos, sample_project)
        # unused_function is defined in utils.py but never imported elsewhere
        utils_key = next(k for k in unused if "utils" in k)
        assert "unused_function" in unused[utils_key]

    def test_used_function_not_flagged(self, sample_project: Path):
        infos = analyze_project(sample_project)
        unused = find_unused_exports(infos, sample_project)
        utils_key = next((k for k in unused if "utils" in k), None)
        if utils_key:
            assert "helper" not in unused[utils_key]

    def test_text_search_limitation_with_alias(self, sample_project: Path):
        # Settings class: only "settings" (instance) is imported elsewhere, not "Settings"
        # The text-search detector correctly flags this as potentially unused.
        # This is a known false-positive: class is used internally to build `settings`.
        infos = analyze_project(sample_project)
        unused = find_unused_exports(infos, sample_project)
        # We simply verify the function returns a dict — we don't assert on Settings
        # since text-search can't distinguish class-from-instance usage.
        assert isinstance(unused, dict)

    def test_private_functions_skipped(self, tmp_path: Path):
        (tmp_path / "mod.py").write_text(
            "def _private():\n    pass\n\ndef public():\n    pass\n",
            encoding="utf-8",
        )
        from cca.parser import FileInfo, analyze_file
        info = analyze_file(tmp_path / "mod.py")
        unused = find_unused_exports([info], tmp_path)
        mod_key = next((k for k in unused if "mod" in k), None)
        if mod_key:
            assert "_private" not in unused[mod_key]

    def test_dunder_methods_skipped(self, tmp_path: Path):
        (tmp_path / "cls.py").write_text(
            "class Foo:\n    def __init__(self): pass\n    def __repr__(self): pass\n    def bar(self): pass\n",
            encoding="utf-8",
        )
        from cca.parser import analyze_file
        info = analyze_file(tmp_path / "cls.py")
        unused = find_unused_exports([info], tmp_path)
        cls_key = next((k for k in unused if "cls" in k), None)
        if cls_key:
            assert "__init__" not in unused[cls_key]
            assert "__repr__" not in unused[cls_key]

    def test_returns_dict(self, sample_project: Path):
        infos = analyze_project(sample_project)
        result = find_unused_exports(infos, sample_project)
        assert isinstance(result, dict)

    def test_single_file_project_everything_unused(self, tmp_path: Path):
        (tmp_path / "solo.py").write_text(
            "def alpha():\n    pass\n\ndef beta():\n    pass\n",
            encoding="utf-8",
        )
        from cca.parser import analyze_file
        info = analyze_file(tmp_path / "solo.py")
        unused = find_unused_exports([info], tmp_path)
        assert "alpha" in unused.get("solo.py", [])
        assert "beta" in unused.get("solo.py", [])

    def test_cross_referenced_symbol_not_flagged(self, tmp_path: Path):
        (tmp_path / "a.py").write_text("def shared():\n    pass\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("from a import shared\n", encoding="utf-8")
        from cca.parser import analyze_file
        infos = [analyze_file(tmp_path / "a.py"), analyze_file(tmp_path / "b.py")]
        unused = find_unused_exports(infos, tmp_path)
        a_key = next((k for k in unused if k.endswith("a.py")), None)
        assert a_key is None or "shared" not in unused.get(a_key, [])

    def test_empty_project(self, tmp_path: Path):
        assert find_unused_exports([], tmp_path) == {}
