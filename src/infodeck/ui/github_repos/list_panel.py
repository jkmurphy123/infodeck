"""GitHub repo list panel (left side) with Refresh button."""

import asyncio

from nicegui import ui

from infodeck.state.app_state import AppMode, InfodeckUiState, RepoSummary


def build_repo_list_panel(
    *,
    state: InfodeckUiState,
    config,  # InfodeckConfig
) -> None:
    """Build the left-side repo list with refresh button."""

    with ui.column().classes("w-full h-full gap-2 p-2"):

        # Refresh button at top
        with ui.row().classes("w-full items-center gap-2"):
            ui.label("Repositories").classes("text-sm font-semibold text-slate-700")
            ui.space()
            refresh_btn = ui.button(
                "Refresh",
                icon="refresh",
                on_click=lambda: _on_refresh(state, config, refresh_btn),
            ).props("size=sm outline")

        ui.separator()

        # Repo list container
        list_container = ui.column().classes("w-full gap-0")

    state._github_list_container = list_container
    state._github_refresh_btn = refresh_btn


def _on_refresh(state: InfodeckUiState, config, btn: ui.button) -> None:
    """Handle refresh button click — load repos and trigger analysis."""
    btn.props("loading")
    btn.update()

    # Run in background
    async def _do_refresh():
        try:
            state.github_is_refreshing = True
            state.status = "fetching repos..."

            from infodeck.data.github import fetch_repos, find_local_path, check_gh_available

            if not check_gh_available():
                state.last_error = "gh CLI not available or not authenticated"
                state.status = "error"
                return

            repos = fetch_repos(config.github.owner, config.github.max_repos)

            # Load analysis cache
            from infodeck.data.repo_analysis import (
                load_summary_cache,
                run_full_analysis,
                save_summary_cache,
            )

            cache = load_summary_cache(config.cache_dir)

            # Merge cache summaries into repos
            for repo in repos:
                if repo.name in cache:
                    repo.summary = cache[repo.name]["summary"]
                    repo.has_analysis = True
                else:
                    repo.summary = repo.description or None
                    repo.has_analysis = bool(repo.description)
                repo.language = cache.get(repo.name, {}).get("language") or repo.language

            # Find local paths
            for repo in repos:
                repo.local_path = find_local_path(
                    repo.name, config.github.local_projects_root
                )

            # Check if first-time — if cache is empty, run full analysis
            if not cache:
                state.status = "analyzing repos (first run)..."
                await asyncio.to_thread(
                    run_full_analysis,
                    config.github.owner, repos, config.cache_dir,
                )
                # Reload cache after analysis
                cache = load_summary_cache(config.cache_dir)
                for repo in repos:
                    if repo.name in cache:
                        repo.summary = cache[repo.name]["summary"]
                        repo.has_analysis = True

            state.github_repos = repos
            state.github_total_count = len(repos)
            state.github_analysis_count = sum(1 for r in repos if r.has_analysis)
            state.github_selected_index = 0 if repos else None
            state.status = "ready"

            # Re-render the list
            _render_repo_list(state)

        except Exception as exc:
            state.last_error = str(exc)
            state.status = "error"
        finally:
            state.github_is_refreshing = False
            btn.props(remove="loading")
            btn.update()

    ui.timer(0.05, lambda: None, once=True)  # allow UI update before async
    asyncio.ensure_future(_do_refresh())


def _render_repo_list(state: InfodeckUiState) -> None:
    """Render the repo list from current state."""
    container = getattr(state, "_github_list_container", None)
    if container is None:
        return

    container.clear()

    with container:
        repos = state.github_repos
        if not repos:
            ui.label("No repos found. Click Refresh to load.").classes(
                "text-sm text-slate-500 p-4"
            )
            return

        for i, repo in enumerate(repos):
            with ui.row().classes(
                "w-full items-center gap-2 p-2 cursor-pointer hover:bg-slate-100 rounded"
                + (" bg-blue-50" if i == state.github_selected_index else "")
            ).on("click", lambda _, idx=i: _select_repo(state, idx)):

                # Language badge dot
                lang_color = _lang_color(repo.language)
                ui.element("div").classes(
                    f"w-2 h-2 rounded-full {lang_color} flex-shrink-0"
                )

                with ui.column().classes("gap-0 min-w-0 flex-1"):
                    ui.label(repo.name).classes(
                        "text-sm font-medium text-slate-800 truncate"
                    )
                    summary_text = repo.summary or repo.description or ""
                    if summary_text:
                        ui.label(summary_text[:60]).classes(
                            "text-xs text-slate-500 truncate"
                        )

                if repo.has_analysis:
                    ui.element("div").classes(
                        "w-1.5 h-1.5 rounded-full bg-green-400 flex-shrink-0"
                    )


def _select_repo(state: InfodeckUiState, index: int) -> None:
    """Handle repo selection — update state and detail panel."""
    state.github_selected_index = index
    # Re-render list to update highlight
    _render_repo_list(state)
    # Update detail panel
    _render_detail(state)


def _render_detail(state: InfodeckUiState) -> None:
    """Render details for the selected repo in the right panel."""
    container = getattr(state, "_github_detail_container", None)
    if container is None:
        return

    container.clear()

    index = state.github_selected_index
    if index is None or index >= len(state.github_repos):
        with container:
            ui.label("Select a repository").classes("text-slate-400 p-4")
        return

    repo = state.github_repos[index]

    with container:
        # Header
        ui.label(repo.name).classes("text-lg font-semibold text-slate-900")

        if repo.language:
            ui.label(repo.language).classes(
                "text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded inline-block"
            )

        ui.separator()

        # Summary
        summary = repo.summary or repo.description
        if summary:
            ui.label("Summary").classes("text-xs font-semibold text-slate-700 mt-2")
            ui.label(summary).classes("text-sm text-slate-600")

        # Metadata
        ui.label("Details").classes("text-xs font-semibold text-slate-700 mt-4")

        if repo.url:
            ui.link(repo.url, repo.url, new_tab=True).classes("text-xs text-blue-600")

        details = []
        if repo.created_at:
            details.append(f"Created: {repo.created_at[:10]}")
        if repo.updated_at:
            details.append(f"Updated: {repo.updated_at[:10]}")
        if repo.local_path:
            details.append(f"Local: {repo.local_path}")

        for detail in details:
            ui.label(detail).classes("text-xs text-slate-500")

        if not repo.has_analysis and not repo.description:
            ui.label("No description or analysis available.").classes(
                "text-xs text-amber-600 mt-2"
            )


_LANG_COLORS: dict[str, str] = {
    "Python": "bg-blue-500",
    "JavaScript": "bg-yellow-400",
    "TypeScript": "bg-blue-400",
    "Rust": "bg-orange-600",
    "Go": "bg-cyan-400",
    "Java": "bg-red-500",
    "C": "bg-gray-500",
    "C++": "bg-pink-500",
    "HTML": "bg-orange-500",
    "CSS": "bg-purple-400",
}


def _lang_color(language: str | None) -> str:
    if not language:
        return "bg-gray-300"
    return _LANG_COLORS.get(language, "bg-gray-400")
