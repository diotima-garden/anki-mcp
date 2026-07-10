# 03 — red-edit rework ✓ DONE

*Depends on: 02 (extractor). Files: `.claude/skills/anki-process-red-edit/SKILL.md`,
`.claude/skills/edit-card-batch/SKILL.md` (both builder mode).*

## Goal

Rework `anki-process-red-edit` to consume the extractor's JSON instead of LLM-parsing `[...]`,
apply the edit (LLM judgment), then update managed fields and the flag.

## What was built (actual implementation — differs from the original plan below)

The original plan (kept verbatim further down for history) had red-edit itself building a custom
per-card text block for the edit step, and manually doing three separate write operations (fields,
clear feedback, append log, flip flag) per card. Mid-implementation this shifted to a simpler,
more robust design after questioning why the LLM step and the write step should each reinvent
plumbing the MCP layer could own instead:

1. **`extract_feedback(deck)`** (02) → JSON records, passed **raw, unreformatted** into step 2.
   Since D10 the records are already in `update_note_fields_batch`'s input shape
   (`{note_id, new_fields, model}`, feedback inside `new_fields`).
2. **`/edit-card-batch`** (renamed from `edit-card`) — now JSON-in/JSON-out instead of a
   custom anchor-block format. It receives the extractor's records directly (no translation layer
   in red-edit) and returns `[{"note_id", "new_fields"}]`, where `new_fields` carries **only the
   fields the edit changed** plus `"user_feedback": ""` (D10; originally the complete fields dict —
   changed so unchanged values never round-trip the LLM and can't suffer copy-drift). The rename
   reflects that this skill is now hard-wired to the extractor's JSON shape rather than being a
   generic anchor-format editor — it was never reused anywhere else anyway
   (`disable-model-invocation`/`user-invocable: false`).
3. **User confirmation** — red-edit diffs each returned record against the input `fields` itself,
   for display only, to build the numbered proposed-changes list.
4. **Apply, one MCP call for the whole batch** — `update_note_fields_batch(updates)`, not a
   per-card loop. This only works because of a companion change to the underlying single-note
   tool (also in anki-mcp, `managed_note_types/tools/edits.py`):
   - `update_note_fields` was generalized to accept **any subset of a note's fields — including
     all of them** — and now diffs internally against the note's current values before writing or
     logging anything. A field round-tripped unchanged is silently dropped; a pure no-op call
     writes nothing at all.
   - This is what lets edit-card-batch return only the fields it changed (D10), and is also what
     makes `"user_feedback": ""` self-documenting as "mark processed" — passing it is free when
     unchanged, and meaningful (diffed + logged + flag-flipped) when it actually clears real
     feedback text. It's also the loud-failure guard: a record forwarded with its feedback still
     non-empty is rejected per-note by the batch tool.
   - `update_note_fields_batch(updates)` loops this per-note logic, **continuing past per-note
     failures** (bad `note_id`, rejected `user_feedback`) and returning a per-note
     `{"changed": [...]} | {"error": "..."}` report instead of aborting the whole batch.
5. **Report** — built from the batch tool's per-note-id results.

Naming: the skill name/trigger language shifted from "RED-flagged" to "cards with feedback"; the
flag is a *view* set by the extractor, not the trigger (D1/D2) — matches the original plan's intent.

**Not yet done:** the full chain (extract → edit-card-batch → batch apply) has only been verified
at the MCP layer with hand-seeded dummy notes (`edits.py`'s diff/batch logic). The skill files
themselves have not been exercised end-to-end via an actual `/anki-process-red-edit` run — that's
the first thing worth doing in the next session, ideally on a real deck with a real feedback note.

## Done when

- [x] red-edit no longer parses `[...]`; it reads the extractor JSON.
- [x] After a run: edited fields updated, `user_feedback` cleared, `log` appended, flag GREEN.
- [x] The old bracket-stripping logic is gone; docs/usage updated.
- [ ] End-to-end live run of `/anki-process-red-edit` on a real deck (see "Not yet done" above).

## Open questions (resolved, except the last)

- ~~Does red-edit write `log` directly, or delegate to a shared helper?~~ → Neither, in the sense
  planned: the diff-and-log logic lives **inside anki-mcp's `update_note_fields`** itself, not in a
  project-level skill helper. Any caller going through that tool gets consistent log formatting for
  free — red-edit today, add-cards/refine later if they ever touch fields through this path.
- **Still open:** keep a separate `.edit-ledger.json` artifact for refine (04), or does refine
  re-run the extractor / read `log`? Decide with 04. The actual `log` entry format is documented in
  `05-card-log.md` (JSON-per-line, not the human `edited <ts> | ...` line originally sketched there).

---

## Original plan (kept for history — see "What was built" above for what actually shipped)

Replace current Steps 1–2 (find flagged + parse brackets) with:
1. Call the **extractor tool** (02) → JSON of cards with non-empty `user_feedback`.
2. **Apply edits** — LLM interprets each card's `user_feedback` and edits the relevant fields
   (this is the retained `edit-card` judgment step; feedback is now card-level, LLM decides which
   fields to touch).
3. **User confirmation** — as today.
4. **On apply, per card:**
   - `update_note_fields` with the changed fields;
   - **clear `user_feedback`** (processed);
   - **append to `log`** an edit entry (`edited <ts> | <feedback> | <field>: before→after`);
   - flip flag RED → **GREEN** (`set_card_flag`).
5. **Report** — as today.
