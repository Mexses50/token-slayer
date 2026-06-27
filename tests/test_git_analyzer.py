"""Tests for cca.git_analyzer — git history analysis."""
from __future__ import annotations

from pathlib import Path

import pytest

from cca.git_analyzer import get_hot_files, is_git_repo


class TestIsGitRepo:
    def test_returns_false_for_plain_dir(self, tmp_path: Path):
        assert is_git_repo(tmp_path) is False

    def test_returns_true_for_git_repo(self, git_project: Path):
        assert is_git_repo(git_project) is True

    def test_returns_false_for_nonexistent(self, tmp_path: Path):
        assert is_git_repo(tmp_path / "nonexistent") is False


class TestGetHotFiles:
    def test_returns_dict(self, git_project: Path):
        result = get_hot_files(git_project)
        assert isinstance(result, dict)

    def test_changed_files_appear(self, git_project: Path):
        result = get_hot_files(git_project)
        # utils.py and config.py were modified in the second commit
        paths = set(result.keys())
        assert any("utils" in p for p in paths)
        assert any("config" in p for p in paths)

    def test_values_are_positive_ints(self, git_project: Path):
        result = get_hot_files(git_project)
        assert all(isinstance(v, int) and v > 0 for v in result.values())

    def test_non_git_repo_returns_empty(self, tmp_path: Path):
        (tmp_path / "main.py").write_text("x = 1\n", encoding="utf-8")
        result = get_hot_files(tmp_path)
        assert result == {}

    def test_n_commits_limits_scan(self, git_project: Path):
        result_1 = get_hot_files(git_project, n_commits=1)
        result_50 = get_hot_files(git_project, n_commits=50)
        # Scanning 1 commit should find <= files than scanning 50
        assert len(result_1) <= len(result_50)

    def test_respects_py_filter(self, git_project: Path):
        # Add a non-Python file change
        readme = git_project / "README.md"
        readme.write_text("# Project\n", encoding="utf-8")
        from git import Repo
        repo = Repo(git_project)
        repo.index.add(["README.md"])
        repo.index.commit("docs: add readme")

        result = get_hot_files(git_project)
        # README.md should NOT appear (we only track .py files)
        assert not any(p.endswith(".md") for p in result.keys())
