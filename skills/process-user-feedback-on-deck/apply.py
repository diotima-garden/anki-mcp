#!/usr/bin/env python3
"""
CLI entrypoint for process-user-feedback-on-deck's Apply step.

Reads the edit-output file written by edit.py, drops any note_ids the user skipped in
Confirm, applies the rest via update_note_fields_batch, and prints the per-note results
as JSON on stdout for the orchestrator's Report step.

Clearing `user_feedback` is what "applied" means, so this script sets it on every
surviving entry itself — edit.py never needs to emit it.

Usage: python3 apply.py [skip_note_id ...]
"""
import json
import pathlib
import sys

_anki_mcp_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_anki_mcp_root))

from core import _log  # noqa: E402
from managed_note_types import EDIT_OUTPUT_PATH  # noqa: E402
from managed_note_types.tools.edits import update_note_fields_batch  # noqa: E402


def main() -> int:
    skip_ids = {int(x) for x in sys.argv[1:]}

    updates = json.loads(EDIT_OUTPUT_PATH.read_text(encoding="utf-8"))
    updates = [u for u in updates if u["note_id"] not in skip_ids]
    for u in updates:
        u["fields"]["user_feedback"] = ""

    results = update_note_fields_batch(updates)
    _log(f"apply.py: applied {len(updates)} update(s), skipped {len(skip_ids)}")

    print(json.dumps(results, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
