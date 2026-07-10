"""
Feedback extraction for managed note types.

Not an MCP tool — extract_feedback_records() is a plain function, called only by
skills/process-user-feedback-on-deck/extract.py (a skill-local CLI). Kept out of the
tool list because it has exactly one caller and would otherwise sit in every
session's context for no benefit.
"""
from datetime import datetime, timezone

from core import _call, _log, FLAGS


def extract_feedback_records(deck: str) -> list[dict]:
    """
    Find all notes in `deck` with non-empty `user_feedback`.

    Side effect: sets RED flag on every card belonging to a matched note (D2).
    Returns one rich record per matched note; empty list if no matches.
    Each record carries the current value of every note field except `log` —
    `user_feedback` (non-empty by the filter) stays in place like any other field,
    never special-cased.
    """
    note_ids: list[int] = _call("findNotes", query=f'deck:"{deck}"')
    if not note_ids:
        return []

    infos: list[dict] = _call("notesInfo", notes=note_ids)

    records = []
    for info in infos:
        if not info["fields"].get("user_feedback", {}).get("value", "").strip():
            continue

        card_ids: list[int] = info.get("cards", [])
        for cid in card_ids:
            _call("setSpecificValueOfCard", card=cid, keys=["flags"], newValues=[FLAGS["red"]])

        fields = {
            name: fdata["value"]
            for name, fdata in info["fields"].items()
            if name != "log"
        }

        records.append({
            "note_id": info["noteId"],
            "card_ids": card_ids,
            "model": info["modelName"],
            "fields": fields,
            "tags": info["tags"],
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        })

    _log(f"extract_feedback: {len(records)} notes with feedback in '{deck}'")
    return records
