"""
Field updates for managed note types — supersedes the plain update_note_fields tool.
"""
import json
from datetime import datetime, timezone

from core import mcp, _call, _log, FLAGS
from managed_note_types import MANAGED_FIELDS


def _update_note_fields(note_id: int, new_fields: dict) -> list[str]:
    """
    Core update logic, shared by the single-note and batch tools.

    Accepts any subset of the note's fields — values equal to the note's current
    value are dropped before anything is written or logged. Returns the list of
    field names actually changed (empty list means no-op, nothing written).
    """
    if new_fields.get("user_feedback", "") != "":
        raise ValueError("user_feedback may only be set to '' — it is user-authored input")

    info = _call("notesInfo", notes=[note_id])
    if not info or not info[0]:
        raise ValueError(f"note_id {note_id} not found")
    current_fields = info[0]["fields"]

    changed = {
        name: value
        for name, value in new_fields.items()
        if value != current_fields.get(name, {}).get("value", "")
    }
    if not changed:
        return []

    is_managed = all(f in current_fields for f in MANAGED_FIELDS)
    if not is_managed:
        _log(f"update_note_fields: note_id={note_id}, fields={list(changed)}")
        _call("updateNoteFields", note={"id": note_id, "fields": changed})
        return list(changed)

    log_entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        **{
            name: {"old": current_fields.get(name, {}).get("value", ""), "new": new_value}
            for name, new_value in changed.items()
        },
    }
    current_log = current_fields.get("log", {}).get("value", "")
    entry_line = json.dumps(log_entry, ensure_ascii=False)
    new_log = f"{current_log}\n{entry_line}" if current_log else entry_line

    write_fields = {**changed, "log": new_log}
    _call("updateNoteFields", note={"id": note_id, "fields": write_fields})

    if "user_feedback" in changed:
        for card_id in info[0].get("cards", []):
            _call("setSpecificValueOfCard", card=card_id, keys=["flags"], newValues=[FLAGS["green"]])

    _log(f"update_note_fields: note_id={note_id}, fields={list(changed)}, managed=True")
    return list(changed)


@mcp.tool()
def update_note_fields(note_id: int, new_fields: dict) -> None:
    """
    Update one or more fields on an existing note in-place.

    Supply any subset of the note's fields — including all of them. Values that
    already match the note's current value are silently ignored: no write, no log
    entry, no flag change for a call that changes nothing.

    Examples:
      Basic card:  new_fields={"Front": "new question", "Back": "new answer"}
      Cloze card:  new_fields={"Text": "{{c1::new cloze}}", "Back Extra": "hint"}

    Field names must match the note's model exactly (case-sensitive).

    For managed note types (carrying `user_feedback` + `log`), every field that actually
    changes is diffed against its prior value and appended as one JSON log entry — no
    separate logging call needed. Non-managed notes are updated plainly, unchanged from
    the old behavior.

    To process a card's feedback, include `"user_feedback": ""` in new_fields alongside
    the domain field changes. If the note's feedback was already empty this is a no-op
    for that field; if it was non-empty, clearing it is diffed into the log like any other
    change and flips the note's cards from RED to GREEN.

    user_feedback may only ever be cleared this way — its new value must be "". This field
    is user-authored input; nothing programmatic may set it to non-empty text.
    """
    _update_note_fields(note_id, new_fields)


def update_note_fields_batch(updates: list[dict]) -> dict:
    """
    Apply update_note_fields to many notes in one call.

    Not an MCP tool — called only by skills/process-user-feedback-on-deck/apply.py (a
    skill-local CLI). Kept out of the tool list: it has exactly one caller and would
    otherwise sit in every session's context for no benefit.

    `updates` is a list of {"note_id": int, "new_fields": dict}, same semantics as
    update_note_fields per item (any subset of fields; unchanged values are ignored).

    Continues past per-note failures rather than aborting the batch — a bad note_id
    or a rejected user_feedback value fails only that entry.

    Returns {note_id (str): {"changed": [field, ...]} | {"error": "<message>"}}.
    Note IDs are stringified because JSON object keys must be strings.
    """
    results: dict[str, dict] = {}
    for update in updates:
        note_id = update["note_id"]
        try:
            changed = _update_note_fields(note_id, update["new_fields"])
            results[str(note_id)] = {"changed": changed}
        except Exception as e:
            results[str(note_id)] = {"error": str(e)}
    return results
