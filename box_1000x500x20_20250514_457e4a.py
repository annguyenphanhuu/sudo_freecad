#!/usr/bin/env python3
import FreeCAD as App
import Part
import math
import os
import Import
import Mesh

# -----------------------------
# Document Setup
# -----------------------------
sanitized_title = "Perforated_sheet_with_hexagonal_holes"
doc = App.newDocument("GeneratedModel")
doc.Label = sanitized_title

# -----------------------------
# Parameters (mm)
# -----------------------------
plate_length    = 100.0    # X dimension of the sheet
plate_width     = 50.0     # Y dimension of the sheet
plate_thickness = 2.0      # Z dimension (thickness)

hole_diameter = 5.0        # hexagon circumcircle diameter
hole_radius   = hole_diameter / 2.0

pitch_x = 10.0             # center-to-center spacing in X
pitch_y = 10.0             # center-to-center spacing in Y

tol = 1e-6                 # tolerance for boundary checks

# -----------------------------
# Compute number of holes and margins
# -----------------------------
if plate_length < hole_diameter:
    n_cols = 0
else:
    n_cols = int((plate_length - hole_diameter) / pitch_x) + 1
if n_cols > 0:
    span_x   = (n_cols - 1) * pitch_x + hole_diameter
    margin_x = (plate_length - span_x) / 2.0
else:
    margin_x = plate_length / 2.0

if plate_width < hole_diameter:
    n_rows = 0
else:
    n_rows = int((plate_width - hole_diameter) / pitch_y) + 1
if n_rows > 0:
    span_y   = (n_rows - 1) * pitch_y + hole_diameter
    margin_y = (plate_width - span_y) / 2.0
else:
    margin_y = plate_width / 2.0

# -----------------------------
# Create the base plate
# -----------------------------
base_plate = Part.makeBox(
    plate_length,
    plate_width,
    plate_thickness,
    App.Vector(0.0, 0.0, 0.0)
)

# -----------------------------
# Helper: create a single extruded hexagon hole
# -----------------------------
def make_hexagon_hole(cx, cy, radius, thickness):
    """
    Creates a regular hexagon centered at (cx,cy) with circumcircle radius 'radius',
    extruded by 'thickness' in Z.
    """
    pts = []
    for angle_deg in range(0, 360 + 1, 60):
        rad = math.radians(angle_deg)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        pts.append(App.Vector(x, y, 0.0))
    wire = Part.makePolygon(pts)
    face = Part.Face(wire)
    solid = face.extrude(App.Vector(0.0, 0.0, thickness))
    return solid

# -----------------------------
# Build all hexagonal hole tools in a staggered grid pattern
# -----------------------------
hole_tools = []
for row in range(n_rows):
    cy = margin_y + hole_radius + row * pitch_y
    # stagger odd rows by half the X pitch
    x_offset = (pitch_x / 2.0) if (row % 2 == 1) else 0.0
    for col in range(n_cols):
        cx = margin_x + hole_radius + col * pitch_x + x_offset
        # boundary check
        if (cx - hole_radius >= -tol and cx + hole_radius <= plate_length + tol and
            cy - hole_radius >= -tol and cy + hole_radius <= plate_width  + tol):
            hole = make_hexagon_hole(cx, cy, hole_radius, plate_thickness)
            hole_tools.append(hole)

# -----------------------------
# Boolean cut: subtract all holes at once
# -----------------------------
if hole_tools:
    compound_holes = Part.makeCompound(hole_tools)
    result_shape   = base_plate.cut(compound_holes)
else:
    result_shape   = base_plate

# -----------------------------
# Create and register final object
# -----------------------------
plate_obj = doc.addObject("Part::Feature", "PerforatedSheet")
plate_obj.Label = sanitized_title
plate_obj.Shape = result_shape
doc.recompute()

# -----------------------------
# Export to STEP and OBJ
# -----------------------------
if "__file__" in globals():
    script_dir = os.path.dirname(os.path.abspath(__file__))
else:
    script_dir = os.getcwd()
output_dir_abs = os.path.abspath(os.path.join(script_dir, "..", "cad_outputs_generated"))
os.makedirs(output_dir_abs, exist_ok=True)

step_filename_abs = os.path.join(output_dir_abs, f"{sanitized_title}.step")
Import.export([plate_obj], step_filename_abs)
print(f"Model exported to {step_filename_abs}")

obj_filename_abs = os.path.join(output_dir_abs, f"{sanitized_title}.obj")
Mesh.export([plate_obj], obj_filename_abs)
print(f"Model exported to {obj_filename_abs}")