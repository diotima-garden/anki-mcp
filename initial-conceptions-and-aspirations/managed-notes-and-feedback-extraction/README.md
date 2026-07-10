# Managed Notes & Feedback Extraction

Big-picture initiative doc. Read this first each session; then open the subtask file you're
tackling. Keep this file the source of truth for **locked decisions** so future sessions don't
relitigate them.

## Where things stand

01, 02, 03 are done and committed (anki-mcp submodule + monorepo pointer bumps). The pipe shapes
were then revised as **D10** (aligned shapes, subset LLM output — see Locked decisions): the
extractor now returns batch-tool-shaped records and `edit-card-batch` emits only changed fields.
**Still outstanding: a live end-to-end run of `/anki-process-red-edit` on a real deck** — the
chain has only been verified piece-by-piece, and the D10 extractor change needs a Claude Code
restart before it's live. That run is the natural next step before starting 04. See
`03-red-edit-rework.md` for the full account of what changed from the original plan and why.

Also decided (not yet executed): the feedback-processing skills will eventually move into an
anki-mcp **plugin** (`.claude-plugin/` + `skills/` inside the anki-mcp repo, installed from
`plugins/` like context-compiler) so the flow ships with the server and version-locks to its
tool contracts. Separate infra step, after the e2e run.

---

## The problem

- Red-flag corrections fix one card but discard *why* it was wrong.
- The `[...]`-in-a-field convention is LLM-fragile and collides with real content.
- Extraction that should be **deterministic** is currently done by an LLM.
- Guideline gaps that caused the error are never fed back into card generation, so the same
  class of mistake recurs.

## The shift

1. **Deterministic extraction, LLM judgment.** Cards get a dedicated `user_feedback` field.
   A deterministic anki-mcp tool extracts feedback → JSON. The LLM only does what it's good at:
   applying the edit and proposing guideline improvements.
2. **Close the loop.** After edits are applied, propose improvements to the deck's *compiled
   context* so the same error is prevented at generation time — landed in source layers via the
   existing `context-compiler:reverse-propagate`.

## Smart-MCP boundary

anki-mcp gains awareness of **managed note types** — models carrying `user_feedback` + `log`
fields. It owns the *mechanism*; the project owns the *policy*.

| Concern | Owner |
|---|---|
| Field contract (`user_feedback`, `log`), ensure-fields, extraction, flag-setting | **anki-mcp** |
| *Which* note types are managed | **project** (injected into anki-mcp, never hardcoded) |

anki-mcp is a standalone public submodule — keeping policy out preserves its reusability.

## Field contract

- **`user_feedback`** — user-written input. Non-empty = "process me". Cleared after processing.
- **`log`** — append-only history (creation source, edit transitions). Hidden: not referenced in
  card templates, so it never renders on a card.

## Lifecycle (current state — 01–03 shipped, 04 not started)

```
user types feedback in `user_feedback`
   → extract_feedback(deck): sets RED flag (visual convenience only) + emits records
     already in update_note_fields_batch's input shape: {note_id, new_fields, model},
     new_fields = every field except `log` (feedback still inside, D10)
   → edit-card-batch: LLM applies each record's user_feedback,
     returns [{note_id, new_fields}] (new_fields = ONLY changed fields + user_feedback: "")
   → update_note_fields_batch: diffs each note's new_fields against current values,
     writes only what changed, appends to `log`, flips flag GREEN — one MCP call for the batch
   → [not built] refine: LLM proposes compiled-context chunks → user approves subset
   → [not built] apply chunks to .compiled.md → reverse-propagate to source layers
```

## Locked decisions

| # | Decision |
|---|---|
| D1 | Trigger is **`user_feedback` non-empty**, not the flag. |
| D2 | The extractor **sets the RED flag itself**, purely for visual convenience in Anki's browser. |
| D3 | The extractor is an **MCP tool in the anki-mcp repo** (deterministic Python), reused by red-edit and refine. |
| D4 | anki-mcp is **"smart"**: aware of `user_feedback` + `log` fields = managed models. |
| D5 | **Mechanism in anki-mcp; the managed-model set is project policy**, injected (config/param), never hardcoded in anki-mcp. |
| D6 | Two fields, two lifecycles: `user_feedback` (input, cleared) and `log` (append-only history). |
| D7 | Refine still writes to `.compiled.md` then runs `reverse-propagate` — unchanged from earlier plan. |
| D8 | Adding fields to existing note types is acceptable; new users need a **bootstrap** step ("MCP ensures your note types have the managed fields"). |
| D9 | `update_note_fields` (anki-mcp) accepts **any subset of a note's fields — including all of them** — and diffs internally against current values before writing/logging. Added mid-03; with D10 this is exactly what lets `edit-card-batch` emit only the fields it changed. A `update_note_fields_batch` tool loops this with per-note error isolation. Generalizes the tool beyond red-edit's original ask. |
| D10 | **Aligned pipe shapes, subset output.** `extract_feedback` returns records in `update_note_fields_batch`'s input shape — `{note_id, new_fields, model}`, `new_fields` = every field except `log`, pending feedback in place, never special-cased. `edit-card-batch` (the LLM step) emits **only the fields it changed** plus the mandatory `user_feedback: ""` — unchanged values never round-trip the LLM, so they cannot suffer copy-drift. An unprocessed record forwarded verbatim is rejected by the batch tool (non-empty `user_feedback`): the identity transform fails loudly. The rich record (`+ card_ids, tags, extracted_at`) goes only to the opt-in JSONL artifact for refine (04). |

## Subtasks

| File | Subtask | Depends on | Status |
|---|---|---|---|
| `01-managed-fields-foundation.md` | Field contract + bootstrap + project config for the managed set + onboarding | — | ✓ done |
| `02-feedback-extractor.md` | Deterministic anki-mcp extraction tool → JSON + auto RED flag | 01 | ✓ done |
| `03-red-edit-rework.md` | red-edit consumes JSON; clears feedback, appends log, flips flag | 02 | ✓ done (skill-level e2e run still unverified — see file) |
| `04-refine-context.md` | New `anki-refine-context` skill: chunks → `.compiled.md` → reverse-propagate | 02 (03 useful) | not started |
| `05-card-log.md` | The `log` field: append-only history, retrospection/rollback (was "Task B") | 01 | edit-side done (03); creation-side (`anki-add-cards`) not started |

## Sequencing

```
01 ──► 02 ──► 03
        └───► 04
01 ──────────► 05
```

Start with **01** (foundation) — everything depends on the field contract and the managed-model
config. Then **02** (extractor) unblocks both 03 and 04. **05** can proceed after 01 independently.

## Cross-cutting notes

- **Submodule workflow:** anki-mcp is a separate repo/submodule. Any change there follows the
  established flow: commit upstream in anki-mcp → bump the monorepo's `anki-mcp` pointer.
- **Existing anki-mcp primitives** to build on: `add_model_field`, `model_field_names`,
  `update_note_fields` (now diff-internal, any-subset-of-fields, D9), `update_note_fields_batch`
  (batch apply, per-note error isolation), `extract_feedback` (02), `set_card_flag`, `find_notes`,
  `notes_info`, `get_flagged_notes`.
