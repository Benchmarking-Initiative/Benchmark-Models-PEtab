"""Handling of former problem IDs."""

import warnings

from .C import RENAMED_MODELS


def resolve_id(id_: str) -> str:
    """Map a former problem ID to the current one, with a warning.

    Other IDs are returned unchanged.
    """
    if (new_id := RENAMED_MODELS.get(id_)) is None:
        return id_

    warnings.warn(
        f"Problem `{id_}` was renamed to `{new_id}`. "
        "The old ID will stop working in a future version.",
        FutureWarning,
        stacklevel=3,
    )
    return new_id
