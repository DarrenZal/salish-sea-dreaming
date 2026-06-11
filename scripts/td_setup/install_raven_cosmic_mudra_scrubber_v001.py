"""
Install Raven Sun -> Cosmic Sun as a separate scrub-ready TD component.

Run inside TouchDesigner after opening the v006 mudra scrubber workspace or any
blank project with /project1:

exec(open('/Users/darrenzal/projects/salish-sea-dreaming/scripts/td_setup/install_raven_cosmic_mudra_scrubber_v001.py').read())

The script preserves /project1/ssd_morph_mudra_scrubber, then loads the working
v006 frame-sequence scrubber TOX as:

  /project1/ssd_morph_mudra_scrubber_raven_cosmic

and retargets its frame expression and callback paths to the preferred
Raven -> Cosmic endpoint_correct_v001 frame sequence.
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
PROJECT = "/project1"
COMP_NAME = "ssd_morph_mudra_scrubber_raven_cosmic"
COMP_PATH = f"{PROJECT}/{COMP_NAME}"
BASE_TOX = f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox"
FRAMES_DIR = f"{ROOT}/td/templates/assets/raven_sun_to_cosmic_sun_endpoint_correct_v001_scrub_frames"
RAVEN_TOX = f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_raven_cosmic_v001.tox"
RAVEN_TOE = f"{ROOT}/td/templates/ssd_morph_mudra_workspace_raven_cosmic_v001.toe"

OLD_COMP_PATH = "/project1/ssd_morph_mudra_scrubber"
FRAME_COUNT = 120

FILE_EXPR = (
    "'/Users/darrenzal/projects/salish-sea-dreaming/td/templates/assets/"
    "raven_sun_to_cosmic_sun_endpoint_correct_v001_scrub_frames/frame_%04d.jpg' % "
    "(1 + int(round((op('/project1/ssd_morph_mudra_scrubber_raven_cosmic/morph_control').chan('progress')[0] "
    "if op('/project1/ssd_morph_mudra_scrubber_raven_cosmic/morph_control') "
    "and op('/project1/ssd_morph_mudra_scrubber_raven_cosmic/morph_control').chan('progress') "
    "else 0) * 119)))"
)


def _count_frames():
    if not os.path.isdir(FRAMES_DIR):
        raise RuntimeError(f"Missing Raven -> Cosmic frame directory: {FRAMES_DIR}")
    return len([p for p in os.listdir(FRAMES_DIR) if p.startswith("frame_") and p.endswith(".jpg")])


def _load_base_component():
    project_root = op(PROJECT)
    if project_root is None:
        raise RuntimeError(f"{PROJECT} not found")
    if not os.path.exists(BASE_TOX):
        raise RuntimeError(f"Missing base scrubber TOX: {BASE_TOX}")

    existing = op(COMP_PATH)
    if existing is not None:
        existing.destroy()

    comp = project_root.loadTox(BASE_TOX)
    comp.name = COMP_NAME
    comp.nodeX = 1550
    comp.nodeY = -140
    return comp


def _replace_callback_paths(comp):
    for dat_name in ("mudra_to_progress", "slider_overlay_callbacks", "README"):
        dat = comp.op(dat_name)
        if dat is not None and hasattr(dat, "text"):
            dat.text = dat.text.replace(OLD_COMP_PATH, COMP_PATH)


def _fix_overlay_order(comp):
    over = comp.op("morph_with_slider_overlay")
    movie = comp.op("morph_movie")
    overlay = comp.op("slider_overlay")
    if over is not None and movie is not None and overlay is not None:
        # Over TOP composites input 0 over input 1; overlay must be foreground.
        over.setInputs([overlay, movie])


def install():
    frame_count = _count_frames()
    if frame_count != FRAME_COUNT:
        raise RuntimeError(f"Expected {FRAME_COUNT} Raven -> Cosmic frames, found {frame_count}")

    comp = _load_base_component()
    _replace_callback_paths(comp)

    movie = comp.op("morph_movie")
    ctrl = comp.op("morph_control")
    overlay = comp.op("slider_overlay")
    overlay_cb = comp.op("slider_overlay_callbacks")
    if movie is None or ctrl is None:
        raise RuntimeError("Expected morph_movie and morph_control in base TOX")

    movie.par.file.expr = FILE_EXPR
    movie.par.index.expr = ""
    movie.par.index.val = 0
    movie.par.play.val = False
    movie.par.playmode.val = "specify"
    movie.par.indexunit.val = "frames"
    if hasattr(movie.par, "updateimage"):
        movie.par.updateimage.val = True

    # Reset to source endpoint and keep the working v005/v006 pinch defaults.
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
            "SSD Morph Mudra Scrubber - Raven Sun -> Cosmic Sun v001\n\n"
            "Output TOP: out_morph\n"
            "Control CHOP: morph_control\n\n"
            "This is the preferred deterministic Raven -> Cosmic scrub-ready "
            "transition. It uses 120 JPG frames derived from "
            "raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4, so frame 0 "
            "and the final frame come from verified training JPG endpoints "
            "while the middle preserves the same-viewBox shape morph.\n\n"
            "Pinch thumb/index and move left-right to guide the transition. "
            "The top-left overlay shows hand detection and pinch strength.\n\n"
            "Internal experiment only. Austin per-output approval is required "
            "before public display.\n"
        )

    movie.cook(force=True)
    comp.store("ssd_template_role", "morph_mudra_scrubber_raven_cosmic_v001")
    comp.store("ssd_frame_sequence_dir", FRAMES_DIR)
    comp.store("ssd_source_pair", "Animal_Bird_Raven_Sun -> Nature_Cosmic_Sun")
    comp.save(RAVEN_TOX)
    project.save(RAVEN_TOE)

    return {
        "component": comp.path,
        "output_top": f"{comp.path}/out_morph",
        "control_chop": f"{comp.path}/morph_control",
        "frame_sequence": FRAMES_DIR,
        "frame_count": frame_count,
        "template_tox": RAVEN_TOX,
        "workspace_toe": RAVEN_TOE,
        "file_eval": movie.par.file.eval(),
        "preserved": OLD_COMP_PATH if op(OLD_COMP_PATH) is not None else None,
    }


result = install()
print(json.dumps(result, indent=2))
