#!/usr/bin/env python3
"""
First-hour orchestrator for v2 Austin LoRA pipeline.

Wraps the FIRST_HOUR_AFTER_DRIVE_LANDS.md stage sequence behind a single entry
point. Each stage is idempotent (safe to re-run), records its result in
`austin-v2-ingest/.pipeline-state.json`, and stops at known human-decision
gates rather than auto-advancing past them.

Stages:
  1. preflight              auto    — env / dirs / pod reach
  2. triage                 auto    — run v2_ingest_helper.py (writes _triage.json)
  3. triage-review          GATE    — human edits _triage.json: review→approve|reject
  4. apply                  auto    — v2_ingest_helper.py --apply (moves files, manifest)
  5. prep                   auto    — prep_v2_image.py (512×512 + caption stubs)
  6. captions               GATE    — human authors captions per rubric (no automation)
  7. validate               auto    — validate_v2_captions.py (must pass before train)
  8. upload-training        auto    — jupyter_contents_sync.py upload training/ → pod
  9. train                  GATE    — operator runs accelerate training in pod kernel
 10. upload-eval-script     auto    — jupyter_contents_sync.py upload eval_lora.py
 11. eval-run               GATE    — operator runs eval_lora.py in pod kernel
 12. download               auto    — jupyter_contents_sync.py download eval/ → local

USAGE:
  python3 scripts/austin_v2_pipeline.py status
    -> show table: which stages done, which next, which gated

  python3 scripts/austin_v2_pipeline.py next
    -> advance one stage. Auto stages run + record. Gates print instructions + halt.

  python3 scripts/austin_v2_pipeline.py run <stage>
    -> run a specific stage by name (skips state check)

  python3 scripts/austin_v2_pipeline.py reset
    -> wipe pipeline state file (does NOT touch data dirs)

  python3 scripts/austin_v2_pipeline.py mark <stage>
    -> manually mark an external pod gate complete (`train` or `eval-run`)

  python3 scripts/austin_v2_pipeline.py auto-until-gate
    -> chain auto stages until first GATE; halt with instructions

Design rules:
  - Never auto-skip a gate (human approval is the floor)
  - Never delete user data (reset only clears state, not files)
  - Each stage exits non-zero on failure → state NOT advanced
  - Pod stages (train, eval-run) are GATE-only: orchestrator emits exact
    paste-ready commands; operator runs in pod kernel; operator marks the
    external gate complete with `mark train` / `mark eval-run`
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
INGEST = ROOT / "austin-v2-ingest"
INBOX = INGEST / "inbox"
APPROVED = INGEST / "approved"
TRAINING = INGEST / "training"
MANIFEST = INGEST / "provenance" / "manifest.csv"
TRIAGE = INBOX / "_triage.json"
STATE_FILE = INGEST / ".pipeline-state.json"
EVAL_OUT_LOCAL = ROOT / "output" / "austin-v2-eval"

POD_TRAINING_DIR = "austin-v2-pilot"
POD_LORA_OUT = "austin-v2-lora-out"
POD_EVAL_OUT = "austin-v2-eval"


# ──────────────────────── stage definitions ────────────────────────


@dataclass
class StageResult:
    ok: bool
    message: str
    extras: dict = field(default_factory=dict)


@dataclass
class Stage:
    name: str
    kind: str               # "auto" or "gate"
    description: str
    run: Callable[[], StageResult]
    is_done: Callable[[], bool] | None = None


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"stages": {}}
    try:
        return json.loads(STATE_FILE.read_text())
    except json.JSONDecodeError:
        return {"stages": {}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def mark_done(stage: str, extras: dict | None = None) -> None:
    state = load_state()
    state["stages"][stage] = {
        "done_at": datetime.now().isoformat(timespec="seconds"),
        "extras": extras or {},
    }
    save_state(state)


def is_done(stage: str) -> bool:
    return stage in load_state().get("stages", {})


def shell(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run cmd, stream stdout/stderr, return (rc, full_stdout, full_stderr)."""
    print(f"  $ {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=cwd or ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out_lines: list[str] = []
    err_lines: list[str] = []
    assert proc.stdout and proc.stderr
    for line in proc.stdout:
        out_lines.append(line)
        sys.stdout.write("    " + line)
    for line in proc.stderr:
        err_lines.append(line)
        sys.stderr.write("    " + line)
    rc = proc.wait()
    return rc, "".join(out_lines), "".join(err_lines)


# ──────────────────────── stage implementations ────────────────────────


def stage_preflight() -> StageResult:
    warnings = []
    for d in (INGEST, INBOX, APPROVED, TRAINING, MANIFEST.parent):
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
    if not MANIFEST.exists() or MANIFEST.stat().st_size == 0:
        MANIFEST.write_text("filename,source,sha256,date_received,austin_consent,notes\n")

    pod_url = None
    pod_token = None
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("TELUS_POD_URL="):
                pod_url = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("Jupyter_REST_API="):
                pod_token = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not (pod_url and pod_token):
        warnings.append(".env missing TELUS_POD_URL or Jupyter_REST_API; upload/training will block later")
    else:
        try:
            import urllib.request
            req = urllib.request.Request(
                f"{pod_url}/api/contents/",
                headers={"Authorization": f"token {pod_token}"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status != 200:
                    warnings.append(f"pod contents endpoint returned {r.status}; upload/training will block later")
        except Exception as e:
            warnings.append(f"pod unreachable: {type(e).__name__}: {e}; upload/training will block later")

    def real_files(d: Path) -> list[Path]:
        return [p for p in d.iterdir()
                if p.is_file() and not p.name.startswith((".", "_"))]
    extras = {
        "inbox_count": len(real_files(INBOX)),
        "approved_count": len(real_files(APPROVED)) if APPROVED.exists() else 0,
        "training_count": len(real_files(TRAINING)) if TRAINING.exists() else 0,
        "pod_reachable": not any("pod" in i.lower() or "telus" in i.lower() for i in warnings),
    }
    if warnings:
        extras["warnings"] = warnings
        return StageResult(True, "preflight OK with warnings:\n    - " + "\n    - ".join(warnings), extras)
    return StageResult(True, "preflight OK", extras)


def stage_triage() -> StageResult:
    inbox_files = [p for p in INBOX.iterdir()
                   if p.is_file() and not p.name.startswith((".", "_"))]
    if not inbox_files:
        return StageResult(False,
                           "inbox is empty; drop Austin's files into "
                           f"{INBOX.relative_to(ROOT)}/ first",
                           {"inbox_count": 0})
    rc, _, err = shell(["python3", str(ROOT / "scripts/v2_ingest_helper.py"),
                        "--root", str(INGEST)])
    if rc != 0:
        return StageResult(False, f"v2_ingest_helper failed (rc={rc}): {err[:300]}")
    if not TRIAGE.exists():
        return StageResult(False, "triage script ran but did not produce _triage.json")
    decisions = json.loads(TRIAGE.read_text())
    return StageResult(True, f"triaged {len(decisions)} files → {TRIAGE.relative_to(ROOT)}",
                       {"file_count": len(decisions)})


def stage_triage_review() -> StageResult:
    if not TRIAGE.exists():
        return StageResult(False, "no _triage.json — run triage first")
    decisions = json.loads(TRIAGE.read_text())
    pending_review = [d for d in decisions if d.get("recommendation") == "review"]
    approved = [d for d in decisions if d.get("recommendation") == "approve"]
    rejected = [d for d in decisions if d.get("recommendation") == "reject"]
    if pending_review:
        msg = (f"GATE — {len(pending_review)} of {len(decisions)} files still flagged 'review'.\n"
               f"    Open {TRIAGE.relative_to(ROOT)} and edit each 'recommendation' to 'approve' or 'reject'.\n"
               f"    Per FIRST_HOUR.md hard reject filters: <60% coverage, installation context,\n"
               f"    >20% text, third-party logos, photographs of artist. When in doubt: reject.\n"
               f"    Then re-run: python3 scripts/austin_v2_pipeline.py next")
        return StageResult(False, msg, {"approved": len(approved), "rejected": len(rejected),
                                        "pending_review": len(pending_review)})
    return StageResult(True, f"all triaged: {len(approved)} approved, {len(rejected)} rejected",
                       {"approved": len(approved), "rejected": len(rejected)})


def stage_apply() -> StageResult:
    if not TRIAGE.exists():
        return StageResult(False, "no _triage.json — run triage first")
    rc, _, err = shell(["python3", str(ROOT / "scripts/v2_ingest_helper.py"),
                        "--apply", "--root", str(INGEST)])
    if rc != 0:
        return StageResult(False, f"apply failed (rc={rc}): {err[:300]}")
    approved_count = sum(1 for p in APPROVED.iterdir()
                         if p.is_file() and not p.name.startswith((".", "_")))
    return StageResult(True, f"applied: {approved_count} files in approved/",
                       {"approved_count": approved_count})


def stage_prep() -> StageResult:
    approved_files = [p for p in APPROVED.iterdir()
                      if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")]
    if not approved_files:
        return StageResult(False, "no raster files in approved/ — run apply first")
    rc, _, err = shell(["python3", str(ROOT / "scripts/prep_v2_image.py"),
                        "--src", str(APPROVED), "--dst", str(TRAINING)])
    if rc != 0:
        return StageResult(False, f"prep failed (rc={rc}): {err[:300]}")
    jpgs = list(TRAINING.glob("*.jpg"))
    txts = list(TRAINING.glob("*.txt"))
    return StageResult(True, f"prepared {len(jpgs)} plates + {len(txts)} caption stubs",
                       {"jpg_count": len(jpgs), "txt_count": len(txts)})


def stage_captions() -> StageResult:
    txts = list(TRAINING.glob("*.txt"))
    if not txts:
        return StageResult(False, "no caption files in training/ — run prep first")
    placeholder_count = 0
    for t in txts:
        if "<subject" in t.read_text() or "<primitives present" in t.read_text():
            placeholder_count += 1
    if placeholder_count > 0:
        msg = (f"GATE — {placeholder_count} of {len(txts)} caption files still have placeholders.\n"
               f"    Open each .txt in {TRAINING.relative_to(ROOT)}/ and replace the placeholders\n"
               f"    per austin-v2-ingest/caption-rubric.md. Trigger token already filled in.\n"
               f"    Anti-patterns: project names, generic ethnic framing, subjective quality words.\n"
               f"    Then re-run: python3 scripts/austin_v2_pipeline.py next")
        return StageResult(False, msg, {"total": len(txts), "placeholders": placeholder_count})
    return StageResult(True, f"all {len(txts)} captions appear authored (no placeholders detected)",
                       {"total": len(txts)})


def stage_validate() -> StageResult:
    rc, _, err = shell(["python3", str(ROOT / "scripts/validate_v2_captions.py"),
                        "--root", str(INGEST), "--trigger", "austin_v2",
                        "--min-images", "15"])
    if rc != 0:
        return StageResult(False, f"validate failed (rc={rc}). Fix the errors above before training.")
    return StageResult(True, "captions validated — ready to train")


def stage_upload_training() -> StageResult:
    rc, _, err = shell(["python3", str(ROOT / "scripts/jupyter_contents_sync.py"),
                        "upload", str(TRAINING.relative_to(ROOT)), POD_TRAINING_DIR])
    if rc != 0:
        return StageResult(False, f"upload failed (rc={rc}): {err[:300]}")
    return StageResult(True, f"uploaded training set → pod:{POD_TRAINING_DIR}/")


def stage_train() -> StageResult:
    msg = f"""GATE — Training is run on the pod, not by this orchestrator.

    Paste the following into a pod kernel cell (after `cd {POD_TRAINING_DIR}`):

    accelerate launch diffusers/examples/text_to_image/train_text_to_image_lora.py \\
        --pretrained_model_name_or_path=stable-diffusion-v1-5/stable-diffusion-v1-5 \\
        --train_data_dir={POD_TRAINING_DIR} \\
        --image_column=image \\
        --caption_column=text \\
        --resolution=512 \\
        --random_flip \\
        --train_batch_size=4 \\
        --num_train_epochs=80 \\
        --learning_rate=1e-4 \\
        --lr_scheduler=cosine \\
        --lr_warmup_steps=20 \\
        --rank=16 \\
        --seed=42 \\
        --output_dir={POD_LORA_OUT}

    Wall-clock: ~7 min on H200 for ~30 plates. Watch loss; expect ~0.05-0.15 stable.

    Reference recipe: austin-reference/clean-subset-lora-v1_5/EVAL_SPEC.md (validated path).

    When training finishes, run:
        python3 scripts/austin_v2_pipeline.py mark train
        python3 scripts/austin_v2_pipeline.py next
    to advance to eval script upload."""
    return StageResult(False, msg)


def stage_upload_eval_script() -> StageResult:
    rc, _, err = shell(["python3", str(ROOT / "scripts/jupyter_contents_sync.py"),
                        "upload", "scripts/eval_lora.py", "."])
    if rc != 0:
        return StageResult(False, f"upload failed (rc={rc}): {err[:300]}")
    return StageResult(True, "uploaded eval_lora.py → pod root")


def stage_eval_run() -> StageResult:
    msg = f"""GATE — Eval is run on the pod.

    Paste into pod kernel:

        !python eval_lora.py --version v2 \\
            --lora-dir {POD_LORA_OUT} \\
            --out-dir {POD_EVAL_OUT}

    ~3 min for 28 renders + contact sheet. Outputs land in pod:{POD_EVAL_OUT}/.

    When eval finishes, run:
        python3 scripts/austin_v2_pipeline.py mark eval-run
        python3 scripts/austin_v2_pipeline.py next
    to download results."""
    return StageResult(False, msg)


def stage_download() -> StageResult:
    EVAL_OUT_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    rc, _, err = shell(["python3", str(ROOT / "scripts/jupyter_contents_sync.py"),
                        "download", POD_EVAL_OUT, str(EVAL_OUT_LOCAL.relative_to(ROOT))])
    if rc != 0:
        return StageResult(False, f"download failed (rc={rc}): {err[:300]}")
    n = len(list(EVAL_OUT_LOCAL.glob("*.jpg"))) if EVAL_OUT_LOCAL.exists() else 0
    return StageResult(True, f"downloaded {n} files → {EVAL_OUT_LOCAL.relative_to(ROOT)}/",
                       {"files": n})


# ──────────────────────── pipeline definition ────────────────────────


STAGES: list[Stage] = [
    Stage("preflight",          "auto", "directories + manifest + pod reach",      stage_preflight),
    Stage("triage",             "auto", "run v2_ingest_helper (writes _triage.json)", stage_triage),
    Stage("triage-review",      "gate", "human edits _triage.json review→approve/reject", stage_triage_review),
    Stage("apply",              "auto", "move files into approved/, write manifest", stage_apply),
    Stage("prep",               "auto", "512×512 plates + caption stubs in training/", stage_prep),
    Stage("captions",           "gate", "human authors captions per rubric",        stage_captions),
    Stage("validate",           "auto", "validate captions before training",        stage_validate),
    Stage("upload-training",    "auto", "upload training/ to TELUS pod",            stage_upload_training),
    Stage("train",              "gate", "operator runs accelerate training on pod", stage_train),
    Stage("upload-eval-script", "auto", "upload eval_lora.py to pod",               stage_upload_eval_script),
    Stage("eval-run",           "gate", "operator runs eval_lora.py on pod",        stage_eval_run),
    Stage("download",           "auto", "download eval results → local",            stage_download),
]
STAGE_BY_NAME = {s.name: s for s in STAGES}
MANUAL_MARK_STAGES = {"train", "eval-run"}


# ──────────────────────── command surface ────────────────────────


def cmd_status() -> int:
    state = load_state()
    print(f"Pipeline state: {STATE_FILE.relative_to(ROOT) if STATE_FILE.exists() else '(no state yet)'}")
    print()
    print(f"{'#':>2}  {'STAGE':<22}  {'KIND':<6}  {'STATUS':<14}  WHEN")
    print(f"{'-':>2}  {'-' * 22}  {'-' * 6}  {'-' * 14}  {'-' * 19}")
    for i, s in enumerate(STAGES, 1):
        rec = state.get("stages", {}).get(s.name, {})
        status = "✓ done" if rec else "—"
        when = rec.get("done_at", "")
        kind_label = s.kind.upper()
        print(f"{i:>2}  {s.name:<22}  {kind_label:<6}  {status:<14}  {when}")
    print()
    nxt = next_stage()
    if nxt:
        print(f"Next: {nxt.name} ({nxt.kind}) — {nxt.description}")
    else:
        print("All stages complete.")
    return 0


def next_stage() -> Stage | None:
    for s in STAGES:
        if not is_done(s.name):
            return s
    return None


def run_stage(stage: Stage) -> int:
    print(f"\n=== {stage.name} ({stage.kind.upper()}) — {stage.description} ===")
    result = stage.run()
    print()
    print(("  ✓ " if result.ok else "  ✗ ") + result.message)
    if result.extras:
        for k, v in result.extras.items():
            print(f"    {k}: {v}")
    if result.ok:
        mark_done(stage.name, result.extras)
        return 0
    return 1


def cmd_next() -> int:
    nxt = next_stage()
    if nxt is None:
        print("All stages complete. Nothing to do.")
        return 0
    return run_stage(nxt)


def cmd_run(name: str) -> int:
    if name not in STAGE_BY_NAME:
        print(f"Unknown stage: {name}\nKnown: {', '.join(STAGE_BY_NAME)}", file=sys.stderr)
        return 2
    return run_stage(STAGE_BY_NAME[name])


def cmd_mark(name: str) -> int:
    if name not in STAGE_BY_NAME:
        print(f"Unknown stage: {name}\nKnown: {', '.join(STAGE_BY_NAME)}", file=sys.stderr)
        return 2
    if name not in MANUAL_MARK_STAGES:
        print(
            f"Stage {name!r} cannot be manually marked. "
            f"Manual marks are only for: {', '.join(sorted(MANUAL_MARK_STAGES))}",
            file=sys.stderr,
        )
        return 2
    mark_done(name, {"manual_mark": True})
    try:
        display_path = STATE_FILE.relative_to(ROOT)
    except ValueError:
        display_path = STATE_FILE
    print(f"Marked {name} complete in {display_path}")
    return 0


def cmd_auto_until_gate() -> int:
    while True:
        nxt = next_stage()
        if nxt is None:
            print("\nAll stages complete.")
            return 0
        rc = run_stage(nxt)
        if rc != 0:
            # Failed gate (still waiting for human) OR failed auto stage → stop here
            label = "gate" if nxt.kind == "gate" else "failure"
            print(f"\n[halted at {label}: {nxt.name}]")
            return rc
        # Gate that PASSED (human work already done) — keep going to the next auto stage


def cmd_reset() -> int:
    if STATE_FILE.exists():
        STATE_FILE.unlink()
        print(f"Removed {STATE_FILE.relative_to(ROOT)}")
    else:
        print("No state file to remove.")
    print("(Data directories untouched — only the orchestrator's progress tracker was wiped.)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="show stage table + next stage")
    sub.add_parser("next",   help="run the next-due stage and stop")
    sub.add_parser("auto-until-gate", help="run auto stages until first gate or failure")
    p_run = sub.add_parser("run", help="run a specific stage by name")
    p_run.add_argument("stage")
    p_mark = sub.add_parser("mark", help="manually mark an external pod gate complete")
    p_mark.add_argument("stage", choices=sorted(MANUAL_MARK_STAGES))
    sub.add_parser("reset", help="wipe state file (data untouched)")
    args = ap.parse_args()

    if args.cmd == "status":           return cmd_status()
    if args.cmd == "next":             return cmd_next()
    if args.cmd == "auto-until-gate":  return cmd_auto_until_gate()
    if args.cmd == "run":              return cmd_run(args.stage)
    if args.cmd == "mark":             return cmd_mark(args.stage)
    if args.cmd == "reset":            return cmd_reset()
    return 2


if __name__ == "__main__":
    sys.exit(main())
