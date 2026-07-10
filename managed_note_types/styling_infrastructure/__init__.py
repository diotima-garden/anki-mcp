"""Styling infrastructure: a deterministic vehicle for enriching managed note types.

Kept as its own package so the (soon-to-be-unified) test approach can operate on it in
isolation. Submodules import explicitly — the pure `injection`/`fragments` layers stay
free of any Anki dependency; only `enrich` reaches the collection.
"""
