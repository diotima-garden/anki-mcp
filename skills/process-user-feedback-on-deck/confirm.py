#!/usr/bin/env python3
"""
CLI entrypoint for process-user-feedback-on-deck's Confirm step.

Reads the edit-input (old field values + feedback) and edit-output (changed fields)
handoff files and prints a numbered, human-readable diff to stdout for the orchestrator
to show the user before applying. The artifact paths stay out of the skill markdown —
they are resolved in the module, not hardcoded in prose.

Each record prints its note_id so the orchestrator can identify which entries the user
skips.

Usage: python3 confirm.py
"""
import json
import pathlib
import sys

_anki_mcp_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_anki_mcp_root))

from managed_note_types import EDIT_INPUT_PATH, EDIT_OUTPUT_PATH  # noqa: E402


def main() -> int:
    edit_input = json.loads(EDIT_INPUT_PATH.read_text(encoding="utf-8"))
    edit_output = json.loads(EDIT_OUTPUT_PATH.read_text(encoding="utf-8"))

    old_by_id = {r["note_id"]: r["fields"] for r in edit_input}

    for i, rec in enumerate(edit_output, 1):
        note_id = rec["note_id"]
        old = old_by_id.get(note_id, {})
        new_fields = rec["fields"]
        first_field = next(iter(old.values()), "")
        print(f"{i}. {first_field}  (note {note_id})")
        for field, value in old.items():
            if field == "user_feedback":
                continue
            print(f'   {field}: "{value}"')


        print(f'\n   feedback: "{old.get("user_feedback", "")}"')
        if new_fields:
            for field, new_val in new_fields.items():
                print(f'   → {field}: "{old.get(field, "")}" → "{new_val}"')
        else:
            print("   (no field change)")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
