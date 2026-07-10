---
name: process-user-feedback-on-deck
description: Find cards with pending feedback and apply edit instructions
disable-model-invocation: false
---

Find all cards with non-empty `user_feedback` in a deck, apply the feedback as an edit.
This skill only directs the flow.

**Usage:** `/anki-mcp:process-user-feedback-on-deck <context file path> <ankiDeckName>`

## Extract

```bash
plugins/anki-mcp/.venv/bin/python3 plugins/anki-mcp/skills/process-user-feedback-on-deck/extract.py "<ankiDeckName>" "<context file path>.feedback.jsonl"
```

- in case of a **non-zero exit / failed call** = genuine error (usage or exception). Stop the execution.

## Edit

```bash
plugins/anki-mcp/.venv/bin/python3 plugins/anki-mcp/skills/process-user-feedback-on-deck/edit.py "<context file path>"
```

edit.py internally calls an LLM to apply each card's `user_feedback` and writes the
changed fields itself. A **non-zero exit** = genuine error (usage, LLM failure, or output
that failed validation). Stop the execution.

## Confirm

```bash
plugins/anki-mcp/.venv/bin/python3 plugins/anki-mcp/skills/process-user-feedback-on-deck/confirm.py
```

confirm.py prints the proposed changes, one numbered entry per record (first field, the
`user_feedback` instruction, and each changed field as `old → new`, with the record's
`note_id`). Show that output to the user verbatim.

Ask: **"Apply these N change(s)? [yes / no]"** Note the `note_id` of any skipped entries.

## Apply

```bash
plugins/anki-mcp/.venv/bin/python3 plugins/anki-mcp/skills/process-user-feedback-on-deck/apply.py <skipped note_id ...>
```

## Report

From apply.py's stdout JSON (`{note_id: {"changed": [...]} | {"error": "..."}}`):

```
Processed N card(s):
  ✓ [first-field snippet] — [one-line summary from "changed" fields, excluding user_feedback]
  ⚠ [first-field snippet] — skipped (user skipped)
  ⚠ [first-field snippet] — failed ("error" message)
```
