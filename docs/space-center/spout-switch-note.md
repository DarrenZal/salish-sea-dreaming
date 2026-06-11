# Spout Switch — Autolume → Resolume on Same Machine

> **Source:** prompt-03 deep-research report (compass_artifact_wf-e30d4998…) recommends Spout end-to-end on a single machine; NDI adds latency and compression risk on same-host transports. Currently the SSD plan routes Autolume → Resolume via NDI (Section 4 of canonical plan).
>
> **Caveat:** the report's recommendation assumes a generic same-machine media-pipeline scenario. Verify Autolume actually exposes a Spout sender before changing pipeline (see "Verification" below).
>
> **Fact-check update 2026-05-13:** upstream Autolume has no NDI or Spout references. `installation-archive/scripts/autolume_launch.bat` and `patch_instance.py` show the April production path patched `modules/visualizer.py` for custom NDI names/OSC ports, but the patched `visualizer.py` itself is not archived here. Treat current Autolume video output as a local fork/patch dependency until Pravin confirms the exact source.

## What changes

**Today (per plan Section 4):**
```
Autolume (StyleGAN2) ──NDI──▶ Resolume Arena (master)
```

**Proposed:**
```
Autolume (StyleGAN2) ──Spout──▶ Resolume Arena (master)
```

**Why:** both processes are on the same RTX 3090. NDI on localhost still goes through the NDI runtime (encoding + memory copy + decode), which is unnecessary overhead. Spout shares GPU textures directly via DirectX shared resources — zero-copy, sub-frame latency, no compression artifacts.

**Expected gains:**
- Lower end-to-end latency (~1 frame vs ~2-3 frames for NDI)
- No NDI codec artifacts (NDI uses SpeedHQ; lossy at default settings)
- Slightly lower CPU usage (NDI runtime overhead removed)
- More stable source name binding (NDI source-name discovery occasionally drops; Spout sender-name is direct)

## Verification (must-do before changing the pipeline)

**Open question:** does the SSD Autolume fork/patch have a Spout sender option? Upstream Autolume does not advertise video output protocols; the April show apparently used a patched `modules/visualizer.py` NDI path. Confirm one of:

1. **Native Spout sender** in the SSD-patched Autolume output options — check the actual 3090 install, not upstream docs
2. **Spout via Python wrapper** — `Spout-for-Python` library; would need to wire into the patched Autolume output loop
3. **NDI-only local patch** — keep current NDI and document that the report's Spout recommendation does not apply until a Spout sender is implemented

If (1) or (2): switch is straightforward. If (3): keep NDI for May; document that the report's general recommendation does not apply to our current Autolume patch.

## TouchDesigner side (already Spout-ready)

TD has built-in Spout In TOP and Spout Out TOP. The current pipeline already uses Spout for TD → Resolume. Adding an Autolume Spout source would be a new Spout In TOP wired into the existing Resolume composition, replacing the current NDI In TOP.

## Resolume side (also already Spout-ready)

Resolume Arena 7+ accepts Spout sources natively via Sources tab → Add Source → Spout. Should appear once Autolume's Spout sender is publishing.

## Migration steps (if Autolume supports Spout)

1. **Backup current Resolume composition** — `SSD_spacecenter_v1.toe` lineage convention; tag the pre-change state
2. **Enable Spout sender in the SSD-patched Autolume** (per verification above)
3. **In Resolume:** add new Spout In source pointing at Autolume's sender name
4. **Side-by-side test:** route both NDI source AND Spout source into Resolume; compare quality + latency on a test composition
5. **Cut over:** once Spout source confirmed working, disable NDI source in Resolume composition; remove NDI In TOP if any
6. **Soak:** run 30+ min with Spout-only path; verify auto-heal still works (Autolume crash → restart → Spout source reconnects)

## Plan-edit proposal

Section 4 of canonical plan should say:

> Autolume → Resolume via **Spout if supported by the SSD-patched Autolume output path** (same machine, zero-copy GPU texture share). NDI remains the May fallback if the current local patch is NDI-only. Source-name binding: configure Autolume's Spout sender as `autolume_main` if implemented; otherwise retain the known patched NDI source naming.

Note: this is a small change with verification dependency. Defer the actual pipeline switch until **after** the v2 LoRA work is done and the 3090 is back online (currently tunnel-blocked) — no point switching pipeline elements while the 3090 itself is offline.

## When to do this

- **Not blocking for May:** NDI works, has been running on the show for weeks. Switching to Spout is an optimization, not a requirement.
- **Good candidate for the post-Phase 2 cleanup pass** OR for the 5090 build assembly window if it lands (when we're already touching pipeline anyway).
- **If 3090 access returns and we have a quiet window today/tomorrow**, doing the verification step (does Autolume even support Spout?) is ~30 min of work and unblocks the rest.
