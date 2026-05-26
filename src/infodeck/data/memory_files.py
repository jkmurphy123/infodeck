"""Memory file reader & writer — MEMORY.md / USER.md / SOUL.md.

Entries are delimited by '§' on its own line (\n§\n).
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    """One entry from a memory file."""

    source: str           # "memory", "user", or "soul"
    index: int            # position in file (0-based)
    content: str          # full paragraph text
    preview: str          # first ~80 chars for display


@dataclass
class MemoryFile:
    """Parsed memory file with entries and metadata."""

    path: Path
    source: str           # "memory", "user", or "soul"
    entries: list[MemoryEntry] = field(default_factory=list)
    mtime: float = 0.0


def parse_memory_file(filepath: Path, source: str) -> MemoryFile:
    """Parse a memory file, splitting entries by § delimiter."""
    result = MemoryFile(path=filepath, source=source)

    if not filepath.exists():
        return result

    result.mtime = filepath.stat().st_mtime

    try:
        text = filepath.read_text(encoding="utf-8")
    except OSError:
        return result

    # Split on standalone § lines
    raw_entries = text.split("\n§\n")

    for i, raw in enumerate(raw_entries):
        content = raw.strip()
        if not content:
            continue
        preview = content[:80].replace("\n", " ")
        if len(content) > 80:
            preview += "…"

        result.entries.append(MemoryEntry(
            source=source,
            index=i,
            content=content,
            preview=preview,
        ))

    return result


def write_memory_file(memfile: MemoryFile, backup: bool = True) -> str | None:
    """Write entries back to the memory file.

    Safety measures:
    - Checks mtime before writing (warns if file changed since read)
    - Creates .bak backup first
    - Writes to temp file then renames (atomic)

    Returns error message string on failure, None on success.
    """
    filepath = memfile.path

    # Check mtime — file may have changed since we read it
    if filepath.exists():
        current_mtime = filepath.stat().st_mtime
        if memfile.mtime > 0 and abs(current_mtime - memfile.mtime) > 1.0:
            return (
                f"File was modified since last read "
                f"(read at {memfile.mtime:.0f}, current {current_mtime:.0f}). "
                f"Reload to see latest version."
            )

    # Build file content
    parts = [entry.content for entry in memfile.entries]
    new_content = "\n§\n".join(parts) + "\n"

    # Backup
    if backup and filepath.exists():
        bak_path = filepath.with_suffix(filepath.suffix + ".bak")
        try:
            shutil.copy2(filepath, bak_path)
        except OSError as exc:
            return f"Backup failed: {exc}"

    # Atomic write: temp → rename
    tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        tmp_path.write_text(new_content, encoding="utf-8")
        tmp_path.replace(filepath)
        memfile.mtime = filepath.stat().st_mtime
    except OSError as exc:
        return f"Write failed: {exc}"

    return None


def add_entry(memfile: MemoryFile, content: str) -> int:
    """Append a new entry. Returns the index of the new entry."""
    idx = len(memfile.entries)
    memfile.entries.append(MemoryEntry(
        source=memfile.source,
        index=idx,
        content=content.strip(),
        preview=content.strip()[:80],
    ))
    return idx


def delete_entry(memfile: MemoryFile, index: int) -> bool:
    """Delete an entry by index. Returns True if successful."""
    if index < 0 or index >= len(memfile.entries):
        return False
    memfile.entries.pop(index)
    # Re-index
    for i, entry in enumerate(memfile.entries):
        entry.index = i
    return True


def update_entry(memfile: MemoryFile, index: int, content: str) -> bool:
    """Update an entry's content. Returns True if successful."""
    if index < 0 or index >= len(memfile.entries):
        return False
    content = content.strip()
    memfile.entries[index].content = content
    memfile.entries[index].preview = content[:80]
    return True


def load_all_memory_files(hermes_dir: str) -> dict[str, MemoryFile]:
    """Load all memory files from ~/.hermes/.

    Returns dict keyed by source: {"memory": ..., "user": ..., "soul": ...}
    """
    base = Path(hermes_dir).expanduser()

    memory_path = base / "memories" / "MEMORY.md"
    user_path = base / "memories" / "USER.md"
    soul_path = base / "SOUL.md"

    return {
        "memory": parse_memory_file(memory_path, "memory"),
        "user": parse_memory_file(user_path, "user"),
        "soul": parse_memory_file(soul_path, "soul"),
    }
