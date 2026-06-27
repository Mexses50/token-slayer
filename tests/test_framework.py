"""Tests for cca.framework — framework detection."""
from __future__ import annotations

from pathlib import Path

import pytest

from cca.framework import detect_frameworks
from cca.parser import analyze_file, FileInfo


def _make_info(imports: list[str]) -> FileInfo:
    return FileInfo(path=Path("fake.py"), lines=1, imports=imports)


class TestDetectFrameworks:
    def test_detects_fastapi(self):
        info = _make_info(["fastapi", "fastapi.routing"])
        result = detect_frameworks([info])
        assert "fastapi" in result
        assert result["fastapi"] == "FastAPI"

    def test_detects_flask(self):
        info = _make_info(["flask"])
        result = detect_frameworks([info])
        assert "flask" in result

    def test_detects_django(self):
        info = _make_info(["django.db", "django.http"])
        result = detect_frameworks([info])
        assert "django" in result

    def test_detects_sqlalchemy(self):
        info = _make_info(["sqlalchemy.orm", "sqlalchemy"])
        result = detect_frameworks([info])
        assert "sqlalchemy" in result

    def test_detects_pydantic(self):
        info = _make_info(["pydantic"])
        result = detect_frameworks([info])
        assert "pydantic" in result

    def test_stdlib_not_detected(self):
        info = _make_info(["os", "sys", "pathlib", "typing"])
        result = detect_frameworks([info])
        assert result == {}

    def test_multiple_frameworks(self):
        info = _make_info(["fastapi", "sqlalchemy", "pydantic", "celery"])
        result = detect_frameworks([info])
        assert len(result) == 4

    def test_returns_dict(self):
        result = detect_frameworks([])
        assert isinstance(result, dict)

    def test_deduplicates_same_root(self):
        info = _make_info(["fastapi", "fastapi.routing", "fastapi.middleware"])
        result = detect_frameworks([info])
        assert list(result.keys()).count("fastapi") == 1

    def test_multiple_files(self):
        a = _make_info(["fastapi"])
        b = _make_info(["sqlalchemy"])
        result = detect_frameworks([a, b])
        assert "fastapi" in result
        assert "sqlalchemy" in result
