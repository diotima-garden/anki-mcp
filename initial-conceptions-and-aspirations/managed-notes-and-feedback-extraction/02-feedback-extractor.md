# 02 — Feedback extractor (deterministic anki-mcp tool) ✓ DONE

*Depends on: 01 (field contract + managed-model set).*

## Goal

A deterministic anki-mcp tool that finds cards whose `user_feedback` is non-empty, emits a
structured JSON payload, and flags them RED for visual convenience — the single shared extraction
primitive for both red-edit (03) and refine (04). No LLM in this step (D3).

## Design

**New anki-mcp tool**, e.g. `extract_feedback(models | deck)`:
1. Find notes in the managed models (or a given deck) with non-empty `user_feedback`
   (`find_notes` + `notes_info`, or a query).
2. For each, build a record: `{note_id, card_id, model, fields, user_feedback, tags}`.
3. **Set the RED flag** on each matched card (`set_card_flag`) — visual only (D2); the trigger is
   the field, not the flag (D1).
4. Return the JSON list (and optionally write it next to the deck's `.compiled.md` if a path is
   given, so a later standalone refine can read it).

Deterministic and side-effecting only in the flag-setting sense; the payload is pure data for the
LLM steps to reason over.

## Done when

- anki-mcp exposes `extract_feedback(...)` returning the record schema above, committed upstream +
  pointer bumped.
- Running it on Spanish returns exactly the cards with non-empty `user_feedback` and RED-flags
  them; cards with empty feedback are untouched.

## What was built (actual implementation)

`mcp__anki__extract_feedback(deck, output_path=None) -> list[dict]` in
`anki-mcp/managed_note_types/tools/feedback.py`:

- Scoped **by `deck`** (not by model set) — resolves the first open question in favor of the
  simple current single-deck flow.
- Finds notes in that deck with non-empty `user_feedback`, sets the RED flag on every one of their
  cards (D2), and returns one record per note in **`update_note_fields_batch`'s input shape**
  (D10): `{note_id, new_fields, model}`. `new_fields` carries **full field values** (not
  snippets) for every field except `log` — empty fields included, and the pending `user_feedback`
  in place like any other field, never special-cased.
- **Both** return and persist: always returns the record list; if `output_path` is given, appends
  a *rich* record per note (`+ card_ids, tags, extracted_at`) as one JSONL line (accumulates
  across runs, never overwrites). No caller passes `output_path` yet — 03 (red-edit) doesn't need
  it, and 04 (refine) hasn't been built.

## Open questions (resolved above)

- ~~Scope by deck or models?~~ → deck.
- ~~Return vs persist?~~ → both, persist is opt-in via `output_path`.
- ~~Snippets vs full field values?~~ → full values.
