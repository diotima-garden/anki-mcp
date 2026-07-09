---
name: edit-card-batch
description: Apply each record's user_feedback to its fields, emitting only the changed fields. Internal skill — invoked by process-user-feedback-on-deck only. ARGUMENTS: deck context file path.
context: fork
disable-model-invocation: false
user-invocable: false
---

Read `$ARGUMENTS` for the deck's editing guidelines.

Read `/tmp/anki-mcp-feedback-edit-input.json` — a JSON array of `{note_id, fields, model}`
records. `fields` holds every current field value of the note, empty ones included, plus the
pending `user_feedback` instruction.

For each record:
- Interpret `user_feedback` as an edit instruction for this card. It is card-level, not
  per-field — decide which field(s) it applies to, guided by the deck context and the
  record's `model`.
- Determine `new_fields`: ONLY the fields whose value you changed. Never copy through an
  unchanged field. If the feedback warrants no field change, `new_fields` is `{}`.

If `/tmp/anki-mcp-feedback-edit-output.json` already exists, Read it first (ignore its
contents) — this satisfies the Write tool's read-first requirement.

Write the result to `/tmp/anki-mcp-feedback-edit-output.json` — a JSON array, one object per
input record, same order, none dropped:

```json
[{"note_id": <int>, "new_fields": {<ONLY the fields you changed>}}]
```
