# Salmon Trajectory Grammar - Design - 2026-05-19

Agent A lane. Internal design pass only. No rendering in this document. No contact with Austin, Pravin, or anyone else. No new SD/LoRA work. No edits to Agent B/C/D output folders.

Status: internal design hypothesis for an Austin-review-needed lane. This does not claim Austin authorship, does not assign cultural meaning to primitives, and does not approve public use.

Machine companion (proposed, not yet written): `track2-deterministic/primitive_grammar/salmon_trajectory_recipes_v001.json`. Conforms to `track2-deterministic/primitive_grammar/grammar_v001.json` instance schema.

## Sources Read

- `docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md`
- `docs/space-center/austin-informed-water-phrase-recipes-2026-05-19.md`
- `docs/space-center/primitive-grammar-contract-2026-05-19.md`
- `docs/space-center/deep-research-implementation-brief-2026-05-19.md`
- `docs/space-center/salmon-swim-rig-next-experiments-2026-05-17.md`
- `track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v002_2026-05-19/README.md`
- `track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v003_2026-05-19/README.md`
- `track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v004_2026-05-19/README.md`
- `track2-deterministic/morph_outputs_INTERNAL/primitive_water_grammar_v005_2026-05-19/README.md`
- `scripts/primitive_water_grammar_v5.py` (existing nearest-neighbor tracker, lines 484-528)

## The Core Idea

Real salmon footage drives primitive marks placed in the *water around* each moving fish, not on the fish body. The fish itself is never drawn in the primitive layer. What is drawn is the wake the fish has left, the place the fish is now, and the water the fish is about to disturb. Each fish becomes a tiny river in motion, and the existing water-phrase grammar follows it.

The result is a water layer that happens to be modulated by salmon presence, not a fish-figure layer pretending to be water.

## How This Lane Differs From The Rejected Fish-Glyph Lane

The rejected lane (v004 `01_articulated_fish_glyph` and `02_salmon_proxy_articulated`, v005 `03_articulated_fish_glyph` and `04_salmon_proxy_articulated_smoothed`) built fish *figures* out of primitives. Trigon head, crescent gill, circle body or eye, tapering crescents, trigon tail. Darren's v004 feedback already flagged these as marker-like, and Austin's screen-share brief flagged figure-construction as needing direct Austin approval before any public use.

The fish-glyph lane treats primitives as anatomy. This lane treats primitives as water marks.

| Concern | Rejected fish-glyph lane | Salmon trajectory lane (this design) |
|---|---|---|
| What primitives represent | Anatomical parts: head, gill, body, eye, tail | Water states: wake, anchor, intention |
| Where they sit | On the fish body | In the water around and behind the fish |
| Cultural load | High - reads as named being / specific figure | Low - reads as water response to motion |
| Approval status under primitive-grammar-contract | `Austin-review-needed` for fish role binding | Internal water role, still `Austin-review-needed` for any salmon-derived motion |
| Risk if Austin rejects | Whole lane parked | Re-cast layer as pure current grammar; trajectory anchors become impact/knot anchors not bound to fish |
| Reuse from existing recipes | New "fish" role | Recipe 01 (Pond Ripple), Recipe 02 (River Bend / Eddy Cluster), Recipe 04 (Current Knot) all apply directly to the trajectory geometry |

If Austin says "no body-center circles" on Wednesday, the rejected lane breaks. This lane survives - the same data simply renders as offset wake marks or current knots and the fish position becomes hidden.

## Past / Present / Future Grammar Mapping

Each tracked salmon produces three primitive bundles per frame.

### Past Trail - Fading Crescents

- Buffer the last N frame positions of each track (N around 20-30 frames at 24fps, so ~1 second of wake).
- Place 3-5 crescents along that path, sampled at increasing temporal intervals so the oldest marks are sparsest.
- Cup direction: crescents cup back toward the present anchor, so they read as ripples being left behind, not as ripples chasing the fish.
- Opacity falls off with age. Oldest mark is faintest. Newest mark is strongest but still below present-anchor brightness.
- Scale falls off slightly with age. The oldest crescent is the smallest.
- Tangent: each crescent rotates to the local trajectory tangent at the sampled frame, not the current heading. The wake bends with the path.

### Present Anchor - Circle Or Current Knot

- One small circle per track at the smoothed current position, OR offset perpendicular to the heading by about one fish-body radius (above, beside, or behind the visible head).
- The perpendicular-offset variant is the safer first version because it explicitly does not land on the body center or on the eye location.
- Lower opacity than v005's body-center circle. The anchor reads as "attention to this point in the water" not as "this is the fish's eye".
- Optional behavior: omit the present anchor entirely and let past trail and future intention do all the work. This is the cleanest water-grammar read and the recommended fallback if Austin rejects on-body or near-body circles.

### Future / Intention - Faint Crescents Or Single Trigon Ahead

- Predict 5-15 frames ahead using smoothed velocity and a short Kalman one-step or simple linear extrapolation.
- Place one faint crescent at the +5 to +8 frame prediction and an optional trigon at the +12 to +15 frame prediction.
- The trigon points along the predicted heading. It reads as attenuation of motion, the leading edge of intention.
- Very low opacity. The future bundle must read as forethought, not as a second fish or a ghost.
- If prediction confidence is low (recent direction changes, high Kalman covariance), drop the future bundle entirely for that track on that frame rather than draw a noisy guess.

### Phrase Order Across The Bundle

Reading the three bundles together along the direction of travel, the salmon trajectory writes the canonical phrase order in water:

```text
trigon (faint, ahead) <- crescent (faint, just ahead) <- circle (present anchor) <- crescent (newest wake) <- crescent (older wake) <- crescent (oldest wake)
```

Reversed and read in the order the water sees the fish pass:

```text
circle impact at present -> crescents in widening wake behind -> trigon attenuation as the disturbance dies
```

That is exactly Recipe 01 Pond Ripple, projected onto a moving point. The phrase contract from `primitive-grammar-contract-2026-05-19.md` and `austin-informed-water-phrase-recipes-2026-05-19.md` already covers this read.

## Salmon Trajectory As Moving River

The Austin water examples treat river bends, eddies, and rocks as natural cluster anchors. This lane reuses that observation by treating each peak of trajectory curvature as a cluster anchor in its own right.

- Where a tracked salmon changes direction sharply (curvature peak above a threshold), drop a Recipe 02 River Bend cluster at that point in the wake: small circle at the inside of the bend, crescent on the outside, second crescent curling back, trigon exiting downstream.
- Where two tracked salmon paths cross, drop a Recipe 04 Current Knot cluster at the crossing point: circle at knot, crescent on each tangent, trigon on the dominant release.
- Where a track ends (fish exits frame or detection drops), drop a Recipe 01 Pond Ripple terminator: circle, two attenuating crescents, trigon. The fish leaves the water with a closing ripple.

These three composition rules let the lane reuse Agent C's recipe vocabulary unchanged. No new primitive shapes, no new palette roles, no new projection modes are required. The instance schema in `grammar_v001.json` already carries every field needed.

## Tracking Methods

### MVP - Reuse The v005 Nearest-Neighbor Tracker

`scripts/primitive_water_grammar_v5.py` already contains:

- `detect_salmon_candidates(frame, flow)` - local-darkness detector with PCA axis disambiguated by RAFT-style sparse flow
- `track_update(tracks, detections, next_id, frame_idx)` - nearest-neighbor association, EMA position smoothing at 0.72/0.28, length and angle smoothing, persistent track IDs, 12-frame missing tolerance
- Track dict already carries `x, y, angle, length, age, missing, phase_offset, seen_frame`

To produce the salmon trajectory lane, add only:

1. A per-track ring buffer of the last 30 smoothed positions, headings, and velocities.
2. A per-track Kalman one-step prediction or linear extrapolation for +5, +10, +15 frames using EMA velocity.
3. A renderer that consumes the buffer + prediction and emits past-trail crescents, present anchor, and future-intention marks at the configured opacity profile.

Everything else is already there. Expected diff against `primitive_water_grammar_v5.py` is on the order of 80-120 lines, mostly the new renderer.

### Stronger Path - Multi-Object Tracking And Point Tracking

Optional upgrades, in order of how cleanly they slot into the MVP without forcing a rewrite.

- **ByteTrack on top of a fish-class detector.** A generic YOLOv8 with a `fish` class label (or even the COCO `person` class repurposed for elongated objects) can replace the local-darkness detector and feed ByteTrack for cleaner ID persistence. ByteTrack handles brief occlusions better than nearest-neighbor alone.
- **Point tracking with CoTracker or PIPs++.** Picks a sparse set of points on the salmon body in the first frame and tracks them through occlusion and motion blur. Gives smoother, more visually convincing trajectories than detect-and-associate, especially in turbid H6/H7 footage where detection is fragile.
- **Dense optical flow with RAFT.** Already used by the v002 ocean/kelp clip. Integrating dense flow over time gives streamlines that look like wake-grammar already. Not per-fish, but per-region; useful for the dense-school case below.
- **Kalman filter for future intention.** Instead of linear extrapolation, run a 2D constant-velocity Kalman per track. The covariance ellipse becomes a natural gate on whether to draw a future bundle at all.

These can be added incrementally without breaking the MVP renderer, because all of them produce the same downstream artifact: a per-frame list of (track_id, x, y, vx, vy, confidence).

### Dense School Path - Farneback Streamlines

For H4_dense_school and H7_spawn_feast, individual tracking will fail. Too many candidates per neighborhood, too much occlusion, too short a track lifetime.

In that regime, switch to Farneback dense flow and integrate it forward and backward from a sparse grid of seed points to produce streamlines. Each streamline plays the role of one trajectory. Past, present, and future segments along each streamline get the same primitive treatment. The bundle count per frame is capped to keep the screen sparse.

This degrades gracefully: in clear footage the streamlines look like discrete fish trajectories, in dense footage they look like a coordinated current pattern. Either reading is acceptable as water grammar.

## Candidate Footage

Existing hero-subclips, ranked for this lane.

| Clip | Suitability | Notes |
|---|---|---|
| `media/hero-subclips/H1_salmon_school.mp4` | Best | Discrete salmon, moderate motion, already proven through v002-v005 detector. Use for primary MVP proof. |
| `media/hero-subclips/H7_spawn_feast.mp4` | Medium | High motion energy, occlusion risk. Use for dense-school streamline path, not per-fish tracking. |
| `media/hero-subclips/H4_dense_school.mp4` | Stress test | Too many fish for nearest-neighbor; use Farneback streamlines only. |
| `media/hero-subclips/H6_kelp_forest_floor.mp4` | Fish-free control | No salmon, but pure current trajectories. Useful to test that the same renderer produces clean water grammar when there is no fish to be confused with. |
| `media/hero-subclips/H2_herring_in_kelp.mp4` | Boundary case | Herring, not salmon, but small-fish trajectories test whether the grammar generalizes. Frame as a hypothesis, not a deliverable. |
| `media/hero-subclips/H8_milky_water.mp4` | Skip | Visibility too low for detection or flow integration. |
| `media/hero-subclips/H3_kelp_cathedral.mp4` | Skip | Static scene, no useful trajectories. |
| `media/hero-subclips/H5_reef_garden.mp4` | Skip | Static scene. |
| `media/hero-subclips/H6_kelp_forest_floor_4k.mp4` | Defer | Use only after the 1080p version is grammar-accepted. Do not spend 4K render budget pre-acceptance. |

Lead the proof with H1_salmon_school. Use H6 as the control. Treat H4 and H7 as stress tests that require the streamline path.

## Avoiding Literal Fish-Body Reads

This is the central risk and the design constraint that justifies the whole lane.

- The fish body is never drawn in the layer. The layer ships on pure black; in composite preview the fish are visible only through the source footage underneath.
- The present anchor circle is small, low opacity, and offset by about one body-radius perpendicular to the heading. The default offset direction is above-the-head, which never coincides with eye or joint position for a horizontally-swimming salmon.
- An equally acceptable variant omits the present anchor entirely. Past trail and future intention do all the work. This is the recommended Austin review variant if there is any ambiguity in the body-center question.
- Past trail crescents are spaced wide enough that they never join into a worm-like body silhouette. The no-fuse guarantee is spacing greater than the crescent's own along-path footprint, not a fixed body-length count. The v001 proof ships 0.50 body-lengths (about 1.5x the along-path footprint); see v001 Proof Findings below for why the originally proposed 1.5 body-lengths hid the wake entirely.
- Future intention marks use very low opacity. The eye must read them as intention, not as a second fish.
- Trail and future marks rotate to the trajectory tangent, never to the body axis. The trail bends with the path, not with the spine of the fish.
- The renderer never reads pixels from inside the fish silhouette to colorize a mark. All marks are ivory or pale-cyan on black per the v003 palette finding.
- Resolume mixing: the layer always sits in Screen or Additive mode at modest opacity. Under that blend the marks are visible against water but never replace any part of the visible fish body.

If any of these constraints is broken, the lane is collapsing back toward the rejected fish-glyph reading. The renderer should fail-safe by dropping marks for that frame rather than emitting an uncertain glyph.

## Data Exports

Every render should also write a sidecar pack that conforms to the `primitive-grammar-contract-2026-05-19.md` instance schema. Future TouchDesigner, Blender, and web demos consume the same data without re-running detection.

Suggested layout under each output folder.

- `tracks_per_frame.csv` columns: `frame_idx, track_id, x, y, vx, vy, age, missing, confidence`. One row per active track per frame. Coordinates normalized to [-1, 1] with positive y up per the grammar contract.
- `trajectories.json` shape: `{ "schema_version": "salmon_trajectory_v001", "tracks": [ { "track_id": ..., "frames": [ { "frame": ..., "x": ..., "y": ..., "angle": ..., "vx": ..., "vy": ... }, ... ] }, ... ] }`. One entry per complete or in-progress track.
- `direction_vectors.csv` columns: `frame_idx, track_id, dx, dy`. Unit vectors aligned to smoothed heading per frame.
- `future_intent.csv` columns: `frame_idx, track_id, horizon_frames, x_pred, y_pred, cov_xx, cov_yy, cov_xy, confidence`. One row per active track per prediction horizon (5, 10, 15).
- `primitive_instances.jsonl` one line per primitive emitted per frame, conforming to the `grammar_v001.json` instance schema with `parent_phrase_id` set to a stable id per (`track_id`, `bundle_kind`), where `bundle_kind` is one of `past_trail`, `present_anchor`, `future_intent`.
- `recipe.json` reproducibility manifest: source clip path, detector parameters, tracker parameters, prediction horizon, opacity profile, palette role, palette values, blend mode, output resolution, frame rate, random seeds, agent label `"agent_a_salmon_trajectory_v001"`.

The renderer should refuse to emit any instance with `cultural_status` other than `internal` until Austin reviews the specific use. Every primitive instance carries the explicit `cultural_status: "internal"` and `role: "water_*"`. No salmon-body role bindings are used.

## Rendering Ideas For Resolume Black-Background Layers

- Output 1920x1080 H.264 MP4 on pure black at 24fps to match the v002-v005 packets. Convert to DXV/HAP later if Resolume scrubbing performance becomes an issue, not now.
- One layer per source clip. Layers are independently mixable so Austin can mute the salmon trajectory layer without losing the water-only layers from Agent B v005.
- Composition order in Resolume from bottom: source footage (or fallback wide-wall media), water topology layer (Agent B v005 clip `01`), duality current sheet (Agent B v005 clip `02`), salmon trajectory layer (this lane), optional figure layers parked.
- Start the salmon trajectory layer at 30-40% opacity over footage. Below the v005 water layers because the trajectory marks should look like they live on the same water sheet, not above it.
- Three internal render variants for Austin review:
  - `01_salmon_trajectory_H1_full_v001_black_screen.mp4`: past trail plus present anchor (offset) plus future intent. The full grammar.
  - `02_salmon_trajectory_H1_no_anchor_v001_black_screen.mp4`: past trail plus future intent only. No circle at all. The safest variant if body-center circles are rejected.
  - `03_kelp_streamline_H6_control_v001_black_screen.mp4`: same renderer driven by Farneback streamlines on H6 instead of by salmon detections. The control that proves the layer reads as water grammar even when no fish is present.
- Optional composite previews for review only: `*_composite_*.mp4` with the source footage burned in. Mark these as review artifacts not as ship material. Match the Agent B v002 burn-in disclosure.

## v001 Proof Packet (Shipped 2026-05-19)

The v001 proof was rendered on 2026-05-19.

- Renderer: `scripts/render_salmon_trajectory_v001.py`. Co-located with the v001-v005 family so it imports `detect_salmon_candidates` and `track_update` from `primitive_water_grammar_v5` unchanged, exactly as v5 imports v1. The design's earlier `track2-deterministic/scripts/` path was changed to `scripts/` for clean bare imports.
- Output folder: `track2-deterministic/morph_outputs_INTERNAL/salmon_trajectory_grammar_v001_2026-05-19/` - sibling of, never inside, any Agent B `primitive_water_grammar_v00X_2026-05-19/` folder.
- Deliverables shipped: three 6-second 1920x1080 black-screen MP4s (`01_salmon_trajectory_H1_full`, `02_salmon_trajectory_H1_no_anchor`, `03_kelp_flowpath_control_H6`), midpoint stills, contact sheet, `README.md` mirroring the v005 packet format, and `trajectory_data/tracks_per_frame.csv`.
- Scope held: v005 tracker reused unchanged; no YOLO/ByteTrack/CoTracker; no SD/LoRA; no fish glyphs, no eyes, no body-centre circles; no edits to Agent B/C/D folders.

### v001 Proof Findings

- Trail spacing: the originally proposed minimum of 1.5 body-lengths between trail crescents made the wake invisible. The v005 tracker's heavy position EMA plus short track lifespans (median 14 frames, median observed path 124 px against a mean fish length of 137 px) means most tracks travel under one body-length. Shipped value is 0.50 body-lengths. The no-fuse guarantee still holds because that is roughly 1.5x the crescent's own along-path footprint, which is the figure that actually matters - not a body-length count.
- Track churn: 29 distinct tracks over 144 frames at about 5 active per frame. Each track restart loses its history and its trail. This is the strongest argument for the documented stronger-path upgrade (ByteTrack or point tracking) in a future version.
- Anchor gating: a present anchor on a track younger than 5 frames left lone floating circles; v001 gates the present anchor on track age.
- The fish-free H6 control renders cleanly as flow-advected current paths, confirming the renderer reads as water grammar with no salmon present.

### Future Versions Still Out Of Scope

ByteTrack, CoTracker, RAFT-replacement, 4K rendering, Resolume packaging, alpha channels, prompt-to-primitive integration. These remain the documented stronger-path upgrades, not yet built.

## Austin Review Questions

Frame all of these as internal sketches based on observed grammar, not as Austin artwork.

1. Does marking the water around a moving fish (past wake, present anchor, future intention) read as water grammar, or does it still read as figure decoration?
2. Should the present anchor be a small offset circle, or should the lane omit the anchor entirely and let past trail plus future intention carry the read?
3. Do crescents along a fading wake, cupping back toward the present position, read as ripples being left behind, or as something else?
4. Does a faint trigon a short distance ahead of the fish read as intention/leading-edge attenuation, or as a separate object?
5. Is treating each fish as a tiny moving river acceptable, so that Recipe 02 River Bend cluster grammar applies at curvature peaks of the trajectory?
6. Should solitary fish, schools, and spawning groups use different grammar densities, or is one density profile sufficient?
7. Where two trajectories cross, is Recipe 04 Current Knot the right placement, or should crossings be ignored?
8. When a track ends (fish leaves frame or detection drops), is a Recipe 01 Pond Ripple terminator at the exit point acceptable as a closing phrase?
9. For the dense-school streamline variant on H4/H7, is the resulting field read as water motion or as visual noise?
10. Should the salmon trajectory layer sit below or above Agent B's v005 duality current sheet in Resolume?

These questions are additive to the existing Agent B v005 water questions, not replacements. The water-only review still leads.

## Risks And Failure Modes

- **Circle reads as eye or body center.** Mitigations: perpendicular offset by one body-radius, lower opacity, optional anchor-omitted variant, no pixel sampling from the body interior.
- **Past trail crescents fuse into a body silhouette.** Mitigations: spacing held above the crescent along-path footprint (v001 ships 0.50 body-lengths), scale falloff with age, opacity falloff with age. v001 confirmed no fuse at this spacing.
- **Future intent reads as a ghost fish.** Mitigations: very low opacity, single primitive only, drop the bundle when Kalman covariance exceeds a gate.
- **Wrong direction (head/tail confusion).** Mitigations: PCA axis disambiguated by local optical flow already in v005; trail bundle suppressed for the first 5 frames of a new track until heading stabilizes.
- **Occlusion (fish behind kelp).** Mitigations: 12-frame missing tolerance already in v005, longer fade-out on missing tracks, soft reassociation of new detections to old IDs within a radius.
- **Dense school overload.** Mitigations: switch to Farneback streamline mode at a configurable detection-count threshold; cap visible bundles per frame at 5-7.
- **Camera motion bias.** Real footage drifts. The fish trajectory currently includes camera motion, which contaminates the wake. Mitigations: estimate global flow and subtract it from per-fish velocity before producing trajectories.
- **Trajectory jitter.** Detector noise translates directly into trail noise. Mitigations: EMA smoothing already in v005 (0.72/0.28), additional Savitzky-Golay smoothing across the ring buffer before rendering.
- **Marker-like read returns.** If too many bundles appear at once, the layer reverts to v005's marker problem. Mitigations: cap bundle count, prefer longer-lived tracks over short-lived ones for visible bundles, leave large quiet water areas.
- **Compositional drift past 6 seconds.** Tracks accumulate; new tracks replace old ones; the layer can become visually noisy over time. Mitigations: scope every proof clip to 6 seconds matching the v002-v005 cadence; introduce a soft maximum-active-tracks gate.
- **Cultural-load creep.** If trail bundles begin to suggest a known crest or named figure (Thunderbird arc, serpent path, salmon spirit), the layer must pause and ask Austin. Mitigations: keep all outputs `internal`, never label trajectories by species name in public artifacts, and re-read this risk before any external mixdown.

## Out Of Scope

- No new SD or LoRA work. The salmon trajectory lane is fully deterministic.
- No new broad style transfer work.
- No edits to any `primitive_water_grammar_v00X_*` folder, any `prompt_to_primitive_scene_*` folder, or any Agent C/D output.
- No contact with Austin, Pravin, John, Dan, Natalia, Carol Anne, or any external collaborator.
- No new Resolume composition. The lane ships clips; composition stays with Pravin.
- No public projection, recording, or audience-facing use of any generated material under this lane.
- No promotion of any output above `cultural_status: "internal"` until Austin reviews the specific clip.
- No use of James Harry sculpture references, named beings, chiefs/specific persons, Thunderbird, serpent, whale, or any culturally specific figure as part of this lane.

## Cross-References

- Grammar instance schema and cultural-status fields: `docs/space-center/primitive-grammar-contract-2026-05-19.md`.
- Pond Ripple, River Bend, Current Knot recipes used by this lane: `docs/space-center/austin-informed-water-phrase-recipes-2026-05-19.md` Recipe 01, 02, 04.
- Austin grammar observations that constrain primitive use: `docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md` sections "Transcript-Grounded Grammar" and "Practical Rules For Agent B v005/v006".
- v005 nearest-neighbor tracker that the MVP reuses: `scripts/primitive_water_grammar_v5.py` lines 484-528.
- Existing salmon-rig brainstorming (different lane, includes A.1 straighten-and-swim and A.2 chase-tails): `docs/space-center/salmon-swim-rig-next-experiments-2026-05-17.md`.
- Wednesday review framing and Pravin pacing: `docs/space-center/deep-research-implementation-brief-2026-05-19.md`.
