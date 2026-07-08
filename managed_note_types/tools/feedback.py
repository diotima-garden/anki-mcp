"""
Feedback extraction for managed note types.

Core logic lives in extract_feedback_records(); the MCP tool is a thin wrapper
that adds JSONL persistence and the MCP contract.
"""
import json
import pathlib
from datetime import datetime, timezone

from core import mcp, _call, _log, FLAGS
from managed_note_types import MANAGED_FIELDS


def extract_feedback_records(deck: str) -> list[dict]:
    """
    Find all notes in `deck` with non-empty `user_feedback`.

    Side effect: sets RED flag on every card belonging to a matched note (D2).
    Returns a list of records; empty list if no matches.
    """
    note_ids: list[int] = _call("findNotes", query=f'deck:"{deck}"')
    if not note_ids:
        return []

    infos: list[dict] = _call("notesInfo", notes=note_ids)

    records = []
    for info in infos:
        feedback = info["fields"].get("user_feedback", {}).get("value", "").strip()
        if not feedback:
            continue

        card_ids: list[int] = info.get("cards", [])
        for cid in card_ids:
            _call("setSpecificValueOfCard", card=cid, keys=["flags"], newValues=[FLAGS["red"]])

        domain_fields = {
            name: fdata["value"]
            for name, fdata in info["fields"].items()
            if name not in MANAGED_FIELDS
        }

        records.append({
            "note_id": info["noteId"],
            "card_ids": card_ids,
            "model": info["modelName"],
            "fields": domain_fields,
            "user_feedback": feedback,
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
      - Emits a record: {note_id, card_ids, model, fields, user_feedback, tags, extracted_at}.

    `deck` is required. Missing deck raises ValueError.

    If `output_path` is provided, each record is appended as a JSON line (JSONL)
    to that file — never overwritten. Accumulates feedback across runs so that
    a later refine-context pass can process them in batch.

    Return value is always the full list of matched records (used directly by red-edit).
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

    return records
