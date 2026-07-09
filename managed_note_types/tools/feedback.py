"""
Feedback extraction for managed note types.

Core logic lives in extract_feedback_records(); the MCP tool is a thin wrapper
that adds JSONL persistence and the MCP contract.
"""
import json
import pathlib
from datetime import datetime, timezone

from core import mcp, _call, _log, FLAGS


def extract_feedback_records(deck: str) -> list[dict]:
    """
    Find all notes in `deck` with non-empty `user_feedback`.

    Side effect: sets RED flag on every card belonging to a matched note (D2).
    Returns one rich record per matched note; empty list if no matches.
    `new_fields` carries every note field except `log` — `user_feedback` (non-empty
    by the filter) stays in place like any other field, never special-cased.
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

        new_fields = {
            name: fdata["value"]
            for name, fdata in info["fields"].items()
            if name != "log"
        }

        records.append({
            "note_id": info["noteId"],
            "card_ids": card_ids,
            "model": info["modelName"],
            "new_fields": new_fields,
            "tags": info["tags"],
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        })

    _log(f"extract_feedback: {len(records)} notes with feedback in '{deck}'")
    return records


@mcp.tool()
def extract_feedback(deck: str, output_path: str | None = None) -> list[dict]:
    """
    Extract feedback from all notes in a deck whose `user_feedback` field is non-empty.

    For each matched note:
      - Sets RED flag on all its cards (visual convenience, D2).
      - Returns a record: {note_id, new_fields, model}. `new_fields` carries every
        note field except `log` — domain fields (empty ones included) and the
        pending `user_feedback` text. `model` is advisory context for the editor.

    The return shape is deliberately the input shape of update_note_fields_batch:
    once an editing step blanks `user_feedback` (and edits domain fields), records
    pass straight through. A record piped through *unprocessed* is rejected there,
    because its `user_feedback` is still non-empty — failures are loud, never silent.

    `deck` is required. Missing deck raises ValueError.

    If `output_path` is provided, a rich record per note — the return record plus
    {card_ids, tags, extracted_at} — is appended as a JSON line (JSONL), never
    overwritten. Accumulates feedback across runs so that a later refine-context
    pass can process them in batch.
    """
    if not deck:
        raise ValueError("deck is required")

    records = extract_feedback_records(deck)

    if output_path and records:
        p = pathlib.Path(output_path)
        with p.open("a", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        _log(f"extract_feedback: appended {len(records)} records to {output_path}")

    return [
        {"note_id": r["note_id"], "new_fields": r["new_fields"], "model": r["model"]}
        for r in records
    ]
