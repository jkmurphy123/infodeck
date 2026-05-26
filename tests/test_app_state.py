"""Tests for InfodeckUiState and AppMode."""

from infodeck.state.app_state import AppMode, InfodeckUiState, RepoSummary


class TestAppMode:
    def test_enum_values(self):
        assert AppMode.GITHUB == "github"
        assert AppMode.CONVERSATIONS == "conversations"
        assert AppMode.MEMORY == "memory"

    def test_mode_selection(self):
        assert AppMode("github") == AppMode.GITHUB
        assert AppMode("conversations") == AppMode.CONVERSATIONS


class TestInfodeckUiState:
    def test_defaults(self):
        state = InfodeckUiState()
        assert state.active_mode == AppMode.GITHUB
        assert state.status == "ready"
        assert state.github_repos == []
        assert state.github_selected_index is None
        assert state.github_analysis_count == 0
        assert state.last_error is None

    def test_github_repos_list(self):
        state = InfodeckUiState()
        repo = RepoSummary(
            name="test-repo",
            description="A test repo",
            url="https://github.com/user/test-repo",
            language="Python",
        )
        state.github_repos = [repo]
        state.github_total_count = 1
        assert len(state.github_repos) == 1
        assert state.github_repos[0].name == "test-repo"
        assert state.github_repos[0].has_analysis is False

    def test_repo_with_analysis(self):
        repo = RepoSummary(
            name="analyzed-repo",
            description="",
            summary="A data visualization kiosk",
            language="Python",
            has_analysis=True,
        )
        assert repo.has_analysis is True
        assert repo.summary == "A data visualization kiosk"
        assert repo.description == ""

    def test_repo_summary_fields(self):
        repo = RepoSummary(
            name="test",
            description="desc",
            summary="sum",
            url="http://x.com",
            created_at="2026-01-01",
            updated_at="2026-05-01",
            language="Rust",
            local_path="/tmp/test",
            has_analysis=True,
        )
        assert repo.name == "test"
        assert repo.url == "http://x.com"
        assert repo.created_at == "2026-01-01"
        assert repo.language == "Rust"
        assert repo.local_path == "/tmp/test"
