"""Top-level NiceGUI shell composition for infodeck."""

from nicegui import ui

from infodeck.config import InfodeckConfig
from infodeck.state.app_state import AppMode, InfodeckUiState
from infodeck.ui.conversations.list_panel import (
    build_conversations_panel,
    _render_subjects,
    _render_daily_logs,
)
from infodeck.ui.github_repos.list_panel import (
    build_repo_list_panel,
)
from infodeck.ui.status_bar import build_status_bar
from infodeck.ui.top_bar import build_top_bar


def build_shell(
    *,
    config: InfodeckConfig,
    state: InfodeckUiState,
) -> None:
    """Build the infodeck app shell with 3-zone layout."""

    ui.page_title(config.ui.title)
    ui.add_head_html("""
        <style>
          body { margin: 0; background: #f8fafc; }
          .id-shell { max-width: 1200px; margin: 0 auto; }
        </style>
    """)

    with ui.column().classes("id-shell w-full h-screen no-wrap gap-0"):
        build_top_bar(state=state)

        with ui.row().classes("w-full grow gap-0 overflow-hidden"):
            # --- Left: list panel (mode-switched) ---
            with ui.column().classes(
                "w-80 bg-white border-r h-full"
            ).style("overflow-y: auto"):

                # GitHub repo list
                repo_list = ui.column().classes("w-full")
                with repo_list:
                    build_repo_list_panel(state=state, config=config)

                # Conversations list
                conv_list = ui.column().classes("w-full")
                with conv_list:
                    build_conversations_panel(state=state, config=config)

                # Memory list (M3 placeholder)
                mem_list = ui.column().classes("w-full")
                with mem_list:
                    ui.label("Memory").classes("text-sm text-slate-400 p-4")
                    ui.label("Coming in Milestone 3").classes("text-xs text-slate-400 p-4")

                conv_list.set_visibility(False)
                mem_list.set_visibility(False)

                state._github_list_panel = repo_list
                state._conv_list_panel = conv_list
                state._mem_list_panel = mem_list

            # --- Right: detail panel (mode-switched) ---
            with ui.column().classes("grow p-4 gap-3 overflow-auto"):
                # GitHub detail
                gh_detail = ui.column().classes("w-full gap-3")
                with gh_detail:
                    from infodeck.ui.github_repos.list_panel import _render_detail
                    _render_detail(state)

                # Conversations detail
                conv_detail = ui.column().classes("w-full gap-3")
                with conv_detail:
                    ui.label("Select a subject or date").classes(
                        "text-sm text-slate-400 p-4"
                    )

                # Memory detail (M3 placeholder)
                mem_detail = ui.column().classes("w-full gap-3")
                with mem_detail:
                    ui.label("Memory Editor").classes("text-lg text-slate-400")
                    ui.label("Coming in Milestone 3").classes("text-sm text-slate-400")

                conv_detail.set_visibility(False)
                mem_detail.set_visibility(False)

                state._github_detail_container = gh_detail
                state._conv_detail_container = conv_detail
                state._mem_detail_container = mem_detail

        build_status_bar(state=state)
