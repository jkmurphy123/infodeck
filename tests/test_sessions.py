"""Tests for session indexing and grouping."""

import json
from pathlib import Path

from infodeck.data.sessions import (
    SessionMeta,
    _extract_first_user_message,
    _detect_subjects,
    group_by_subject,
    group_by_date,
    _subject_display_name,
)


class TestExtractFirstMessage:
    def test_simple_user_message(self):
        messages = [
            {"role": "user", "content": "build a dashboard"},
        ]
        result = _extract_first_user_message(messages)
        assert result == "build a dashboard"

    def test_skips_restore(self):
        messages = [
            {"role": "user", "content": "restore session"},
            {"role": "user", "content": "build a dashboard"},
        ]
        result = _extract_first_user_message(messages)
        assert result == "build a dashboard"

    def test_list_content(self):
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": "hello"},
                {"type": "text", "text": "world"},
            ]},
        ]
        result = _extract_first_user_message(messages)
        assert result == "hello world"

    def test_empty(self):
        result = _extract_first_user_message([])
        assert result == "(no user messages)"

    def test_truncates(self):
        long_msg = "x" * 300
        messages = [{"role": "user", "content": long_msg}]
        result = _extract_first_user_message(messages)
        assert len(result) == 200


class TestDetectSubjects:
    def test_cryptogram(self):
        matches = _detect_subjects("build a cipher puzzle solver")
        assert "kadathic_cryptogram" in matches

    def test_prismata(self):
        matches = _detect_subjects("create a data viz kiosk dashboard")
        assert "prismata_display" in matches

    def test_auralith(self):
        matches = _detect_subjects("fix gnome shell extension wallpaper rss")
        assert "auralith_wallpaper" in matches

    def test_hermes(self):
        matches = _detect_subjects("configure hermes agent personality memory")
        assert "hermes" in matches

    def test_multiple_subjects(self):
        matches = _detect_subjects(
            "build a nicegui chatbot for the agent foundry backend"
        )
        assert "kadathic_core" in matches
        assert "kadathic_chat" in matches

    def test_no_match(self):
        matches = _detect_subjects("nothing matches here at all")
        assert matches == ["general"]


class TestGroupBySubject:
    def test_groups(self):
        sessions = [
            SessionMeta(
                session_id="s1", filename="f1", date="2026-05-25",
                datetime="2026-05-25 12:00", model="deepseek",
                message_count=10, first_message="build cryptogram solver",
                subjects=["kadathic_cryptogram"],
            ),
            SessionMeta(
                session_id="s2", filename="f2", date="2026-05-26",
                datetime="2026-05-26 12:00", model="deepseek",
                message_count=20, first_message="build dashboard kiosk",
                subjects=["prismata_display"],
            ),
            SessionMeta(
                session_id="s3", filename="f3", date="2026-05-27",
                datetime="2026-05-27 12:00", model="deepseek",
                message_count=15, first_message="fix cryptogram bug",
                subjects=["kadathic_cryptogram"],
            ),
        ]
        groups = group_by_subject(sessions)
        assert len(groups) == 2
        assert groups[0].key == "kadathic_cryptogram"
        assert groups[0].session_count == 2

    def test_empty(self):
        assert group_by_subject([]) == []


class TestGroupByDate:
    def test_groups(self):
        sessions = [
            SessionMeta(
                session_id="s1", filename="f1", date="2026-05-25",
                datetime="2026-05-25 12:00", model="x", message_count=5,
                first_message="", subjects=[],
            ),
            SessionMeta(
                session_id="s2", filename="f2", date="2026-05-25",
                datetime="2026-05-25 14:00", model="x", message_count=5,
                first_message="", subjects=[],
            ),
            SessionMeta(
                session_id="s3", filename="f3", date="2026-05-26",
                datetime="2026-05-26 10:00", model="x", message_count=5,
                first_message="", subjects=[],
            ),
        ]
        logs = group_by_date(sessions)
        assert len(logs) == 2
        # Newest first
        assert logs[0].date == "2026-05-26"
        assert len(logs[0].sessions) == 1
        assert logs[1].date == "2026-05-25"
        assert len(logs[1].sessions) == 2

    def test_empty(self):
        assert group_by_date([]) == []


class TestDisplayNames:
    def test_known_subject(self):
        assert _subject_display_name("kadathic_cryptogram") == "Cryptogram Solver"

    def test_unknown_subject(self):
        assert _subject_display_name("custom_topic") == "Custom Topic"
