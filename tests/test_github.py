"""Tests for GitHub data layer."""

import pytest
from infodeck.data.github import find_local_path


class TestFindLocalPath:
    def test_exact_match(self, tmp_path):
        # Create a repo dir with .git subdir
        repo_dir = tmp_path / "my-repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        result = find_local_path("my-repo", str(tmp_path))
        assert result == str(repo_dir)

    def test_underscore_variant(self, tmp_path):
        repo_dir = tmp_path / "my_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        result = find_local_path("my-repo", str(tmp_path))
        assert result == str(repo_dir)

    def test_hyphen_variant(self, tmp_path):
        repo_dir = tmp_path / "my-repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()

        result = find_local_path("my_repo", str(tmp_path))
        assert result == str(repo_dir)

    def test_not_found(self, tmp_path):
        result = find_local_path("nonexistent", str(tmp_path))
        assert result is None

    def test_dir_exists_but_no_git(self, tmp_path):
        repo_dir = tmp_path / "my-repo"
        repo_dir.mkdir()

        result = find_local_path("my-repo", str(tmp_path))
        assert result is None

    def test_root_not_a_dir(self):
        result = find_local_path("anything", "/nonexistent/path")
        assert result is None
