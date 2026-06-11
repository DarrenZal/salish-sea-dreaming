# Next-Installation Improvements — toward MOVE37XR Dome (Oct 2026)

**Written:** 2026-06-10 · **Source:** `debrief-impact-2026.md` + the May sprint memory entries · **Next target:** MOVE37XR Dome Theatre, October 2026 (then DEVCON ETH Mumbai, Nov 2026). Strategic context lives in `~/.claude/plans/ok-so-i-polymorphic-melody.md` — this doc is the concrete pre-work list, not a re-statement of the plan.

The dome is a different surface from the Hubble flat-wall: 360° equirectangular/fisheye projection, longer dwell (30s–8min), anteroom + main hall. Improvements below are grouped by whether they're **fixes** (close a known IMPACT gap), **hardening** (make the run more robust), or **process** (how we work between now and Oct).

## Fixes — close the IMPACT gaps

1. **Finish the TELUS port** — swap `openai_client` → `chat_client` in `_label_clusters` (`gallery_server.py:1603`). 10-line edit; removes the 401 log noise and the `"Cluster N"` fallback. (Debrief #1)
2. **Persist the NDI config** — stop the `.toe` reverting `ndiin2` to the MSI name on reboot. Either bake `DESKTOP-37616PR (Autolume Live)` into the saved `.toe` and verify it survives a cold boot, or add a startup script that re-points + saves. This caused black output at IMPACT. (Debrief #2)
3. **Autolume sweep recording** — fix the `visualizer.py` thread-lifecycle bug (start the recording thread in `start_recording`) AND diagnose the "no frames in queue" second bug, so sweeps stop producing 0-byte MP4s. (Debrief #3)
4. **graph-3d starfield** — rebuild against a THREE-exposing bundle (or import THREE separately) so the cosmic register matches dreamworld. Higher value on the dome where the starfield IS the surround. (Debrief #7)

## Hardening — make the dome run robust

5. **Boot-clean verification** — a post-boot health probe that asserts the *right* processes are up and NDI is flowing (`in_mean` ≈ 0.5, not gray), not just "a process exists." The April `SSD-Post-Boot-Verify` task is the skeleton; extend it with the NDI-flow check.
6. **`PYTHONDONTWRITEBYTECODE=1` on the gallery service** — permanently, so a stale `.pyc` can never outlive a show-day patch again. (Debrief #4)
7. **4K master pipeline for the dome** — Pravin captures Resolume at 4K H.265 on his Mac; build/validate the equirectangular/fisheye re-render path from those masters early, not show-week. (`project_video_recording_specs_2026_05`)
8. **Carry the resilience stack forward, deliberately** — the auto-heal / watchdog / tunnel set worked; re-archive its dome-tuned version into `installation-archive/move37xr-2026/` when that show is built (same pattern as `impact-2026/`).

## Process — how we work toward Oct

9. **Visitor-perspective testing as a gate, not an afterthought.** The most expensive IMPACT lesson: agent test sweeps validated data-correctness and missed three visitor-visible bugs (Austin absent from the artists hub, a floating orphan node, an incomplete sponsor list) that the operator's manual browser walk caught at T-1. Adopt the concrete probes from `feedback_test_from_visitor_perspective_not_data_only`: `kg_hub_contains_completeness`, `kg_no_floating_bridge_nodes`, `kg_source_of_truth_diff`, `kg_visitor_click_path`. Browser screenshots, not just curl JSON.
10. **Watch the video before shipping it.** ≥10s in VLC, pacing matched to reference, before any render is called ready. (`feedback_qc_review_means_actually_watching_the_video`)
11. **Consent archival as a same-week ritual.** The IMPACT post-show dream-consent archival ran ~12 days late (sequenced in `TODO.md` / the consolidation plan, still pending). For the dome: pre-write the flip→seed→archive steps into the show's closeout checklist so the "not kept after show" choice is honored within days, not weeks.
12. **End-of-sprint consolidation cadence.** This consolidation found 387 untracked files / 96 GB and 17 days without a commit. Adopt a lightweight weekly (or end-of-sprint) pass: commit text research, gitignore large renders, archive the production stack — so we don't rebuild this backlog before Oct.

## Deferred tech spikes (from the Phase 2 plan — decide timing for Oct)

These were consciously deferred past IMPACT; the dome is the natural home for them. Re-scope each against Oct capacity:
- **StreamDiffusion live style layer** (SDTD) as a live register on the dome.
- **Voice / ambient ASR** input.
- **Kinect / mocap** spike for embodied interaction.
- **5090 build** — if it lands, swaps into production; otherwise 3090 ships for Oct as it did for IMPACT.
