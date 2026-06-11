"""
Upgrade /project1/ssd_morph_mudra_scrubber to v006 frame-sequence scrub.

Keeps v005 visible feedback and actual artwork. Replaces Movie File In TOP
movie-index seeking with a file expression that selects one of 120 extracted
JPEG frames. This avoids TD Movie File In failing to update pixels while its
index parameter changes.
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
COMP_PATH = "/project1/ssd_morph_mudra_scrubber"
FRAMES_DIR = f"{ROOT}/td/templates/assets/cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006"
V006_TOX = f"{ROOT}/td/templates/ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox"

FILE_EXPR = (
    "'/Users/darrenzal/projects/salish-sea-dreaming/td/templates/assets/"
    "cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006/frame_%04d.jpg' % "
    "(1 + int(round((op('/project1/ssd_morph_mudra_scrubber/morph_control').chan('progress')[0] "
    "if op('/project1/ssd_morph_mudra_scrubber/morph_control') "
    "and op('/project1/ssd_morph_mudra_scrubber/morph_control').chan('progress') "
    "else 0) * 119)))"
)


def upgrade():
    if not os.path.isdir(FRAMES_DIR):
        raise RuntimeError(f"Missing frame sequence directory: {FRAMES_DIR}")
    frame_count = len([p for p in os.listdir(FRAMES_DIR) if p.startswith("frame_") and p.endswith(".jpg")])
    if frame_count != 120:
        raise RuntimeError(f"Expected 120 frame JPGs in {FRAMES_DIR}, found {frame_count}")

    comp = op(COMP_PATH)
    if comp is None:
        raise RuntimeError(f"{COMP_PATH} not found")
    movie = comp.op("morph_movie")
    ctrl = comp.op("morph_control")
    if movie is None or ctrl is None:
        raise RuntimeError("Expected morph_movie and morph_control")

    movie.par.file.expr = FILE_EXPR
    movie.par.index.expr = ""
    movie.par.index.val = 0
    movie.par.play.val = False
    movie.par.playmode.val = "specify"
    movie.par.indexunit.val = "frames"
    if hasattr(movie.par, "updateimage"):
        movie.par.updateimage.val = True

    # Reset to hand-control mode at source endpoint.
    ctrl.par.const0value.val = 0.0
    ctrl.par.const1value.val = 0.0
    ctrl.par.const2value.val = 0.0
    ctrl.par.const3value.val = 0.0
    ctrl.par.const4value.val = 0.0
    ctrl.par.const10value.val = 0.0

    notes = comp.op("README")
    if notes is not None:
        notes.text = (
            "SSD Morph Mudra Scrubber v006 frame-sequence scrub\n\n"
            "Output TOP: out_morph\n"
            "Control CHOP: morph_control\n\n"
            "This version uses the actual artwork morph as 120 extracted JPEG "
            "frames and selects the frame by progress. This avoids TD Movie "
            "File In movie-index seeking, which was updating the index but not "
            "the pixels on this machine.\n\n"
            "Pinch thumb/index and move left-right to guide the transition. "
            "The top-left overlay shows hand detection and pinch strength.\n\n"
            "Internal experiment only. Austin per-output approval is required "
            "before public display.\n"
        )

    movie.cook(force=True)
    comp.store("ssd_template_role", "morph_mudra_scrubber_v006_frame_sequence_scrub")
    comp.store("ssd_frame_sequence_dir", FRAMES_DIR)
    comp.save(V006_TOX)
    return {
        "component": comp.path,
        "frame_sequence": FRAMES_DIR,
        "frame_count": frame_count,
        "template_tox": V006_TOX,
        "file_eval": movie.par.file.eval(),
    }


result = upgrade()
print(json.dumps(result, indent=2))
