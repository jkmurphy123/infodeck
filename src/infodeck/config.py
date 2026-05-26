"""Frontend configuration models and loading helpers."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class UiConfig(BaseModel):
    """UI-level settings."""

    title: str = "Infodeck"
    default_mode: str = "github"


class GitHubConfig(BaseModel):
    """GitHub repo list settings."""

    owner: str = "jkmurphy123"
    cache_ttl_minutes: int = Field(default=5, ge=1)
    local_projects_root: str = "/home/ubuntu/ai_projects"
    max_repos: int = Field(default=50, ge=1)


class MemoryConfig(BaseModel):
    """Memory file settings."""

    hermes_dir: str = "/home/ubuntu/.hermes"
    backup_on_save: bool = True


class ConversationsConfig(BaseModel):
    """Conversation indexer settings."""

    sessions_dir: str = "/home/ubuntu/.hermes/sessions"


class InfodeckConfig(BaseModel):
    """Top-level infodeck configuration."""

    ui: UiConfig = Field(default_factory=UiConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    conversations: ConversationsConfig = Field(default_factory=ConversationsConfig)
    source_path: Path | None = None

    @property
    def project_root(self) -> Path:
        """The directory containing this config file, or cwd."""
        if self.source_path is not None:
            return self.source_path.parent.resolve()
        return Path.cwd()

    @property
    def cache_dir(self) -> Path:
        return self.project_root / "cache"


def load_config(path: str | Path | None = None) -> InfodeckConfig:
    """Load config from YAML, falling back to defaults."""
    config_path = _resolve_config_path(path)
    raw: dict[str, Any] = {}
    if config_path is not None:
        with config_path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Config must be a mapping: {config_path}")
        raw = loaded

    config = InfodeckConfig.model_validate(raw)
    config.source_path = config_path
    return config


def _resolve_config_path(path: str | Path | None) -> Path | None:
    if path is not None:
        resolved = Path(path).expanduser().resolve()
        return resolved if resolved.exists() else None
    default_path = Path("frontend.yaml")
    return default_path.resolve() if default_path.exists() else None
