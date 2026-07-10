#!/usr/bin/env python3
"""Pure-string tests for the sentinel injector — no Anki required.

Run: plugins/anki-mcp/.venv/bin/python3 \
     plugins/anki-mcp/managed_note_types/styling_infrastructure/tests/test_injection.py

Deliberately dependency-free (plain asserts, tiny runner) so it survives the coming
unified-test refactor without carrying a framework choice with it.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from managed_note_types.styling_infrastructure.fragments import FEEDBACK_MARKER  # noqa: E402
from managed_note_types.styling_infrastructure.injection import ensure_block  # noqa: E402


def test_append_when_absent():
    out = ensure_block("body{color:red}", "feedback-marker", ".x{}", "css")
    assert out.startswith("body{color:red}")
    assert "/* mnt:feedback-marker:start */" in out
    assert ".x{}" in out


def test_idempotent():
    once = ensure_block("base{}", "feedback-marker", ".x{}", "css")
    twice = ensure_block(once, "feedback-marker", ".x{}", "css")
    assert once == twice


def test_preserves_surrounding_text():
    original = "/* hand-authored */\n.card{ color: gold }\n"
    out = ensure_block(original, "feedback-marker", ".x{}", "css")
    assert out.startswith(original)  # untouched, block appended after


def test_updates_stale_block():
    v1 = ensure_block("", "feedback-marker", ".old{}", "css")
    v2 = ensure_block(v1, "feedback-marker", ".new{}", "css")
    assert ".new{}" in v2
    assert ".old{}" not in v2
    assert v2.count("mnt:feedback-marker:start") == 1


def test_html_style_and_real_fragment():
    out = ensure_block("<div>{{Front}}</div>", FEEDBACK_MARKER.id,
                       FEEDBACK_MARKER.template, "html")
    assert "<!-- mnt:feedback-marker:start -->" in out
    assert "{{#user_feedback}}" in out
    assert ensure_block(out, FEEDBACK_MARKER.id, FEEDBACK_MARKER.template, "html") == out


def _run():
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"{len(tests)} passed")


if __name__ == "__main__":
    _run()
