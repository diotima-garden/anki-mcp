"""
Startup bootstrap for managed note types.

Reads a JSON config (path passed via --managed-config at server startup) and ensures:
  - Each declared note type exists in the collection (creates it if not).
  - Each existing note type has the managed fields appended.

Templates are built from domain fields; managed fields (user_feedback, log) carry no
domain content of their own. They may, however, be referenced by managed rendering
fragments (styling_infrastructure) — e.g. the feedback marker conditions on
user_feedback to surface a bottom-left apple. Such references are owned by the fragment
registry, injected here after fields exist, not authored into base templates by hand.

Deliberately does not call sync: schema changes force a full one-way sync, which can
pop a blocking Upload/Download dialog in the Anki GUI. Pushing that is left to the
caller's own sync step (pipelines bookend Anki-touching work with mcp__anki__sync).
"""
import json
import pathlib

from core import _call, _log
from managed_note_types import MANAGED_FIELDS
from managed_note_types.styling_infrastructure.enrich import enrich_model

_CSS = (
    ".card { font-family: arial; font-size: 20px; "
    "text-align: center; color: black; background-color: white; }"
)


def _build_template(domain_fields: list[str], is_cloze: bool) -> dict:
    if is_cloze:
        front = "{{cloze:" + domain_fields[0] + "}}"
        back_parts = ["{{cloze:" + domain_fields[0] + "}}"] + [
            "{{" + f + "}}" for f in domain_fields[1:]
        ]
        back = "<br>".join(back_parts)
    else:
        front = "{{" + domain_fields[0] + "}}"
        back_parts = ["{{" + f + "}}" for f in domain_fields[1:]]
        back = "{{FrontSide}}<hr id=answer>" + "<br>".join(back_parts)
    return {"Name": "Card 1", "Front": front, "Back": back}


def run(config_path: str) -> None:
    """Bootstrap managed note types from config. Safe to call on every startup."""
    path = pathlib.Path(config_path)
    if not path.exists():
        _log(f"managed-note-types: config not found at {config_path}, skipping")
        return

    config = json.loads(path.read_text())
    specs = config.get("managed_note_types", [])
    if not specs:
        _log("managed-note-types: no note types declared, skipping")
        return

    existing_models = set(_call("modelNames"))

    for spec in specs:
        name = spec["name"]
        domain_fields: list[str] = spec["fields"]
        is_cloze: bool = spec.get("is_cloze", False)

        # Managed fields appended after domain fields (skip any already listed).
        extra = [f for f in MANAGED_FIELDS if f not in domain_fields]
        all_fields = domain_fields + extra

        if name not in existing_models:
            _log(f"managed-note-types: creating '{name}' with fields {all_fields}")
            _call(
                "createModel",
                modelName=name,
                inOrderFields=all_fields,
                isCloze=is_cloze,
                cardTemplates=[_build_template(domain_fields, is_cloze)],
                css=_CSS,
            )
        else:
            existing_fields = set(_call("modelFieldNames", modelName=name))
            for field in MANAGED_FIELDS:
                if field not in existing_fields:
                    _log(f"managed-note-types: adding '{field}' to '{name}'")
                    _call("modelFieldAdd", modelName=name, fieldName=field)

        # Managed rendering fragments (e.g. the feedback marker) run after fields exist,
        # since they reference managed fields. Idempotent; writes only on change.
        enrich_model(name, spec)

    _log("managed-note-types: bootstrap complete")
