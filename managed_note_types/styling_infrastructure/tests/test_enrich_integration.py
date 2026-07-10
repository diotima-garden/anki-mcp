#!/usr/bin/env python3
"""Live-Anki check: enrich a throwaway model and assert idempotent injection.

Run: plugins/anki-mcp/.venv/bin/python3 \
     plugins/anki-mcp/managed_note_types/styling_infrastructure/tests/test_enrich_integration.py

Creates (or reuses) a zz-prefixed dummy model carrying a user_feedback field, adds one
dummy note, enriches, and verifies the marker landed in CSS + both template sides and
that a second pass is a no-op. Deletes the dummy note at the end; the dummy model is
left behind (AnkiConnect exposes no model delete) but is clearly namespaced.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from core import _call  # noqa: E402
from managed_note_types.styling_infrastructure.enrich import enrich_model  # noqa: E402

MODEL = "zz-test-styling"
DECK = "zz-test-styling"


def _ensure_model():
    if MODEL not in _call("modelNames"):
        _call(
            "createModel",
            modelName=MODEL,
            inOrderFields=["Front", "Back", "user_feedback", "log"],
            cardTemplates=[{"Name": "Card 1", "Front": "{{Front}}",
                            "Back": "{{FrontSide}}<hr>{{Back}}"}],
            css=".card{}",
        )


def _run():
    _ensure_model()
    _call("createDeck", deck=DECK)
    note = {"deckName": DECK, "modelName": MODEL,
            "fields": {"Front": "q", "Back": "a", "user_feedback": "fix me"}}
    note_ids = []
    if _call("canAddNotes", notes=[note])[0]:
        note_ids.append(_call("addNote", note=note))

    assert enrich_model(MODEL, {"name": MODEL}) is True, "first enrich should write"
    assert enrich_model(MODEL, {"name": MODEL}) is False, "second enrich must be a no-op"

    css = _call("modelStyling", modelName=MODEL)["css"]
    assert "mnt-feedback-marker" in css
    tmpl = _call("modelTemplates", modelName=MODEL)["Card 1"]
    assert "{{#user_feedback}}" in tmpl["Front"]
    assert "{{#user_feedback}}" in tmpl["Back"]

    if note_ids:
        _call("deleteNotes", notes=note_ids)
    print("integration: passed")


if __name__ == "__main__":
    _run()
