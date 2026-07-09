---
name: edit-card-batch
description: Apply each record's user_feedback to its fields, emitting only the changed fields. Internal skill — invoked by process-user-feedback-on-deck only. ARGUMENTS: deck context markdown, followed by a JSON array of records as returned by mcp__anki__extract_feedback.
context: fork
disable-model-invocation: false
user-invocable: false
---

$ARGUMENTS

For each record in the JSON array above:
- `new_fields` holds every field of the note — empty fields included; they are legitimate
  edit targets — plus the pending `user_feedback` instruction.
- Interpret `user_feedback` as an edit instruction for this card. It is card-level, not
  per-field — decide which field(s) it applies to, guided by the deck context's editing
  guidelines above and the record's `model`.

Output ONLY a JSON array, one object per input record, same order, none dropped:

```json
[{"note_id": <int>, "new_fields": {<ONLY the fields you changed>, "user_feedback": ""}}]
```

Output rules:
- `new_fields` contains ONLY the fields whose value you changed — never copy through an
  unchanged field.
- Every record's `new_fields` carries `"user_feedback": ""` — it marks the feedback processed.
- If the feedback warrants no field change, the record is just
  `{"note_id": <int>, "new_fields": {"user_feedback": ""}}`.

No preamble, no commentary, no markdown code fence, no explanation — the output must parse as
JSON on its own.
