"""Idempotent sentinel-block injection for managed note-type styling.

Pure string operations — no Anki, no I/O. A "managed block" is a fragment of CSS or
template HTML wrapped in comment sentinels so later passes can find it, update it, or
leave it alone without ever touching anything outside its own delimiters. That bounded
blast radius is what makes running this on every server startup safe.
"""
import re

# Sentinel comment syntax per target: CSS uses /* */, templates use HTML comments.
_COMMENT = {"css": "/* {} */", "html": "<!-- {} -->"}


def _sentinels(block_id: str, style: str) -> tuple[str, str]:
    fmt = _COMMENT[style]
    return fmt.format(f"mnt:{block_id}:start"), fmt.format(f"mnt:{block_id}:end")


def ensure_block(text: str, block_id: str, content: str, style: str) -> str:
    """Return `text` with the managed block present and equal to `content`.

    Absent -> appended. Present and current -> `text` unchanged. Present but stale ->
    the block is replaced in place. Only the region between this block's own sentinels
    is ever written; surrounding (hand-authored) text is preserved verbatim.
    """
    start, end = _sentinels(block_id, style)
    desired = f"{start}\n{content}\n{end}"
    existing = re.search(re.escape(start) + r".*?" + re.escape(end), text, re.DOTALL)
    if existing:
        if existing.group(0) == desired:
            return text
        return text[: existing.start()] + desired + text[existing.end() :]
    sep = "" if text == "" or text.endswith("\n") else "\n"
    return f"{text}{sep}{desired}"
