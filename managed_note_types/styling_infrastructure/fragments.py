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
FEEDBACK_MARKER = ManagedFragment(
    id="feedback-marker",
    css=".mnt-feedback-marker { position: fixed; bottom: 12px; left: 12px; "
    "font-size: 22px; line-height: 1; pointer-events: none; }",
    template='{{#user_feedback}}<div class="mnt-feedback-marker">🍎</div>{{/user_feedback}}',
)

FRAGMENTS = [FEEDBACK_MARKER]
