# Underwater Motion Tracking 2D / 2.5D / 3D Feasibility - 2026-05-20

Status: INTERNAL Agent F research/design brief. No rendering. No external browsing or external communication. Not Austin-approved. Not public-use guidance. Not a cultural-grammar claim. This document is about using underwater salmon/kelp footage as motion input for internal primitive water grammar, not about making fish glyphs.

## 1. Short Answer

Can we recover true 3D salmon trajectories from one underwater video?

No, not honestly in the way "true 3D trajectory" usually means: metric `x, y, z` through water over time. A single RGB underwater video gives image-plane motion. Many different 3D paths can project to the same 2D track, and underwater footage adds extra ambiguity: refraction, turbidity, caustics, exposure shifts, motion blur, fish deformation, occlusions, and camera drift.

What we can recover this week:

- **2D trajectories:** good enough. Track points, masks, fish-like blobs, kelp tips, or flow anchors in image coordinates.
- **2D flow fields:** good enough. Optical flow gives local apparent motion and streamlines.
- **2.5D cues:** useful but approximate. Estimate relative near/mid/far ordering from size, blur, contrast/haze, occlusion, vertical placement, and motion parallax. Use this as `depth_rank`, not meters.
- **True 3D:** no, unless we add more information: stereo/multi-camera, calibrated camera motion over mostly static scene, known object sizes with stable orientation, depth sensor, or manual reconstruction constraints.

For this week, build a robust 2D / 2.5D trajectory system and label it as such.

## 2. Source Map

Local sources read:

- `docs/space-center/salmon-trajectory-grammar-design-2026-05-19.md`
- `docs/space-center/austin-informed-water-phrase-recipes-2026-05-19.md`
- `docs/space-center/source-grounded-water-phrase-layout-correction-v002-2026-05-19.md`
- `docs/space-center/deep-research-implementation-brief-2026-05-19.md`
- `docs/space-center/motion-physics-to-primitive-grammar-2026-05-20.md`
- `docs/space-center/functional-salmon-vs-static-replication-2026-05-20.md`
- `docs/space-center/footage-hygiene-review-2026-05-18.md`
- `docs/moonfish-shotlist.md`
- `scripts/primitive_water_grammar_v1.py`
- `scripts/primitive_water_grammar_v5.py`
- `scripts/render_salmon_trajectory_v001.py`
- `scripts/water_flow_phrase_grammar_v002.py`
- `track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v003_2026-05-20/README.md`
- `track2-deterministic/morph_outputs_INTERNAL/water_flow_phrase_grammar_v004_2026-05-20/README.md`

Local availability check:

- Available in `/opt/homebrew/bin/python3.11`: `cv2`, `numpy`, `scipy`, `skimage`, `torch`, `torchvision`, `PIL`.
- Not available locally: `ultralytics`, `segment_anything`, `sam2`, `cotracker`, `filterpy`.
- No local CoTracker/PIPs/Track-Anything repo found in this workspace.

Implication: the practical path this week is OpenCV/scikit-image + existing local trackers. CoTracker/PIPs/Track-Anything/SAM/YOLO are optional later upgrades only if installed with model weights.

## 3. True 3D From One Underwater Video

### 3.1 Why True 3D Is Not Recoverable Reliably

A monocular camera records a 2D projection. Without extra constraints, depth is underdetermined:

```text
same 2D track on screen
  could be a small fish close to camera
  or a larger fish farther away
  or a fish moving diagonally in depth
  or camera drift plus fish motion
```

Underwater makes this worse:

- refraction and lens/housing effects change apparent geometry;
- fish bend and change silhouette length frame to frame;
- kelp moves with current and is not a rigid static reconstruction target;
- schools self-occlude constantly;
- turbidity and haze reduce contrast with depth but also with lighting angle;
- caustics and specular highlights create false motion;
- camera drift often looks like water motion;
- rolling shutter or stabilization can distort apparent trajectories.

Monocular 3D is more plausible for a mostly static scene with camera motion and enough textured background. It is much less plausible for independently moving salmon and kelp in water.

### 3.2 What 3D-Like Work Is Still Useful

Use 2.5D, not 3D:

- `screen_x, screen_y`: tracked image position.
- `vx, vy`: apparent image-plane velocity.
- `depth_rank`: near/mid/far ordinal, low confidence.
- `scale_rank`: apparent size bucket.
- `occlusion_state`: visible, partial, missing, reappeared.
- `confidence`: tracking reliability.

Useful pseudo-depth cues:

- apparent fish length or mask area, with strong caution because fish turn and bend;
- sharpness/blur, with caution because motion blur is not depth blur;
- contrast and saturation loss, with caution because lighting varies;
- occlusion ordering: if fish A passes in front of fish B, A is nearer for that event;
- parallax against stable rocks/kelp only if camera motion is measurable;
- vertical placement only when camera angle and scene plane are known, which is rarely true underwater.

Do not expose this as `z_meters`. Use `z_rank` or `depth_layer`.

### 3.3 When True 3D Becomes Possible Later

Post-IMPACT options:

- stereo or multi-camera underwater footage with calibration;
- synchronized camera pair in known housing geometry;
- clean camera intrinsics/extrinsics plus static background SLAM for kelp/reef only;
- known-size fiducials or known fish-size assumptions for very rough scale;
- manual depth annotation for hero trajectories;
- controlled tank/shallow-water capture.

For Moonfish salmon/kelp footage already on disk, the realistic ceiling is 2D plus 2.5D.

## 4. What Edge Detection Helps With

Edge detection is useful, but it is not tracking and it is not depth.

### Helps With

- **Feature selection:** find high-contrast fish edges, kelp frond boundaries, rocks, and light/dark boundaries that make better tracking seeds than blank water.
- **Motion masks:** combine edges with frame differences or optical-flow magnitude to find moving structures.
- **Silhouette hints:** local-dark fish/kelp components can be bounded by Canny/Scharr/Sobel edges before connected components.
- **Kelp paths:** long curved edges can become candidate splines for kelp-sway tracking.
- **Flow confidence:** optical flow near stable edges is often more trustworthy than flow in flat water.
- **Boundary discipline:** water/kelp masks can keep primitive marks inside the intended water region.
- **Debug overlays:** edges help reviewers see why a track was accepted or rejected.

### Does Not Help With

- true 3D depth;
- identity persistence through dense schools;
- head/tail direction by itself;
- occluded fish behind kelp;
- turbid low-contrast frames;
- separating camera motion from water motion;
- distinguishing fish edges from caustics, bubbles, timecode burn-in, or compression artifacts.

Edge detection should seed and validate tracks. It should not become the visual layer, and it should not be used to draw fish outlines.

Recommended edge stack:

```text
crop burn-in
grayscale / luminance stabilize
CLAHE or gentle contrast normalization
Canny or Sobel/Scharr edges
morphological cleanup
connected components / contour filtering
edge-confidence score for tracks and masks
```

## 5. Best Practical Pipeline This Week

The week-one target should be a reliable `trajectory_recipe` export, not a perfect tracker. The renderer can use trajectories as hidden guides for water grammar.

### 5.1 Preprocess

1. Use cropped footage that removes bottom filename/source-timecode burn-in.
2. Work at 1920x1080 output, but estimate flow at 480x270, 640x360, or 960x540 depending speed.
3. Normalize luminance gently; do not over-sharpen caustics.
4. Build a low-confidence mask for frame edges, burn-in area, heavy blur, low texture, bubbles, and hard cuts.
5. Estimate global camera drift per frame from median flow or feature homography. Store it even if not subtracted.

Important distinction:

- For **visual lock to footage**, advect primitives by full apparent flow so marks stay glued to visible features.
- For **water-relative motion analysis**, subtract global motion first, but expect errors because global camera drift and bulk school motion can be hard to separate.

### 5.2 Optical Flow

Immediate local tool: OpenCV Farneback already exists in `scripts/primitive_water_grammar_v1.py`.

Use it for:

- frame-synchronous advection;
- streamline extraction;
- heading disambiguation for fish-like blobs;
- local motion confidence;
- curl/divergence/strain proxy fields.

Recommended flow hygiene:

- estimate every frame pair, not only a mean field, when the goal is perceptual lock;
- temporal smooth over 3-5 frames;
- spatial smooth before gradients;
- magnitude gate tiny jitter;
- use robust percentiles for normalization;
- keep debug flow fields and selected anchors.

Known tradeoff from local v003/v004:

- mean-field structure loops cleanly but can look visually detached from frame motion;
- frame-synchronous advection locks to footage but does not loop seamlessly.

For this week, prefer frame-synchronous advection for evidence, and keep mean-field loops as fallback show layers.

### 5.3 Sparse Point Tracking

Local fallback: OpenCV KLT/Lucas-Kanade.

Use:

- `goodFeaturesToTrack` on edges/textured regions;
- `calcOpticalFlowPyrLK` forward;
- forward-backward consistency check;
- re-seed lost points at controlled intervals;
- cluster points into trajectories or path bundles.

Better optional upgrades if installed later:

- **CoTracker:** strong general point tracking across frames; useful for fish edges, kelp tips, and water features. Produces point tracks, not semantic fish masks.
- **PIPs / PIPs++:** similar point-track lane; useful for long-range point persistence.
- **Track-Anything:** mask propagation lane. Useful after an operator/SAM prompt on a clear fish or kelp frond; weak for dense self-occluding schools without good initial masks.

This week: design around point tracks as optional input, not dependency. The renderer only needs `(track_id, x, y, vx, vy, confidence, depth_rank)`.

### 5.4 Detection / Segmentation

Local current detector:

- `scripts/primitive_water_grammar_v5.py` has a local-darkness component detector for salmon candidates.
- It uses PCA for axis and optical flow to disambiguate heading.
- It feeds nearest-neighbor tracks with EMA smoothing and a 12-frame missing tolerance.

Use this only when the footage has discrete fish. It fails gracefully into flow/streamline mode for dense schools.

SAM / YOLO status:

- `ultralytics`, `segment_anything`, and `sam2` are not installed locally.
- Generic YOLO is not enough unless a fish-capable model or custom weights exist. COCO-style detectors are not a reliable salmon detector.
- SAM can refine masks from boxes/points if available, but it does not solve temporal identity by itself.
- Track-Anything-style SAM + propagation can be useful for one clear fish or kelp frond, but it is not the right first dependency for this week.

Recommendation:

- Do not spend this week installing/training YOLO/SAM unless the optical-flow path fails.
- If SAM/YOLO weights are already available elsewhere, use them as a mask assist, not as the core pipeline.

### 5.5 Kalman / Smoothing

Use smoothing as mandatory hygiene.

Minimum:

- EMA on position, angle, and length.
- Short rolling median or Savitzky-Golay on trajectory buffers.
- Birth/death hysteresis.
- Minimum visible lifetime before any primitive phrase appears.

Kalman:

- Use a constant-velocity 2D Kalman filter per track.
- State: `[x, y, vx, vy]`.
- Measurement: `[x, y]`.
- Covariance gates whether future-intention marks are drawn.
- If covariance grows after occlusion, fade the track and omit future marks.

`filterpy` is not installed, but a small constant-velocity Kalman can be implemented directly with NumPy in under 60 lines. Do not add a dependency just for this.

### 5.6 Pseudo-Depth

Output 2.5D fields only:

```json
{
  "track_id": 17,
  "x": 0.42,
  "y": 0.58,
  "vx": 0.01,
  "vy": -0.02,
  "depth_rank": "near|mid|far|unknown",
  "depth_confidence": 0.43,
  "depth_cues": ["mask_area", "contrast", "occlusion"]
}
```

Use pseudo-depth for:

- opacity: farther tracks dimmer;
- scale: farther tracks smaller;
- parallax offset in a 2.5D composite;
- layer ordering in Resolume or TD;
- gating: low depth confidence uses flat 2D mode.

Do not use pseudo-depth for:

- claims of true depth;
- metric 3D path plots;
- strong 3D camera moves;
- collision/occlusion logic unless manually verified.

## 6. Mapping Trajectories To Primitive Grammar Without Fish Glyphs

The tracker sees salmon or kelp. The primitive layer should show water response.

Do:

- Treat each trajectory as a hidden current path.
- Draw primitives around, behind, or offset from the tracked object.
- Use the same water recipes for fish, kelp, and current anchors.
- Keep the source footage responsible for showing fish; the primitive layer shows wake, current, pressure, and attenuation.

Do not:

- draw fish outlines;
- put trigons on heads or tails;
- put circles on eyes, body centers, or joints;
- use crescent gills/fins/ribs;
- build salmon anatomy from primitive marks;
- make a fish-shaped glyph out of the trail.

### 6.1 Default Trajectory Phrase

For each high-confidence mover:

```text
past wake:      fading crescents along previous positions
present water:  optional offset circle/current knot beside the mover, not on body
future motion:  faint crescent or trigon along predicted heading
```

Safer no-anchor variant:

```text
past wake crescents -> faint future trigon
```

This avoids circles near fish entirely.

### 6.2 Kelp Motion Phrase

For kelp:

- track frond tips, long edges, or flow-advected anchors;
- use circles only at current knots or bend pressure points;
- use crescents along the sway path;
- use a trigon at release/down-current attenuation;
- keep marks outside the kelp silhouette when possible.

### 6.3 Dense School Phrase

For dense schools:

- stop trying to maintain individual fish identities;
- use dense optical flow and streamlines;
- rank streamlines by length, stability, and local non-global motion;
- render only 3-7 phrase bundles;
- label them as current/school-motion paths, not salmon paths.

### 6.4 Confidence Gates

Drop primitives instead of guessing when:

- track age is too young;
- covariance is high;
- point/mask confidence is low;
- occlusion is active;
- global motion dominates local residual;
- track enters the burn-in/crop boundary;
- trail would fuse into a fish-shaped body.

## 7. Footage Types

### Best

- One to five visible fish, separated enough for identity to persist.
- Kelp fronds with strong edges and slow sway.
- Stable camera or slow predictable drift.
- Good contrast between fish/kelp and water.
- Moderate motion, not too fast for motion blur.
- Textured background for camera drift estimation.
- Long enough shot continuity for 3-6 second trajectory phrases.

Best local candidates:

- `media/hero-subclips/H1_salmon_school.mp4` for discrete salmon tests.
- `media/collaborators/moonfish-video/underwater/P1111785.mp4` for true kelp/frond motion.
- `media/collaborators/moonfish-video/underwater/P1099653.mp4` for dense school/current stress tests.

### Medium

- Herring through kelp: smaller targets, more occlusion, but good flow.
- Dense salmon/herring school: good collective motion, poor identity persistence.
- Camera-drift shots: useful if visual lock is the goal, weaker for water-relative analysis.
- Footage with burn-in if cropped before processing.

Medium local candidates:

- `media/hero-subclips/H2_herring_in_kelp.mp4`
- `media/hero-subclips/H4_dense_school.mp4`
- `media/hero-subclips/H7_spawn_feast.mp4`
- `media/collaborators/moonfish-video/underwater/P1077716.mp4`
- `media/collaborators/moonfish-video/underwater/P1111707.mp4`

### Worst

- Milky/turbid water with little texture.
- Dense self-occluding schools when individual identity matters.
- Strong caustics, bubbles, particles, or specular flicker.
- Fast pans, zooms, whip motion, or heavy stabilization artifacts.
- Static reef scenes with no useful motion.
- Shots where the bottom burn-in band is not cropped before flow/tracking.
- Low contrast fish against low contrast water.

Worst local candidates for trajectory extraction:

- `media/hero-subclips/H8_milky_water.mp4` for tracking.
- Static reef/kelp scenes for trajectories, unless used as background only.
- Any raw/proxy Moonfish clip before burn-in crop if the lower band is inside the analysis region.

## 8. Recommended Trajectory Data Contract

Every prototype should write data first, media second:

```text
trajectory_recipe.json
tracks_per_frame.csv
streamlines.json
flow_summary.json
debug_frames/
```

Suggested `tracks_per_frame.csv` columns:

```text
frame_idx, track_id, source_kind, x, y, vx, vy,
depth_rank, depth_confidence,
age, missing, covariance_xx, covariance_yy,
confidence, global_flow_x, global_flow_y,
local_residual_speed, primitive_policy
```

Suggested primitive policy:

- `water_wake_only`
- `offset_current_anchor`
- `flow_streamline`
- `kelp_sway`
- `drop_low_confidence`

Every primitive instance should carry:

- `role: water_wake|current_knot|flow_release|kelp_sway`
- `cultural_status: internal`
- `source_track_id`
- `confidence`
- `rendered: true|false`
- `drop_reason` when false.

## 9. Three Concrete Prototype Recommendations

### Prototype 1: Frame-Locked 2D Flow Trajectories

Purpose: prove the overlay is perceptually locked to underwater motion.

Source:

- primary: `media/collaborators/moonfish-video/underwater/P1099653.mp4`, a 6s high-motion window;
- alternate: `media/hero-subclips/H1_salmon_school.mp4`.

Method:

- crop burn-in;
- estimate Farneback or existing frame-pair flow;
- temporal smooth 3 frames;
- seed 5 phrase anchors on strong local non-global motion;
- advect anchors by full apparent flow;
- retain short wake history;
- write debug overlay with flow vectors and anchor trails;
- output trajectory CSV/JSON.

Primitive mapping:

- no fish glyphs;
- circles are current anchors only, optionally omitted;
- crescents are recent wake;
- trigons are low-opacity release.

Success:

- a debug viewer can pick one anchor and see it ride visible footage motion frame to frame;
- black-screen layer has 3-7 sparse phrases;
- no primitive sits on an eye/body-center role.

Risk:

- not seamless. This is acceptable; it is a motion-lock proof, not a loop.

### Prototype 2: Sparse Point/Kelp Tracker Benchmark

Purpose: compare practical tracking inputs before adopting heavier learned trackers.

Sources:

- `media/hero-subclips/H1_salmon_school.mp4` for fish-like motion;
- `media/collaborators/moonfish-video/underwater/P1111785.mp4` for kelp/frond motion;
- optional stress: `media/hero-subclips/H4_dense_school.mp4`.

Method:

- Canny/Sobel edges + `goodFeaturesToTrack`;
- OpenCV KLT forward/backward tracking;
- local Farneback direction for points that drift;
- optional local-darkness fish component detector from v005 on H1;
- constant-velocity Kalman smoothing in NumPy;
- track quality score: length, stability, residual speed, edge support, occlusion count.

Output:

- no render required for first pass;
- `tracks_per_frame.csv`;
- `track_quality_summary.md`;
- 6 debug stills with accepted/rejected tracks.

Upgrade switch:

- if CoTracker/PIPs becomes available locally with weights, run it against the same frames and compare track length and jitter against KLT.
- if SAM/Track-Anything becomes available, test one isolated fish and one kelp frond only.

Success:

- 5-20 high-confidence tracks survive at least 2 seconds in H1/P1111785;
- jitter after smoothing is low enough for primitive placement;
- dense-school stress test correctly falls back to streamlines instead of fake identities.

### Prototype 3: 2.5D Water-Wake Primitive Recipe

Purpose: turn trajectories into primitive grammar without rendering fish glyphs.

Sources:

- use Prototype 1 or 2 trajectories;
- start with H1 and P1111785;
- use H4/H7 only as dense-school streamline stress cases.

Method:

- assign `depth_rank` from size/contrast/blur/occlusion cues with confidence;
- create three primitive policies:
  - `wake_only`: crescents behind, faint trigon ahead, no circle;
  - `offset_anchor`: small circle/current knot offset off body/frond;
  - `streamline_field`: no object identity, only flow paths;
- write primitive instances to JSONL;
- optional black-screen layer only after data review.

Primitive mapping:

- fish/kelp path is hidden;
- wake marks live beside/behind motion;
- near tracks are slightly brighter/larger, far tracks dimmer/smaller;
- low depth confidence collapses to flat 2D.

Success:

- one still frame reads as water response, not fish anatomy;
- the same renderer works on kelp-only footage;
- every primitive has a water role and a confidence reason.

## 10. Week-Plan Recommendation

Do this order:

1. **Build data-only tracker benchmark** on H1 and P1111785. Use OpenCV KLT/Farneback plus v005 detector; write track quality summary.
2. **Run one frame-locked flow proof** on a high-motion P1099653/H1 window. Include debug overlay; do not force it to loop.
3. **Create primitive recipe JSONL** from trajectories using `wake_only` and `offset_anchor` variants. Render later only if the recipe inspection passes.

Do not do this week:

- install/train YOLO as a first move;
- make SAM/Track-Anything a dependency;
- claim true 3D;
- draw fish glyphs;
- put circles on fish body centers;
- spend time on 4K before the tracking/grammar is accepted;
- use pseudo-depth as anything stronger than relative layer ordering.

## 11. Bottom Line

The honest technical target is not "recover 3D salmon." It is:

```text
underwater video
  -> reliable 2D apparent motion
  -> optional 2.5D depth ordering
  -> smoothed high-confidence trajectories
  -> water-response primitive phrases
  -> black-screen additive layer
```

That path is feasible this week with local tools. True 3D is a post-IMPACT capture/design problem, not something to infer from one underwater RGB clip.
