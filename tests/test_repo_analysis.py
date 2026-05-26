"""Tests for repo analysis."""

import json
from pathlib import Path

from infodeck.data.repo_analysis import (
    generate_summary,
    load_summary_cache,
    save_summary_cache,
    load_analysis_state,
    save_analysis_state,
)


class TestGenerateSummary:
    def test_finds_description_paragraph(self):
        doc = """# My Project

Some badges here.

A fullscreen data visualization kiosk with animated charts and plugin architecture.

## Installation
pip install...
"""
        result = generate_summary(doc, "Python")
        assert "data visualization" in result
        assert "Python" in result

    def test_falls_back_to_first_meaningful(self):
        doc = """# Untitled

Just some random text that goes on for a while and makes a paragraph.

More text.
"""
        result = generate_summary(doc, "Rust")
        assert "random text" in result
        assert "Rust" in result

    def test_empty_doc(self):
        result = generate_summary("", "Go")
        assert "Go" in result

    def test_only_headings(self):
        doc = """# Title

## Subtitle

### Another
"""
        result = generate_summary(doc, "Python")
        assert "Python" in result

    def test_strips_markdown_badges(self):
        doc = """# Project

[![Build](badge.svg)]

A tool for managing agent workflows.
"""
        result = generate_summary(doc, "Python")
        assert "agent workflows" in result
        assert "[!" not in result


class TestSummaryCache:
    def test_load_empty_cache(self, tmp_path):
        cache = load_summary_cache(tmp_path)
        assert cache == {}

    def test_save_and_load(self, tmp_path):
        data = {
            "repo1": {"summary": "test", "language": "Python"},
            "repo2": {"summary": "test2", "language": "Rust"},
        }
        save_summary_cache(tmp_path, data)

        loaded = load_summary_cache(tmp_path)
        assert loaded == data

    def test_overwrite(self, tmp_path):
        data1 = {"repo1": {"summary": "v1"}}
        data2 = {"repo2": {"summary": "v2"}}
        save_summary_cache(tmp_path, data1)
        save_summary_cache(tmp_path, data2)

        loaded = load_summary_cache(tmp_path)
        assert loaded == data2


class TestAnalysisState:
    def test_load_empty_state(self, tmp_path):
        state = load_analysis_state(tmp_path)
        assert state["last_full_analysis"] is None
        assert state["repos_analyzed"] == 0

    def test_save_and_load(self, tmp_path):
        state = {"last_full_analysis": "2026-05-26T12:00:00Z", "repos_analyzed": 30}
        save_analysis_state(tmp_path, state)

        loaded = load_analysis_state(tmp_path)
        assert loaded == state
