#!/usr/bin/env python3
"""
Anki MCP server — entry point.

Sets up the import path, imports core (mcp instance + _call),
then imports the tools package which triggers @mcp.tool() registration
across all submodules.

All logging goes to the project file logger (never stdout — stdout is the stdio transport).
"""
import pathlib
import sys

_here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_here))           # anki-mcp/ → core, launcher, tools, utils

import core
from core import mcp, _log
import tools    # noqa: F401 — import triggers @mcp.tool() registration in all submodules
import prompts  # noqa: F401 — import triggers @mcp.prompt() registration

if __name__ == "__main__":
    import argparse
    from managed_note_types import bootstrap

    parser = argparse.ArgumentParser()
    parser.add_argument("--managed-config", default=None)
    args, _ = parser.parse_known_args()

    _log("server starting")
    if args.managed_config:
        config_path = args.managed_config
        core._lazy_bootstrap = lambda: bootstrap.run(config_path)
    mcp.run()
