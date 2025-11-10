#!/usr/bin/env python3
"""ShokoBot CLI entry point.

This module serves as the main entry point for the ShokoBot CLI.
Commands are auto-loaded from the cli package.
"""

from cli import cli

if __name__ == "__main__":
    cli()
