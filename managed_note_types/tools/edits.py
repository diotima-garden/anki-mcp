"""
Field updates for managed note types — supersedes the plain update_note_fields tool.
"""
import json
from datetime import datetime, timezone

from core import mcp, _call, _log, FLAGS
from managed_note_types import MANAGED_FIELDS


@mcp.tool()
def update_note_fields(note_id: int, new_fields: dict) -> None:
    """
    Update one or more fields on an existing note in-place.

    Supply only the fields you want to change — omitted fields are untouched.

    Examples:
      Basic card:  new_fields={"Front": "new question", "Back": "new answer"}
      Cloze card:  new_fields={"Text": "{{c1::new cloze}}", "Back Extra": "hint"}

    Field names must match the note's model exactly (case-sensitive).

    For managed note types (carrying `user_feedback` + `log`), every changed field is
    automatically diffed against its prior value and appended as one JSON log entry —
    no separate logging call needed. Non-managed notes are updated plainly, unchanged
    from the old behavior.

    To process a card's feedback, include `"user_feedback": ""` in new_fields alongside
    the domain field changes. Since user_feedback is just another field being changed, it
    gets diffed into the log entry like everything else (old = the original feedback text,
    new = "") — and its presence in new_fields is also the signal that flips the note's
    cards from RED to GREEN.

    user_feedback may only ever be cleared this way — its new value must be "". This field
    is user-authored input; nothing programmatic may set it to non-empty text.
    """
    if new_fields.get("user_feedback", "") != "":
        raise ValueError("user_feedback may only be set to '' — it is user-authored input")

    info = _call("notesInfo", notes=[note_id])
    if not info:
        raise ValueError(f"note_id {note_id} not found")
    current_fields = info[0]["fields"]

    is_managed = all(f in current_fields for f in MANAGED_FIELDS)
    if not is_managed:
        _log(f"update_note_fields: note_id={note_id}, fields={list(new_fields)}")
        _call("updateNoteFields", note={"id": note_id, "fields": new_fields})
        return

    log_entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        **{
            name: {"old": current_fields.get(name, {}).get("value", ""), "new": new_value}
            for name, new_value in new_fields.items()
        },
    }
    current_log = current_fields.get("log", {}).get("value", "")
    entry_line = json.dumps(log_entry, ensure_ascii=False)
    new_log = f"{current_log}\n{entry_line}" if current_log else entry_line

    write_fields = {**new_fields, "log": new_log}
    _call("updateNoteFields", note={"id": note_id, "fields": write_fields})

    if "user_feedback" in new_fields:
        for card_id in info[0].get("cards", []):
            _call("setSpecificValueOfCard", card=card_id, keys=["flags"], newValues=[FLAGS["green"]])

    _log(f"update_note_fields: note_id={note_id}, fields={list(new_fields)}, managed=True")
