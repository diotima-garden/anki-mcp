"""Apply managed rendering fragments to a note type's live CSS and templates.

The only Anki-touching layer of the styling infrastructure. Reads the model's current
styling + templates, runs the pure `ensure_block` injector for each applicable fragment,
and writes back only when something actually changed — an already-enriched model incurs
no write and no collection churn.
"""
from core import _call, _log
from managed_note_types.styling_infrastructure.fragments import FRAGMENTS
from managed_note_types.styling_infrastructure.injection import ensure_block


def enrich_model(model_name: str, spec: dict, fragments=FRAGMENTS) -> bool:
    """Ensure every applicable fragment is present in `model_name`. Idempotent.

    Returns True iff a write occurred.
    """
    applicable = [f for f in fragments if f.applies_to(spec)]
    if not applicable:
        return False

    changed = False

    css = _call("modelStyling", modelName=model_name)["css"]
    new_css = css
    for frag in applicable:
        if frag.css:
            new_css = ensure_block(new_css, frag.id, frag.css, "css")
    if new_css != css:
        _call("updateModelStyling", model={"name": model_name, "css": new_css})
        changed = True

    templates = _call("modelTemplates", modelName=model_name)
    new_templates = {}
    tmpl_changed = False
    for card_name, sides in templates.items():
        new_sides = dict(sides)
        for side in ("Front", "Back"):
            if side not in new_sides:
                continue
            updated = new_sides[side]
            for frag in applicable:
                if frag.template:
                    updated = ensure_block(updated, frag.id, frag.template, "html")
            if updated != sides[side]:
                new_sides[side] = updated
                tmpl_changed = True
        new_templates[card_name] = new_sides
    if tmpl_changed:
        _call("updateModelTemplates", model={"name": model_name, "templates": new_templates})
        changed = True

    if changed:
        _log(f"styling: enriched '{model_name}'")
    return changed
