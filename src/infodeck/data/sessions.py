"""Session indexer — reads ~/.hermes/sessions JSON files for metadata.

Extracts: date, model, first meaningful user message, message count.
Groups into subjects (by keyword) and daily logs (by date).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# Known project/topic keywords mapped to display names
SUBJECT_KEYWORDS: dict[str, list[str]] = {
    "kadathic_cryptogram": ["cryptogram", "cipher", "substitution", "solve", "puzzle"],
    "prismata_display": ["kiosk", "visualization", "chart", "prismata", "data viz", "dashboard"],
    "auralith_wallpaper": ["wallpaper", "rss", "gnome shell", "extension", "auralith"],
    "infodeck": ["infodeck", "memory wiki", "project dashboard"],
    "kadathic_core": ["agent foundry", "backend", "runtime", "provider adapter"],
    "kadathic_chat": ["chatbot", "nicegui chat", "chat frontend"],
    "hermes": ["hermes", "agent config", "personality", "skill", "memory file", "config.yaml"],
    "prompt_design": ["prompt", "hint", "retry", "llm response", "structured output"],
    "world_building": ["world", "story", "narrative", "creative writing", "fiction"],
    "gnome_development": ["gnome", "gjs", "gtk", "libadwaita", "gsettings"],
}


@dataclass
class SessionMeta:
    """Lightweight session metadata (no full message content)."""

    session_id: str
    filename: str          # e.g. "session_20260525_131103_6c10ef.json"
    date: str              # "2026-05-25"
    datetime: str          # full ISO timestamp
    model: str
    message_count: int
    first_message: str     # first meaningful user message (truncated)
    subjects: list[str] = field(default_factory=list)


@dataclass
class SubjectGroup:
    """A topic grouping with associated sessions."""

    name: str              # display name
    key: str               # internal key
    session_count: int
    last_date: str
    sessions: list[SessionMeta] = field(default_factory=list)


@dataclass
class DailyLog:
    """Sessions grouped by date."""

    date: str              # "2026-05-25"
    sessions: list[SessionMeta] = field(default_factory=list)


def index_sessions(sessions_dir: str | Path, max_files: int = 200) -> list[SessionMeta]:
    """Scan all session JSON files and extract metadata.

    Returns list sorted by date (newest first).
    """
    sessions_path = Path(sessions_dir).expanduser()
    if not sessions_path.is_dir():
        return []

    sessions: list[SessionMeta] = []
    files = sorted(sessions_path.glob("*.json"), reverse=True)

    for filepath in files[:max_files]:
        meta = _parse_session_file(filepath)
        if meta:
            sessions.append(meta)

    return sessions


def _parse_session_file(filepath: Path) -> SessionMeta | None:
    """Parse one session JSON file, extracting metadata only."""
    try:
        with filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    session_id = data.get("session_id", "")
    session_start = data.get("session_start", "")
    model = data.get("model", "unknown")
    message_count = data.get("message_count", 0)

    # Extract date
    date = ""
    datetime_str = session_start
    if session_start:
        try:
            dt = datetime.fromisoformat(session_start)
            date = dt.strftime("%Y-%m-%d")
            datetime_str = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            date = session_start[:10]

    # Find first meaningful user message (skip "restore session")
    first_message = _extract_first_user_message(data.get("messages", []))
    subjects = _detect_subjects(first_message)

    return SessionMeta(
        session_id=session_id,
        filename=filepath.name,
        date=date,
        datetime=datetime_str,
        model=model,
        message_count=message_count,
        first_message=first_message,
        subjects=subjects,
    )


def _extract_first_user_message(messages: list[dict]) -> str:
    """Extract the first meaningful user message from a message list.

    Skips "restore session" messages that are just session-restore commands.
    """
    for msg in messages:
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if isinstance(content, list):
            # Multi-part content
            text = " ".join(
                c.get("text", "") for c in content
                if isinstance(c, dict) and c.get("text")
            )
            content = text

        if not content or not isinstance(content, str):
            continue

        stripped = content.strip()

        # Skip pure restore commands
        if stripped.lower() in ("restore session", "/restore", "restore"):
            continue

        return stripped[:200]

    return "(no user messages)"


def _detect_subjects(text: str) -> list[str]:
    """Detect which subjects a session relates to based on keyword matching."""
    text_lower = text.lower()
    matched: list[str] = []

    for subject, keywords in SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                matched.append(subject)
                break

    return matched if matched else ["general"]


def group_by_subject(sessions: list[SessionMeta]) -> list[SubjectGroup]:
    """Group sessions by detected subject keywords.

    A session can appear in multiple groups if it matches multiple subjects.
    Returns groups sorted by session count (most active first).
    """
    groups: dict[str, SubjectGroup] = {}

    for session in sessions:
        for subject in session.subjects:
            if subject not in groups:
                groups[subject] = SubjectGroup(
                    name=_subject_display_name(subject),
                    key=subject,
                    session_count=0,
                    last_date=session.date,
                )
            g = groups[subject]
            g.session_count += 1
            g.sessions.append(session)
            if session.date > g.last_date:
                g.last_date = session.date

    return sorted(groups.values(), key=lambda g: g.session_count, reverse=True)


def group_by_date(sessions: list[SessionMeta]) -> list[DailyLog]:
    """Group sessions by date, newest first."""
    date_map: dict[str, DailyLog] = {}

    for session in sessions:
        date = session.date
        if date not in date_map:
            date_map[date] = DailyLog(date=date)
        date_map[date].sessions.append(session)

    return sorted(date_map.values(), key=lambda d: d.date, reverse=True)


def _subject_display_name(key: str) -> str:
    """Convert internal subject key to display name."""
    names = {
        "kadathic_cryptogram": "Cryptogram Solver",
        "prismata_display": "Prismata Display",
        "auralith_wallpaper": "Desktop RSS Wall",
        "infodeck": "Infodeck",
        "kadathic_core": "Agent Foundry Core",
        "kadathic_chat": "Agent Foundry Chat",
        "hermes": "Hermes Configuration",
        "prompt_design": "Prompt Design",
        "world_building": "World Building",
        "gnome_development": "GNOME Development",
        "general": "General",
    }
    return names.get(key, key.replace("_", " ").title())


@dataclass
class ConversationMessage:
    """A single display-ready message from a session."""

    role: str              # "user", "assistant", or "tool"
    content: str           # display text
    is_reasoning: bool = False
    tool_name: str | None = None


def load_conversation(sessions_dir: str | Path, filename: str) -> list[ConversationMessage]:
    """Load a session file and extract display-ready messages.

    Returns a list of ConversationMessage objects representing the full
    conversation flow. Tool calls and reasoning are included as labeled
    entries so the user can follow the agent's thought process.
    """
    filepath = Path(sessions_dir).expanduser() / filename
    if not filepath.exists():
        return []

    try:
        with filepath.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    messages = data.get("messages", [])
    result: list[ConversationMessage] = []

    for msg in messages:
        role = msg.get("role", "unknown")

        if role == "user":
            content = _extract_text_content(msg.get("content", ""))
            if content.strip():
                result.append(ConversationMessage(
                    role="user", content=content,
                ))

        elif role == "assistant":
            # Reasoning content (agent's thinking)
            reasoning = msg.get("reasoning_content") or msg.get("reasoning")
            if reasoning and reasoning.strip():
                result.append(ConversationMessage(
                    role="assistant", content=reasoning.strip()[:500],
                    is_reasoning=True,
                ))

            # Tool calls
            tool_calls = msg.get("tool_calls") or []
            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "unknown")
                args_str = _summarize_args(fn.get("arguments", ""))
                result.append(ConversationMessage(
                    role="tool",
                    content=f"→ {name}({args_str})",
                    tool_name=name,
                ))

            # Assistant text content (after reasoning/tool calls)
            content = _extract_text_content(msg.get("content", ""))
            if content.strip():
                result.append(ConversationMessage(
                    role="assistant", content=content,
                ))

        elif role == "tool":
            tool_name = msg.get("name", "unknown")
            tool_content = _extract_text_content(msg.get("content", ""))
            # Truncate long tool outputs
            if len(tool_content) > 300:
                tool_content = tool_content[:300] + "..."
            result.append(ConversationMessage(
                role="tool",
                content=tool_content,
                tool_name=tool_name,
            ))

    return result


def _extract_text_content(content: str | list | dict) -> str:
    """Extract plain text from potentially structured content."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return " ".join(parts)
    if isinstance(content, dict):
        return content.get("text", "")
    return str(content) if content else ""


def _summarize_args(args_str: str) -> str:
    """Summarize tool call arguments for compact display."""
    if not args_str:
        return ""
    try:
        args = json.loads(args_str)
        if not isinstance(args, dict):
            return "..."
        # Show first 2 meaningful keys
        keys = [k for k in args if k not in ("content", "old_string")]
        if not keys:
            return "..."
        parts = []
        for k in keys[:2]:
            v = args[k]
            if isinstance(v, str) and len(v) > 40:
                v = v[:40] + "..."
            elif isinstance(v, (list, dict)):
                v = "..."
            parts.append(f"{k}={v!r}")
        return ", ".join(parts)
    except (json.JSONDecodeError, TypeError):
        return "..."
