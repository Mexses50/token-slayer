"""Analyze git history to find hot (frequently changed) files."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

try:
    from git import Repo, InvalidGitRepositoryError
    _HAS_GIT = True
except ImportError:
    _HAS_GIT = False


def is_git_repo(path: Path) -> bool:
    if not _HAS_GIT:
        return False
    try:
        Repo(path, search_parent_directories=True)
        return True
    except Exception:
        return False


def get_hot_files(repo_path: Path, n_commits: int = 50) -> dict[str, int]:
    """Return {relative_path: change_count} for the last N commits."""
    if not _HAS_GIT:
        return {}
    try:
        repo = Repo(repo_path, search_parent_directories=True)
    except Exception:
        return {}

    counter: Counter[str] = Counter()
    for commit in list(repo.iter_commits(max_count=n_commits)):
        if not commit.parents:
            continue
        diff = commit.parents[0].diff(commit)
        for change in diff:
            if change.a_path and change.a_path.endswith(".py"):
                counter[change.a_path] += 1
            if change.b_path and change.b_path != change.a_path and change.b_path.endswith(".py"):
                counter[change.b_path] += 1

    return dict(counter.most_common(20))
