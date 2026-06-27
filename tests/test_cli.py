"""CLI integration tests using Typer's CliRunner."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cca.cli import app

runner = CliRunner()


class TestAnalyzeCommand:
    def test_exits_zero_on_valid_project(self, sample_project: Path):
        result = runner.invoke(app, ["analyze", str(sample_project)])
        assert result.exit_code == 0, result.output

    def test_output_contains_file_names(self, sample_project: Path):
        result = runner.invoke(app, ["analyze", str(sample_project)])
        assert "main.py" in result.output
        assert "config.py" in result.output

    def test_output_contains_analysis_columns(self, sample_project: Path):
        result = runner.invoke(app, ["analyze", str(sample_project)])
        # Rich may truncate column headers; check for "Lines" and "Funcs" which are short enough
        assert "Lines" in result.output
        assert "Funcs" in result.output

    def test_tokens_flag_shows_token_report(self, sample_project: Path):
        result = runner.invoke(app, ["analyze", str(sample_project), "--tokens"])
        assert result.exit_code == 0, result.output
        assert "tasarruf" in result.output or "token" in result.output.lower()

    def test_dead_code_flag_shows_unused_section(self, sample_project: Path):
        result = runner.invoke(app, ["analyze", str(sample_project), "--dead-code"])
        assert result.exit_code == 0, result.output
        # Either shows dead code panel or "no dead code" message
        assert "Dead Code" in result.output or "dead code" in result.output.lower()

    def test_nonexistent_path_exits_nonzero(self, tmp_path: Path):
        result = runner.invoke(app, ["analyze", str(tmp_path / "doesnotexist")])
        assert result.exit_code != 0

    def test_file_instead_of_dir_exits_nonzero(self, tmp_path: Path):
        f = tmp_path / "file.py"
        f.write_text("x = 1\n", encoding="utf-8")
        result = runner.invoke(app, ["analyze", str(f)])
        assert result.exit_code != 0

    def test_empty_project_exits_zero(self, tmp_path: Path):
        result = runner.invoke(app, ["analyze", str(tmp_path)])
        assert result.exit_code == 0

    def test_all_flags_combined(self, sample_project: Path):
        result = runner.invoke(app, ["analyze", str(sample_project), "--tokens", "--dead-code"])
        assert result.exit_code == 0, result.output


class TestGenerateConfigCommand:
    def test_exits_zero(self, sample_project: Path):
        result = runner.invoke(app, ["generate-config", str(sample_project)])
        assert result.exit_code == 0, result.output

    def test_creates_claude_md(self, sample_project: Path):
        runner.invoke(app, ["generate-config", str(sample_project)])
        assert (sample_project / "CLAUDE.md").exists()

    def test_claude_md_content_valid(self, sample_project: Path):
        runner.invoke(app, ["generate-config", str(sample_project)])
        content = (sample_project / "CLAUDE.md").read_text(encoding="utf-8")
        assert "# CLAUDE.md" in content
        assert "## Project Overview" in content

    def test_custom_output_path(self, sample_project: Path, tmp_path: Path):
        out = tmp_path / "my_config.md"
        result = runner.invoke(app, ["generate-config", str(sample_project), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_nonexistent_path_exits_nonzero(self, tmp_path: Path):
        result = runner.invoke(app, ["generate-config", str(tmp_path / "nope")])
        assert result.exit_code != 0

    def test_shows_token_report(self, sample_project: Path):
        result = runner.invoke(app, ["generate-config", str(sample_project)])
        assert "tasarruf" in result.output or "token" in result.output.lower()


class TestVersionCommand:
    def test_shows_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "cca v" in result.output

    def test_version_string_format(self):
        result = runner.invoke(app, ["version"])
        # Should be something like "cca v0.1.0"
        import re
        assert re.search(r"cca v\d+\.\d+\.\d+", result.output)


class TestHelpText:
    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "analyze" in result.output
        assert "generate-config" in result.output

    def test_analyze_help(self):
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "--tokens" in result.output
        assert "--dead-code" in result.output
