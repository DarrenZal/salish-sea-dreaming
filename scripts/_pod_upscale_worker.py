"""
TELUS H200 pod-side upscale worker.

Runs on the Jupyter kernel via exec(); driven by scripts/telus_upscale.py.
Reads job config from env vars set by the driver immediately before exec.

Required env vars:
    TELUS_UPSCALE_JOB_DIR   absolute path to job dir on pod
    TELUS_UPSCALE_INPUT     input MP4 filename inside job dir
    TELUS_UPSCALE_OUTPUT    output MP4 filename inside job dir
    TELUS_UPSCALE_WEIGHTS   absolute path to ESRGAN .pth weights
    TELUS_UPSCALE_MODEL     "x2plus" | "x4plus" (drives downfit logic)
    TELUS_UPSCALE_CANVAS    "WIDTHxHEIGHT" target canvas (e.g. "3840x2160")

Writes:
    <job_dir>/_status.txt    "DONE" / "ERROR: <msg>"
    <job_dir>/_progress.txt  per-frame N/total during inference
    <job_dir>/<output>       upscaled MP4

The DONE marker is the driver's polling signal.
"""

import os
import subprocess
import sys
import time
import traceback
from pathlib import Path


def _status(msg: str, status_path: Path) -> None:
    status_path.write_text(msg + "\n")


def _progress(msg: str, progress_path: Path) -> None:
    progress_path.write_text(msg + "\n")
    print(msg, flush=True)


def main() -> int:
    job_dir = Path(os.environ["TELUS_UPSCALE_JOB_DIR"])
    input_name = os.environ["TELUS_UPSCALE_INPUT"]
    output_name = os.environ["TELUS_UPSCALE_OUTPUT"]
    weights_path = Path(os.environ["TELUS_UPSCALE_WEIGHTS"])
    model_kind = os.environ["TELUS_UPSCALE_MODEL"]
    canvas_w, canvas_h = (int(x) for x in os.environ["TELUS_UPSCALE_CANVAS"].split("x"))
    framing = os.environ.get("TELUS_UPSCALE_FRAMING", "letterbox")
    if framing not in ("letterbox", "crop"):
        raise ValueError(f"unknown framing {framing!r}")

    status_path = job_dir / "_status.txt"
    progress_path = job_dir / "_progress.txt"
    frames_in = job_dir / "frames_in"
    frames_out = job_dir / "frames_out"
    input_path = job_dir / input_name
    output_path = job_dir / output_name

    try:
        frames_in.mkdir(exist_ok=True)
        frames_out.mkdir(exist_ok=True)

        # 1) Extract frames + read source fps via ffprobe (JSON for stable parse).
        _progress("[1/4] Probing input + extracting frames", progress_path)
        import json as _json
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate,width,height",
             "-of", "json", str(input_path)],
            check=True, capture_output=True, text=True,
        )
        s = _json.loads(probe.stdout)["streams"][0]
        src_w, src_h = int(s["width"]), int(s["height"])
        num, den = (int(x) for x in s["r_frame_rate"].split("/"))
        src_fps = num / den
        _progress(f"  source: {src_w}x{src_h} @ {src_fps:.3f}fps", progress_path)

        # Wipe any prior extraction, re-extract.
        for p in frames_in.glob("*.png"):
            p.unlink()
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_path),
             "-vsync", "0", str(frames_in / "frame_%06d.png")],
            check=True, capture_output=True,
        )
        frame_files = sorted(frames_in.glob("*.png"))
        n_frames = len(frame_files)
        if n_frames == 0:
            raise RuntimeError("frame extraction produced zero frames")
        _progress(f"  extracted {n_frames} frames", progress_path)

        # 2) Load model.
        _progress("[2/4] Loading ESRGAN model", progress_path)
        import torch
        from spandrel import ModelLoader
        import torch.nn.functional as F
        from PIL import Image
        import numpy as np

        device = torch.device("cuda")
        model = ModelLoader().load_from_file(str(weights_path)).model
        model = model.to(device).eval().half()
        scale = 4 if model_kind == "x4plus" else 2

        # 3) Inference per frame.
        _progress(f"[3/4] Upscaling {n_frames} frames x{scale} on H200", progress_path)
        t0 = time.time()

        with torch.inference_mode():
            for i, fp in enumerate(frame_files):
                img = np.asarray(Image.open(fp).convert("RGB"), dtype=np.float32) / 255.0
                t = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).half().to(device)
                up = model(t)  # (1, 3, H*scale, W*scale)

                # Aspect-preserving downfit ONLY if upscaled overshoots the canvas
                # in either dimension. E.g. 1024² → x4 → 4096² → fits-to 3840×2160
                # via 2160² letterboxed by the ffmpeg pad step. For 1920×1080 → x2
                # → 3840×2160 (exact canvas), this is a no-op.
                _, _, h, w = up.shape
                if w > canvas_w or h > canvas_h:
                    fit = min(canvas_w / w, canvas_h / h)
                    new_w = round(w * fit)
                    new_h = round(h * fit)
                    up = F.interpolate(up.float(), size=(new_h, new_w), mode="area").half()

                up_np = (up.clamp(0, 1)[0].permute(1, 2, 0).float().cpu().numpy() * 255.0).round().astype(np.uint8)
                Image.fromarray(up_np).save(frames_out / fp.name)

                if (i + 1) % 24 == 0 or (i + 1) == n_frames:
                    elapsed = time.time() - t0
                    fps_render = (i + 1) / elapsed
                    eta = (n_frames - (i + 1)) / max(fps_render, 1e-6)
                    _progress(
                        f"  frame {i+1}/{n_frames} | {fps_render:.2f} fps | ETA {eta:.0f}s",
                        progress_path,
                    )

        # 4) Encode output MP4. Framing controls how content meets the canvas.
        _progress(f"[4/4] Encoding output MP4 (framing={framing})", progress_path)
        canvas_aspect = canvas_w / canvas_h  # e.g. 16/9 = 1.778
        if framing == "letterbox":
            # Scale-to-fit + black-pad. Square content → bars left+right on 16:9.
            vf = (
                f"scale='if(gt(iw,{canvas_w}),{canvas_w},iw)':"
                f"'if(gt(ih,{canvas_h}),{canvas_h},ih)':force_original_aspect_ratio=decrease,"
                f"pad={canvas_w}:{canvas_h}:(ow-iw)/2:(oh-ih)/2:color=black"
            )
        else:  # crop
            # Crop to canvas aspect from the center, then upscale to canvas size
            # via lanczos. For 2048² → take 2048×1152 center band → upscale 1.875×.
            vf = (
                f"crop=iw:iw/{canvas_aspect:.6f},"
                f"scale={canvas_w}:{canvas_h}:flags=lanczos"
            )
        subprocess.run(
            ["ffmpeg", "-y",
             "-framerate", f"{src_fps:.6f}",
             "-i", str(frames_out / "frame_%06d.png"),
             "-vf", vf,
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
             "-preset", "slow",
             str(output_path)],
            check=True, capture_output=True,
        )

        elapsed = time.time() - t0
        _progress(f"DONE in {elapsed:.1f}s ({n_frames} frames at {n_frames/elapsed:.2f} fps render).", progress_path)
        _status("DONE", status_path)
        return 0

    except Exception as e:
        tb = traceback.format_exc()
        _status(f"ERROR: {e}\n\n{tb}", status_path)
        print(tb, file=sys.stderr)
        return 1


if __name__ == "__main__":
    # Don't sys.exit — when this is exec()'d inside a Jupyter kernel, SystemExit
    # propagates as an "error" even on success. The driver polls _status.txt
    # instead, so a return value isn't needed.
    main()
