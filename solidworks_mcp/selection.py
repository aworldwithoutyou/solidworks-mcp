"""Stable entity-selection helpers for SolidWorks documents.

SolidWorks selection is stateful and order-dependent, which makes it a common
source of fragile automation. These helpers wrap the two robust ways to address
an entity -- by its persistent name, or by a point -- behind a small API, and
keep "clear then select" explicit so callers do not depend on leftover state.
"""

from __future__ import annotations

# swSelectType_e string values accepted by SelectByID2.
SEL_EDGE = "EDGE"
SEL_FACE = "FACE"
SEL_VERTEX = "VERTEX"
SEL_SKETCH = "SKETCH"
SEL_PLANE = "PLANE"
SEL_AXIS = "AXIS"


def clear(doc) -> None:
    """Remove any current selection."""
    doc.ClearSelection2(True)


def select_by_name(
    doc,
    name: str,
    type_: str,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    append: bool = False,
    mark: int = 0,
) -> bool:
    """Select an entity by persistent name; clears first unless ``append``."""
    if not append:
        clear(doc)
    result = doc.Extension.SelectByID2(name, type_, x, y, z, append, mark, None, 0)
    return bool(result) if result is not None else False


def selected_count(doc) -> int:
    """Number of currently selected entities."""
    value = doc.SelectionManager.GetSelectedObjectCount2(-1)
    return int(value)
