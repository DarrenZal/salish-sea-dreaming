#!/usr/bin/env python3
"""
Blender Python script: set up iridescent oyster-pearl material on the
existing exp4 pearl mesh (`exp4_hybrid_pearl_container_model_2026-05-16.ply`)
per the pearl-interior spec (`pearl-interior-experiment-spec-2026-05-17.md`).

Run with:
  blender --background --python scripts/setup_pearl_material_blender.py \
    -- --output /path/to/test_render.png

Or open Blender interactively, then in the Python console:
  exec(open("/Users/darrenzal/projects/salish-sea-dreaming/scripts/setup_pearl_material_blender.py").read())

Then render the test (operator decides aesthetic tuning).

Produces a fully-shaded pearl with:
  - Principled BSDF: transmission 0.85, roughness 0.10, IOR 1.55 (real pearl nacre)
  - Thin-film interference: enabled, ~450nm thickness (peach/teal nacre shimmer)
  - Subsurface scattering: warm cream tint for depth
  - Soft ambient + 1 key + 1 rim lighting (no harsh shadows)
  - HDRI background optional (light-source environment)
  - Camera positioned for clean front-quarter view

INTERNAL: per Austin consent floor, output renders go to
morph_outputs_INTERNAL/ with provenance.csv entry. Treat as Tier 1.1
material-pass deliverable per pearl-interior spec.
"""
import sys
from pathlib import Path

try:
    import bpy
    import mathutils
except ImportError:
    print("ERROR: This script must be run inside Blender (bpy module not available)")
    print("Usage: blender --background --python <this_script> -- --output <png_path>")
    sys.exit(1)

# Parse CLI args (everything after `--`)
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

OUTPUT_PATH = None
PLY_PATH = None
if "--output" in argv:
    OUTPUT_PATH = Path(argv[argv.index("--output") + 1])
if "--ply" in argv:
    PLY_PATH = Path(argv[argv.index("--ply") + 1])
else:
    PLY_PATH = Path("/Users/darrenzal/projects/salish-sea-dreaming/track2-deterministic/morph_outputs/exp4_hybrid_pearl_container_model_2026-05-16.ply")


def reset_scene():
    """Clear the default scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    # Delete all materials, meshes, lights, cameras data-blocks
    for collection in [bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images]:
        for item in list(collection):
            collection.remove(item)


def import_pearl_mesh(ply_path):
    """Import the .ply mesh."""
    if not ply_path.exists():
        print(f"ERROR: .ply file not found at {ply_path}")
        print("       Run track2-deterministic/scripts/exp4_hybrid_pearl_container.py first to regenerate.")
        sys.exit(1)
    bpy.ops.wm.ply_import(filepath=str(ply_path))
    pearl_obj = bpy.context.selected_objects[0]
    pearl_obj.name = "Pearl"
    # Auto-center + scale to reasonable bounds
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    pearl_obj.location = (0, 0, 0)
    # Smooth shading
    bpy.ops.object.shade_smooth()
    return pearl_obj


def create_pearl_material():
    """Create iridescent oyster-pearl Principled BSDF material."""
    mat = bpy.data.materials.new(name="OysterPearl_Iridescent")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output node
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)

    # Principled BSDF
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    # Per pearl-interior spec
    bsdf.inputs['Base Color'].default_value = (0.95, 0.92, 0.88, 1.0)  # warm cream
    bsdf.inputs['Roughness'].default_value = 0.10  # soft satin, not mirror
    bsdf.inputs['IOR'].default_value = 1.55  # real pearl nacre range
    bsdf.inputs['Transmission Weight'].default_value = 0.85  # translucent
    # Subsurface scattering for depth
    if 'Subsurface Weight' in bsdf.inputs:
        bsdf.inputs['Subsurface Weight'].default_value = 0.25
        bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.6, 0.4)  # warm scatter
    # Coat layer for surface bloom
    if 'Coat Weight' in bsdf.inputs:
        bsdf.inputs['Coat Weight'].default_value = 0.30
        bsdf.inputs['Coat Roughness'].default_value = 0.05
    # Iridescent thin-film (Blender 4.x has this)
    if 'Coat IOR' in bsdf.inputs:
        bsdf.inputs['Coat IOR'].default_value = 1.6
    # Try the actual thin-film inputs if present
    for input_name in ['Thin Film Thickness', 'Coat Tint']:
        if input_name in bsdf.inputs:
            if input_name == 'Thin Film Thickness':
                bsdf.inputs[input_name].default_value = 450  # ~450nm = peach/teal nacre
            elif input_name == 'Coat Tint':
                bsdf.inputs[input_name].default_value = (0.95, 0.85, 0.95, 1.0)  # pink-violet sheen

    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def setup_lighting():
    """Soft ambient + 1 key + 1 rim — no harsh shadows."""
    # World ambient (low warm)
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    world_nodes = world.node_tree.nodes
    world_nodes.clear()
    bg = world_nodes.new(type='ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.05, 0.06, 0.08, 1.0)  # deep dusk
    bg.inputs['Strength'].default_value = 0.3
    out = world_nodes.new(type='ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs['Background'], out.inputs['Surface'])

    # Key light (upper-front)
    bpy.ops.object.light_add(type='AREA', location=(2.5, -2.0, 3.0))
    key = bpy.context.active_object
    key.name = "KeyLight"
    key.data.energy = 80.0
    key.data.size = 2.5
    key.data.color = (1.0, 0.95, 0.88)  # warm white
    key.rotation_euler = (0.6, 0.6, 0)

    # Rim light (back-side, cooler)
    bpy.ops.object.light_add(type='AREA', location=(-1.5, 2.0, 1.5))
    rim = bpy.context.active_object
    rim.name = "RimLight"
    rim.data.energy = 30.0
    rim.data.size = 1.5
    rim.data.color = (0.7, 0.85, 1.0)  # cool blue
    rim.rotation_euler = (1.0, -0.7, 0)


def setup_camera():
    """Position camera for clean front-quarter view."""
    bpy.ops.object.camera_add(location=(0, -4.0, 1.2))
    cam = bpy.context.active_object
    cam.name = "Camera"
    # Point at origin
    direction = mathutils.Vector((0, 0, 0)) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50  # 50mm — pleasant for product/portrait
    bpy.context.scene.camera = cam


def configure_render():
    """Cycles renderer with pearl-friendly settings."""
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'  # better tone-mapping for HDR


def main():
    print("=" * 60)
    print("Pearl Tier 1.1 Material Setup (Blender)")
    print(f"  PLY: {PLY_PATH}")
    print(f"  Output: {OUTPUT_PATH or '(interactive — no auto-render)'}")
    print("=" * 60)

    reset_scene()
    pearl_obj = import_pearl_mesh(PLY_PATH)
    mat = create_pearl_material()
    pearl_obj.data.materials.clear()
    pearl_obj.data.materials.append(mat)
    setup_lighting()
    setup_camera()
    configure_render()

    print("Scene set up.")
    print(f"  Pearl object: {pearl_obj.name}")
    print(f"  Material: {mat.name} (iridescent thin-film, IOR 1.55, subsurface)")
    print(f"  Lighting: KeyLight + RimLight + ambient")
    print(f"  Renderer: Cycles, 256 samples, 1920x1080, AgX tonemap")

    if OUTPUT_PATH:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        bpy.context.scene.render.filepath = str(OUTPUT_PATH)
        print(f"Rendering to {OUTPUT_PATH}...")
        bpy.ops.render.render(write_still=True)
        print(f"  → {OUTPUT_PATH}")
    else:
        print("No --output given. Open Blender GUI to render interactively, or save:")
        print("  bpy.ops.wm.save_as_mainfile(filepath='/path/to/save.blend')")

    # Save the .blend file for later interactive work
    blend_out = Path("/Users/darrenzal/projects/salish-sea-dreaming/track2-deterministic/morph_outputs_INTERNAL/pearl_tier1_material.blend")
    blend_out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_out))
    print(f"Saved .blend file: {blend_out}")


if __name__ == "__main__":
    main()
