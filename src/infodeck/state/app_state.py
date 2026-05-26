"""Local UI state for the infodeck app."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AppMode(str, Enum):
    GITHUB = "github"
    CONVERSATIONS = "conversations"
    MEMORY = "memory"


@dataclass
class RepoSummary:
    """A GitHub repo with optional analysis summary."""

    name: str
    description: str          # from GitHub, may be empty
    summary: str | None = None  # from cache/repo_summaries.json
    url: str = ""
    created_at: str = ""       # ISO timestamp
    updated_at: str = ""       # ISO timestamp
    language: str | None = None
    local_path: str | None = None
    has_analysis: bool = False


@dataclass
class InfodeckUiState:
    """Mutable state for one infodeck UI session."""

    # Mode
    active_mode: AppMode = AppMode.GITHUB

    # GitHub mode
    github_repos: list[RepoSummary] = field(default_factory=list)
    github_selected_index: int | None = None
    github_analysis_count: int = 0
    github_total_count: int = 0
    github_is_refreshing: bool = False

    # Conversations mode  (M2)
    conversation_subjects: list = field(default_factory=list)
    conversation_daily_logs: list = field(default_factory=list)
    conversation_selected_id: str | None = None

    # Memory mode (M3)
    memory_entries: list = field(default_factory=list)
    memory_selected_index: int | None = None
    memory_dirty: bool = False

    # General
    status: str = "ready"
    last_error: str | None = None

    # Internal references (set by UI builders, not serialized)
    _mode_buttons: dict = field(default_factory=dict, repr=False, compare=False)
    _github_list_container: object = field(default=None, repr=False, compare=False)
    _github_detail_container: object = field(default=None, repr=False, compare=False)
    _github_refresh_btn: object = field(default=None, repr=False, compare=False)
    _github_panel: object = field(default=None, repr=False, compare=False)
    _conversations_panel: object = field(default=None, repr=False, compare=False)
    _memory_panel: object = field(default=None, repr=False, compare=False)
    _conv_subjects_container: object = field(default=None, repr=False, compare=False)
    _conv_logs_container: object = field(default=None, repr=False, compare=False)
    _conv_detail_container: object = field(default=None, repr=False, compare=False)
    _github_list_panel: object = field(default=None, repr=False, compare=False)
    _conv_list_panel: object = field(default=None, repr=False, compare=False)
    _mem_list_panel: object = field(default=None, repr=False, compare=False)
    _mem_detail_container: object = field(default=None, repr=False, compare=False)
