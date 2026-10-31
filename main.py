#!/usr/bin/env python3
"""Entry point: starts the Charlie GUI (no arguments) or the CLI (with arguments)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    from cli.main import app, run_gui
    if len(sys.argv) == 1:
        run_gui()
    else:
        app()


if __name__ == "__main__":
    main()
