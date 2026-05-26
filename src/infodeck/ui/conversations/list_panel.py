"""Conversations list panel — subjects + daily logs."""

from nicegui import ui

from infodeck.data import sessions as session_data
from infodeck.state.app_state import InfodeckUiState


def build_conversations_panel(
    *,
    state: InfodeckUiState,
    config,  # InfodeckConfig
) -> None:
    """Build the conversations list panel with expandable sections."""

    with ui.column().classes("w-full h-full gap-2 p-2"):
        ui.label("Conversations").classes("text-sm font-semibold text-slate-700 mb-2")

        # Load sessions
        if not state.conversation_subjects:
            _load_data(state, config)

        # --- Subjects section ---
        subjects = state.conversation_subjects
        with ui.expansion("By Subject", value=True).classes("w-full"):
            subjects_list = ui.column().classes("w-full gap-0")

        state._conv_subjects_container = subjects_list
        _render_subjects(state, subjects)

        # --- Daily Logs section ---
        daily_logs = state.conversation_daily_logs
        with ui.expansion("Daily Logs", value=False).classes("w-full"):
            logs_list = ui.column().classes("w-full gap-0")

        state._conv_logs_container = logs_list
        _render_daily_logs(state, daily_logs)


def _load_data(state: InfodeckUiState, config) -> None:
    """Load session data from disk."""
    sessions_dir = config.conversations.sessions_dir
    try:
        sessions = session_data.index_sessions(sessions_dir)
        subjects = session_data.group_by_subject(sessions)
        daily_logs = session_data.group_by_date(sessions)

        state.conversation_subjects = subjects
        state.conversation_daily_logs = daily_logs
    except Exception:
        state.conversation_subjects = []
        state.conversation_daily_logs = []


def _render_subjects(state: InfodeckUiState, groups: list) -> None:
    """Render subject groups in the list."""
    container = getattr(state, "_conv_subjects_container", None)
    if container is None:
        return
    container.clear()

    with container:
        if not groups:
            ui.label("No sessions found").classes("text-sm text-slate-400 p-2")
            return

        for g in groups:
            with ui.row().classes(
                "w-full items-center gap-2 p-2 cursor-pointer hover:bg-slate-100 rounded"
            ).on("click", lambda _, grp=g: _select_subject(state, grp)):
                with ui.column().classes("gap-0 min-w-0 flex-1"):
                    ui.label(g.name).classes("text-sm font-medium text-slate-800")
                    ui.label(
                        f"{g.session_count} sessions · last {g.last_date}"
                    ).classes("text-xs text-slate-500")


def _render_daily_logs(state: InfodeckUiState, logs: list) -> None:
    """Render daily log entries."""
    container = getattr(state, "_conv_logs_container", None)
    if container is None:
        return
    container.clear()

    with container:
        if not logs:
            ui.label("No sessions found").classes("text-sm text-slate-400 p-2")
            return

        for log in logs:
            date_display = _format_date(log.date)
            with ui.row().classes(
                "w-full items-center gap-2 p-2 cursor-pointer hover:bg-slate-100 rounded"
            ).on("click", lambda _, l=log: _select_daily_log(state, l)):
                with ui.column().classes("gap-0 min-w-0 flex-1"):
                    ui.label(date_display).classes("text-sm font-medium text-slate-800")
                    ui.label(
                        f"{len(log.sessions)} session{'s' if len(log.sessions) != 1 else ''}"
                    ).classes("text-xs text-slate-500")


def _select_subject(state: InfodeckUiState, group) -> None:
    """Show sessions for a selected subject in the detail panel."""
    state.conversation_selected_id = group.key
    _render_subject_detail(state, group)


def _select_daily_log(state: InfodeckUiState, log) -> None:
    """Show sessions for a selected date in the detail panel."""
    state.conversation_selected_id = log.date
    _render_daily_detail(state, log)


def _render_subject_detail(state: InfodeckUiState, group) -> None:
    """Render subject details in the right panel."""
    container = getattr(state, "_conv_detail_container", None)
    if container is None:
        return
    container.clear()

    with container:
        ui.label(group.name).classes("text-lg font-semibold text-slate-900")
        ui.label(
            f"{group.session_count} sessions · last activity {group.last_date}"
        ).classes("text-xs text-slate-500")

        ui.separator()

        for session in sorted(group.sessions, key=lambda s: s.date, reverse=True):
            with ui.card().classes("w-full p-3 gap-1"):
                ui.label(session.datetime).classes("text-xs text-slate-500")
                ui.label(session.first_message[:120]).classes(
                    "text-sm text-slate-700"
                )
                ui.label(
                    f"{session.model} · {session.message_count} messages"
                ).classes("text-xs text-slate-400")


def _render_daily_detail(state: InfodeckUiState, log) -> None:
    """Render daily log details in the right panel."""
    container = getattr(state, "_conv_detail_container", None)
    if container is None:
        return
    container.clear()

    with container:
        ui.label(_format_date(log.date)).classes("text-lg font-semibold text-slate-900")
        ui.label(
            f"{len(log.sessions)} session{'s' if len(log.sessions) != 1 else ''}"
        ).classes("text-xs text-slate-500")

        ui.separator()

        for session in log.sessions:
            with ui.card().classes("w-full p-3 gap-1"):
                ui.label(session.datetime).classes("text-xs text-slate-500")
                ui.label(session.first_message[:120]).classes(
                    "text-sm text-slate-700"
                )
                subjects_str = ", ".join(
                    session_data._subject_display_name(s) for s in session.subjects
                )
                ui.label(
                    f"{session.model} · {session.message_count} msgs · {subjects_str}"
                ).classes("text-xs text-slate-400")


def _format_date(date_str: str) -> str:
    """Format ISO date to readable form."""
    try:
        dt = __import__("datetime").datetime.fromisoformat(date_str)
        return dt.strftime("%A, %B %d, %Y")
    except (ValueError, ImportError):
        return date_str
