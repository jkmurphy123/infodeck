# Infodeck — Design Document

A personal memory wiki and project dashboard with a NiceGUI frontend.

**Project path:** `/home/ubuntu/ai_projects/infodeck`
**GitHub repo:** `jkmurphy123/infodeck`
**Stack:** Python 3.12, NiceGUI, Pydantic, gh CLI

---

## Layout (3-zone, mode-switched)

```
┌──────────────────────────────────────────────────────────────────┐
│ Top Bar                                                          │
│  [GitHub Repos]  [Conversations]  [Memory]     ← tab-style modes │
├──────────────┬───────────────────────────────────────────────────┤
│              │                                                   │
│  List Panel  │  Detail / Edit Panel                              │
│  (w-80)      │  (grow, read-only or editable)                    │
│              │                                                   │
├──────────────┴───────────────────────────────────────────────────┤
│ Status Bar                                                        │
│  status message  |  entry count  |  last refresh time              │
└──────────────────────────────────────────────────────────────────┘
```

This reuses the same structural pattern as kadathic_cryptogram (shell.py):
- `top_bar` — mode tab buttons (replaces the old left-side mode panel)
- `list_panel` (left column) — scrollable list of items
- `detail_panel` (right column, grow) — content area, mode-dependent
- `status_bar` — compact info strip at bottom

The tab buttons live in the top bar, not a separate left panel. When the user
clicks a tab, the list and detail panels re-render for that mode.

---

## Mode 1: GitHub Repos

**Data sources:**
1. `gh repo list --json name,description,createdAt,updatedAt,url,language` (live list)
2. `cache/repo_summaries.json` (persistent, hand-curated summaries)
3. `cache/repo_analysis_state.json` (tracks which repos have been analyzed + timestamps)

The live list gives us names, dates, URLs, and language. The cache gives us
human-readable summaries. They're joined by repo name at render time.

**Repo Analysis (one-time, then incremental):**

On first run (or when cache is empty), a background job:
1. Fetches all repos via `gh repo list`
2. For each repo WITHOUT a description on GitHub, inspects the repo to
   generate one. Strategy:
   - Check for README.md on the default branch (gh api)
   - Check for AGENTS.md, DESIGN.md, or PROJECT_OUTLINE.md
   - If the project is cloned locally, scan those files directly
   - Produces a 1-2 sentence summary: what it does + main language
3. Stores the result in `cache/repo_summaries.json`
4. Records the timestamp in `cache/repo_analysis_state.json`

Repos that already have a GitHub description are not re-analyzed (the
description is used as-is) unless the user explicitly triggers a re-analysis.

**Refresh button (incremental):**
- Fetches fresh repo list
- Compares `createdAt` against `last_analyzed_at` in the state file
- Only analyzes repos created AFTER the last analysis timestamp
- Updates both cache files
- Status bar shows: "3 new repos analyzed, 30 total"

**Left panel:**
- Scrollable list of all repos, sorted by most-recently-updated
- Each entry shows: name + language badge
- Click selects it, loads details on the right
- "Refresh" button at top of list triggers incremental analysis
- Optionally: filter/search box

**Right panel (read-only detail):**
- Repo name (header)
- Summary (from cache, or GitHub description as fallback)
- URL (clickable link)
- Last updated / created dates
- Primary language
- Local path (if cloned under ~/ai_projects or similar)
- "Open in Browser" button

**Cache file format** (`cache/repo_summaries.json`):

```json
{
  "prismata_display": {
    "summary": "A fullscreen Pygame data visualization kiosk...",
    "language": "Python",
    "analyzed_at": "2026-05-26T12:00:00Z"
  }
}
```

**State file format** (`cache/repo_analysis_state.json`):

```json
{
  "last_full_analysis": "2026-05-26T12:00:00Z",
  "repos_analyzed": 30
}
```

**Status bar for this mode:**
- "30 repos | 27 with summaries | refreshed 5m ago"

---

## Mode 2: Conversations

**Data sources:**
1. **Hermes sessions** — metadata from session files (69 sessions in ~/.hermes/sessions/)
2. **session_search tool** — for recalling past conversations
3. **AGENTS.md / PROJECT_OUTLINE.md / DESIGN.md** — per-project docs for context

**Left panel:**
- Two grouped lists (accordion-style or collapsible sections):
  - **By Subject** — topics inferred from session_search queries + project names
    (e.g., "kadathic_cryptogram", "auralith_wallpaper", "prismata_display",
    "hermes configuration", "prompt design")
  - **Daily Logs** — sessions grouped by date, newest first
    Each entry shows: date + short summary / first user message
- Click a subject → shows all sessions related to that topic
- Click a daily log entry → shows that session's summary

**Right panel (read-only detail):**
*Subject view:* list of session dates + one-line summaries for that topic
*Session view:*
- Date/time
- Model used
- Project context (if any)
- Full summary of what was discussed and accomplished
- Optionally: key files touched, decisions made

**Status bar for this mode:**
- Total session count, subject count, date range

---

## Mode 3: Memory (What Hermes Knows About Me)

**Data sources (read directly from disk, not via the Hermes CLI):**
1. `/home/ubuntu/.hermes/memories/MEMORY.md` — project/environment facts
2. `/home/ubuntu/.hermes/memories/USER.md` — user profile/preferences
3. `/home/ubuntu/.hermes/SOUL.md` — agent persona (read-only)

**Left panel:**
- Two sections: "Your Profile" (USER.md) and "Project Knowledge" (MEMORY.md)
- Each entry is a paragraph (delimited by `§` in the source files)
- Each entry shows a truncated preview (first 80 chars)
- Click selects it, loads full content on the right

**Right panel (editable):**
- Full text of the selected entry
- Edit mode: textarea with the entry content
- Save button writes back to the source file
- Delete button removes the entry (with confirmation)
- Add button to append a new entry

**Edit constraints & safety:**
- Entries in MEMORY.md and USER.md are separated by `§` followed by newline
- Editing preserves the delimiter structure
- A backup is written before any write (`<file>.bak`)
- SOUL.md is display-only (not editable through this UI)

**Status bar for this mode:**
- Entry count (profile + knowledge), last save time

---

## File Structure

```
infodeck/
  AGENTS.md
  DESIGN.md            ← this file
  README.md
  pyproject.toml

  src/
    infodeck/
      __init__.py
      app.py            # NiceGUI app factory
      main.py           # CLI entry point
      config.py         # InfodeckConfig (Pydantic)

      state/
        __init__.py
        app_state.py    # InfodeckUiState dataclass + AppMode enum

  data/
    __init__.py
    github.py         # GitHub repo data layer (gh CLI wrapper)
    repo_analysis.py  # Repo analysis: README/doc scanning + summary generation
    memory_files.py   # MEMORY.md / USER.md reader & writer
    sessions.py       # Session indexer (reads ~/.hermes/sessions/ metadata)

  cache/
    repo_summaries.json       # persisted repo summaries
    repo_analysis_state.json  # tracks last analysis timestamp

      ui/
        __init__.py
        shell.py         # Main layout: top_bar + list + detail + status_bar
        top_bar.py       # Mode tab buttons
        status_bar.py    # Footer info strip

        github_repos/
          __init__.py
          list_panel.py  # Repo list (left)
          detail_panel.py # Repo detail (right)

        conversations/
          __init__.py
          list_panel.py  # Subjects + daily logs (left)
          detail_panel.py # Session/subject detail (right)

        memory/
          __init__.py
          list_panel.py  # Memory entries list (left)
          detail_panel.py # Memory entry editor (right)

  tests/
    test_config.py
    test_memory_files.py
    test_github.py
    test_app_state.py
```

---

## Data Models

### AppState

```python
class AppMode(str, Enum):
    GITHUB = "github"
    CONVERSATIONS = "conversations"
    MEMORY = "memory"

@dataclass
class InfodeckUiState:
    active_mode: AppMode = AppMode.GITHUB
    status: str = "ready"

    # GitHub mode
    github_repos: list[RepoSummary] = field(default_factory=list)
    github_selected_index: int | None = None
    github_last_refresh: float | None = None

    # Conversations mode
    conversation_subjects: list[SubjectGroup] = field(default_factory=list)
    conversation_daily_logs: list[DailyLogEntry] = field(default_factory=list)
    conversation_selected_id: str | None = None

    # Memory mode
    memory_entries: list[MemoryEntry] = field(default_factory=list)
    memory_selected_index: int | None = None
    memory_dirty: bool = False   # unsaved changes in editor

    # General
    last_error: str | None = None
```

### GitHub

```python
@dataclass
class RepoSummary:
    name: str
    description: str          # from GitHub, may be empty
    summary: str | None       # from cache/repo_summaries.json (analyzed)
    url: str
    created_at: str           # ISO timestamp
    updated_at: str           # ISO timestamp
    language: str | None
    local_path: str | None    # path on disk if cloned
    has_analysis: bool        # True if summary exists in cache

@dataclass
class RepoAnalysisState:
    last_full_analysis: str | None   # ISO timestamp
    repos_analyzed: int = 0
```

### Memory Files

```python
@dataclass
class MemoryEntry:
    source: str           # "memory" or "user"
    index: int            # position in file (0-based)
    content: str          # full paragraph text
    preview: str          # first ~80 chars
```

### Conversations

```python
@dataclass
class SubjectGroup:
    name: str             # e.g. "kadathic_cryptogram", "hermes"
    session_count: int
    last_date: str

@dataclass
class DailyLogEntry:
    date: str             # "2026-05-25"
    session_ids: list[str]
    summary: str          # from session metadata
    model: str | None
```

---

## Data Flow

### GitHub mode
1. On mode switch → `data/github.py` calls `gh repo list`
2. `data/repo_analysis.py` loads `cache/repo_summaries.json` and joins by name
3. Left panel renders the list (with analysis badges); click → right panel shows detail
4. "Refresh" button → incremental analysis of new repos only
5. Display text: `summary` (from cache) if available, else fall back to `description`

### Conversations mode
1. On mode switch → `data/sessions.py` indexes session files
2. Session metadata extracted: date, model, first user message
3. Groups built: by subject (keyword-based) and by date
4. Left panel renders groups; click → right panel shows detail
5. Session detail can optionally use `session_search` results (pre-cached or async)
6. No writes happen (read-only mode)

### Memory mode
1. On mode switch → `data/memory_files.py` reads MEMORY.md and USER.md
2. Entries parsed using `§` delimiter
3. Left panel renders previews; click → right panel shows full text
4. User edits → `memory_dirty = True`; Save writes back to source file
5. Backup created at `<file>.bak` before overwrite

---

## Configuration (frontend.yaml)

```yaml
ui:
  title: Infodeck
  default_mode: github

github:
  owner: jkmurphy123
  cache_ttl_minutes: 5
  local_projects_root: /home/ubuntu/ai_projects

memory:
  hermes_dir: /home/ubuntu/.hermes
  backup_on_save: true

conversations:
  sessions_dir: /home/ubuntu/.hermes/sessions
```

---

## Key Design Decisions

1. **No backend dependency.** Unlike kadathic_cryptogram which depends on Agent Foundry,
   infodeck is self-contained. It reads local files and calls `gh` CLI directly.
   No LLM calls, no agent framework.

2. **Tab-based mode switching.** The cryptogram app uses a left-side mode panel
   with vertical buttons. Infodeck puts mode switching in the top bar as horizontal
   tabs — the user explicitly asked for this ("like a tab control").

3. **Parse the delimited files, don't treat them as structured data.** MEMORY.md and
   USER.md use `§` as entry separators. The app reads/writes them faithfully without
   imposing a rigid schema. This keeps compatibility with Hermes reading/writing the
   same files.

4. **Read-only for GitHub and Conversations, editable for Memory.** Only Mode 3
   has write capability — editing what Hermes knows. Modes 1 and 2 are purely
   informational.

5. **No real-time sync with Hermes.** Changes to memory files are written to disk
   immediately on save. Hermes reads MEMORY.md/USER.md fresh each turn, so changes
   will be picked up on the next conversation. No Hermes API call needed.

6. **Session search is optional enrichment.** The conversations mode works with
   lightweight metadata parsing (dates, first messages). For richer summaries,
   it could optionally call `session_search` results, but that would require
   Hermes to be running — so it's a deferred feature.

---

## Pitfalls & Constraints

- **§ delimiter fragility:** If a memory entry itself contains `§`, the parser
  will split it incorrectly. The current entries don't do this, but the editor
  should warn the user.
- **gh CLI dependency:** `gh` must be installed and authenticated. Fallback
  should show a clear error message.
- **Memory file locking:** Hermes might write MEMORY.md while the app has it
  open. The app should re-read before writing to avoid clobbering. Use a simple
  mtime check and warn the user.
- **Session files are JSON:** ~/.hermes/sessions/ contains JSON files. We can
  parse metadata (date, model, first message) without reading full content.
  Full content reading is blocked by Hermes security — we only use metadata.
- **No search in v1:** Adding search/filter across all modes is valuable but
  deferred past the initial milestone.

---

## Milestone Plan

### Milestone 1 — Skeleton + GitHub mode
- Project scaffolding, config, state
- UI shell with top_bar (mode tabs) + list + detail + status_bar layout
- GitHub Mode: gh CLI integration, repo list, detail view
- Repo analysis engine: README/doc scanning, summary cache (JSON)
- "Refresh" button with incremental analysis of new repos
- Tests for config, state, github data layer, repo analysis

### Milestone 2 — Conversations mode
- Session indexer (metadata-only parsing)
- Subject grouping + daily log listing
- Conversation detail view
- Tests for session parsing

### Milestone 3 — Memory mode
- MEMORY.md / USER.md reader with § delimiter
- Memory editor (view, edit, save, delete, add)
- Safety: backup before write, mtime conflict detection
- SOUL.md read-only display
- Tests for memory file parsing and writing

### Milestone 4 — Polish
- Search/filter across modes
- Better error states, loading indicators
- Sort options for GitHub repos
- "Re-analyze single repo" button in detail view
