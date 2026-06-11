"""
Install primitive cycle / primitive field as low-load TD scrubber fallbacks.

Run inside TouchDesigner after opening the Raven/Cosmic or v006 mudra scrubber
workspace:

exec(open('/Users/darrenzal/projects/salish-sea-dreaming/scripts/td_setup/install_primitive_fallback_scrubbers_v001.py').read())

The script preserves existing scrubber components and creates:

  /project1/ssd_morph_mudra_scrubber_primitive_cycle
  /project1/ssd_morph_mudra_scrubber_primitive_field
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
PROJECT = "/project1"
BASE_TOX = f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox"
WORKSPACE_TOE = f"{ROOT}/td/templates/ssd_morph_mudra_workspace_raven_cosmic_fallbacks_v001.toe"
OLD_COMP_PATH = "/project1/ssd_morph_mudra_scrubber"

COMPONENTS = [
    {
        "name": "ssd_morph_mudra_scrubber_primitive_cycle",
        "label": "Primitive Cycle",
        "role": "morph_mudra_scrubber_primitive_cycle_v001",
        "frames_dir": f"{ROOT}/td/templates/assets/primitive_cycle_scrub_frames_v001",
        "tox": f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_primitive_cycle_v001.tox",
        "nodeX": 1550,
        "nodeY": -420,
    },
    {
        "name": "ssd_morph_mudra_scrubber_primitive_field",
        "label": "Primitive Field",
        "role": "morph_mudra_scrubber_primitive_field_v001",
        "frames_dir": f"{ROOT}/td/templates/assets/primitive_field_scrub_frames_v001",
        "tox": f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_primitive_field_v001.tox",
        "nodeX": 1550,
        "nodeY": -700,
    },
]


def _count_frames(frames_dir):
    if not os.path.isdir(frames_dir):
        raise RuntimeError(f"Missing frame sequence directory: {frames_dir}")
    return len([p for p in os.listdir(frames_dir) if p.startswith("frame_") and p.endswith(".jpg")])


def _file_expr(comp_path, frames_dir, frame_count):
    return (
        f"'{frames_dir}/frame_%04d.jpg' % "
        f"(1 + int(round((op('{comp_path}/morph_control').chan('progress')[0] "
        f"if op('{comp_path}/morph_control') "
        f"and op('{comp_path}/morph_control').chan('progress') "
        f"else 0) * {frame_count - 1})))"
    )


def _replace_callback_paths(comp, comp_path):
    for dat_name in ("mudra_to_progress", "slider_overlay_callbacks", "README"):
        dat = comp.op(dat_name)
        if dat is not None and hasattr(dat, "text"):
            dat.text = dat.text.replace(OLD_COMP_PATH, comp_path)


def _fix_overlay_order(comp):
    over = comp.op("morph_with_slider_overlay")
    movie = comp.op("morph_movie")
    overlay = comp.op("slider_overlay")
    if over is not None and movie is not None and overlay is not None:
        # Over TOP composites input 0 over input 1; overlay must be foreground.
        over.setInputs([overlay, movie])


def _install_one(spec):
    project_root = op(PROJECT)
    if project_root is None:
        raise RuntimeError(f"{PROJECT} not found")
    if not os.path.exists(BASE_TOX):
        raise RuntimeError(f"Missing base scrubber TOX: {BASE_TOX}")

    comp_path = f"{PROJECT}/{spec['name']}"
    existing = op(comp_path)
    if existing is not None:
        existing.destroy()

    frame_count = _count_frames(spec["frames_dir"])
    if frame_count != 120:
        raise RuntimeError(f"Expected 120 frames for {spec['label']}, found {frame_count}")

    comp = project_root.loadTox(BASE_TOX)
    comp.name = spec["name"]
    comp.nodeX = spec["nodeX"]
    comp.nodeY = spec["nodeY"]
    _replace_callback_paths(comp, comp_path)

    movie = comp.op("morph_movie")
    ctrl = comp.op("morph_control")
    overlay = comp.op("slider_overlay")
    overlay_cb = comp.op("slider_overlay_callbacks")
    if movie is None or ctrl is None:
        raise RuntimeError(f"Expected morph_movie and morph_control in {comp_path}")

    movie.par.file.expr = _file_expr(comp_path, spec["frames_dir"], frame_count)
    movie.par.index.expr = ""
    movie.par.index.val = 0
    movie.par.play.val = False
    movie.par.playmode.val = "specify"
    movie.par.indexunit.val = "frames"
    if hasattr(movie.par, "updateimage"):
        movie.par.updateimage.val = True

    ctrl.par.const0value.val = 0.0
    ctrl.par.const1value.val = 0.0
    ctrl.par.const2value.val = 0.0
    ctrl.par.const3value.val = 0.0
    ctrl.par.const4value.val = 0.0
    ctrl.par.const10value.val = 0.0

    if overlay is not None and overlay_cb is not None:
        overlay.par.callbacks.val = overlay_cb.path
        overlay.cook(force=True)
    _fix_overlay_order(comp)

    notes = comp.op("README")
    if notes is not None:
        notes.text = (
            f"SSD Morph Mudra Scrubber - {spec['label']} v001\n\n"
            "Output TOP: out_morph\n"
            "Control CHOP: morph_control\n\n"
            "Low-load gesture-control fallback using a 120-frame JPG sequence "
            "selected by progress. Pinch thumb/index and move left-right to "
            "guide the scrubber.\n\n"
            "Internal experiment only. Keep separate from Austin-specific "
            "per-output review until explicitly framed.\n"
        )

    movie.cook(force=True)
    comp.store("ssd_template_role", spec["role"])
    comp.store("ssd_frame_sequence_dir", spec["frames_dir"])
    comp.save(spec["tox"])
    return {
        "component": comp.path,
        "output_top": f"{comp.path}/out_morph",
        "control_chop": f"{comp.path}/morph_control",
        "frame_sequence": spec["frames_dir"],
        "frame_count": frame_count,
        "template_tox": spec["tox"],
        "file_eval": movie.par.file.eval(),
    }


def install():
    results = [_install_one(spec) for spec in COMPONENTS]
    project.save(WORKSPACE_TOE)
    return {
        "components": results,
        "workspace_toe": WORKSPACE_TOE,
    }


result = install()
print(json.dumps(result, indent=2))
