# SSD Phase 2 — Current State (snapshot 2026-05-16 eve)

> ⚠️ **SUPERSEDED (2026-06-10).** This is a pre-show snapshot kept for history. For current state see the project `CLAUDE.md` "Current Status" block, `docs/space-center/debrief-impact-2026.md`, and `docs/space-center/next-installation-improvements.md`.

> One-page reorientation index. Last updated 2026-05-16 evening after the Prav call + Squamish Longhouse dome thread resolution.
>
> If you're picking this up tomorrow, read the **Active dependencies** section first — it tells you whether you're blocked or unblocked.

## Overnight results — 2026-05-17 night → 2026-05-18 AM

**Morning review starts here:** `docs/space-center/morning-review-index-2026-05-18.md` — single-page guide to all 2026-05-17 ship-worthy artifacts with show/don't-show status per item.

**Morning checklist:** `docs/space-center/morning-checklist-2026-05-18.md` — what to watch, what's canonical, what failed, what needs Pravin/Austin, what Agent 3 should continue.

**Overnight log (5 priorities executed):** `docs/space-center/overnight-log-2026-05-17-to-18.md`

| Priority | Output | Status |
|---|---|---|
| #1 TheCreator pearl-bridge composite | `morph_outputs_INTERNAL/thecreator-pearl-bridge-composite-2026-05-17/` | DONE. INTERNAL observation, NOT cosmological claim. |
| #2 Abstract primitive-bridge toy demo | `morph_outputs_INTERNAL/lane_2e_abstract_primitive_grammar_toy.mp4` | DONE. 12 clean primitives, no Austin assets, communicates Lane 2E grammar abstractly. |
| #3 Pair-scouting report | `docs/space-center/austin-piece-pair-scouting-report-2026-05-17.md` | DONE. Top 5 piece-pair recommendations + cultural-load notes. No new renders. |
| #4 Curation index | `docs/space-center/morning-review-index-2026-05-18.md` | DONE. |
| #5 Notes/state cleanup | this entry + meeting note update + morning checklist | DONE. |

**Canonical artifacts locked overnight:**
- Salmon swim rig v005 = canonical "salmon alive in piece" (in packet item 08)
- Cosmic_Sun breathing v003c = canonical radial-piece breathing
- Lane 2E concept = ROUTING RULE (not visual deliverable) for future cross-piece morphs

**Failed lanes (preserved as labeled controls — do not promote):**
- Salmon line-swim (v001-v006: TPS, rectification, column-median) — auto-extraction can't unfold formline salmon; needs hand-authored vector puppet
- Salmon big-shapes-alive sprite translation — can't become swimming
- Salmon circle chase — geometry mismatch (orbit vs body length)
- Lane 2E POC v001+v002 — mechanism works but too few atoms to communicate; locked as concept-not-visual
- Roe-particle-field v001+v002 — wrong architecture (Codex worker owns v003)

## REAL overnight shift (2026-05-17 night → 2026-05-18 AM) — second batch

After the preflight 5 priorities, full overnight queue of 5 deeper priorities executed autonomously.

| Priority | Output | Status |
|---|---|---|
| #1 TD/demo readiness | v007 Cosmic→Salmon TD scrub pack (NEW); v006 README added; runbook updated. 5 scrub packs all READMEs present. | DONE |
| #2 Austin review packet v2 | Contact sheet PNG (15 artifacts grid) + HTML index + thumbnails + README. Path: `morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/` | DONE |
| #3 Pair-morph experiments | SCOPED DOWN — only 5 SVGs decomposed; low-risk pairs need un-decomposed Heron/Orca/Octopus SVGs. Time reallocated to #4. | CONSTRAINED |
| #4 Primitive grammar expansion | `primitive_field_v002_flocking_light.mp4` + `primitive_field_v002_flocking_dark.mp4`. 60 atoms curl-noise drift, dual BG. Zero cultural risk. | DONE |
| #5 Production hygiene | Morning-checklist updated with overnight outputs + TD/Resolume ready section. Overnight log finalized. CURRENT_STATE updated (this entry). | DONE |

**Open question for Pravin**: ask Austin whether more vector exports are available for pieces beyond the 5 already decomposed (Cosmic, Raven_Sun, Wolf, Salmon, TheCreator). Would unblock Heron↔Salmon, Orca↔Octopus, and other low-cultural-load pair experiments.

**Morning starts here**: `docs/space-center/morning-checklist-2026-05-18.md`. Contact sheet PNG at `morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/contact_sheet.png` for 30-second one-glance review.

**Single-entry-point demo folder**: `morph_outputs_INTERNAL/morning-demo-folder-2026-05-18/` (4 subfolders + README + HTML index, 27 symlinked artifacts).

**Tomorrow handoff brief**: `docs/space-center/tomorrow-handoff-brief-2026-05-18.md` — what to show Pravin / Austin / avoid / TD-Resolume / Agent 3 + recommended next experiment.

**Source inventory (MAJOR DISCOVERY)**: `docs/space-center/austin-source-inventory-2026-05-18.md` — 7 PDFs available in `austin-v2-ingest/approved/` alongside 5 SVGs. `pdftocairo` installed → unblocks decomposition of 7 more pieces. Heron→Salmon recommended as next morph experiment.

**Verification**: 35/35 artifacts verified intact via `scripts/verify_overnight_artifacts.py`. No canonical overwrites.

## Recent resolutions (2026-05-17 PM — cross-dissolve regression + recovery)

- **TouchDesigner mudra scrubber v006 demo-ready.** Static-output bug fixed by switching from Movie File In TOP index seeking to a 120-frame image sequence; `progress=0` selects `frame_0001.jpg`, `progress=1` selects `frame_0120.jpg`, and output pixels differ across full image bounds. Saved workspace: `td/templates/ssd_morph_mudra_workspace_template_v006_frame_sequence_scrub.toe`; reusable component: `td/templates/ssd_morph_mudra_scrubber_template_v006_frame_sequence_scrub.tox`; frame sequence: `td/templates/assets/cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006/`; runbook: `docs/space-center/td-mudra-scrubber-demo-2026-05-18.md`. Internal-only until Austin per-output OK.
- **ControlNet + Austin v2 LoRA motion finishing test passed on H200.** Raven Sun -> Cosmic Sun 48-frame / 4-sec excerpt holds structure; primitive shapes remain legible, edges stay stable, and LoRA adds warmth/register without inventing new figures in this test. Default candidate: Canny + LoRA 0.35 + denoise 0.30 + ControlNet 0.78. Safer fallback: Canny + LoRA 0.25 + denoise 0.30. Results: `track2-deterministic/morph_outputs_INTERNAL/austin-controlnet-lora-motion-raven-cosmic-2026-05-17/results_r2/`; runbook: `docs/space-center/controlnet-lora-motion-finishing-pipeline-2026-05-18.md`. Internal-only until Austin per-output OK.
- **Cross-dissolve regression caught and reversed.** Earlier "endpoint cleanup" pass overwrote `raven_sun_to_salmon_spawn.mp4` and `cosmic_sun_to_salmon_spawn.mp4` with image cross-dissolves that killed the primitive-motion behavior operator had explicitly liked. Peer agent recovered originals from surviving frame directories (morph engine PNGs survived; only MP4 wrappers were clobbered). Saved as `*_RAW_SHAPE_MORPH_from-frames_2026-05-17.mp4`; cross-dissolves preserved as `*_CURRENT_2026-05-17-1259_crossdissolve-regressed.mp4` (labeled controls — do not promote). Canonical names now alias raw shape morph versions.
- **Versioning discipline locked in.** New doc: `track2-deterministic/morph_outputs_INTERNAL/VERSIONING_DISCIPLINE.md`. No script may overwrite canonical filename — every output requires variant suffix (e.g., `_endpoint_emerge_v001`). Composites encode their input lane variants in filename. Promotion to canonical is operator-confirmed only. Provenance.csv tracks promotions.
- **Experiment lanes spec written.** `docs/space-center/morph-experiment-lanes-2026-05-17.md`. Five parallel lanes: Lane 1 (atom-snap endpoint, MVP shipped as `endpoint_emerge_v001`), Lane 2 (atom-aware: roe-particle-field / central-pivot / body-contour / wolf-salmon symmetry), Lane 3 (primitive-field, positive/negative inversion), Lane 4 (more pair exploration), Lane 5 (catalog cleanup). Multi-pearl is a COMPOSITE — only re-renders when underlying edges have approved lane variants.
- **Lane 1 v001 shipped** (~1:21 PM PT): `raven_sun_to_salmon_spawn_endpoint_emerge_v001.mp4` + `cosmic_sun_to_salmon_spawn_endpoint_emerge_v001.mp4`. Script: `scripts/morph_endpoint_emerge.py`. Technique: preserves morph engine output in frames 0-101, blends destination SVG luma-mask over frames 102-119 with ease-in ramp. Honest naming: structural-emerge, NOT true shape-motion atom-snap (v002+ requires per-frame shape data from morph engine). Operator review pending.

## Recent resolutions (2026-05-16 eve)

- **dome-thread-closed / Squamish Longhouse dome render resolved — NOT a render bug, viewer-format mismatch.** John's latest videos are 360 VR equirectangular for Space Centre workflow. The SAT online viewer (`https://domeport.sat.qc.ca/`) was warping them because it expects fisheye. Preview the new format in VLC. Old fisheye file still works in the SAT viewer with 180/no-tilt setting (link in John's Sat 9:09 PM email, Message-ID `CAKvvtQA6Zh8hq8AXyds24bBu2BWP_d+2o4znYn7ut2PG=gwreA@mail.gmail.com`). Pravin's thread reply confirmed: "render looks good to go for the test. Nothing further should be needed from Dan at this stage." **Black-arc-fill ask is moot — there was no bug.** Next gate = Tuesday 2026-05-19 3-5 PM dome test (John + Dan in Vancouver).
- **Two action items from the 5/16 Pravin call dropped before send** — "send screenshots to Pravin" (already reviewed together in person, in VLC) + "request black-arc fill on dome thread" (superseded by John clarification). Both task files marked `cancelled` with audit trail; backend synced.
- **5090 procurement decision:** buy complete PC from MemEx Victoria (not just-the-card-into-3090). Target spec: 5090 + 64 GB RAM + 1 TB HDD + 1 TB SSD + liquid cooling, ~$8K base + ~$600 for RAM. MOVE37XR asset, Pravin's credit card. Sun MemEx call → potential Sun PM Victoria pickup or Tue en-route pickup. Full doc: `docs/space-center/5090-procurement-options-for-pravin-call-2026-05-16.md`.

## Active dependencies

| Dependency | Owner | What unblocks | Status |
|---|---|---|---|
| Austin's curated Drive folder | Pravin → Austin → Pravin → us | Whole v2 LoRA + Track 2 Austin-data path | **PENDING.** Proton Bridge check on 2026-05-14 found no incoming Austin/INDIGITAL reply; Darren's May 13 "SSD files access + a quick hello" was sent. When Drive lands → drop files into `austin-v2-ingest/inbox/`, then run `python3 scripts/austin_v2_pipeline.py auto-until-gate` |
| Dan Dome specs call | Dan (via Kurt) | Native Dome render format / timeline for Living Intelligence cosmic journey visuals | **QUEUED for 2026-05-14 4 PM.** Specs received: OpenSpace 0.21.3, equirectangular H.265 MP4 `6144x3072`, 30 fps, 8-bit, center 180 degrees; Dan sent OpenSpace encoder links. Hold final Dome media delivery until encoder path is tested |
| 3090 SSH tunnel / TD access | Pravin / Darren | Remote LoRA training, TD pipeline integration, output-path verification | **SSH UP; five-minute flap cause fixed.** Live check on 2026-05-14 returned `DESKTOP-37616PR`; poly `127.0.0.1:2222` is open. Root cause of repeated exits was poly crontab `*/5 * * * * /home/poly/clean_tunnel.sh`; that script killed healthy idle reverse-forward listeners. Cron line disabled 2026-05-14, backup at `/home/poly/crontab.backup.20260515-032306`; post-fix watch through the next former kill window showed no new `Tunnel exited`. **Fallback verified:** `windows-desktop-wg` over WireGuard reaches the 3090; `WireGuardTunnel$wg-koi` is running/automatic. Tailscale is not verified from Darren's Mac today. `C:\Users\user\autolume\modules\visualizer.py` exists and is NDI-based (`NDIlib`, sender `Autolume Live`, `ndi.send_send_video_v2`). No Spout evidence found in that file. TD live-feed callback is locally smoke-tested; live TD/Autolume hookup still needs a safe window so it does not interrupt active 3090 work |
| John's contact channel | Pravin (or via him) | Sending the projector test pack zip | **NEEDED** |
| Prav reply on 5090 spec + Natalia approval | Pravin / Natalia | Hardware procurement decision | **PENDING** (sent earlier) |
| Carol Anne sign-off on protocol/sharing posture | Pravin (async via Signal) | Cultural-protocol floor for show framing | **PENDING** (Prav-owned) |
| GAN-axis question to Arshia | Darren → Arshia | Autolume resolution path for the 2×2560×1600 canvas / 5090 value | **SENT 2026-05-16 ~23:25 PDT** to "Salish Sea Dreaming Tactical" Signal group (Signal ts `1779000294779`). 3-way scoping (1024 retrain ≈5 days vs 120 kimg @ 512 + Real-ESRGAN x4 vs faster box) + canvas-role ambiguity + side note about Pravin's parallel research convergence + unverified NVIDIA Upscaler TOP claim. Awaiting reply. |
| Pravin reflection-on-research | Darren → Pravin | Pravin loop-in + accuracy review of Arshia message | **SENT 2026-05-16 ~23:31 PDT** to Pravin 1:1 Signal (ts `1779000706549`). Acknowledges convergence of his agent's "don't chase native 4K" research with our independent hypothesis; notes NVIDIA Upscaler TOP went into Arshia message as explicit unverified claim; invites Pravin to flag mischaracterizations before Arshia replies. |
| Cross-creature internal experiment lane | Darren / Pravin / Austin | Internal render sequencing without accidental show staging | **POLICY EXISTS.** `docs/space-center/sunday-internal-experiment-lane-2026-05-17.md`: experiment broadly, share narrowly, ship only with Austin's explicit OK. No cross-creature experiments queued tonight. |
| Pearl interior experiment spec | Darren (Sunday AM execution) | Vision direction + 13-experiment menu across 5 tiers for pearl-interior creative work, plus Tier 6 with 49 more ranked ideation items (62 total) | **SPEC WRITTEN 2026-05-16 late eve.** `docs/space-center/pearl-interior-experiment-spec-2026-05-17.md`. Architectural pivot: Blender (Cycles + thin-film iridescence) as primary tool for structural pearl work; SD + Austin LoRA narrowed to thin atmospheric pass only. Re-uses existing `exp4_hybrid_pearl_container_model_2026-05-16.ply` as starting mesh. Tier 0 sanity check → Tier 1 material + motion fix → Tier 2 compositional grammar (operator's Circle+2Crescent+2Trigon vision) → Tier 3 motion dynamics → Tier 4 style pass → Tier 5 TD port. Tier 6 ranked ideation (S+F-A) — top picks: bioregional data driver, tide cycle, bioluminescent pearl, schooling-fish primitives, pearl-rewards-attention, pearl-listens, sonic instrument, cymatic primitives, whale-song driver, triptych-within-triptych. |
| **Austin graph + show architecture spec** | Darren / Pravin (Sunday + sprint week) | Major architectural reframe: show as multi-minute live graph traversal of Austin's 18 pieces, embedded in project's larger living-graph family (salishseadreaming.art dreams + Indigenomics AI dome KG + bioregional + pearl-interior + Austin's pieces) | **SPEC WRITTEN 2026-05-16 late eve, REFINED 2026-05-17 AM with peer-review additions.** `docs/space-center/austin-graph-show-architecture-2026-05-17.md`. Refinements: place-anchored Salish Sea substrate (coordinate-system fork, not whole-aesthetic fork); pearl-bead-on-edges concept added (graph alive with traveling pearls each carrying a real-time morph — unifies graph + morphs + pearl into one logic); D-4 recombination corrected (exploration-OK internal, use-needs-Austin-OK); ranking bug fixed; scope distinction made honest (conceptual reduction vs technical TD layer); legibility risk + docking framing called out; cultural language softened ("visual relationship" not "teaching" externally). |
| **Pearl-bead-on-edges prototype mockup** | Darren (rendered 2026-05-17 AM) | Static visual demonstrating pearl-bead concept for 4pm Pravin call | **RENDERED.** `track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/`. Four artifacts: 01_progression_3stage.png (pearl at t=0/0.5/1.0), 02_single_scene_t05.png (1920×1080 hero), 03_animation_strip.png (8-frame strip), 04_pearl_bead_traversal.mp4 (4-sec @ 24fps). v1 was too dark per operator + peer feedback; v2 re-rendered with brighter texture-dominant approach (reduced radial shading, subtle rim, tiny specular). Uses Exp 2 Raven_Sun→Cosmic_Sun morph clip as texture data. PIL-composite (NOT true 3D UV-mapped); legibility caveats noted in README. Internal-only with provenance.csv row + README. Generated by `scripts/pearl_bead_mockup.py`. |
| **Multi-pearl-on-multi-edges mockup** | Darren (rendered 2026-05-17 AM) | Demonstrates polyphonic "graph alive with multiple morphs in flight" — 3 Austin nodes in triangle (Raven_Sun, Cosmic_Sun, Salmon_Spawn) with 2 pearls traversing different edges simultaneously | **RENDERED.** `track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/`. 4 artifacts: 02_multi_pearl_hero_t045.png (1920×1080 hero), 03_multi_pearl_strip.png (8-moment strip), 04_multi_pearl_animation.mp4 (5-sec @ 24fps). Uses 3 different morph clips as edge-texture sources. Generated by `scripts/multi_pearl_mockup.py`. |
| **Primitive cycle video** | Darren (rendered 2026-05-17 AM) | 18-sec continuous Circle→Crescent→Trigon→Circle morph cycle — demonstrates Austin's three fundamental shapes (Coast Salish primitives) for 4pm call | **RENDERED.** `track2-deterministic/morph_outputs_INTERNAL/primitive-cycle-2026-05-17/01_circle_crescent_trigon_circle.mp4`. Concatenation of 3 existing primitive morphs (prim_circle_to_crescent + prim_crescent_to_trigon + prim_trigon_to_circle) into one continuous video. Provenance.csv entry added. |
| **Austin atom decomposition + AI classification** | Darren (Sunday morning) | 504 atoms across 5 SVG pieces decomposed into isolated PNGs + context PNGs + metadata CSV with AI-classified Coast Salish formline labels | **COMPLETE.** `austin-v2-ingest/decomposed/`. Pipeline: `scripts/decompose_austin_pieces.py` (SVG → isolated atom PNGs + context highlights via ImageMagick + xml.etree), `scripts/build_atom_catalog.py` (full sortable HTML grid), `scripts/build_primitives_catalog.py` (focused 3-column view of Circle/Crescent/Trigon). 4 sub-agents ran in parallel for AI labeling (image-reasoning via Read tool on PNGs, classify into 15-class formline taxonomy, Edit CSV). Findings: Wolf is 2-fold rotational symmetry (NOT 4-fold) with 2 wolves joined by central hub; Salmon is two-salmon yin-yang with 184 roe forming field around composition; Raven_Sun shares Cosmic_Sun's trigon-spike vocabulary (stable primitive library); **TheCreator contains literal pearl-with-being-inside structure (atom_0114 = dark sphere + atom_0117 = small held figure)** — Austin's own composition resonates with our pearl-interior concept (surface as observation only, do not claim). 179 primitives total across all 5 pieces (43 circle / 78 crescent / 58 trigon). |
| **More morph experiments rendered Sunday AM** | Darren | Cosmic_Sun↔Salmon (Nature↔Animal trophic edge) + Raven_Sun↔Salmon (origin-light↔return narrative) added to internal library | **RENDERED.** `track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn.mp4` (5 sec) + `raven_sun_to_salmon_spawn.mp4` (5 sec). Provenance.csv entries added. New rows added to `track2-deterministic/morph_pairs.csv`. |
| **Blender Pearl Tier 1.1 material setup script** | Darren (ready to run on 5090 when delivered) | Blender Python script that imports existing exp4 .ply mesh + applies iridescent oyster-pearl Principled BSDF (transmission 0.85, IOR 1.55, thin-film 450nm, subsurface scattering, coat layer) + soft 3-light setup + Cycles render | **WRITTEN.** `scripts/setup_pearl_material_blender.py`. Run with `blender --background --python ... -- --output <png_path>`. Saves a .blend file for interactive iteration. For Tue arrival of new machine. |
| **4pm Pravin call brief** | Darren (call at 4pm Sun) | Scrollable cheat-sheet for the Sunday 4pm call: lead with pearl-bead concept (one decision ask only), unpack only if engaged, hold the 27 experiments + place substrate | **WRITTEN.** `docs/space-center/pravin-4pm-call-brief-2026-05-17.md`. Per peer's strip-down. Updated with TheCreator pearl-bridge finding. |

## Today's deliverables (2026-05-13) — done

| Artifact | Path | Notes |
|---|---|---|
| **John projector test pack v1** | `austin-reference/john-projector-test-pack-v1_2026-05-13.zip` | 14 MB, 4 PNGs + README. SHA256 prefix `cada4bad`. |
| John handoff message draft | `docs/space-center/drafts/john-handoff-message-2026-05-13.md` | Paste-ready when contact arrives |
| Austin/Prav drive-received draft | `docs/space-center/drafts/austin-prav-drive-received-message-2026-05-13.md` | Paste-ready when drive lands |
| **Austin consent + review packet** | `docs/space-center/austin-consent-map.md`, `docs/space-center/austin-review-packet-2026-05-14.md` | Canonical approval map now covers source assets, AI workflows, output queue, public language, attribution, retention, revocation, and tomorrow's Austin review agenda |
| **Pending Austin public-language drafts** | `docs/space-center/drafts/wall-card-pending-austin-review-2026-05-14.md`, `docs/space-center/drafts/sponsor-impact-program-copy-pending-austin-review-2026-05-14.md`, `docs/space-center/drafts/internal-team-description-pending-austin-review-2026-05-14.md` | Wall card, sponsor/IMPACT copy, and internal team description drafted with ownership matrices + line IDs. Consent map public-language table now references the exact lines needing approval |
| **Day 4 execution plan** | `docs/space-center/day4-execution-plan-2026-05-14.md` | Branch plan for Drive landed / no Drive / v2 pass / v2 fail / 3090 tunnel return. Defines Day 4 end targets and no-go list |
| **Triptych show integration board** | `docs/space-center/triptych-show-integration-board-2026-05-14.md` | Maps all ready scripts/assets into left/center/right panel roles, layer stack, 7-minute breath cycle, live-data mappings, approval gates, and Resolume/TD handoff shape |
| **Resolume show package checklist** | `docs/space-center/resolume-show-package-checklist-2026-05-14.md` | Defines the projector-ready package structure, variants for Drive/no-Drive states, clip specs, provenance/approval records, hard exclusions, and Resolume layer order |
| **Resolume package scaffold + validator** | `scripts/scaffold_resolume_package.py`, `scripts/validate_resolume_package.py` | Creates clean show-package folders/templates, then validates required dirs, panel media dimensions, mixed frame rates, hard-exclusion tokens, and provenance filename coverage |
| **Moonfish / Denning reuse confirmation packet** | `docs/space-center/moonfish-denning-reuse-confirmation-2026-05-14.md` | Inventories the 8 ready hero subclips, flags mixed frame rates, defines written permission questions, and includes paste-ready asks for Moonfish Media and David Denning |
| **IMPACT Hubble + Dome integration brief** | `docs/space-center/impact-hubble-dome-integrated-experience-2026-05-14.md` | Corrects framing to two surfaces in one IMPACT event arc; maps visitor app / KG bridge; preserves Hubble vs Dome content boundaries |
| **Friday Dome asset brief** | `docs/space-center/dome-cosmic-journey-friday-asset-brief-2026-05-14.md` | Defines the 10 concept visuals/GIFs for Carol Anne's AI presentation, with title list, style rules, and "pre-recorded first" boundary |
| **Friday Dome concept assets** | `scripts/generate_dome_cosmic_journey_assets.py`, `output/dome-cosmic-journey-2026-05-15/`, `output/dome-cosmic-journey-2026-05-15.zip` | Generated 10 abstract KG constellation stills (1920x1080) + 10 GIFs (960x540), contact sheet + manifest included. Zip 23 MB, SHA256 starts `59e69436`. Concept material only until Dan confirms native Dome specs |
| **Dome coordination drafts** | `docs/space-center/drafts/carol-anne-shawn-dome-assets-handoff-2026-05-14.md` | Carol Anne/Shawn Friday asset handoff draft staged but should be held or revised pending Dan specs unless concept visuals are requested before native render format is known |
| **Visitor app v5 IMPACT integration spec** | `docs/space-center/visitor-app-v5-impact-integration-spec-2026-05-14.md` | Corrected after Kurt reply: Whova owns survey/polling/word-cloud; Hubble app stays a graph/offering bridge and should not implement survey intake |
| **Prav catch-up call prep** | `docs/space-center/prav-catchup-call-prep-2026-05-14.md` | Current call brief with Austin/Drive status, Hubble blockers, Dan/OpenSpace specs, Whova scope correction, 5090 decision, and recommended asks |
| Pearl triptych mock | `austin-reference/pearl-triptych-mock/` | Non-AI PIL proof: 3840×1080 continuous + 3× 1920×1080 panels + seam_check_overlay. No Austin motifs. |
| v2 ingest pipeline scaffold + orchestrator | `austin-v2-ingest/`, `scripts/austin_v2_pipeline.py`, `scripts/validate_v2_captions.py` | Hard reject filters, caption rubric, caption validator, FIRST_HOUR checklist, manifest skeleton, status-table orchestrator. Validator self-test passes and catches rehearsal placeholder captions. Production ingest dirs restored pristine: `inbox/`, `approved/`, `training/` contain only `.gitkeep`; no `.pipeline-state.json`. Preflight treats TELUS reach as warning so local triage/caption work can proceed if pod is temporarily unreachable. External pod gates use `mark train` / `mark eval-run` after the operator completes the pod command |
| Track 2 deterministic morph engine — DRY RUN | `track2-deterministic/` | See "Track 2 dry run" section below |
| **v2 ingest pipeline rehearsal** (proven on 8 clean plates) | `austin-v2-ingest/REHEARSAL_FINDINGS_2026-05-13.md` | Pipeline works end-to-end. Caught 1 bug (hardcoded paths), shipped fix (`--root` override). Calibration: ~45 min wall-clock for ~30-plate real drop |
| **Fact-check pass on 4 claims** | `docs/space-center/fact-checks-2026-05-13.md` | ⚠️ **Autolume NDI output not in upstream** — flag for Pravin re: April patch source. Other 3 confirmed (Orbbec/TD, CHS IWLS 07735, SAGE/VTG) |
| **Autolume output patch evidence** | `docs/space-center/spout-switch-note.md`, `installation-archive/scripts/autolume_launch.bat`, `installation-archive/scripts/patch_instance.py` | Live 3090 `visualizer.py` checked 2026-05-14: NDI output is present; no Spout evidence in the file. Treat NDI as the verified current path until a deliberate Spout patch is built/tested |
| **Live feed OSC contract + bridge** | `docs/next-iteration/_research/live-feed-osc-contract.md`, `scripts/bioregional_osc_bridge.py`, `scripts/test_bioregional_osc_bridge.py` | End-to-end local OSC receiver test passed against live IWLS Vancouver 07735 + Fraser 08MF005. Received all 8 contract addresses with expected packet types |
| **TD live-feed receiver callback** | `scripts/td_bioregional_osc_callbacks.py`, `scripts/test_td_bioregional_callbacks.py`, `docs/space-center/td-live-feed-receiver-2026-05-13.md` | Standalone TD OSC In DAT callback for `/sea/*`, `/river/*`, `/system/*`. Local fake-TD smoke passed: storage writes, table upsert, unknown/bad payload ignore. Recommended TD port `7001` to avoid visitor/audio port `7000` |
| **TELUS scripts archived locally** | `austin-v2-ingest/telus-scripts-archive/` | Pod reachable. Pulled v1/v1.5 train/eval/checkpoint/IP-Adapter/AnimateDiff scripts so v2 work survives pod reset |
| **Temporal style-transfer fallback plan** | `docs/space-center/temporal-style-transfer-fallback-2026-05-13.md` | Recovery path from failed AnimateDiff: real footage motion + v2 style post-process + optical-flow propagation; Track 2 remains center shape-bearing layer |
| **Temporal style smoke inputs + runner staged** | `docs/space-center/temporal-style-smoke-runbook-2026-05-13.md`, `scripts/prepare_temporal_style_smoke.py`, `scripts/run_temporal_style_smoke.py`, `output/temporal-style-smoke-2026-05-13/` | Three clean 5s 1280×720/24fps video-only excerpts from H2/H5/H8 plus a dry-run-tested runner for sparse keyframe style transfer + OpenCV optical-flow propagation. Ready for TELUS upload if v2 LoRA passes still eval |
| **`scripts/eval_lora.py` parameterized** | `scripts/eval_lora.py` | Single eval runner for every LoRA version. `--version v2` swaps trigger to `austin_v2`. `--dry-run` validates locally without GPU. Replaces inline FIRST_HOUR eval block + per-version copy-paste. Smoke-tested locally with `--dry-run` (28-render matrix prints clean for v2; 14 renders for v15+2 scales). |
| 5090 build spec (verified pricing) | `docs/space-center/5090-build-spec-2026-05-13.md` | $5,499 CAD GPU verified vs MSRP-anchored memory error caught + corrected |
| Memory entries (8 new) | `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/` | Most important: `feedback_verify_pricing_before_sponsor_facing.md`, `project_v1_lora_finding_2026-05-13.md`, `feedback_austin_consent_trust_floor.md` |

## Track 2 dry run — engine ready for Austin's vectors

Built today as the production-safe motion path. Schemas + tooling are the same that Austin's data will populate.

| Artifact | Path | Status |
|---|---|---|
| README + decomposition workflow | `track2-deterministic/README.md`, `decomposition-workflow.md` | ✅ |
| Auto bbox/centroid (svgpathtools) | `track2-deterministic/scripts/compute_svg_bbox.py` | ✅ tested on bezier SVG |
| Morph engine (svgpathtools resample, easing, MP4 compile, approval gate + summary) | `track2-deterministic/scripts/morph_engine.py` | ✅ approval gate proven — refuses dry-run rows by default |
| Composed-scene dry run (3 elements, orbits, breath, triptych split) | `track2-deterministic/scripts/compose_pearl_dry_run.py` | ✅ 168 frames @ 1920×1080 + 3× panel-cropped MP4s |
| Austin screenshare worksheet template | `track2-deterministic/austin-screenshare-worksheet-template.md` | ✅ ready for Signal walkthrough |
| Boundary doc | `track2-deterministic/DRY_RUN_README.md` | ✅ "[DRY-RUN PLACEHOLDER — NOT ARTWORK]" fence on every render |

**When Austin's vectors arrive:** decompose in Inkscape → run `compute_svg_bbox.py` → walk through screenshare worksheet → flip approved rows → run `morph_engine.py` (no flags) → only Austin-approved morphs render.

## Strategic anchors (don't drift from these)

- **Plan:** `~/.claude/plans/ok-so-i-polymorphic-melody.md` (14 sections, lint-clean, 3 Codex rounds)
- **Date:** 2026-05-13 (Phase 2 sprint Day 3 of ~14, doors May 25)
- **Venue:** HR MacMillan Space Centre, Hubble Space — Indigenomics IMPACT (same event, clarified)
- **Cultural floor:** per `feedback_austin_consent_trust_floor.md` — per-output OK is the floor not the milestone. Default-pause, not default-ship. Public framing language ("pearl", "teaching", "three shapes") in scope, not just visual motifs.
- **Consent map:** `docs/space-center/austin-consent-map.md` is the canonical approval record for source assets, AI workflows, generated outputs, Track 2 morphs, public copy, attribution, retention, and revocation.
- **License policy:** CC0 / CC BY / CC BY-SA only for any non-Austin material. CC BY-NC excluded.
- **IMPACT framing:** Hubble Space SSD and Dome Living Intelligence are two surfaces in one event arc. Hubble uses water / pearl / Austin-approved triptych grammar; Dome uses constellation / graph grammar. Whova owns survey/polling/word-cloud on a standard screen unless scope changes.

## Tomorrow's first 3 actions (priority order)

Start with `docs/space-center/day4-execution-plan-2026-05-14.md` if more than one dependency changed overnight.
Use `docs/space-center/triptych-show-integration-board-2026-05-14.md` when deciding what any generated or pre-rendered asset is actually for.
Use `docs/space-center/resolume-show-package-checklist-2026-05-14.md` before anything is handed to John, Prav, or venue testing as a show-content package.

1. **Status-check:** has Austin's drive landed overnight? If yes → drop files into `austin-v2-ingest/inbox/` and run `python3 scripts/austin_v2_pipeline.py auto-until-gate`. Use `FIRST_HOUR_AFTER_DRIVE_LANDS.md` as the operator/runbook reference. If no → skip to 2.
2. **Status-check:** is the 3090 safe to use interactively? SSH is up and the five-minute cleanup bug is disabled; ask/confirm before opening TD or Autolume if Prav is actively using the box. Use `windows-desktop-wg` if the poly reverse tunnel misbehaves.
3. **Status-check:** any reply from John (contact info), Natalia (5090 sign-off), Carol Anne (protocol)? Each unblocks a specific message-send.

If all three are still pending → continue Track 2 dry-run / pearl mock refinement on local CPU, or run the temporal-style smoke only after a v2 LoRA passes still eval. TD live-feed testing still needs a safe TD runtime window; local `127.0.0.1:9981` is currently closed. **Do not start more generative experiments dependent on `austin-reference/` (the scrape).** Per today's finding: clean-subset v1.5 LoRA proved the recipe; further experiments on stale scraped data won't surface new information.

## Reference: pre-2026-05-13 production stack (intact, dormant since exhibition wrap)

Autolume 120 kimg + StreamDiffusion sd-turbo + Resolume Arena + visitor web app + auto-heal + SSH reverse tunnel + visitor MediaPipe mudras. Briony layer DROPPED for Phase 2 (Coast Salish aesthetic mismatch). Production-stack changes for Space Centre are tracked in the canonical plan, not here.

## Memory index (most-relevant for Phase 2)

Top of mind for any new session:

- `feedback_austin_consent_trust_floor.md` — per-output approval floor
- `feedback_austin_no_ai_generation.md` — Austin's evolved stance (style transfer top priority per Prav 2026-05-13)
- `project_austin_pearl_vision.md` — pearl + 3 shapes dramaturgical container
- `feedback_exploration_over_lockin.md` — don't lock in early
- `feedback_visitor_interactivity_primary.md` — visitor app + MediaPipe are PRIMARY content surfaces, not Tier-2
- `feedback_verify_pricing_before_sponsor_facing.md` — always web-verify before sponsor-facing send
- `project_v1_lora_finding_2026-05-13.md` — v1 LoRA scale-vs-coherence trade-off; v2 fixes via element-level captions
- `project_kwaxala_is_ours.md` — Kwaxala is Darren's framing; don't bother Carol Anne to "verify"
- `reference_telus_access.md` — TELUS H200 token already in `.env`; no provisioning needed
- `feedback_ssd_email_address_per_thread.md` — SSD venue thread = `darrenzal@protonmail.com` not gmail
- `reference_proton_send_skill.md` — `proton-send` skill wraps local Proton Bridge SMTP
