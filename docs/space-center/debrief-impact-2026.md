# Debrief — IMPACT 2026 (HR MacMillan Space Centre, May 27–28)

**Written:** 2026-06-10 (post-show consolidation) · **Surfaces:** Hubble = SSD installation, Dome = Living Intelligence cosmic-journey · **Call on show morning:** 🟢 GREEN (188/196 probe sweep; no P0 visitor-blockers).

Synthesis of the show-morning audit (`show-morning-audit-2026-05-27.md`), the May sprint memory entries, and post-show collaborator feedback. Source of authority for each quirk is the named project-memory file; this doc is the narrative that ties them together and carries lessons forward to MOVE37XR (Oct 2026).

---

## What worked

- **The core visitor flow held end-to-end.** Submit dream → TD snap-card → dreamworld deep-link (`?dream=<id>` opens the focused panel with cluster context), with semantic clustering visible and kNN neighbor edges drawn. That is the show, and it was wired and serving fresh 540 KB JPEGs on a 4-second cadence with 8h+ server uptime at doors.
- **Event-scoping was clean.** `/dreams/3d` returned IMPACT-only vs Digital-Ecologies-only with zero leakage — the multi-show data separation worked.
- **Integrity gates passed.** All three KG invariants + the entity-links integrity check green. The `scripts/test/` suite (now committed) earned its keep.
- **TELUS sovereignty port mostly landed.** Embeddings (`_embed_via_telus`) and chat (`chat_client`) both verified on TELUS NVIDIA endpoints — off OpenAI for the paths visitors actually touch.
- **The April resilience stack carried over.** Auto-heal / watchdog / tunnel infrastructure from the Salt Spring show kept the box self-healing; remote SSH access held throughout.
- **Chatbot honesty held under adversarial probes.** The "I don't have specific information — try the team" non-answers were the *correct* behavior per the `/about/ai` canon (a confident wrong answer is worse than an honest non-answer), not voice drift.

## What failed under pressure (and the fix)

> **Operator: please sanity-check this section before it's committed** — it's the load-bearing "what actually went wrong" record and I want no mis-attribution.

| # | Issue | Root cause | Status / fix |
|---|---|---|---|
| 1 | **`_label_clusters` still hit OpenAI** | SHOW-10 ported embed + chat to TELUS but missed the cluster-label path (`gallery_server.py:1603`); every UMAP recompute emitted 8× 401s, `clusterLabel` fell back to `"Cluster 2"` | **Mitigated, not fixed.** Visitors never saw it — `/cloud` overrides labels client-side via `improveClusterLabels()`. 10-line post-show fix: swap `openai_client` → `chat_client` in `_label_clusters`. |
| 2 | **NDI source name reverts on reboot** | TD `.toe` resets `ndiin2` source from `DESKTOP-37616PR (Autolume Live)` back to hardcoded `MSI (Autolume Live)`; `in_mean` drops to 0 → TD outputs gray → site shows black snapshots | Fix = re-point source + `Ctrl+S` so it persists. Needs a **persistent NDI config** for Oct. See `project_ndi_source_name_reverts_on_reboot`. |
| 3 | **Autolume sweep produced 0-byte MP4s** | `visualizer.py` starts the recording thread in `stop_recording` (not `start_recording`) and flips `is_recording=False` immediately; frames never reach the queue | Partial fix found (move thread start into `start_recording`); a second bug (no frames in queue) undiagnosed. See `reference_autolume_sweep_recording_bug_2026_05_25`. |
| 4 | **Stale `.pyc` outlived source patches** | Patched `gallery_server.py`, restarted, but old bytecode in `__pycache__` still executed (mtime rounding); `inspect.getsource` misleadingly showed new code | Rule now: delete `__pycache__` first, run with `-B` / `PYTHONDONTWRITEBYTECODE=1`. See `reference_pyc_cache_can_outlive_source_patches`. |
| 5 | **Visitor-visible KG bugs slipped past agent test sweeps** | Agents tested "is the data correct," not "what does the visitor *see*." Operator's manual browser audit (T-1) caught: Austin/Matt missing from `hub:artists.contains`, a floating "Indigenomics Themes" orphan node, incomplete sponsor list | The biggest process lesson. Codified as `feedback_test_from_visitor_perspective_not_data_only` with concrete probe titles to add. |
| 6 | **Shipped a 1.75× too-fast render on ffprobe-only QC** | QC'd an Autolume "2× slow" test with brightness/ffprobe stats instead of watching it; needed ~3.5×, did 2× | `feedback_qc_review_means_actually_watching_the_video` — watch ≥10s in VLC before declaring any video ready. |
| 7 | **Smaller cosmetics** | `/graph-3d` starfield no-ops (`window.THREE` undefined under the bundled `3d-force-graph`); one `Kwaxala` mention left in `/about/mudra` | Both non-blocking; queued post-show. |

## Operational quirks (carry-forward)

- **`.toe` over scp** — always `scp -O`; plain scp truncates binaries at 200 KB. (`feedback_macos_scp_toe_truncation`)
- **Large 3090 files** — upload 3090 → Google Drive directly (wired gigabit), not scp-through-WireGuard (~7 MB/s). (`project_large_file_transfer_3090_to_drive`)
- **OBS plugins over SSH** — GUI installers hang in Session 0 (no UAC display); use the portable-ZIP + per-user `%APPDATA%\obs-studio\plugins\` path. (`reference_obs_plugin_ssh_install_workaround`)
- **3090 critical processes** — `streamdiffusionTD\td_main.py` is the live SD inference loop, never kill without sign-off; check `nvidia-smi` AND process roles before firing compute. (`reference_3090_critical_processes`)
- **Recording path** — Pravin captures Resolume directly on his Mac (4K H.265, 80+ Mbps), not via NDI→3090 OBS, to avoid double encode/decode. 4K masters are the source for the Oct dome equirectangular re-render. (`project_video_recording_specs_2026_05`)

## Collaborator feedback

- **Arshia (SFU MetaCreation Lab)** attended live, positive — *"great catching up… I'd love to keep exploring the ideas we chatted about"* (Signal, May 28). Worth a follow-up thread before MOVE37XR given the Autolume lineage.

## Carry-forward to MOVE37XR (Oct 2026)

The actionable items are detailed in `next-installation-improvements.md`. Headlines: persist the NDI config; adopt visitor-perspective + browser-screenshot test discipline as a gate (not an afterthought); finish the `_label_clusters` TELUS port; make the same-week consent archival a ritual; produce 4K masters for the dome equirectangular pipeline.
