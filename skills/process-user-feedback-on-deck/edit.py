#!/usr/bin/env python3
"""
CLI entrypoint for process-user-feedback-on-deck's Edit step.

Replaces the former `edit-card-batch` fork. The edit is the only genuinely
LLM-shaped step in the pipeline (interpret each card's `user_feedback`, decide which
fields change, generate the new values in the deck's style). Everything around it is
deterministic Python, so this step is driven from Python too:

  - reads the edit-input records (note_id + full field map incl. `user_feedback`)
  - reads the deck's compiled editing guidelines (the context file path argument)
  - asks a fresh, context-free `claude -p` to return ONLY the changed fields, as JSON
    on stdout (via utils llm call, which pipes the prompt over stdin so a large
    compiled context isn't capped by the 128 KiB argv limit)
  - validates the returned JSON against the input note_ids and writes edit-output

Routing the model output through the subprocess's stdout (not the Write tool) is the
point: no Write-tool call means no file-overwrite permission prompt, no spawn-time
staleness, and — unlike the old fork — Python can validate the JSON and retry once
before failing.

A non-zero exit is a genuine error (usage, LLM failure, unparseable/invalid output);
the caller stops on it, matching the extract/confirm/apply contract.

Usage: python3 edit.py <compiled-context-path>
"""
import json
import pathlib
import sys

_anki_mcp_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_anki_mcp_root))

from core import _log  # noqa: E402
from managed_note_types import EDIT_INPUT_PATH, EDIT_OUTPUT_PATH  # noqa: E402
from utils.llm_triggers import call_isolated  # noqa: E402

MODEL = "sonnet"

_PROMPT = """\
You are editing Anki cards. Apply each card's `user_feedback` instruction to its \
fields, following the deck's editing guidelines below.

=== DECK EDITING GUIDELINES ===
{guidelines}
=== END GUIDELINES ===

Here are the cards, as a JSON array. Each has a `note_id`, a `model` (note type), and \
a `fields` map holding the current value of every field — empty ones included — plus \
the pending `user_feedback` instruction:

{records}

For each card:
- Read `user_feedback` as a card-level edit instruction. Decide which field(s) it \
applies to, guided by the guidelines and the card's model. It is not tied to one field.
- Produce ONLY the fields whose value you are changing, with their new values. Omit \
every field you are not changing. Never emit `user_feedback` (clearing it is a later \
step's job). If the feedback warrants no change, emit an empty `fields` map.

Return a JSON array with one object per input card, in the same order, none dropped:

  [{{"note_id": <id>, "fields": {{"<field>": "<new value>", ...}}}}, ...]

Output the raw JSON array and nothing else — no prose, no markdown code fences.\
"""


def _strip_fences(text: str) -> str:
    """Tolerate a model that wraps its JSON in ```/```json fences despite instructions."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def _parse_and_validate(raw: str, input_ids: set[int]) -> list[dict]:
    """Parse the model output and enforce the edit-output contract, or raise ValueError."""
    try:
        parsed = json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise ValueError(f"output was not valid JSON: {exc}")

    if not isinstance(parsed, list):
        raise ValueError("output was not a JSON array")

    out_ids: list[int] = []
    for rec in parsed:
        if not isinstance(rec, dict) or "note_id" not in rec or "fields" not in rec:
            raise ValueError(f"record missing note_id/fields: {rec!r}")
        if not isinstance(rec["fields"], dict):
            raise ValueError(f"'fields' is not an object for note {rec['note_id']!r}")
        rec["fields"].pop("user_feedback", None)  # never applied here; belt-and-suspenders
        out_ids.append(int(rec["note_id"]))
        rec["note_id"] = int(rec["note_id"])

    if set(out_ids) != input_ids:
        raise ValueError(
            f"note_id mismatch: got {sorted(out_ids)}, expected {sorted(input_ids)}"
        )
    if len(out_ids) != len(input_ids):
        raise ValueError(f"duplicate note_ids in output: {out_ids}")
    return parsed


def main() -> int:
    if len(sys.argv) < 2:
        _log("edit.py: missing required <compiled-context-path>")
        print("USAGE_ERROR: missing required <compiled-context-path>", file=sys.stderr)
        return 2

    context_path = pathlib.Path(sys.argv[1])
    if not context_path.is_file():
        _log(f"edit.py: context file not found: {context_path}")
        print(f"ERROR: context file not found: {context_path}", file=sys.stderr)
        return 2

    records = json.loads(EDIT_INPUT_PATH.read_text(encoding="utf-8"))
    if not records:
        # Nothing to edit; write an empty output so confirm/apply see a consistent file.
        EDIT_OUTPUT_PATH.write_text("[]", encoding="utf-8")
        print("EDITED 0 card(s) — nothing pending")
        return 0

    input_ids = {int(r["note_id"]) for r in records}
    prompt = _PROMPT.format(
        guidelines=context_path.read_text(encoding="utf-8"),
        records=json.dumps(records, ensure_ascii=False, indent=2),
    )

    last_err = None
    for attempt in (1, 2):
        try:
            raw = call_isolated(prompt, MODEL, recursion_guard=True)
            result = _parse_and_validate(raw, input_ids)
            break
        except (ValueError, RuntimeError) as exc:
            last_err = exc
            _log(f"edit.py: attempt {attempt} failed: {exc}")
    else:
        print(f"ERROR: edit LLM produced no usable output: {last_err}", file=sys.stderr)
        return 1

    EDIT_OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False), encoding="utf-8"
    )
    _log(f"edit.py: wrote {len(result)} edited record(s) to {EDIT_OUTPUT_PATH}")
    print(f"EDITED {len(result)} card(s) — proceed to Confirm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
