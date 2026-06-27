"""Tests for cca.config_gen — CLAUDE.md generation."""
from __future__ import annotations

from pathlib import Path

import pytest

from cca.config_gen import generate_claude_md, CLAUDEIGNORE_PATTERNS
from cca.graph import build_graph, get_most_imported
from cca.parser import analyze_project
from cca.dead_code import find_unused_exports


@pytest.fixture
def full_analysis(sample_project: Path):
    infos = analyze_project(sample_project)
    graph = build_graph(infos, sample_project)
    most_imported = get_most_imported(graph, n=10)
    unused = find_unused_exports(infos, sample_project)
    return infos, most_imported, unused, sample_project


class TestGenerateClaudeMd:
    def test_returns_string(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert isinstance(result, str)

    def test_starts_with_heading(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert result.startswith("# CLAUDE.md")

    def test_contains_project_overview(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert "## Project Overview" in result

    def test_file_count_correct(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert f"**Files:** {len(infos)} Python files" in result

    def test_contains_core_files_section_when_imported(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert "## Core Files" in result

    def test_config_py_appears_in_core_files(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert "config.py" in result

    def test_hot_files_section_shown_when_provided(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        hot = {"app/config.py": 5, "main.py": 2}
        result = generate_claude_md(root, infos, most_imported, hot, unused)
        assert "## Hot Files" in result
        assert "app/config.py" in result

    def test_hot_files_section_absent_when_empty(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert "## Hot Files" not in result

    def test_contains_claudeignore_section(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert "## Recommended .claudeignore" in result

    def test_token_savings_shown_when_provided(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused, token_savings_pct=42.5)
        assert "42.5%" in result

    def test_token_savings_absent_when_none(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused, token_savings_pct=None)
        assert "token reduction" not in result

    def test_dead_code_section_shown(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        if unused:
            result = generate_claude_md(root, infos, most_imported, {}, unused)
            assert "## Possible Dead Code" in result

    def test_dead_code_absent_when_none(self, full_analysis):
        infos, most_imported, _, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, {})
        assert "## Possible Dead Code" not in result

    def test_contains_project_structure(self, full_analysis):
        infos, most_imported, unused, root = full_analysis
        result = generate_claude_md(root, infos, most_imported, {}, unused)
        assert "## Project Structure" in result


class TestClaudeignorePatterns:
    def test_is_list(self):
        assert isinstance(CLAUDEIGNORE_PATTERNS, list)

    def test_contains_common_patterns(self):
        patterns_text = "\n".join(CLAUDEIGNORE_PATTERNS)
        assert "__pycache__" in patterns_text
        assert ".venv" in patterns_text
        assert "*.pyc" in patterns_text

    def test_no_empty_strings(self):
        assert all(p.strip() for p in CLAUDEIGNORE_PATTERNS)
