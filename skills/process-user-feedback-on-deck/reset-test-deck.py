#!/usr/bin/env python3
"""
Reset the process-user-feedback-on-deck test deck to a pristine, known state.

Idempotent test fixture. Lets the skill be run standalone in any session without
hand-crafting cards or seeding feedback by hand:

  - ensures the `zz-test-feedback` deck exists
  - deletes every note currently in it
  - re-adds a canonical set of Production notes, each carrying a distinct, non-empty
    `user_feedback` — seeded via raw addNotes, which is the "user authored feedback"
    path (it bypasses the managed update-guard that forbids programmatically setting
    user_feedback, exactly as a person typing in the Anki GUI would)
  - stages a FRESH copy of the given compiled context into the skill's gitignored
    `.artifacts/` area and clears that copy's `.feedback.jsonl`, so a run uses the
    real deck's editing guidelines yet never appends to the real grove's audit log
  - clears the pipeline handoff files (edit-input / edit-output)

The staged context copy is what the standalone skill run should be pointed at; its
path is stable across sessions and printed at the end together with the canonical
invocation.

Usage: python3 reset-test-deck.py <source-compiled-context-path>

The source path is an argument (not hardcoded) so this fixture stays decoupled from
any particular consumer's directory layout — anki-mcp is a standalone repo.
"""
import pathlib
import shutil
import sys

_anki_mcp_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_anki_mcp_root))

from core import _call, _log  # noqa: E402
from managed_note_types import EDIT_INPUT_PATH, EDIT_OUTPUT_PATH, feedback_log_path  # noqa: E402

DECK = "zz-test-feedback"
MODEL = "Production"

# One fixture note per pending edit. Each targets a different field so a single run
# exercises multiple cards with feedback simultaneously and produces visibly distinct
# diffs in the Confirm step.
FIXTURE_NOTES = [
    {
        "fields": {
            "Front": "el gato",
            "Back": "the cat",
            "Hint": "animal",
            "Interesting Facts": "",
            "user_feedback": "Add a short Rioplatense example sentence using voseo to "
                             "Interesting Facts, with its English translation.",
        },
    },
    {
        "fields": {
            "Front": "el auto",
            "Back": "the car",
            "Hint": "vehicle",
            "Interesting Facts": "",
            "user_feedback": "Translate the Hint field into Rioplatense Spanish.",
        },
    },
    {
        "fields": {
            "Front": "la casa",
            "Back": "the house",
            "Hint": "building",
            "Interesting Facts": "Vivo en una casa grande.",
            "user_feedback": "Rewrite the Interesting Facts example in Rioplatense "
                             "voseo style and add its English translation.",
        },
    },
]


def _test_context_path(source: pathlib.Path) -> pathlib.Path:
    """Staged copy lives beside the pipeline handoff files, keyed by source filename."""
    return EDIT_INPUT_PATH.parent / source.name


def main() -> int:
    if len(sys.argv) < 2:
        _log("reset-test-deck.py: missing required <source-compiled-context-path>")
        return 2

    source = pathlib.Path(sys.argv[1]).resolve()
    if not source.is_file():
        _log(f"reset-test-deck.py: source context not found: {source}")
        return 2

    _call("createDeck", deck=DECK)

    existing = _call("findNotes", query=f'deck:"{DECK}"')
    if existing:
        _call("deleteNotes", notes=existing)

    notes_payload = [
        {
            "deckName": DECK,
            "modelName": MODEL,
            "fields": n["fields"],
            "tags": ["test"],
            "options": {"allowDuplicate": True},
        }
        for n in FIXTURE_NOTES
    ]
    added = _call("addNotes", notes=notes_payload)

    # Stage a fresh context copy and clear its audit log + the handoff files.
    test_context = _test_context_path(source)
    test_context.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, test_context)
    for stale in (
        feedback_log_path(test_context),
        EDIT_INPUT_PATH,
        EDIT_OUTPUT_PATH,
    ):
        stale.unlink(missing_ok=True)

    _log(f"reset-test-deck.py: reset '{DECK}' with {len(added)} notes")

    print(f"Reset deck '{DECK}': {len(added)} notes, each with pending user_feedback.")
    print(f"Staged context copy: {test_context}")
    print()
    print("Run the skill standalone with:")
    cwd = pathlib.Path.cwd()
    rel = test_context.relative_to(cwd) if cwd in test_context.parents else test_context
    print(f"  /anki-mcp:process-user-feedback-on-deck {rel} {DECK}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
