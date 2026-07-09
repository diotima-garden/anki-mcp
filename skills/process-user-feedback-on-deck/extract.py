#!/usr/bin/env python3
"""
CLI entrypoint for process-user-feedback-on-deck's Extract step.

Finds pending user_feedback in `deck`, RED-flags matches, and writes edit-ready
records straight to the static edit-input file for edit-card-batch to read — the
record payload (full field values, HTML, accented text) never round-trips through
the orchestrator's context. The orchestrator checks the outcome by reading
EDIT_INPUT_PATH itself (empty list = nothing pending), same as it already does for
Confirm — no stdout contract to keep in sync.

Usage: python3 extract.py <deck> [jsonl_output_path]
"""
import json
import pathlib
import sys

_anki_mcp_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_anki_mcp_root))

from core import _log  # noqa: E402
from managed_note_types import EDIT_INPUT_PATH  # noqa: E402
from managed_note_types.feedback import extract_feedback_records  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        _log("extract.py: missing required <deck> argument")
        return 2

    deck = sys.argv[1]
    jsonl_path = sys.argv[2] if len(sys.argv) > 2 else None

    records = extract_feedback_records(deck)

    if jsonl_path and records:
        p = pathlib.Path(jsonl_path)
        with p.open("a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        _log(f"extract.py: appended {len(records)} records to {jsonl_path}")

    edit_input = [
        {"note_id": r["note_id"], "fields": r["new_fields"], "model": r["model"]}
        for r in records
    ]
    EDIT_INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EDIT_INPUT_PATH.write_text(json.dumps(edit_input, ensure_ascii=False), encoding="utf-8")
    _log(f"extract.py: wrote {len(edit_input)} records to {EDIT_INPUT_PATH}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
