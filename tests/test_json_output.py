"""Tests for --json output flag on CLI commands."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cca.cli import app

runner = CliRunner()


@pytest.fixture()
def simple_project(tmp_path: Path) -> Path:
    (tmp_path / "main.py").write_text(
        "def hello() -> None:\n    print('hi')\n", encoding="utf-8"
    )
    return tmp_path


class TestAnalyzeJsonOutput:
    def test_analyze_json_valid(self, simple_project: Path):
        result = runner.invoke(app, ["analyze", str(simple_project), "--json"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert "files" in data
        assert "total_lines" in data
        assert "frameworks" in data

    def test_analyze_json_files_count(self, simple_project: Path):
        result = runner.invoke(app, ["analyze", str(simple_project), "--json"])
        data = json.loads(result.output)
        assert data["files"] == 1

    def test_analyze_json_with_tokens(self, simple_project: Path):
        result = runner.invoke(
            app, ["analyze", str(simple_project), "--json", "--tokens"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "tokens" in data
        assert "baseline" in data["tokens"]
        assert "optimized" in data["tokens"]

    def test_analyze_json_with_cycles(self, simple_project: Path):
        result = runner.invoke(
            app, ["analyze", str(simple_project), "--json", "--cycles"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "cycles" in data
        assert isinstance(data["cycles"], list)

    def test_analyze_json_with_quality(self, simple_project: Path):
        result = runner.invoke(
            app, ["analyze", str(simple_project), "--json", "--quality"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "quality" in data
        assert "avg_complexity" in data["quality"]


class TestTokensJsonOutput:
    def test_tokens_json_valid(self, simple_project: Path):
        result = runner.invoke(app, ["tokens", str(simple_project), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "baseline_tokens" in data
        assert "optimized_tokens" in data
        assert "savings_pct" in data

    def test_tokens_json_savings_range(self, simple_project: Path):
        result = runner.invoke(app, ["tokens", str(simple_project), "--json"])
        data = json.loads(result.output)
        assert 0 <= data["savings_pct"] <= 100


class TestScoreCommand:
    def test_score_exits_ok(self, simple_project: Path):
        result = runner.invoke(app, ["score", str(simple_project)])
        assert result.exit_code == 0

    def test_score_json_structure(self, simple_project: Path):
        result = runner.invoke(app, ["score", str(simple_project), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total" in data
        assert "grade" in data
        assert "breakdown" in data

    def test_score_grade_is_letter(self, simple_project: Path):
        result = runner.invoke(app, ["score", str(simple_project), "--json"])
        data = json.loads(result.output)
        assert data["grade"] in {"A", "B", "C", "D"}

    def test_score_total_in_range(self, simple_project: Path):
        result = runner.invoke(app, ["score", str(simple_project), "--json"])
        data = json.loads(result.output)
        assert 0 <= data["total"] <= 100


class TestAuditJsonOutput:
    def test_audit_json_no_claude_md(self, simple_project: Path):
        result = runner.invoke(app, ["audit", str(simple_project), "--json"])
        data = json.loads(result.output)
        assert "ok" in data
        assert "issues" in data
        assert "passed" in data
        assert not data["passed"]

    def test_audit_json_with_claude_md(self, simple_project: Path):
        # Create CLAUDE.md so the first check passes
        (simple_project / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
        result = runner.invoke(app, ["audit", str(simple_project), "--json"])
        data = json.loads(result.output)
        assert isinstance(data["ok"], list)
        assert isinstance(data["issues"], list)


class TestInitHooks:
    def test_no_git_dir_exits_nonzero(self, tmp_path: Path):
        (tmp_path / "mod.py").write_text("x = 1\n", encoding="utf-8")
        result = runner.invoke(app, ["init-hooks", str(tmp_path)])
        assert result.exit_code != 0

    def test_writes_hook_file(self, tmp_path: Path):
        (tmp_path / "mod.py").write_text("x = 1\n", encoding="utf-8")
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        result = runner.invoke(app, ["init-hooks", str(tmp_path)])
        assert result.exit_code == 0
        hook = tmp_path / ".git" / "hooks" / "pre-commit"
        assert hook.exists()
        content = hook.read_text(encoding="utf-8")
        assert "tslayer audit" in content

    def test_existing_hook_blocked_without_force(self, tmp_path: Path):
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        (git_dir / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
        result = runner.invoke(app, ["init-hooks", str(tmp_path)])
        assert result.exit_code != 0

    def test_force_overwrites_hook(self, tmp_path: Path):
        git_dir = tmp_path / ".git" / "hooks"
        git_dir.mkdir(parents=True)
        (git_dir / "pre-commit").write_text("#!/bin/sh\n# old\n", encoding="utf-8")
        result = runner.invoke(app, ["init-hooks", str(tmp_path), "--force"])
        assert result.exit_code == 0
        content = (git_dir / "pre-commit").read_text(encoding="utf-8")
        assert "tslayer audit" in content
