"""
autolume_autostart.py — wrapper that launches Autolume and auto-enters live render mode.

Subclasses Autolume to skip the Welcome/Splash screens, seed a specific .pkl model,
and (optionally) apply a saved preset once the renderer is up.

Usage (from the autolume source dir):
    python autolume_autostart.py \
        --pkl C:\\Users\\user\\Documents\\models\\network-snapshot-000120.pkl \
        --preset C:\\Users\\user\\Documents\\presets\\0

Both args are optional. If only --preset is given, the preset's embedded pickle.pkl
reference supplies the model. If only --pkl is given, no preset state is applied
(plain model load in live mode).
"""
import argparse
import multiprocessing
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Autolume autostart wrapper")
    parser.add_argument("--pkl", help="absolute path to a .pkl model to pre-load")
    parser.add_argument("--preset", help="absolute path to a preset directory to load after render starts")
    parser.add_argument(
        "--autolume-dir",
        default=r"C:\Users\user\autolume",
        help="path to the Autolume source tree (default: C:\\Users\\user\\autolume)",
    )
    args = parser.parse_args()

    # Autolume expects to be run from its own directory (for assets/, presets/, etc.)
    os.chdir(args.autolume_dir)
    sys.path.insert(0, args.autolume_dir)

    import torch
    from modules.autolume_live import Autolume, States

    class AutostartAutolume(Autolume):
        def __init__(self, pkl=None, preset=None):
            super().__init__()
            self._pending_preset = preset
            self._preset_loaded = False

            if pkl or preset:
                if pkl:
                    if not os.path.isfile(pkl):
                        print(f"[autostart] WARNING: --pkl path does not exist: {pkl}")
                    else:
                        self.pkls = [pkl]
                # start_renderer jumps to States.RENDER and loads self.pkls[0] if present.
                # If only --preset was given (no --pkl), start_renderer still transitions
                # to RENDER — the preset load later pulls in the model via pickle_widget.
                self.start_renderer()
                print(f"[autostart] renderer started (pkl={pkl}, preset={preset})")

        def draw_frame(self):
            # Once the visualizer is fully wired up, apply the preset exactly once.
            if (
                not self._preset_loaded
                and self._pending_preset
                and self.state == States.RENDER
                and self.viz is not None
                and getattr(self.viz, "preset_widget", None) is not None
            ):
                try:
                    self.viz.preset_widget.load(self._pending_preset)
                    print(f"[autostart] preset loaded: {self._pending_preset}")
                except Exception as e:
                    print(f"[autostart] preset load FAILED: {e}")
                self._preset_loaded = True

            super().draw_frame()

    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.set_grad_enabled(False)

    app = AutostartAutolume(pkl=args.pkl, preset=args.preset)
    while not app.should_close():
        app.draw_frame()
    app.close()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)
    main()
