"""Memory editor — left entry list + right editor with save/delete/add."""

from nicegui import ui

from infodeck.data.memory_files import (
    MemoryEntry,
    MemoryFile,
    add_entry,
    delete_entry,
    load_all_memory_files,
    parse_memory_file,
    update_entry,
    write_memory_file,
)
from infodeck.state.app_state import InfodeckUiState


def build_memory_panel(
    *,
    state: InfodeckUiState,
    config,  # InfodeckConfig
) -> None:
    """Build the memory list panel with sections for each source."""

    with ui.column().classes("w-full h-full gap-2 p-2"):
        ui.label("Memory").classes("text-sm font-semibold text-slate-700 mb-2")

        # Load memory files
        if not state.memory_entries:
            _load_memory(state, config)

        # --- Your Profile (USER.md) ---
        with ui.expansion("Your Profile", value=True).classes("w-full"):
            user_list = ui.column().classes("w-full gap-0")

        # --- Project Knowledge (MEMORY.md) ---
        with ui.expansion("Project Knowledge", value=True).classes("w-full"):
            mem_list = ui.column().classes("w-full gap-0")

        # --- Agent Persona (SOUL.md, read-only) ---
        with ui.expansion("Agent Persona", value=False).classes("w-full"):
            soul_list = ui.column().classes("w-full gap-0")

        # Add button
        with ui.row().classes("w-full gap-2 mt-2"):
            ui.button(
                "Add Entry",
                icon="add",
                on_click=lambda: _add_new_entry(state),
            ).props("size=sm outline").classes("w-full")

    state._mem_user_container = user_list
    state._mem_memory_container = mem_list
    state._mem_soul_container = soul_list

    _render_all_lists(state)


def _load_memory(state: InfodeckUiState, config) -> None:
    """Load memory files into state."""
    hermes_dir = config.memory.hermes_dir
    try:
        files = load_all_memory_files(hermes_dir)
        state._memory_files = files
        state._memory_selected = None
        state._memory_dirty = False
    except Exception as e:
        state.last_error = str(e)
        state._memory_files = {}


def _render_all_lists(state: InfodeckUiState) -> None:
    """Render all three entry lists."""
    files = getattr(state, "_memory_files", {})
    if not files:
        return

    _render_entry_list(state, files.get("user"), "Your Profile", "_mem_user_container")
    _render_entry_list(state, files.get("memory"), "Project Knowledge", "_mem_memory_container")
    _render_entry_list(state, files.get("soul"), "Agent Persona", "_mem_soul_container")


def _render_entry_list(
    state: InfodeckUiState,
    memfile: MemoryFile | None,
    label: str,
    container_attr: str,
) -> None:
    """Render entries from one memory file into its container."""
    container = getattr(state, container_attr, None)
    if container is None:
        return
    container.clear()

    if not memfile or not memfile.entries:
        with container:
            ui.label(f"No {label.lower()} entries yet").classes(
                "text-xs text-slate-400 p-2"
            )
        return

    with container:
        for entry in memfile.entries:
            is_selected = (
                getattr(state, "_memory_selected", None) is not None
                and state._memory_selected[0] == memfile.source
                and state._memory_selected[1] == entry.index
            )

            with ui.row().classes(
                "w-full items-start gap-2 p-2 cursor-pointer hover:bg-slate-100 rounded"
                + (" bg-blue-50" if is_selected else "")
            ).on("click", lambda _, mf=memfile, e=entry: _select_entry(state, mf, e)):
                ui.label(entry.preview).classes(
                    "text-xs text-slate-700 leading-snug"
                )


def _select_entry(state: InfodeckUiState, memfile: MemoryFile, entry: MemoryEntry) -> None:
    """Select an entry and show it in the editor."""
    state._memory_selected = (memfile.source, entry.index)
    state._memory_dirty = False
    _render_all_lists(state)
    _render_editor(state, memfile, entry)


def _render_editor(
    state: InfodeckUiState,
    memfile: MemoryFile | None,
    entry: MemoryEntry | None,
) -> None:
    """Render the right-side editor for the selected entry."""
    container = getattr(state, "_mem_editor_container", None)
    if container is None:
        return
    container.clear()

    if entry is None:
        with container:
            ui.label("Select an entry to view or edit").classes("text-slate-400 p-4")
        return

    is_soul = memfile.source == "soul"
    source_label = {
        "memory": "Project Knowledge",
        "user": "Your Profile",
        "soul": "Agent Persona (read-only)",
    }.get(memfile.source, memfile.source)

    with container:
        ui.label(source_label).classes("text-xs font-semibold text-slate-500 mb-1")

        if is_soul:
            # Read-only display for SOUL.md
            ui.label(entry.content).classes(
                "text-sm text-slate-700 whitespace-pre-wrap p-3 bg-slate-50 rounded"
            )
            return

        # Editable textarea
        textarea = ui.textarea(
            value=entry.content,
            on_change=lambda e: _mark_dirty(state),
        ).classes("w-full").style("min-height: 300px; font-size: 13px;")

        with ui.row().classes("w-full gap-2 mt-2"):
            ui.button(
                "Save",
                icon="save",
                on_click=lambda: _save_entry(state, memfile, entry, textarea),
            ).props("size=sm")

            ui.button(
                "Delete",
                icon="delete",
                color="red",
                on_click=lambda: _confirm_delete(state, memfile, entry),
            ).props("size=sm outline")

            ui.button(
                "Cancel",
                icon="close",
                on_click=lambda: _cancel_edit(state, memfile, entry),
            ).props("size=sm flat")

            if state._memory_dirty:
                ui.label("Unsaved changes").classes(
                    "text-xs text-amber-600 self-center"
                )

        state._mem_textarea = textarea


def _mark_dirty(state: InfodeckUiState) -> None:
    """Mark the current editor as having unsaved changes."""
    state._memory_dirty = True


def _save_entry(
    state: InfodeckUiState,
    memfile: MemoryFile,
    entry: MemoryEntry,
    textarea,
) -> None:
    """Save the current entry content back to disk."""
    new_content = textarea.value
    update_entry(memfile, entry.index, new_content)

    config = getattr(state, "_config", None)
    backup = config.memory.backup_on_save if config else True

    error = write_memory_file(memfile, backup=backup)
    if error:
        ui.notify(f"Save failed: {error}", type="negative", position="top")
        return

    state._memory_dirty = False
    state.status = f"Saved {memfile.source} entry #{entry.index}"
    _render_all_lists(state)
    _render_editor(state, memfile, entry)
    ui.notify("Saved successfully", type="positive", position="top")


def _confirm_delete(
    state: InfodeckUiState,
    memfile: MemoryFile,
    entry: MemoryEntry,
) -> None:
    """Show delete confirmation dialog."""
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Delete this entry?").classes("text-lg font-semibold")
        ui.label(entry.preview).classes("text-sm text-slate-600")
        with ui.row().classes("gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Delete",
                color="red",
                on_click=lambda: _do_delete(state, memfile, entry, dialog),
            )
    dialog.open()


def _do_delete(
    state: InfodeckUiState,
    memfile: MemoryFile,
    entry: MemoryEntry,
    dialog,
) -> None:
    """Execute the delete."""
    dialog.close()
    delete_entry(memfile, entry.index)

    config = getattr(state, "_config", None)
    backup = config.memory.backup_on_save if config else True

    error = write_memory_file(memfile, backup=backup)
    if error:
        ui.notify(f"Delete failed: {error}", type="negative", position="top")
        return

    state._memory_selected = None
    state._memory_dirty = False
    state.status = f"Deleted {memfile.source} entry #{entry.index}"
    _render_all_lists(state)
    _render_editor(state, memfile, None)
    ui.notify("Entry deleted", type="positive", position="top")


def _cancel_edit(
    state: InfodeckUiState,
    memfile: MemoryFile,
    entry: MemoryEntry,
) -> None:
    """Cancel editing and reload original content."""
    if state._memory_dirty:
        # Reload original content from the entry object
        state._memory_dirty = False
        _render_editor(state, memfile, entry)


def _add_new_entry(state: InfodeckUiState) -> None:
    """Add a new empty entry to MEMORY.md."""
    files = getattr(state, "_memory_files", {})
    memfile = files.get("memory")
    if not memfile:
        ui.notify("Memory file not loaded", type="negative", position="top")
        return

    idx = add_entry(memfile, "New entry — edit me")
    state._memory_selected = ("memory", idx)
    state._memory_dirty = True
    _render_all_lists(state)
    _render_editor(state, memfile, memfile.entries[idx])
