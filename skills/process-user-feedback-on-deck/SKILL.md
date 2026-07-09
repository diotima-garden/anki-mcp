---
name: process-user-feedback-on-deck
description: Find cards with pending feedback and apply edit instructions
disable-model-invocation: false
---

Find all cards with non-empty `user_feedback` in a deck, apply the feedback as an edit, then
clear it (which flips the flag to GREEN). This skill only directs the flow — records pass
between steps verbatim, shapes are owned by the tools themselves.

**Usage:** `/anki-mcp:process-user-feedback-on-deck <compiled context file path> <ankiDeckName>`

## Extract

Call `mcp__anki__extract_feedback` with `deck=<ankiDeckName>`.
If empty: report "No cards with pending feedback found in <ankiDeckName>." and stop.

## Edit

Invoke `/anki-mcp:edit-card-batch` once with all records: pass the content of
`<compiled context file path>`, a blank line, then the raw JSON array from Extract.

## Confirm

Show a numbered list of proposed changes (pair each returned field with its old value from
the Extract records; `user_feedback` clearing needs no mention). Ask:
**"Apply these N change(s)? [yes / no]"** Drop skipped entries from the batch.

## Apply

Call `mcp__anki__update_note_fields_batch` with the confirmed entries as `updates`, exactly
as edit-card-batch returned them. One call for the whole batch; managed notes get `log`
appended and flags flipped RED → GREEN automatically. Skipped cards stay RED and are picked
up by the next run.

## Report

From the batch tool's per-note result:

```
Processed N card(s):
  ✓ [first-field snippet] — [one-line summary from "changed" fields]
  ⚠ [first-field snippet] — skipped (user skipped)
  ⚠ [first-field snippet] — failed ("error" message)
```
