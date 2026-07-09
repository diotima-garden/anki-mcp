# 05 — Card log field (was "Task B")

*Depends on: 01 (the `log` field is part of the managed contract). Analysis-first; do not rush to
implementation.*

## Goal

An append-only, hidden per-card `log` recording lifecycle events — so you can later assess
progress, bootstrap/reduce the deck as your knowledge or tooling improves, and roll changes back
without a backup.

## Why native Anki isn't enough

Anki natively stores the **review log (revlog)** — timing/ease/interval per review — and a per-note
`mod` timestamp. It has **no field-level edit history and no record of what a card was generated
from.** So the instinct is correct: native history does not support "what changed field-by-field"
or "which source produced this card."

## Events to log

- `created <ts> | source: <deck spec / input string>` — **not yet implemented.** `anki-add-cards`
  does not currently write a creation entry to `log`.
- **Edit events — implemented, format differs from the original sketch below.** `03` shipped one
  JSON object per line (not the human `edited <ts> | ...` line originally planned), written by
  `_update_note_fields` in `anki-mcp/managed_note_types/tools/edits.py`:

  ```json
  {"date": "<iso8601 utc>", "<changed field>": {"old": "<before>", "new": "<after>"}, ...}
  ```

  One key per **actually-changed** field (unchanged fields supplied in the same call are dropped
  before logging — see `03-red-edit-rework.md`). `user_feedback` appears as just another key when
  it's the one being cleared, e.g. `{"date": "...", "Back": {"old": "x", "new": "y"},
  "user_feedback": {"old": "fix this", "new": ""}}`. Multiple entries accumulate newline-separated
  in the `log` field over a note's lifetime.

Format: one parseable line per event (machine-reversible; JSON per line for edits). Hidden — `log`
is not referenced in card templates, so it never renders.

## The coupling decision — LOCKED (01)

- `Production` is Spanish-only → `log` is low-risk.
- `Cloze` is a global Anki model → **option 2 chosen**: add `log` globally. Empty on unrelated
  notes; trades purity for simplicity. Both fields are already being added by bootstrap (01).

- **Unify the write-path with 03/add-cards:** both edit and creation events append to the same
  `log` via one shared helper — don't add a separate logging mechanism.
  **Partially done:** the edit side's write-path lives in anki-mcp's `update_note_fields` itself
  (see `03-red-edit-rework.md`), so any future caller that touches fields through that tool gets
  logging for free. The creation side (`anki-add-cards` writing a `created` entry) doesn't exist
  yet, so "unified" is aspirational until that's built — when it is, it should call into the same
  diff/append logic rather than reimplementing it.

## Done when (future)

- [x] Managed models carry a hidden `log`.
- [x] Edit events append consistently (03, JSON-per-line format documented above).
- [ ] Creation events append consistently (`anki-add-cards` — not started).
- [ ] A documented way to read/parse the log for retrospection exists (log format is now
  documented here; no reader/parser tool built yet).
