# AGENTS.md

## Project: Infodeck

A NiceGUI desktop app — a personal memory wiki and project dashboard with
three modes accessible via top-bar tabs.

**Stack:** Python 3.12, NiceGUI, Pydantic, gh CLI
**Project path:** /home/ubuntu/ai_projects/infodeck

---

## Project Structure

```
infodeck/
  AGENTS.md
  DESIGN.md
  pyproject.toml

  src/
    infodeck/
      __init__.py
      app.py               # NiceGUI app factory (build_shell)
      main.py              # CLI entry point
      config.py            # InfodeckConfig Pydantic model

      state/
        app_state.py       # InfodeckUiState dataclass + AppMode enum

      data/
        github.py          # GitHub repo list via gh CLI
        repo_analysis.py   # README/doc scanning + summary cache
        memory_files.py    # MEMORY.md / USER.md reader & writer (M3)
        sessions.py        # Session indexer (M2)

      ui/
        shell.py           # Top-level layout
        top_bar.py         # Mode tab buttons
        status_bar.py      # Footer info strip
        github_repos/      # Mode 1 panels
        conversations/     # Mode 2 panels (M2)
        memory/            # Mode 3 panels (M3)

  cache/
    repo_summaries.json        # persisted repo analysis
    repo_analysis_state.json   # last analysis timestamp

  tests/
```

---

## Architecture

Self-contained NiceGUI app with no backend dependency. Reads local files and
calls `gh` CLI directly. No LLM, no agent framework.

- **UI is dumb (mostly).** Layout and event handling in `ui/`.
- **Data layer** in `data/` wraps CLI calls and file I/O.
- **Cache** layer in `cache/*.json` for repo analysis persistence.
- **State** is a single `InfodeckUiState` dataclass passed through the shell.

---

## Running

```bash
cd /home/ubuntu/ai_projects/infodeck
.venv/bin/python -m infodeck --host 127.0.0.1 --port 8080
```

Tests:

```bash
.venv/bin/python -m pytest tests/ -v
```
