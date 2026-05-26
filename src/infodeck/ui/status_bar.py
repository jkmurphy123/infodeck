"""Status bar for the infodeck app."""

from nicegui import ui

from infodeck.state.app_state import AppMode, InfodeckUiState


def build_status_bar(*, state: InfodeckUiState) -> None:
    """Render the bottom status bar."""

    with ui.row().classes(
        "w-full items-center gap-4 bg-white px-4 py-2 border-t text-xs text-slate-600"
    ):
        ui.label(f"Status: {state.status}")

        if state.active_mode == AppMode.GITHUB:
            ui.label(f"Repos: {state.github_total_count}")
            if state.github_analysis_count:
                ui.label(f"With summaries: {state.github_analysis_count}")

        ui.space()

        if state.last_error:
            ui.label(state.last_error).classes("text-red-700")
