"""Top bar with mode tab buttons — GitHub / Conversations / Memory."""

from nicegui import ui

from infodeck.state.app_state import AppMode, InfodeckUiState


def build_top_bar(*, state: InfodeckUiState) -> None:
    """Render the top bar with tab-style mode buttons."""

    with ui.row().classes(
        "w-full items-center gap-2 bg-white px-4 py-3 border-b"
    ):
        ui.label("Infodeck").classes("text-lg font-semibold text-slate-900 mr-4")

        modes = [
            (AppMode.GITHUB, "GitHub Repos", "code"),
            (AppMode.CONVERSATIONS, "Conversations", "chat"),
            (AppMode.MEMORY, "Memory", "psychology"),
        ]

        btn_refs: dict[AppMode, ui.button] = {}
        for mode, label, icon in modes:
            btn = ui.button(
                label,
                icon=icon,
                on_click=lambda _, m=mode: _switch_mode(state, m, btn_refs),
            ).props(
                f'color="primary"' if state.active_mode == mode else "flat"
            )
            btn_refs[mode] = btn

        ui.space()

        # Version label
        ui.label("v0.1.0").classes("text-xs text-slate-400")

    state._mode_buttons = btn_refs


def _switch_mode(
    state: InfodeckUiState,
    mode: AppMode,
    btn_refs: dict[AppMode, ui.button],
) -> None:
    state.active_mode = mode
    state.status = "ready"
    state.last_error = None

    # Update button styling
    for m, btn in btn_refs.items():
        btn.props("color=primary" if m == mode else "flat")

    # Toggle panel visibility
    _toggle_panels(state, mode)


def _toggle_panels(state: InfodeckUiState, mode: AppMode) -> None:
    """Show/hide the mode-specific panels on both sides."""
    # Left panels
    left_panels = {
        AppMode.GITHUB: getattr(state, "_github_list_panel", None),
        AppMode.CONVERSATIONS: getattr(state, "_conv_list_panel", None),
        AppMode.MEMORY: getattr(state, "_mem_list_panel", None),
    }
    for m, panel in left_panels.items():
        if panel is not None:
            panel.set_visibility(m == mode)

    # Right panels
    right_panels = {
        AppMode.GITHUB: getattr(state, "_github_detail_container", None),
        AppMode.CONVERSATIONS: getattr(state, "_conv_detail_container", None),
        AppMode.MEMORY: getattr(state, "_mem_detail_container", None),
    }
    for m, panel in right_panels.items():
        if panel is not None:
            panel.set_visibility(m == mode)
