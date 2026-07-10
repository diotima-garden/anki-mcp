"""Registry of managed rendering fragments injected into every managed note type.

Each fragment is a fixed slice of CSS and/or template HTML keyed by a stable id that
becomes its sentinel. The fragments are uniform across models — no per-model authoring
— which is exactly why injection stays deterministic and needs no LLM.
"""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ManagedFragment:
    id: str
    css: str = ""  # appended to model styling
    template: str = ""  # appended to each card template's Front and Back
    applies_to: Callable[[dict], bool] = lambda spec: True


# Red apple pinned bottom-left, shown only while `user_feedback` is non-empty — a
# render-time stand-in for the RED "pending feedback" flag, so the user never hand-sets
# a flag and never re-opens the editor just to check whether feedback was left. Both
# card sides carry it; on backs that echo {{FrontSide}} the two fixed-positioned copies
# land on identical coordinates, so it still reads as a single apple.
#
# Rendered as an inline SVG rather than the 🍎 emoji: emoji glyphs depend on the host
# having a color-emoji font installed (Anki's bundled Qt WebEngine often doesn't on
# Linux, rendering as a tofu box), while inline SVG is self-contained vector markup
# that needs no font, no media file, and nothing for Anki's "Check Media" to prune.
_APPLE_SVG = (
    '<svg viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">'
    '<ellipse cx="12" cy="14" rx="7" ry="7.5" fill="#d32f2f"/>'
    '<rect x="11.2" y="3" width="1.6" height="4" rx="0.8" fill="#6d4c2f"/>'
    '<path d="M12.6 4.5c1.8-1.6 4.3-1 4.6 1.2-1.9.7-4-.1-4.6-1.2z" fill="#4caf50"/>'
    "</svg>"
)

FEEDBACK_MARKER = ManagedFragment(
    id="feedback-marker",
    css=".mnt-feedback-marker { position: fixed; bottom: 12px; left: 12px; "
    "line-height: 1; pointer-events: none; z-index: 2147483647; }",
    template=(
        '{{#user_feedback}}<div class="mnt-feedback-marker">' + _APPLE_SVG + "</div>{{/user_feedback}}"
    ),
)

FRAGMENTS = [FEEDBACK_MARKER]
