"""
Bootstrap a fresh TouchDesigner workspace for SSD morph/mudra experiments.

Run this inside TouchDesigner Textport in a blank project:

exec(open('/Users/darrenzal/projects/salish-sea-dreaming/scripts/td_setup/bootstrap_morph_mudra_workspace.py').read())

It loads the repo-local MCP WebServer component, loads MediaPipe if needed, runs
the morph/mudra scrubber installer, and saves a new versioned .toe template.
"""

import json
import os


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
MCP_BUNDLE_DIR = f"{ROOT}/td/templates/touchdesigner-mcp"
MCP_TOX = f"{MCP_BUNDLE_DIR}/mcp_webserver_base.tox"
MEDIAPIPE_TOX = f"{ROOT}/tools/mediapipe/MediaPipe.tox"
HAND_TRACKING_TOX = f"{ROOT}/tools/mediapipe/hand_tracking.tox"
INSTALLER = f"{ROOT}/scripts/td_setup/install_morph_mudra_scrubber.py"
MCP_REPAIR = f"{ROOT}/scripts/td_setup/repair_mcp_bridge.py"
UPGRADE_V002 = f"{ROOT}/scripts/td_setup/upgrade_morph_mudra_interaction_v002.py"
UPGRADE_V003 = f"{ROOT}/scripts/td_setup/upgrade_morph_mudra_interaction_v003_low_latency.py"
UPGRADE_V004 = f"{ROOT}/scripts/td_setup/upgrade_morph_mudra_interaction_v004_robust_pinch.py"
UPGRADE_V005 = f"{ROOT}/scripts/td_setup/upgrade_morph_mudra_interaction_v005_visible_pinch_feedback.py"
UPGRADE_V006 = f"{ROOT}/scripts/td_setup/upgrade_morph_mudra_interaction_v006_frame_sequence_scrub.py"
TEMPLATE_DIR = f"{ROOT}/td/templates"
TEMPLATE_PREFIX = "ssd_morph_mudra_workspace"


def _next_template_path():
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    for i in range(1, 1000):
        path = f"{TEMPLATE_DIR}/{TEMPLATE_PREFIX}_v{i:03d}.toe"
        if not os.path.exists(path):
            return path
    raise RuntimeError("No available template version path")


def _load_tox(parent_path, tox_path, expected_path, node_x=0, node_y=0):
    existing = op(expected_path)
    if existing is not None:
        return existing
    if not os.path.exists(tox_path):
        raise RuntimeError(f"Missing TOX: {tox_path}")
    parent_comp = op(parent_path)
    if parent_comp is None:
        raise RuntimeError(f"Missing parent COMP: {parent_path}")
    loaded = parent_comp.loadTox(tox_path)
    loaded.nodeX = node_x
    loaded.nodeY = node_y
    return loaded


def bootstrap():
    if op("/project1") is None:
        raise RuntimeError("/project1 not found; start from a normal blank TD project")

    mcp = _load_tox("/", MCP_TOX, "/mcp_webserver_base", -900, 450)
    if mcp.name != "mcp_webserver_base":
        mcp.name = "mcp_webserver_base"
    with open(MCP_REPAIR, "r") as fh:
        exec(fh.read(), globals())

    mp = _load_tox("/project1", MEDIAPIPE_TOX, "/project1/MediaPipe", -900, 150)
    if mp.name != "MediaPipe":
        mp.name = "MediaPipe"

    # The scrubber reads /project1/MediaPipe/hands directly, so hand_tracking is
    # optional. Loading it keeps the workspace close to the April show setup.
    ht = op("/project1/hand_tracking2") or op("/project1/hand_tracking")
    if ht is None and os.path.exists(HAND_TRACKING_TOX):
        ht = op("/project1").loadTox(HAND_TRACKING_TOX)
        ht.name = "hand_tracking2"
        ht.nodeX = -900
        ht.nodeY = -100

    exec_globals = globals()
    with open(INSTALLER, "r") as fh:
        exec(fh.read(), exec_globals)
    with open(UPGRADE_V002, "r") as fh:
        exec(fh.read(), exec_globals)
    with open(UPGRADE_V003, "r") as fh:
        exec(fh.read(), exec_globals)
    with open(UPGRADE_V004, "r") as fh:
        exec(fh.read(), exec_globals)
    with open(UPGRADE_V005, "r") as fh:
        exec(fh.read(), exec_globals)
    with open(UPGRADE_V006, "r") as fh:
        exec(fh.read(), exec_globals)

    template_path = _next_template_path()
    project.save(template_path)
    result = {
        "mcp": mcp.path,
        "mcp_bundle": MCP_BUNDLE_DIR,
        "mediapipe": mp.path,
        "hand_tracking": ht.path if ht is not None else None,
        "scrubber": "/project1/ssd_morph_mudra_scrubber",
        "saved_template": template_path,
    }
    print(json.dumps(result, indent=2))
    return result


bootstrap_result = bootstrap()
