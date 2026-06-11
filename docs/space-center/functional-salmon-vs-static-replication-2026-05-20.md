# Functional Salmon vs Static Replication - Decision Brief - 2026-05-20

Internal decision brief. No rendering. Decides what the salmon lane does next.

## Decision

Static Austin-like salmon style replication is **parked**. Do not push the
style studies closer to Austin's source composition, and do not start the
functional fish rig build yet. The salmon lane's next step is an **Austin
review** that decides direction - not more rendering. Exact-source animation of
Austin's own salmon stays gated behind explicit Austin source-usage clearance.

## Where The Salmon Work Stands

Four internal lanes have run this sprint, each getting closer on *style* but
none producing a *functional* element:

- Salmon trajectory grammar v001 - read as segmented path markers, not salmon.
- Primitive salmon morphology v001 / v002 - read as salmon, but generic.
- Austin-informed salmon style study v001 - reached the source palette and
  composition logic.
- Austin-informed salmon style study v002 - reached an expanded, smoother form
  vocabulary (S-crescents, ovoids, curved rays, interlocking pair).

Every one of these is a **static still**. The iteration budget has gone to
style and replication. The installation's actual need - a salmon that *does*
something - is still unbuilt.

## When Is The Salmon Worth Continuing?

The salmon is worth continuing only as a **functional element with a defined
role in the show**: a fish that moves, schools, follows currents, emerges from
the water, and resolves back into a source piece. It is not worth continuing as
an open-ended exercise in making a prettier static copy of Austin's
spawn composition.

Three gates - continue only when all three are met:

1. There is a defined role for salmon *motion* in the show composition (the
   dreaming field, a transition, the Pearl narrative).
2. Austin has reviewed the style direction and set the source-usage boundary.
3. The work produces a reusable rig, not another one-off still.

Until all three hold: pause.

## Required Functional Capabilities

A salmon that earns its place in the installation must provide capabilities a
still cannot:

- **Swim any direction** - the body re-poses and re-orients to any heading and
  path, not one baked curl per render.
- **School** - many coherent fish moving together with common-fate behaviour,
  not copies of one pose.
- **Follow currents** - fish motion is driven by the water/current grammar
  layers (optical flow, current fields), so the salmon belongs to the water.
- **Emerge from water geometry** - salmon forms resolve *out of* the ripple and
  current grammar rather than being pasted on top; water becomes fish.
- **Return to the source piece** - the salmon can swim back into Austin's rest
  composition (the yin-yang spawn pose), giving a beginning / middle / end loop.
- **Exact-source animation** - animating Austin's actual salmon vector, a
  separate and higher-approval-load capability, gated on Austin sign-off.

## Why Static Austin-Like Studies Are Not Enough

- A still provides none of the six capabilities above. The installation is a
  living, moving piece; a fixed pose cannot serve it.
- Style is necessary but not sufficient. The style studies did their job - they
  found the Austin-informed vocabulary. Past this point they have diminishing
  returns.
- Replication drifts toward copying. The closer a static study gets to Austin's
  authored spawn composition, the more it simply *is* his artwork. That is a
  consent and authorship concern, not only an aesthetic one - per the project's
  per-output-sign-off floor, the goal is a salmon that is Austin-*informed* and
  does its own work in the show, not a pixel-closer copy of his piece.
- Both failure modes are now visible: animating a generic fish produced
  better-moving generic fish; perfecting a static fish produces a
  better-looking motionless fish. The deliverable has to be Austin-informed in
  style **and** functional in behaviour - and only a rig delivers the second.

## What A Proper Functional Fish Rig Requires

- **Smooth deformable spine** - a bezier/skeleton spine that bends, straightens,
  and re-poses, replacing the fixed per-still cubic/ring-arc spine. The prior
  swim-rig TPS work (`salmon_swim_rig_v004_confined`,
  `salmon_line_swim_v004_width_anchored_tps`) is the prototype foundation.
- **Direction control** - drive the body to a target heading and path;
  straighten the curl, swim in a line, enter/exit frame, turn.
- **Scale variation** - one rig renders fish at many sizes (near/far, school
  members) without re-authoring.
- **Flocking** - a boids layer (separation, alignment, cohesion) so a school
  reads as common-fate movement, not duplicated poses.
- **Water interaction** - fish motion coupled to the current/optical-flow
  grammar: fish follow currents, wakes disturb water, fish emerge from water
  geometry. This binds the salmon lane to the water-grammar lane.
- **Source-approval boundary** - a hard, built-in separation (below) between our
  own procedural functional salmon and exact-source animation of Austin's work.

## The Source-Approval Boundary

The rig must keep two tracks permanently separate:

- **Track 1 - our own procedural Austin-informed functional salmon.** Internal
  R&D. May be prototyped, but the *style* it renders needs Austin's review
  before any public use.
- **Track 2 - exact-source animation of Austin's salmon vector** (the swim-rig
  lane). Needs explicit Austin source-usage clearance plus per-output review.
  Stays parked until that clearance is granted.

The rig must never blur Track 1 and Track 2, and no output may imply Austin
authorship or cultural approval without his sign-off.

## Recommendation: Pause Until Austin Review

**Pause all new salmon production - static studies and the rig build alike -
until the next Austin review.**

Rationale: a rig renders a style. Building the rig before the style and the
functional direction are reviewed repeats the mistake of animating an
unreviewed thing - it would yield a well-rigged fish in a direction Austin has
not blessed. The review is the gate.

Use the pause to assemble the review packet, not to render more. After the
Austin review, green-light the functional rig only if:

- functional swimming / schooling / emerging salmon is actually wanted for the
  show, and
- the Austin-informed style direction is accepted, and
- the source-usage boundary is explicitly set.

Otherwise re-scope the salmon lane or drop it. Exact-source animation stays
parked behind source clearance regardless of the outcome.

## What The Austin Review Needs As Input

- The v001 and v002 Austin-informed salmon style studies (the style direction).
- This brief (the functional-vs-static framing and the capability list).
- Three explicit questions for Austin:
  1. Do you want salmon that swim, school, and emerge from water in the show,
     or is the salmon a static element?
  2. Is the Austin-informed style direction in the v002 study the right one?
  3. Where is the line between our own functional procedural salmon and your
     authored composition / exact-source use?

## Cross-References

- Style studies: `track2-deterministic/morph_outputs_INTERNAL/austin_informed_salmon_style_study_v001_2026-05-19/` and `..._v002_2026-05-19/`.
- Morphology studies: `primitive_salmon_morphology_v001_2026-05-19/`, `..._v002_2026-05-19/`.
- Trajectory grammar: `salmon_trajectory_grammar_v001_2026-05-19/` and `docs/space-center/salmon-trajectory-grammar-design-2026-05-19.md`.
- Exact-source swim-rig prototypes: `salmon_swim_rig_v004_confined/`, `salmon_line_swim_v004_width_anchored_tps/`, `austin_006_salmon_body_articulation_v002/`.
- Swim-rig next-experiments brainstorm: `docs/space-center/salmon-swim-rig-next-experiments-2026-05-17.md`.
- Source artwork: `track2-deterministic/source-vectors/Animal_Salmon_Spawn_Eggs.svg`.
