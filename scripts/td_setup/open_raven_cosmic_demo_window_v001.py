"""
Open a reliable TouchDesigner demo window for the Raven Sun -> Cosmic Sun scrubber.

Run inside TouchDesigner:

exec(open('/Users/darrenzal/projects/salish-sea-dreaming/scripts/td_setup/open_raven_cosmic_demo_window_v001.py').read())

The window displays a Container COMP whose background TOP is the scrubber output.
That avoids Window COMP ambiguity when pointing directly at a raw TOP.
"""

import json


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
PROJECT = "/project1"
OUT_TOP = "/project1/ssd_morph_mudra_scrubber_raven_cosmic/out_morph"
PANEL_PATH = "/project1/ssd_morph_demo_panel"
WINDOW_PATH = "/project1/ssd_morph_demo_window"
WORKSPACE_TOE = f"{ROOT}/td/templates/ssd_morph_mudra_workspace_raven_cosmic_fallbacks_v001.toe"


def _set(pars, name, value):
    if hasattr(pars, name):
        getattr(pars, name).val = value


def open_demo_window():
    root = op(PROJECT)
    out_top = op(OUT_TOP)
    if root is None:
        raise RuntimeError(f"{PROJECT} not found")
    if out_top is None:
        raise RuntimeError(f"{OUT_TOP} not found")

    panel = op(PANEL_PATH)
    if panel is None:
        panel = root.create("containerCOMP", PANEL_PATH.rsplit("/", 1)[-1])
    panel.nodeX = 1880
    panel.nodeY = -20
    _set(panel.par, "w", 900)
    _set(panel.par, "h", 900)
    _set(panel.par, "top", OUT_TOP)
    _set(panel.par, "bgcolorr", 0)
    _set(panel.par, "bgcolorg", 0)
    _set(panel.par, "bgcolorb", 0)
    _set(panel.par, "bgalpha", 1)
    try:
        panel.par.topfill.val = "fill"
    except Exception:
        pass
    try:
        panel.par.fit.val = "fill"
    except Exception:
        pass
    panel.viewer = True
    panel.display = True

    win = op(WINDOW_PATH)
    if win is None:
        win = root.create("windowCOMP", WINDOW_PATH.rsplit("/", 1)[-1])
    win.nodeX = 1880
    win.nodeY = 120
    _set(win.par, "winop", panel.path)
    _set(win.par, "title", "SSD Raven -> Cosmic Mudra Scrubber")
    _set(win.par, "winw", 900)
    _set(win.par, "winh", 900)
    _set(win.par, "borders", True)
    _set(win.par, "alwaysontop", True)
    _set(win.par, "cursorvisible", True)
    _set(win.par, "closeescape", False)
    try:
        win.par.size.val = "custom"
    except Exception:
        pass

    for path in (
        "/project1/MediaPipe/video",
        "/project1/MediaPipe/Viewer",
        "/project1/ssd_morph_mudra_scrubber_raven_cosmic/out_morph",
    ):
        viewer_op = op(path)
        if viewer_op is not None:
            try:
                viewer_op.closeViewer()
            except Exception:
                pass

    out_top.cook(force=True)
    win.par.winopen.pulse()
    try:
        win.setForeground()
    except Exception:
        pass

    return {
        "panel": panel.path,
        "panel_top": str(panel.par.top.eval()),
        "window": win.path,
        "window_operator": str(win.par.winop.eval()),
        "is_open": bool(win.isOpen),
        "size": [win.width, win.height],
        "xy": [win.x, win.y],
    }


result = open_demo_window()
project.save(WORKSPACE_TOE)
print(json.dumps(result, indent=2))
