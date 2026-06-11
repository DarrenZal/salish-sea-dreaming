"""
autolume_sweep.py — render N short clips from Autolume at varied settings.

Subclasses Autolume's live renderer to drive a state machine that:
    load preset 0 → settle → record variant 1 → settle → record variant 2 → ...

Each variant overrides a small set of dials on top of the preset (truncation,
noise seed, noise animation). Output MP4s land in an --output-dir on disk,
one file per variant, recorded via Autolume's internal cv2 VideoWriter
(mp4v @ 30fps) at the live-render resolution (usually 1024² for the 120-kimg
PKL we use).

Usage (from the autolume source dir on the 3090):
    python autolume_sweep.py \
        --pkl  C:\\Users\\user\\Documents\\models\\network-snapshot-000120.pkl \
        --preset C:\\Users\\user\\Documents\\presets\\0 \
        --output-dir C:\\Users\\user\\autolume_sweep\\20260522-0100 \
        --record-seconds 15 --settle-seconds 2

Variants are configured below in the DEFAULT_VARIANTS list. The first variant
is always the as-loaded preset (no overrides) — this is the April-show baseline.
"""

import argparse
import multiprocessing
import os
import sys
import time
from pathlib import Path


# Aesthetic dial sweep — picked for Pravin's "different settings of the GAN
# model" ask. Each variant FULLY specifies every dial; we never inherit from
# the previous variant. Preset 0's defaults are psi=0.8, seed=0, anim=False.
DEFAULT_VARIANTS = [
    # As-loaded preset 0 — April-show baseline.
    {"name": "01_baseline",     "trunc_psi": 0.8, "noise_seed": 0,  "noise_anim": False},
    # Tighter truncation = denser, less wild.
    {"name": "02_tight_psi050", "trunc_psi": 0.5, "noise_seed": 0,  "noise_anim": False},
    # Wider truncation = maximum diversity, most abstract — likely Pravin's
    # "intricate version emerging out of the Autolume dreaming."
    {"name": "03_wild_psi120",  "trunc_psi": 1.2, "noise_seed": 0,  "noise_anim": False},
    # Animated noise on baseline psi → particles keep mutating, "alive" texture.
    {"name": "04_noise_drift",  "trunc_psi": 0.8, "noise_seed": 0,  "noise_anim": True},
    # Different noise seed, baseline psi — same aesthetic, totally different
    # latent trajectory.
    {"name": "05_seed42",       "trunc_psi": 0.8, "noise_seed": 42, "noise_anim": False},
]


def _apply_variant(viz, variant: dict) -> None:
    """Mutate viz widget state per variant config. Missing keys = keep preset."""
    tnw = viz.trunc_noise_widget
    if "trunc_psi" in variant:
        tnw.params.trunc_psi = float(variant["trunc_psi"])
    if "noise_seed" in variant:
        tnw.params.noise_seed = int(variant["noise_seed"])
    if "noise_anim" in variant:
        tnw.params.noise_anim = bool(variant["noise_anim"])
    # 2026-05-25: walk_speed override (default 0.25 in latent_widget; range -5..5)
    # Lower = smaller latent steps per frame = smoother slow morph between
    # adjacent GAN positions. Critical fix for "wayyyy too fast and jumps"
    # feedback from Pravin on May 24 22-min baseline render.
    if "walk_speed" in variant:
        viz.latent_widget.latent.speed = float(variant["walk_speed"])


def _format_state(viz) -> str:
    tnw = viz.trunc_noise_widget
    walk = getattr(getattr(viz, "latent_widget", None), "latent", None)
    walk_s = walk.speed if walk is not None else "?"
    return (f"psi={tnw.params.trunc_psi:.3f} "
            f"seed={tnw.params.noise_seed} "
            f"anim={tnw.params.noise_anim} "
            f"walk_speed={walk_s}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Autolume parameter sweep")
    parser.add_argument("--pkl", required=True,
                        help="absolute path to a .pkl model")
    parser.add_argument("--preset", required=True,
                        help="absolute path to the baseline preset dir")
    parser.add_argument("--output-dir", required=True,
                        help="absolute dir where per-variant MP4s land")
    parser.add_argument("--autolume-dir", default=r"C:\Users\user\autolume",
                        help="Autolume source tree (default %(default)s)")
    parser.add_argument("--record-seconds", type=float, default=15.0,
                        help="record length per variant (default 15s)")
    parser.add_argument("--settle-seconds", type=float, default=2.0,
                        help="settle frames between variants (default 2s)")
    parser.add_argument("--target-fps", type=float, default=30.0,
                        help="frame budget assumes this fps for timing")
    parser.add_argument("--variants", default=None,
                        help="optional JSON list overriding DEFAULT_VARIANTS")
    parser.add_argument("--variants-file", default=None,
                        help="path to JSON file with variants list (avoids cmd escaping)")
    args = parser.parse_args()

    if args.variants_file:
        import json
        with open(args.variants_file, "r") as f:
            variants = json.load(f)
    elif args.variants:
        import json
        variants = json.loads(args.variants)
    else:
        variants = list(DEFAULT_VARIANTS)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Autolume expects to be run from its own directory.
    os.chdir(args.autolume_dir)
    sys.path.insert(0, args.autolume_dir)

    import torch
    from modules.autolume_live import Autolume, States

    record_frames = max(1, int(round(args.record_seconds * args.target_fps)))
    settle_frames = max(1, int(round(args.settle_seconds * args.target_fps)))

    class SweepAutolume(Autolume):
        def __init__(self):
            super().__init__()
            self._pending_preset = args.preset
            self._preset_loaded = False
            # State machine: "preset_load" -> "settle" -> "record" (loop)
            self._phase = "preset_load"
            self._phase_frame = 0
            self._variant_idx = 0
            self._done = False
            self._started_at = time.time()
            # Force RENDER state with the model loaded.
            self.pkls = [args.pkl]
            self.start_renderer()
            print(f"[sweep] renderer started; pkl={args.pkl}", flush=True)
            print(f"[sweep] {len(variants)} variants, "
                  f"{record_frames} record frames, {settle_frames} settle frames",
                  flush=True)

        def draw_frame(self):
            # Step 1: load preset once, on first frame where viz exists.
            if (not self._preset_loaded
                    and self.state == States.RENDER
                    and self.viz is not None
                    and getattr(self.viz, "preset_widget", None) is not None):
                try:
                    self.viz.preset_widget.load(self._pending_preset)
                    print(f"[sweep] preset loaded: {self._pending_preset}",
                          flush=True)
                except Exception as e:
                    print(f"[sweep] preset load FAILED: {e}", flush=True)
                self._preset_loaded = True

            # Step 2: run the parent's frame. This is what actually renders +
            # feeds frame_queue when is_recording.
            super().draw_frame()

            # Step 3: drive the state machine only once viz exists + preset is in.
            if not self._preset_loaded or self.viz is None:
                return

            if self._phase == "preset_load":
                # First frame after preset load → enter settle.
                self._phase = "settle"
                self._phase_frame = 0
                self._begin_settle()
                return

            self._phase_frame += 1

            if self._phase == "settle":
                if self._phase_frame >= settle_frames:
                    self._begin_record()
            elif self._phase == "record":
                if self._phase_frame >= record_frames:
                    self._end_record()

        def _begin_settle(self):
            v = variants[self._variant_idx]
            _apply_variant(self.viz, v)
            print(f"[sweep] variant {self._variant_idx+1}/{len(variants)} "
                  f"'{v['name']}' → settling. State: {_format_state(self.viz)}",
                  flush=True)

        def _begin_record(self):
            v = variants[self._variant_idx]
            out_path = str(output_dir / f"{v['name']}.mp4")
            self.viz.start_recording(out_path)
            self._phase = "record"
            self._phase_frame = 0
            print(f"[sweep] recording → {out_path}", flush=True)

        def _end_record(self):
            self.viz.stop_recording()
            elapsed = time.time() - self._started_at
            print(f"[sweep] variant {self._variant_idx+1}/{len(variants)} done "
                  f"({elapsed:.1f}s wall-clock total)", flush=True)
            self._variant_idx += 1
            if self._variant_idx >= len(variants):
                self._done = True
                print("[sweep] all variants done", flush=True)
            else:
                self._phase = "settle"
                self._phase_frame = 0
                self._begin_settle()

        def should_close(self):
            return super().should_close() or self._done

    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.set_grad_enabled(False)

    app = SweepAutolume()
    while not app.should_close():
        app.draw_frame()
    app.close()
    print("[sweep] exit clean", flush=True)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)
    main()
