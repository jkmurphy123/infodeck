"""Repo analysis: scan README/docs to generate summaries.

Reads the repo's documentation (README.md, AGENTS.md, DESIGN.md,
PROJECT_OUTLINE.md) via gh CLI and extracts a short summary.
Results are persisted to cache/repo_summaries.json.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUFFIXES = [".md", ".rst", ".txt"]
DOC_FILES = [
    "README",
    "AGENTS",
    "DESIGN",
    "PROJECT_DESIGN",
    "PROJECT_OUTLINE",
]


def load_summary_cache(cache_dir: Path) -> dict[str, dict[str, Any]]:
    """Load cached repo summaries, or empty dict if cache doesn't exist."""
    cache_path = cache_dir / "repo_summaries.json"
    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_summary_cache(cache_dir: Path, cache: dict[str, dict[str, Any]]) -> None:
    """Write repo summaries to the cache file."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "repo_summaries.json"
    # Write to temp then rename for atomicity
    tmp = cache_path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, sort_keys=True)
    tmp.rename(cache_path)


def load_analysis_state(cache_dir: Path) -> dict[str, Any]:
    """Load analysis state, or return defaults."""
    state_path = cache_dir / "repo_analysis_state.json"
    if state_path.exists():
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_full_analysis": None, "repos_analyzed": 0}


def save_analysis_state(cache_dir: Path, state: dict[str, Any]) -> None:
    """Write analysis state."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    state_path = cache_dir / "repo_analysis_state.json"
    tmp = state_path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp.rename(state_path)


def fetch_doc_content(owner: str, repo_name: str) -> str | None:
    """Fetch the first documentation file found in the repo via gh api.

    Tries known doc filenames. Returns content of the first one found,
    or None if none exist.
    """
    for filename in DOC_FILES:
        for suffix in SUFFIXES:
            path = f"{filename}{suffix}"
            content = _try_fetch_file(owner, repo_name, path)
            if content:
                return content
    return None


def _try_fetch_file(owner: str, repo_name: str, path: str) -> str | None:
    """Try to fetch a single file from a GitHub repo via gh api."""
    cmd = [
        "gh", "api",
        f"/repos/{owner}/{repo_name}/contents/{path}",
        "--jq", ".content",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    # Content is base64-encoded
    import base64
    try:
        return base64.b64decode(result.stdout.strip()).decode("utf-8", errors="replace")
    except Exception:
        return None


def generate_summary(doc_text: str, language: str | None = None) -> str:
    """Extract a short summary from documentation text.

    Strategy:
    1. Look for a project description line (first non-heading, non-empty text)
    2. Look for lines starting with "A " or "An " (common in project descriptions)
    3. Fall back to first paragraph of README
    """
    lines = doc_text.split("\n")
    paragraphs: list[str] = []
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        # Skip headings, badges, horizontal rules
        if not stripped or stripped.startswith("#") or stripped.startswith("---") or stripped.startswith("==="):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        # Skip badge/image links
        if stripped.startswith("[!") or stripped.startswith("<img") or stripped.startswith("!["):
            continue
        current.append(stripped)

    if current:
        paragraphs.append(" ".join(current))

    # Find the best description paragraph
    for p in paragraphs:
        if len(p) < 20:
            continue
        # Prefer lines that read like a description
        if p.startswith(("A ", "An ", "This ", "Infodeck ", "The ")):
            summary = p[:200].rsplit(".", 1)[0] + "."
            if len(summary) < 10:
                continue
            if language and language.lower() not in summary.lower():
                summary += f" ({language})"
            return summary

    # Fallback: first meaningful paragraph
    for p in paragraphs:
        if len(p) >= 30:
            summary = p[:200].rsplit(".", 1)[0] + "."
            if language and language.lower() not in summary.lower():
                summary += f" ({language})"
            return summary

    return f"A {language or 'code'} project." if language else "A code project."


def analyze_repo(
    owner: str,
    repo_name: str,
    description: str,
    language: str | None,
    force: bool = False,
) -> dict[str, Any] | None:
    """Analyze one repo and return a summary entry.

    If the repo already has a GitHub description and force=False,
    uses it as-is. Otherwise fetches docs and generates a summary.

    Returns a dict suitable for the summary cache, or None if
    analysis was skipped.
    """
    if description and not force:
        return {
            "summary": description,
            "language": language,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "source": "github_description",
        }

    doc_content = fetch_doc_content(owner, repo_name)
    if not doc_content:
        # No docs found, fall back to description
        fallback = description or f"A {language or 'code'} project."
        return {
            "summary": fallback,
            "language": language,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "source": "fallback",
        }

    summary = generate_summary(doc_content, language)
    return {
        "summary": summary,
        "language": language,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "source": "doc_analysis",
    }


def run_full_analysis(
    owner: str,
    repos: list[Any],  # list of RepoSummary-like objects
    cache_dir: Path,
) -> dict[str, dict[str, Any]]:
    """Run analysis on all repos that need it.

    Repos with existing GitHub descriptions are used as-is.
    Repos with empty descriptions get doc analysis.

    Returns the updated cache dict.
    """
    cache = load_summary_cache(cache_dir)
    analyzed_count = 0

    for repo in repos:
        name = repo.name if hasattr(repo, "name") else repo["name"]
        if name in cache and cache[name].get("source") == "github_description":
            continue  # already has a good description from GitHub

        entry = analyze_repo(
            owner, name,
            description=repo.description if hasattr(repo, "description") else repo.get("description", ""),
            language=repo.language if hasattr(repo, "language") else repo.get("language"),
            force=(name in cache),  # re-analyze only if previously analyzed (update)
        )
        if entry:
            cache[name] = entry
            analyzed_count += 1

    # Update state
    state = load_analysis_state(cache_dir)
    state["last_full_analysis"] = datetime.now(timezone.utc).isoformat()
    state["repos_analyzed"] = analyzed_count
    save_analysis_state(cache_dir, state)
    save_summary_cache(cache_dir, cache)

    return cache


def run_incremental_analysis(
    owner: str,
    repos: list[Any],
    cache_dir: Path,
) -> tuple[dict[str, dict[str, Any]], int]:
    """Run analysis only on repos created since last analysis.

    Returns (updated_cache, new_repos_analyzed).
    """
    state = load_analysis_state(cache_dir)
    last_analysis = state.get("last_full_analysis")
    cache = load_summary_cache(cache_dir)

    new_count = 0
    for repo in repos:
        name = repo.name if hasattr(repo, "name") else repo["name"]
        created = repo.created_at if hasattr(repo, "created_at") else repo.get("created_at", "")

        # Skip if already cached
        if name in cache:
            continue

        # Only analyze repos created after last analysis
        if last_analysis and created and created <= last_analysis:
            continue

        entry = analyze_repo(
            owner, name,
            description=repo.description if hasattr(repo, "description") else repo.get("description", ""),
            language=repo.language if hasattr(repo, "language") else repo.get("language"),
        )
        if entry:
            cache[name] = entry
            new_count += 1

    if new_count > 0:
        state["last_full_analysis"] = datetime.now(timezone.utc).isoformat()
        state["repos_analyzed"] = new_count
        save_analysis_state(cache_dir, state)
        save_summary_cache(cache_dir, cache)

    return cache, new_count
