#!/usr/bin/env -S uv run -s
# /// script
# dependencies = []
# ///
# this_file: src/imgcolorshine/__main__.py

"""
Entry point for imgcolorshine package.

Thin wrapper that calls the Fire CLI.
"""

from imgcolorshine.cli import main

if __name__ == "__main__":
    main()
