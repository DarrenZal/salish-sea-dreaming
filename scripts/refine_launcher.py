#!/usr/bin/env python3
"""
Refinement Launcher — Runs all 3 refinement experiments sequentially.
=====================================================================
Installs deps, then runs R1 → R2 → R3 in sequence to avoid GPU contention.

Run: nohup python3 /home/jovyan/refine/refine_launcher.py > /home/jovyan/refine/progress.log 2>&1 &
"""

import os
import sys
import time
import datetime
import subprocess


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [LAUNCHER] {msg}", flush=True)


def run_step(name, cmd):
    """Run a command and log results."""
    log(f"Starting: {name}")
    start = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=False)
    elapsed = time.time() - start
    if result.returncode == 0:
        log(f"DONE: {name} — {elapsed/60:.1f} min")
    else:
        log(f"FAILED: {name} — exit code {result.returncode} after {elapsed/60:.1f} min")
    return result.returncode


def main():
    log("=" * 70)
    log("SALISH SEA DREAMING — REFINEMENT EXPERIMENTS")
    log("=" * 70)
    log(f"Node: TELUS H200 (ssd-style-transfer-2)")
    log(f"Start time: {datetime.datetime.now().isoformat()}")

    refine_dir = "/home/jovyan/refine"
    os.makedirs(f"{refine_dir}/output", exist_ok=True)

    # ---- Step 0: Install dependencies ----
    log("\n--- STEP 0: Install Dependencies ---")
    deps = [
        "pip install -q diffusers transformers accelerate safetensors",
        "pip install -q controlnet_aux",
        "pip install -q imageio imageio-ffmpeg",
        "pip install -q scipy",
        "pip install -q xformers 2>/dev/null || true",
    ]
    for dep in deps:
        log(f"  {dep}")
        subprocess.run(dep, shell=True, capture_output=True)
    log("Dependencies installed.")

    # GPU check
    import torch
    if torch.cuda.is_available():
        gpu = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        log(f"GPU: {gpu} ({vram:.1f} GB VRAM)")
    else:
        log("FATAL: No CUDA GPU!")
        sys.exit(1)

    global_start = time.time()
    results = {}

    # ---- Refinement 1: Murmuration with BG anchoring ----
    log("\n" + "=" * 70)
    log("REFINEMENT 1: School→Murmuration with Background Anchoring")
    log("=" * 70)
    rc = run_step(
        "R1: Murmuration BG Anchor",
        f"python3 {refine_dir}/refine_01_murmuration_bg.py"
    )
    results["R1"] = "OK" if rc == 0 else f"FAIL({rc})"

    # Clear GPU memory between runs
    torch.cuda.empty_cache()

    # ---- Refinement 2: Living Paintings ----
    log("\n" + "=" * 70)
    log("REFINEMENT 2: Living Paintings")
    log("=" * 70)
    rc = run_step(
        "R2: Living Paintings",
        f"python3 {refine_dir}/refine_02_living_paintings.py"
    )
    results["R2"] = "OK" if rc == 0 else f"FAIL({rc})"

    torch.cuda.empty_cache()

    # ---- Refinement 3: Eco HQ Re-renders ----
    log("\n" + "=" * 70)
    log("REFINEMENT 3: Eco HQ Re-renders")
    log("=" * 70)
    rc = run_step(
        "R3: Eco HQ Re-renders",
        f"python3 {refine_dir}/refine_03_eco_hq.py"
    )
    results["R3"] = "OK" if rc == 0 else f"FAIL({rc})"

    # ---- Summary ----
    total_time = time.time() - global_start
    log("\n" + "=" * 70)
    log("ALL REFINEMENTS COMPLETE")
    log("=" * 70)
    log(f"Total time: {total_time/60:.1f} min ({total_time/3600:.1f} hours)")
    for name, status in results.items():
        log(f"  {name}: {status}")

    # List all outputs
    output_dir = f"{refine_dir}/output"
    log(f"\nAll output files in {output_dir}:")
    for root, dirs, files in os.walk(output_dir):
        for f in sorted(files):
            if f.endswith(".mp4") or f.endswith(".png") and "background" in f:
                path = os.path.join(root, f)
                size_mb = os.path.getsize(path) / 1e6
                rel = os.path.relpath(path, output_dir)
                log(f"  {rel} ({size_mb:.1f} MB)")

    # Write completion marker
    marker_path = os.path.join(output_dir, "REFINE_COMPLETE")
    with open(marker_path, "w") as fh:
        fh.write(f"Completed: {datetime.datetime.now().isoformat()}\n")
        fh.write(f"Total time: {total_time/60:.1f} minutes\n")
        for name, status in results.items():
            fh.write(f"{name}: {status}\n")
    log(f"Completion marker: {marker_path}")
    log("DONE.")


if __name__ == "__main__":
    main()
