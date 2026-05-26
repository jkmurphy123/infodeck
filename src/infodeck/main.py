"""CLI entry point for Infodeck."""

from __future__ import annotations

import argparse
from pathlib import Path

from infodeck.app import create_app
from infodeck.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Infodeck — personal memory wiki and project dashboard"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to frontend.yaml config file",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    # Build the NiceGUI app
    from nicegui import ui

    create_app(config)

    ui.run(
        host=args.host,
        port=args.port,
        title=config.ui.title,
        reload=False,
    )


if __name__ == "__main__":
    main()
