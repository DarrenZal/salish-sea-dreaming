# TELUS Abstract Cymatic Rendering Notes - 2026-05-21

Status: batch-render readiness plan and smoke test. Generated abstract wave /
cymatic geometry only. No Austin assets, no source artwork, no cultural claims.

## Goal

Make it easy to run UHD abstract cymatic render variants on TELUS Jupyter
machines, with local scratch frame output, CPU multiprocessing, ffmpeg encoding,
contact sheets, loop diagnostics, JSON variant sweeps, and a small optional GPU
field-evaluation benchmark.

## Existing Renderer Dependency Inspection

Relevant renderer trail:

- `scripts/cymatic_field_topology_v001.py` through
  `scripts/cymatic_field_topology_v007.py`: latest mature abstract scalar-field
  renderer line. Uses `numpy`, `cv2`, Python stdlib, and ffmpeg via
  `subprocess`. v007 is useful design reference, but it is fixed at 1920x1080,
  24 fps, 6 seconds, hardcoded output paths, and OpenCV-dependent.
- `scripts/cymatic_radiant_water_geometry_v001.py`: generated geometric study,
  but imports project primitive helper scripts as well as `numpy`, `cv2`, and
  ffmpeg. Less portable as a standalone TELUS payload.
- `scripts/cymatic_standing_wave_phase_inversion_v002.py`,
  `scripts/cymatic_topology_cells_v003.py`, and
  `scripts/cymatic_topology_cells_v004.py`: useful generated topology studies,
  but also depend on OpenCV and local project imports.
- `scripts/primitive_standing_wave_field_v001.py` and `_v002.py`: generated
  standing-wave field scripts using `numpy`, `cv2`, and ffmpeg.

Repository `requirements.txt` currently lists only `Pillow>=10.0`, while the
existing cymatic scripts also need NumPy/OpenCV. On this machine, `python3`
has NumPy and Pillow but not OpenCV; `python3.11` has NumPy, OpenCV, Pillow, and
Torch. That version split is a portability risk.

## Minimal TELUS Payload

Use the new self-contained harness:

- `scripts/telus_abstract_cymatic_batch.py`
- one optional JSON config file for variant sweeps
- ffmpeg available on `PATH`

Main render dependencies:

```bash
python -m pip install numpy Pillow
```

Optional GPU field benchmark dependencies:

```bash
python -m pip install cupy-cuda12x
# or use a TELUS image with PyTorch CUDA already installed
```

The harness does not import OpenCV and does not read any asset directory.

## Harness Capabilities

`scripts/telus_abstract_cymatic_batch.py` supports:

- headless CLI usage or import from a Jupyter notebook
- default UHD render settings: 3840x2160, 24 fps, 5 seconds
- CPU multiprocessing with `ProcessPoolExecutor`
- local scratch discovery via `--scratch`, `TELUS_SCRATCH`, `SLURM_TMPDIR`, or
  `/tmp`
- PNG frame writing to scratch
- MP4 encoding through ffmpeg / libx264
- contact sheet output
- loop diagnostic image and JSON metrics
- JSON variant sweeps with Cartesian product expansion
- CPU serial vs multiprocessing benchmark
- optional CuPy/PyTorch CUDA field-evaluation benchmark only

## TELUS Commands

Write a sweep config template:

```bash
python scripts/telus_abstract_cymatic_batch.py write-example-config \
  telus-abstract-cymatic-sweep.json
```

Run a 3840x2160 batch from JSON:

```bash
python scripts/telus_abstract_cymatic_batch.py render \
  --config telus-abstract-cymatic-sweep.json \
  --scratch "$TELUS_SCRATCH" \
  --width 3840 \
  --height 2160 \
  --duration 5 \
  --fps 24 \
  --field-scale 0.375 \
  --workers "$(python -c 'import os; print(os.cpu_count())')"
```

Run the CPU benchmark:

```bash
python scripts/telus_abstract_cymatic_batch.py benchmark \
  --width 1920 \
  --height 1080 \
  --frames 32 \
  --field-scale 0.375 \
  --workers 2,4,8
```

Run the optional TELUS GPU POC benchmark:

```bash
python scripts/telus_abstract_cymatic_batch.py gpu-benchmark \
  --width 3840 \
  --height 2160 \
  --frames 32 \
  --field-scale 0.375
```

Jupyter import pattern from repo root:

```python
import os
from pathlib import Path

from scripts.telus_abstract_cymatic_batch import (
    RenderSettings,
    load_config,
    run_batch,
)

config = load_config("telus-abstract-cymatic-sweep.json")
settings = RenderSettings(
    width=3840,
    height=2160,
    fps=24,
    duration_seconds=5.0,
    field_scale=0.375,
    crf=18,
    preset="medium",
    keep_frames=True,
)
run_batch(
    config,
    scratch=Path(os.environ.get("TELUS_SCRATCH", "/tmp")),
    settings=settings,
    workers=os.cpu_count(),
)
```

## Smoke Render Produced

Command run locally:

```bash
python3 scripts/telus_abstract_cymatic_batch.py render \
  --scratch tmp/telus_abstract_cymatic_test \
  --width 1920 \
  --height 1080 \
  --duration 5 \
  --fps 24 \
  --field-scale 0.33 \
  --workers 8 \
  --preset veryfast \
  --crf 22
```

Outputs:

- MP4:
  `tmp/telus_abstract_cymatic_test/telus_abstract_cymatic_batch/abstract_membrane_seed/abstract_membrane_seed_1920x1080_120f.mp4`
- contact sheet:
  `tmp/telus_abstract_cymatic_test/telus_abstract_cymatic_batch/abstract_membrane_seed/abstract_membrane_seed_contact_sheet.png`
- loop diagnostic:
  `tmp/telus_abstract_cymatic_test/telus_abstract_cymatic_batch/abstract_membrane_seed/abstract_membrane_seed_loop_diagnostics.png`
- manifest:
  `tmp/telus_abstract_cymatic_test/telus_abstract_cymatic_batch/abstract_membrane_seed/abstract_membrane_seed_manifest.json`

ffprobe confirmed: 1920x1080, 24 fps, 5.000 seconds, 120 frames, 1,824,010
bytes.

Render timing from manifest: 15.161s frame render/write, 5.335s ffmpeg encode,
7.915 effective rendered fps on 8 local CPU workers.

Loop diagnostic after periodicity fix:

| metric | value |
|---|---:|
| first-last mean abs RGB delta | 2.2166 |
| adjacent-frame median mean abs RGB delta | 2.3626 |
| loop-to-adjacent ratio | 0.9382 |
| first-last p95 abs RGB delta | 10.0 |

The seam now measures like normal frame-to-frame motion.

## CPU Benchmark

Local benchmark command:

```bash
python3 scripts/telus_abstract_cymatic_batch.py benchmark \
  --width 1920 \
  --height 1080 \
  --frames 32 \
  --field-scale 0.375 \
  --workers 2,4,8
```

This benchmark evaluates frames in memory; it excludes PNG disk write and ffmpeg
encode so CPU scaling is easier to read.

| mode | workers | seconds | frames/sec | megapixels/sec | speedup vs serial |
|---|---:|---:|---:|---:|---:|
| serial | 1 | 8.8046 | 3.6345 | 7.536 | 1.00x |
| multiprocessing | 2 | 5.0424 | 6.3461 | 13.159 | 1.75x |
| multiprocessing | 4 | 3.2585 | 9.8204 | 20.364 | 2.70x |
| multiprocessing | 8 | 2.5406 | 12.5957 | 26.118 | 3.47x |

## GPU POC Status

The harness includes a field-evaluation-only GPU benchmark. It does not rewrite
the full renderer and does not include PNG/MP4 transfer costs.

Local command run:

```bash
python3 scripts/telus_abstract_cymatic_batch.py gpu-benchmark \
  --width 1920 \
  --height 1080 \
  --frames 16 \
  --field-scale 0.375
```

Local result: skipped because this `python3` environment had no CuPy and no
PyTorch CUDA module available. Run the same command on TELUS H200 before any GPU
rewrite decision.

## Recommendation

Use CPU multiprocessing for the first TELUS batch. It is already a clean
portable path, scales on local CPU cores, and avoids GPU readback/PNG bottleneck
risk. Start TELUS UHD checks at `field_scale=0.30` or `0.375`, then raise toward
`0.50` only if the contact sheets justify the added cost.

Treat GPU acceleration as a later optimization. Only rewrite more of the render
path if the TELUS `gpu-benchmark` shows at least a clear 3x field-evaluation
win and a separate full render profile shows field evaluation is still the main
bottleneck after PNG write and ffmpeg encode.
