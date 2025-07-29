"""Aggregate references into an index."""

import acailib.EntityReader as er


class ReferencesIndex:
    """Index of BCV references.

    This is multi-level: reference -> reftype -> list of entity IDs.

    Example: "01041050" -> {'key_references': ['person:Manasseh', 'person:Joseph.10', ...],}
    for 'person:Manasseh',

    Caveats:
    - 'references' may include metonymies (especially for the patriarchs of the 12 tribes)
    - 'key_references' may not be named references
    """
