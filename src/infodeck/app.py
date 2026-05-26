"""NiceGUI app factory for Infodeck."""

from __future__ import annotations

from pathlib import Path

from nicegui import ui

from infodeck.config import InfodeckConfig, load_config
from infodeck.state.app_state import InfodeckUiState
from infodeck.ui.shell import build_shell


def create_app(config: InfodeckConfig | None = None) -> None:
    """Build and mount the Infodeck NiceGUI app.

    Called once on startup — this function runs at import time inside
    the NiceGUI main page handler.
    """
    if config is None:
        config = load_config()

    # Ensure cache directory exists
    config.cache_dir.mkdir(parents=True, exist_ok=True)

    state = InfodeckUiState()
    build_shell(config=config, state=state)
