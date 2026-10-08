"""MCP server exposing SolidWorks automation as tools.

Session/meta tools (connect, inspect, open, save, screenshot) plus parameterized
part-modeling tools (sketches, features, patterns). All share one COM session
via :mod:`solidworks_mcp.runtime`.
"""

from __future__ import annotations

from typing import Optional

from mcp.server.mcpserver import MCPServer

from . import runtime

mcp_server = MCPServer("solidworks")


# --- session / meta --------------------------------------------------------
@mcp_server.tool()
def sw_connect(visible: bool = True) -> dict:
    """Connect to SolidWorks (launching it if needed). Call this first."""
    session = runtime.get_session(visible=visible)
    return {"ok": True, "revision": session.connect()}


@mcp_server.tool()
def sw_version() -> dict:
    """Return the connected SolidWorks revision string."""
    session = runtime.get_session()
    if not session.connected:
        session.connect()
    return {"revision": session.revision()}


@mcp_server.tool()
def sw_new_part(template: Optional[str] = None) -> dict:
    """Create a new part document and return its title."""
    return {"title": runtime.get_session().new_document("part", template)}


@mcp_server.tool()
def sw_open(path: str, kind: str = "part") -> dict:
    """Open a document. kind is 'part' | 'assembly' | 'drawing'."""
    return {"title": runtime.get_session().open_document(path, kind)}


@mcp_server.tool()
def sw_save(path: Optional[str] = None) -> dict:
    """Save the active document, optionally to a new path."""
    return {"path": runtime.get_session().save(path)}


@mcp_server.tool()
def sw_close(title: Optional[str] = None) -> dict:
    """Close a document by title, or the active document when omitted."""
    return {"closed": runtime.get_session().close(title)}


@mcp_server.tool()
def sw_list_documents() -> dict:
    """List the titles of all open documents."""
    return {"titles": runtime.get_session().list_open_documents()}


@mcp_server.tool()
def sw_screenshot(path: str, width: int = 1280, height: int = 960) -> dict:
    """Save a bitmap of the active document view for visual verification."""
    return {"path": runtime.get_session().save_screenshot(path, width, height)}


# --- selection -------------------------------------------------------------
@mcp_server.tool()
def sw_select(name: str, entity_type: str = "EDGE", append: bool = False, mark: int = 0) -> dict:
    """Select an entity by name. entity_type is EDGE|FACE|VERTEX|PLANE|SKETCH|AXIS."""
    return {"selected": runtime.get_modeling().select(name, entity_type, append, mark)}


@mcp_server.tool()
def sw_clear_selection() -> dict:
    """Clear the current selection."""
    runtime.get_modeling().clear_selection()
    return {"ok": True}


# --- sketches --------------------------------------------------------------
@mcp_server.tool()
def sw_sketch_rectangle(plane: str, x1: float, y1: float, x2: float, y2: float) -> dict:
    """Create a closed rectangle sketch on a plane (mm). plane: front|top|right."""
    return {"sketch": runtime.get_modeling().sketch_rectangle(plane, x1, y1, x2, y2)}


@mcp_server.tool()
def sw_sketch_circle(plane: str, cx: float, cy: float, radius: float) -> dict:
    """Create a circle sketch on a plane (mm)."""
    return {"sketch": runtime.get_modeling().sketch_circle(plane, cx, cy, radius)}


# --- features --------------------------------------------------------------
@mcp_server.tool()
def sw_extrude(depth: float, through_all: bool = False, flip: bool = False) -> dict:
    """Extrude the active sketch into a boss (depth in mm)."""
    return {"feature": runtime.get_modeling().extrude(depth, through_all, flip)}


@mcp_server.tool()
def sw_extrude_cut(depth: float, through_all: bool = True, flip: bool = False) -> dict:
    """Cut-extrude the active sketch (depth in mm)."""
    return {"feature": runtime.get_modeling().extrude_cut(depth, through_all, flip)}


@mcp_server.tool()
def sw_revolve(angle_deg: float = 360.0, is_cut: bool = False) -> dict:
    """Revolve the active sketch about a centerline (angle in degrees)."""
    return {"feature": runtime.get_modeling().revolve(angle_deg, is_cut)}


@mcp_server.tool()
def sw_fillet(radius: float, propagate: bool = True) -> dict:
    """Fillet the selected edges (radius in mm)."""
    return {"feature": runtime.get_modeling().fillet(radius, propagate)}


@mcp_server.tool()
def sw_chamfer(width: float, angle_deg: float = 45.0, equal_distance: bool = True) -> dict:
    """Chamfer the selected edges (width in mm)."""
    return {"feature": runtime.get_modeling().chamfer(width, angle_deg, equal_distance)}


@mcp_server.tool()
def sw_shell(thickness: float, outward: bool = False) -> dict:
    """Shell the body, removing the selected faces (thickness in mm)."""
    runtime.get_modeling().shell(thickness, outward)
    return {"ok": True}


@mcp_server.tool()
def sw_linear_pattern(count1: int, spacing1: float, count2: int = 1, spacing2: float = 0.0,
                      flip1: bool = False, flip2: bool = False) -> dict:
    """Linear-pattern the selected features/bodies (spacing in mm)."""
    return {"feature": runtime.get_modeling().linear_pattern(count1, spacing1, count2, spacing2, flip1, flip2)}


@mcp_server.tool()
def sw_circular_pattern(count: int, angle_deg: float = 360.0, axis_name: Optional[str] = None) -> dict:
    """Circular-pattern the selected features/bodies about an axis."""
    return {"feature": runtime.get_modeling().circular_pattern(count, angle_deg, axis_name)}


@mcp_server.tool()
def sw_mirror(geometry_pattern: bool = True, merge: bool = False) -> dict:
    """Mirror the selected features/bodies about the selected face."""
    return {"feature": runtime.get_modeling().mirror(geometry_pattern, merge)}


@mcp_server.tool()
def sw_hole_wizard(diameter: float, depth: Optional[float] = None, standard_index: int = 1,
                   fastener_type: int = 0, end_type: int = 0) -> dict:
    """Create a hole-wizard hole at the active sketch points (diameter in mm)."""
    return {"feature": runtime.get_modeling().hole_wizard(diameter, depth, standard_index, fastener_type, end_type)}


@mcp_server.tool()
def sw_rebuild() -> dict:
    """Force a full model rebuild (Ctrl-Q equivalent)."""
    runtime.get_modeling().rebuild()
    return {"ok": True}


@mcp_server.tool()
def sw_mass_properties(density_kg_m3: float = 1000.0) -> dict:
    """Return volume/area/mass of the first solid body (SI-derived, mm units)."""
    return runtime.get_modeling().mass_properties(density_kg_m3)


# --- drawing ---------------------------------------------------------------
@mcp_server.tool()
def sw_new_drawing(template: Optional[str] = None) -> dict:
    """Create a new drawing document from the GB template."""
    return {"title": runtime.get_drawing().new_drawing(template)}


@mcp_server.tool()
def sw_create_view(model_path: str, view: str = "front", x: float = 0.0, y: float = 0.0) -> dict:
    """Insert a model view (front|top|right|left|back|bottom|isometric|...)."""
    return {"view": runtime.get_drawing().create_view(model_path, view, x, y)}


@mcp_server.tool()
def sw_insert_annotations(all_views: bool = True) -> dict:
    """Insert the model's dimensions/annotations onto the drawing views."""
    runtime.get_drawing().insert_model_annotations(all_views)
    return {"ok": True}


@mcp_server.tool()
def sw_export(path: str) -> dict:
    """Export the active drawing by extension (e.g. .pdf or .dwg)."""
    return {"path": runtime.get_drawing().export(path)}


# --- assembly --------------------------------------------------------------
@mcp_server.tool()
def sw_new_assembly(template: Optional[str] = None) -> dict:
    """Create a new assembly document from the GB template."""
    return {"title": runtime.get_assembly().new_assembly(template)}


@mcp_server.tool()
def sw_add_component(path: str, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> dict:
    """Insert a part into the assembly (position in mm)."""
    return {"component": runtime.get_assembly().add_component(path, x, y, z)}


@mcp_server.tool()
def sw_select_at(x: float, y: float, z: float, type_: str = "FACE", append: bool = True) -> dict:
    """Select the entity nearest a point (mm). type_ is FACE|EDGE|VERTEX."""
    return {"selected": runtime.get_assembly().select_at(x, y, z, type_, append)}


@mcp_server.tool()
def sw_add_mate(mate_type: int = 0, align: int = 2, distance: float = 0.0, angle: float = 0.0) -> dict:
    """Add a mate between the selected entities. mate_type: 0=coincident 1=concentric 3=parallel 5=distance 6=angle."""
    return runtime.get_assembly().add_mate(mate_type, align, distance, angle)


@mcp_server.tool()
def sw_interference_check(coincident: bool = True) -> dict:
    """Run interference check on all components; returns the interference count."""
    return runtime.get_assembly().interference_check(coincident)


@mcp_server.tool()
def sw_create_exploded_view() -> dict:
    """Create an exploded view in the active configuration."""
    return {"created": runtime.get_assembly().create_exploded_view()}


@mcp_server.tool()
def sw_add_explode_step(distance: float, reverse: bool = False) -> dict:
    """Add an explode step for the selected component(s)."""
    return {"ok": runtime.get_assembly().add_explode_step(distance, reverse)}


# --- batch -----------------------------------------------------------------
@mcp_server.tool()
def sw_get_parameter(name: str) -> dict:
    """Read a named dimension value in mm (e.g. 'D1@凸台-拉伸1')."""
    return {"value_mm": runtime.get_batch().get_parameter(name)}


@mcp_server.tool()
def sw_set_parameter(name: str, value_mm: float) -> dict:
    """Set a named dimension (mm) and rebuild."""
    return {"value_mm": runtime.get_batch().set_parameter(name, value_mm)}


@mcp_server.tool()
def sw_export_document(path: str) -> dict:
    """Export the active document by extension (STEP/DXF/PDF/...)."""
    return {"path": runtime.get_batch().export(path)}


def main() -> None:
    mcp_server.run()


if __name__ == "__main__":
    main()
