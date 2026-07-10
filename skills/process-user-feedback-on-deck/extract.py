#!/usr/bin/env python3
"""
CLI entrypoint for process-user-feedback-on-deck's Extract step.

Finds pending user_feedback in `deck`, RED-flags matches, and writes two sinks:
EDIT_INPUT_PATH (transient handoff for edit.py, overwritten) and, next to the given
context file, the append-only `<context>.feedback.jsonl` audit log — see
managed_note_types.feedback_log_path for the shape/lifecycle split.

Stdout's leading token is the orchestrator's signal:
  EXTRACTED <n> …       — proceed to Edit
  NO_PENDING_FEEDBACK … — report and stop (exit 0, not an error)
Genuine errors exit non-zero (usage, unhandled exception).

Usage: python3 extract.py <deck> [context-file-path]
"""
import json
import pathlib
import sys

_anki_mcp_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_anki_mcp_root))

from core import _log  # noqa: E402
from managed_note_types import EDIT_INPUT_PATH, feedback_log_path  # noqa: E402
from managed_note_types.feedback import extract_feedback_records  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        _log("extract.py: missing required <deck> argument")
        print("USAGE_ERROR: missing required <deck> argument", file=sys.stderr)
        return 2

    deck = sys.argv[1]
    context_path = sys.argv[2] if len(sys.argv) > 2 else None

    records = extract_feedback_records(deck)

    if context_path and records:
        log_path = feedback_log_path(context_path)
        with log_path.open("a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        _log(f"extract.py: appended {len(records)} records to {log_path}")

    edit_input = [
        {"note_id": r["note_id"], "fields": r["fields"], "model": r["model"]}
        for r in records
    ]
    EDIT_INPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EDIT_INPUT_PATH.write_text(json.dumps(edit_input, ensure_ascii=False), encoding="utf-8")
    _log(f"extract.py: wrote {len(edit_input)} records to {EDIT_INPUT_PATH}")

    if edit_input:
        print(f"EXTRACTED {len(edit_input)} pending-feedback card(s) — proceed to Edit")
    else:
        print(f"NO_PENDING_FEEDBACK — no cards with pending feedback in {deck!r}. Stop and report this.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
