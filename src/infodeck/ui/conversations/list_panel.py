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

    # Store sessions_dir for message loading
    state._conv_sessions_dir = config.conversations.sessions_dir


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
            _render_session_card(state, session)


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
            _render_session_card(state, session)


def _render_session_card(state: InfodeckUiState, session) -> None:
    """Render a session card that opens a dialog with the full conversation."""
    subjects_str = ", ".join(
        session_data._subject_display_name(s) for s in session.subjects
    )

    with ui.card().classes(
        "w-full p-3 gap-1 cursor-pointer hover:bg-slate-50"
    ).on("click", lambda _ev, s=session: _open_conversation_dialog(state, s)):
        ui.label(
            f"{session.datetime} — {session.first_message[:80]}"
        ).classes("text-sm font-medium text-slate-800")
        ui.label(
            f"{session.model} · {session.message_count} msgs · {subjects_str}"
        ).classes("text-xs text-slate-400")
        ui.label("Click to view full conversation").classes("text-xs text-slate-300")


def _open_conversation_dialog(state: InfodeckUiState, session) -> None:
    """Open a dialog showing the full conversation."""
    sessions_dir = getattr(state, "_conv_sessions_dir", "")

    # Load messages
    try:
        messages = session_data.load_conversation(sessions_dir, session.filename)
    except Exception:
        messages = []

    # Build HTML
    if not messages:
        html_content = "<p>No messages available.</p>"
    else:
        parts = [
            '<div style="max-height:70vh; overflow-y:auto; font-size:13px; '
            'line-height:1.6; padding:8px;">'
        ]
        for msg in messages:
            text = (msg.content
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

            if msg.is_reasoning:
                parts.append(
                    f'<div style="color:#94a3b8; font-style:italic; padding:2px 4px;">'
                    f'💭 {text}</div>'
                )
            elif msg.role == "user":
                parts.append(
                    f'<div style="color:#1d4ed8; background:#eff6ff; padding:4px 6px; '
                    f'border-radius:3px; margin:2px 0;">👤 {text}</div>'
                )
            elif msg.role == "tool":
                parts.append(
                    f'<div style="color:#64748b; font-family:monospace; font-size:11px; '
                    f'padding:1px 4px;">{text}</div>'
                )
            elif msg.role == "assistant":
                parts.append(
                    f'<div style="color:#334155; background:#f8fafc; padding:4px 6px; '
                    f'border-radius:3px; margin:2px 0;">{text}</div>'
                )
        parts.append('</div>')
        html_content = "".join(parts)

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-4xl"):
        ui.label(
            f"{session.datetime} — {session.model} · {session.message_count} msgs"
        ).classes("text-sm font-semibold text-slate-900")
        ui.label(session.first_message[:200]).classes("text-xs text-slate-500 mb-2")
        ui.separator()
        ui.html(html_content)
        ui.button("Close", on_click=dialog.close).props("flat")

    dialog.open()


def _load_conversation_html(sessions_dir: str, filename: str) -> None:
    """Load conversation and render as a single scrollable HTML block."""
    try:
        messages = session_data.load_conversation(sessions_dir, filename)
    except Exception:
        ui.label("Could not load conversation.").classes("text-xs text-red-500 p-2")
        return

    if not messages:
        ui.label("No messages in this session.").classes("text-xs text-slate-400 p-2")
        return

    # Build formatted HTML as a single string
    html_parts = [
        '<div style="max-height:500px; overflow-y:auto; font-size:12px; '
        'line-height:1.5; border:1px solid #e2e8f0; border-radius:4px; padding:4px;">'
    ]
    for msg in messages:
        text = (msg.content
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;"))

        if msg.is_reasoning:
            html_parts.append(
                f'<div style="color:#94a3b8; font-style:italic; padding:2px 4px;">'
                f'💭 {text}</div>'
            )
        elif msg.role == "user":
            html_parts.append(
                f'<div style="color:#1d4ed8; background:#eff6ff; padding:2px 4px; '
                f'border-radius:2px; margin:1px 0;">👤 {text}</div>'
            )
        elif msg.role == "tool":
            html_parts.append(
                f'<div style="color:#64748b; font-family:monospace; font-size:11px; '
                f'padding:1px 4px;">{text}</div>'
            )
        elif msg.role == "assistant":
            html_parts.append(
                f'<div style="color:#334155; background:#f8fafc; padding:2px 4px; '
                f'border-radius:2px; margin:1px 0;">{text}</div>'
            )
    html_parts.append('</div>')

    ui.html("".join(html_parts))


def _format_date(date_str: str) -> str:
    """Format ISO date to readable form."""
    try:
        dt = __import__("datetime").datetime.fromisoformat(date_str)
        return dt.strftime("%A, %B %d, %Y")
    except (ValueError, ImportError):
        return date_str
