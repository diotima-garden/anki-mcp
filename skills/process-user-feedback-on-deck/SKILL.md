---
name: process-user-feedback-on-deck
description: Find cards with pending feedback and apply edit instructions
disable-model-invocation: false
---

Find all cards with non-empty `user_feedback` in a deck, apply the feedback as an edit, then
clear it (which flips the flag to GREEN). This skill only directs the flow.

**Usage:** `/anki-mcp:process-user-feedback-on-deck <context file path> <ankiDeckName>`

## Extract

```bash
plugins/anki-mcp/.venv/bin/python3 plugins/anki-mcp/skills/process-user-feedback-on-deck/extract.py "<ankiDeckName>" "<context file path>.feedback.jsonl"
```

Read `/tmp/anki-mcp-feedback-edit-input.json`. If it's `[]`: report "No cards with pending
feedback found in <ankiDeckName>." and stop.

## Edit

Invoke `/anki-mcp:edit-card-batch` with `<context file path>` as `$ARGUMENTS`.

## Confirm

Read `/tmp/anki-mcp-feedback-edit-input.json` (old values, `fields`) and
`/tmp/anki-mcp-feedback-edit-output.json` (new values, `new_fields`). Show each proposed
change, one numbered entry per record:

```
N. [first-field snippet]
   feedback: "<fields.user_feedback from edit-input>"
   <field>: "<old value>" → "<new value>"
   <field>: "<old value>" → "<new value>"
```

List every changed field.

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
