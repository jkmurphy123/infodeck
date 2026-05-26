"""GitHub repo list via gh CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from infodeck.state.app_state import RepoSummary


def fetch_repos(owner: str, max_repos: int = 50) -> list[RepoSummary]:
    """Fetch all repos for an owner via `gh repo list`.

    Returns a list of RepoSummary objects with fields from the GitHub API.
    Does NOT include analysis summaries — those come from the cache layer.
    """
    cmd = [
        "gh", "repo", "list", owner,
        "--limit", str(max_repos),
        "--json", "name,description,createdAt,updatedAt,url,primaryLanguage",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        error_msg = result.stderr.strip() or "gh CLI failed"
        raise RuntimeError(f"gh repo list failed: {error_msg}")

    raw = json.loads(result.stdout)
    repos = []
    for item in raw:
        lang_data = item.get("primaryLanguage") or {}
        repos.append(RepoSummary(
            name=item.get("name", ""),
            description=(item.get("description") or "").strip(),
            url=item.get("url", ""),
            created_at=item.get("createdAt", ""),
            updated_at=item.get("updatedAt", ""),
            language=lang_data.get("name") if lang_data else None,
        ))
    return repos


def find_local_path(name: str, projects_root: str) -> str | None:
    """Check if a repo is cloned locally under projects_root.

    Tries exact match first, then common variations (underscore vs hyphen).
    """
    root = Path(projects_root).expanduser()
    if not root.is_dir():
        return None

    # Exact match
    candidate = root / name
    if candidate.is_dir() and (candidate / ".git").exists():
        return str(candidate)

    # Variations: swap hyphens/underscores
    variant = name.replace("-", "_")
    if variant != name:
        candidate = root / variant
        if candidate.is_dir() and (candidate / ".git").exists():
            return str(candidate)

    variant = name.replace("_", "-")
    if variant != name:
        candidate = root / variant
        if candidate.is_dir() and (candidate / ".git").exists():
            return str(candidate)

    return None


def check_gh_available() -> bool:
    """Return True if gh CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
