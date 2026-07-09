import pathlib

MANAGED_FIELDS: tuple[str, ...] = ("user_feedback", "log")

# Static handoff files for the process-user-feedback-on-deck pipeline. One run at a
# time: extract.py overwrites EDIT_INPUT_PATH, edit-card-batch overwrites
# EDIT_OUTPUT_PATH. apply.py reads EDIT_OUTPUT_PATH and prints its results to stdout
# for the orchestrator — no third file, nothing downstream reads it from disk. Under
# /tmp so the two files never show up in `git status`.
EDIT_INPUT_PATH = pathlib.Path("/tmp/anki-mcp-feedback-edit-input.json")
EDIT_OUTPUT_PATH = pathlib.Path("/tmp/anki-mcp-feedback-edit-output.json")
