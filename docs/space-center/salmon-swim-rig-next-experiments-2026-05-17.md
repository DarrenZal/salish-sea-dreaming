# Salmon swim rig — next experiments (2026-05-17 PM)

After Salmon swim rig v004 landed (yin-yang counterphase swim with
continuous cv2.remap body deformation), brainstorm of next-step
experiment ideas. Operator-surfaced 2026-05-17 ~3:45 PM:

> "can we isolate a fish, and then have that fish (which is curved)
> straighten out a bit and start swimming in a line? or could the two
> fish start swimming in circles, chasing each others tails?"

Plus other ideas. Ranked by impact-per-effort.

## A. Operator-surfaced directly

### A.1 — Isolate fish, straighten body, swim in a line
**Effort:** ~2-3 hrs.

**Concept:** the upper salmon in the source piece is curved in a
yin-yang arc. Take it, de-curve the body (straighten the spine), then
apply the existing swim rig + translate the whole fish across the
canvas in a straight line.

**Mechanism:**
1. Detect spine as polyline (not just head→tail line) — use skeletonization
   on the body mask + bezier fit to get the actual curved spine
2. Define target straight-spine: line of same length as current spine,
   in operator-chosen direction (e.g., left→right horizontal)
3. Thin-Plate Spline (TPS) warp: morph the body so its curved spine maps
   to the straight spine
4. Apply existing swim wave to the straightened body
5. Translate the whole RGBA layer across canvas at chosen speed

**Output:** `salmon_straight_swim_v001.mp4`

**Why interesting:** demonstrates the rig can RE-POSE the figure, not
just animate its existing pose. Opens door to fish swimming TO the
piece, AWAY from the piece, INTO the piece from offscreen, etc.

### A.2 — Two fish swimming in circles chasing tails
**Effort:** ~2-3 hrs.

**Concept:** both salmon follow circular paths around canvas center,
bodies bend in direction of motion, tails follow heads (yin-yang made
literal — actual chasing).

**Mechanism:**
1. Define circular path for each fish (radius, center, angular speed)
2. At each frame, compute fish's position on circle + tangent direction
3. Spine angle = aligned with tangent (head at "front" of circle direction)
4. Apply TPS to re-pose body curve to match the circle's curvature
5. Apply swim wave for body undulation
6. Translate fish to current circle position
7. Two fish offset 180° on circle = always opposite, chasing

**Output:** `salmon_circle_chase_v001.mp4`

**Why interesting:** the literal yin-yang animation. Could loop forever
as a contemplative meditation visual.

## B. Other directions worth exploring

### B.1 — Fish swimming AWAY (exit) / INTO (enter)
**Effort:** ~1-2 hrs (extends A.1).

Fish swims from rest position OUT of frame (translate + swim), or
reverse: starts off-frame and swims TO rest position. Useful for
transitions between pieces (fish from Salmon piece "swims into"
Cosmic_Sun piece, etc.).

### B.2 — School of fish
**Effort:** ~1-2 hrs (extends v004).

Duplicate single salmon at 3-5 different sizes/positions, all swimming
with phase offsets. Could appear like a small school passing through.

### B.3 — Fish swimming through roe field
**Effort:** ~3-4 hrs.

Fish translates across canvas, roe parts radially as fish passes
through, then closes back. Requires roe field reactivity (not just
static). Roe animation needs to be position-aware — react to fish's
displacement vector.

### B.4 — Combine breathing + swimming
**Effort:** ~1 hr (extends v004 + Cosmic_Sun v003c).

Apply v003c breathing-shimmer to roe field while salmon bodies swim.
Two motion layers compositing — meditative + alive.

### B.5 — Spawning ritual
**Effort:** ~4-5 hrs.

Two salmon swim toward each other from offscreen positions, meet in
center, deposit roe (roe appears in the meeting position), separate
back to offscreen. Narrative arc — could be the visual for a "spawning
season" data driver.

## C. Architectural extensions

### C.1 — Apply rig to other Austin pieces
**Effort:** ~30-60 min per piece (once rig is parameterized).

The cv2.remap warp approach generalizes to any piece with a figure
that has a head + tail/extremity. Candidates:
- Animal_Bird_Raven_Sun — raven flap (wings as warp targets)
- Animal_Bird_Heron — heron neck sway / wading
- Animal_Wolf_Spindle_Whorl — two wolves rotating around central hub
  (might want rotation rig not swim rig)
- Animal_Insect_Bee — bee hover (subtle wing-buzz warp)

### C.2 — Spine as bezier curve, not straight line
**Effort:** ~2-3 hrs.

Current rig: spine = single line from head to tail. For curved fish,
this approximates poorly. Upgrade: detect spine via skeletonization,
fit bezier, compute displacement perpendicular to the LOCAL spine
tangent at each pixel. More expressive warps possible (gentle S-curves
that respect body anatomy).

### C.3 — Multi-segment puppet rig
**Effort:** ~3-4 hrs.

Treat body as articulated segments (head / mid-body / tail), each
with own transform. Apply rig: head leads, segments follow with delay
+ spring constraints. More animatorlike control than continuous wave.

### C.4 — Audio-reactive swim
**Effort:** ~2-3 hrs.

Pipe audio amplitude into swim amplitude/frequency. Fish swims faster
during loud audio, gentler during quiet. Or audio frequency bands map
to different swim parameters (low bass = body sway, high freq = tail flutter).

## D. Composition / scene-level

### D.1 — Fish swims into a different piece
Cross-piece transition: fish exits Salmon_Spawn_Eggs frame on right,
enters Cosmic_Sun frame on left. Continuous shot effect — the salmon
is "leaving its home piece" to visit another. Storytelling potential.

### D.2 — Salmon swimming → returns home
Operator-mentioned arc: salmon swims away from piece, returns to its
yin-yang rest pose. Beginning, middle, end — natural loop.

### D.3 — Underwater current background
Apply gentle drift wave across whole canvas as base motion layer.
Salmon swim on top. Roe drift slowly with current. Background piece
itself sways slightly. Whole composition feels submerged.

## Ranked top picks for next session

1. **A.1 — Straighten + swim in a line** (operator-asked, expands the rig's
   capabilities most, ~2-3 hrs)
2. **A.2 — Circles chasing tails** (operator-asked, literal yin-yang, ~2-3 hrs)
3. **C.1 — Apply rig to Raven/Heron** (proves generalization, easy
   wins on other pieces, ~30 min each)
4. **B.2 — School of fish** (cheap extension, multiplies the visual
   density of what we have, ~1-2 hrs)
5. **C.2 — Bezier spine** (improves quality of A.1 + A.2 + all future
   rigs, ~2-3 hrs)

Lower-priority but interesting:
6. B.5 spawning ritual (narrative arc)
7. C.4 audio-reactive (for live performance integration)
8. D.2 swim-away-return (emotional loop)

## Open questions for operator

1. Should A.1 fish swim left-to-right (like a reader) or another direction?
2. For A.2 circles: clockwise / counterclockwise / both?
3. Do you want to LOCK swim rig v004 as the canonical Salmon mechanic
   and start applying to other pieces (C.1), or keep iterating Salmon
   first (A.1 / A.2)?
