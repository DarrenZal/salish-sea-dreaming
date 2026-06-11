# Primitive Pattern Language: Next System Brief - 2026-05-19

Status: internal design-theory brief only. No rendering. This is not Austin-approved, not public-use guidance, not a traditional-meaning claim, and not a general Coast Salish grammar claim.

Related contract: `docs/space-center/primitive-grammar-contract-2026-05-19.md`

## Core Thesis

The next system should stop treating circle, crescent, trigon, oval, and line as clip-art symbols. Treat them as a small morphology and syntax space:

- Morphology defines how each shape can vary while remaining recognizable.
- Adjacency defines how shapes touch, cup, nest, enclose, release, and chain.
- Motion defines why a phrase changes over time.
- Topology defines where phrases are allowed to appear.

The design target is not "more primitives." It is fewer, better-related primitives whose placement, orientation, and motion make a phrase readable before texture, SDF, 3D, or footage integration.

## Shape Morphology Space

`circle / oval`

- Circle: origin, pivot, impact, joint, orb, knot, eye only under review.
- Oval: stretched circle where direction matters: eye direction, body axis, eddy shear, membrane pressure, boundary.
- Controls: radius, stroke/hollow ratio, aspect ratio, edge softness, whether it is filled or outline.
- Risk: repeated circles quickly read as eyes, roe, bubbles, or generic particles.

`crescent`

- Crescent: cupping, phase, wake, rotation, body arc, wing arc, mist arc.
- Controls: thickness, arc angle, tip sharpness, inner offset, concavity, cup direction.
- Quality rule: the concave side should usually cup an origin, pivot, path, or body. A crescent facing away from its relation reads wrong.

`trigon`

- Trigon: release, point, fin, ray, head/tail, attenuation.
- Controls: point length, curvature, concavity, base flatness, corner rounding, point direction.
- Quality rule: it must be a curved pointed primitive with a deliberate rear base, not a generic triangle, arrow, or spike.

`line / outline`

- Line: flow spine, skeleton, path, guide, horizon, current trace.
- Outline: membrane, body field, eddy field, water boundary, containment zone.
- Controls: curvature, taper, stroke width, dash/continuity, enclosure, child containment.
- Risk: visible outlines can become unreviewed masks, faces, bodies, or crests if not constrained.

## Adjacency Syntax

`cupping`

- Circle or oval anchors the phrase.
- Crescents cup the anchor, or cup a path bend, eddy center, joint, or membrane pressure point.

`nesting`

- A smaller anchor can sit inside a larger oval/outline or between crescents only when the role is explicit.
- Accidental circular gaps between crescent and trigon are invalid.

`touching`

- Crescents and trigons can nearly touch when the trigon is a release from the crescent.
- Touching should clarify continuity, not create clutter.

`enclosing`

- Ovals and outlines can contain phrase children.
- Children should stay inside the membrane or boundary unless marked as spray, ray spill, or review exception.

`releasing`

- Trigon follows crescent.
- The point direction should carry downstream flow, fin/tail action, ray direction, or attenuation.

`radial symmetry`

- Useful for sun/ray, impact, and orb-pivot studies.
- Review-needed when it approaches Austin-derived sun behavior, face structure, eyes, or exact-source composition.

`S-curve chaining`

- Phrases follow a river, body spine, flock path, or current.
- Compression occurs at bends, rocks, joints, and constrictions; spacing opens along calmer runs.
- This is the most promising syntax for moving from isolated phrase units to composition.

## Motion Semantics

- Pivot: circle/oval acts as the rotation center for wing, fin, joint, eddy, or ray behavior.
- Joint: circle/oval links body sections; connected arcs must articulate around it.
- Pulse: circle or orb expands/fades as origin, impact, or pressure.
- Ripple: circle initiates; crescents propagate; trigon attenuates.
- Rotation: crescents sweep around a pivot or eddy; trigon may release from the rotation.
- Expansion: spacing and scale move outward from a local origin.
- Contraction: phrases tighten at constrictions, bends, joints, or impact sites.
- Flocking: many tiny phrase agents share heading and spacing, but must not become random decorative marks.
- Swimming: spine-led figure motion where trigon head/tail and crescent body arcs phase along a curve; Austin approval required for figure use.
- Current: line/spline-led drift with phrases locked to local tangent and topology.

## Generative Systems Worth Testing

`graph grammar`

- Best for syntax validation.
- Nodes are primitives; edges are adjacency relations like cups, releases, encloses, follows, pivots.
- Use first to prevent invalid pairs before animation.

`L-system`

- Best for branching rays, rib sequences, feather/fin arrays, and repeated phrase growth.
- Keep depth shallow; uncontrolled recursion becomes wallpaper.

`cellular automata`

- Best for membrane pressure, local activation, and edge propagation.
- Only useful if cells emit sparse phrase events, not a pixel field.

`boids / flocking`

- Best for fish school, bird flock, current particles, and phrase agents following common fate.
- Figure/flock identity needs Austin review; generic motion-only tests can stay internal.

`reaction-diffusion-like fields`

- Best as an invisible substrate for where phrases form, thicken, or fade.
- Do not let it replace readable primitives with generic organic texture.

`spline / spine rigs`

- Best immediate path.
- A phrase follows a curve; shapes orient from tangent and origin; spacing compresses at curvature and constriction.
- Use this for water/current first, then only later for fish, wings, ribs, or figures.

## From Crude Symbols To Sophisticated Compositions

1. Start with one readable phrase: `circle -> crescent -> crescent -> trigon`.
2. Give it a topology: impact point, bend, eddy, fall axis, membrane, or path.
3. Tune morphology: crescent thickness/arc, trigon rear base, oval stretch, line taper.
4. Add adjacency rules: cup, touch, enclose, release, chain.
5. Animate only the relationship: origin pulse, crescent phase, trigon release.
6. Add a second phrase only if the two share a path, boundary, or topology.
7. Scale to composition through S-curves, membranes, and sparse clusters, not grids.
8. Add substrate effects last: SDF, heightfield, reaction field, blur, or footage.

The key sophistication jump is relational clarity. A primitive phrase should still read in a still frame; motion should deepen the relation, not explain a weak layout.

## Safety Boundary

Safe internal exploration:

- Water-first phrase tests: pond ripple, current, river bend, waterfall, rain impact, mist as partial phrase.
- Abstract topology: bends, eddies, constrictions, paths, membranes, boundaries.
- Graph validation, spline rigs, and black-background phrase studies.
- Generic morphology tests for crescent thickness, trigon base, oval stretch, and line taper.

Austin approval required:

- Public use of any Austin-derived grammar.
- Fish, birds, wings, fins, ribs, eyes, face structures, rays, sun/sky behavior, or figure semantics.
- Exact Austin source geometry, palette, composition, or atom adjacency.
- Any claim of traditional meaning, Coast Salish grammar, cultural approval, crest/clan reference, named being, or public readiness.
- Relief/wrapped 3D or James Harry sculpture-derived topology.

## Practical 48-Hour Prototype Roadmap

### Hours 0-6: Syntax Validator

- Implement a small JSON phrase validator against `grammar_v001.json`.
- Check shape order, adjacency, cultural status, orientation source, and boundary role.
- Output text diagnostics only; no media.

### Hours 6-12: Morphology Harness

- Define parameter ranges for circle/oval, crescent, trigon, line/outline.
- Generate numeric recipe variants only: no rendered frames.
- Flag invalid variants such as generic triangles, backwards crescents, and accidental circle gaps.

### Hours 12-24: Spline Phrase Engine

- Build data structures for one path-led phrase: origin, tangent, curvature, compression, release.
- Author three water-only test recipes as JSON: pond ripple, river bend, waterfall axis.
- Keep all outputs as recipe JSON and debug logs.

### Hours 24-36: Graph Grammar Layer

- Add node/edge representation: cups, follows, releases, encloses, pivots.
- Convert the three water recipes into graphs.
- Add invalid adjacency tests so future renderers fail before drawing bad layouts.

### Hours 36-48: Motion Semantics Draft

- Add time fields to recipes: pulse, phase, rotation, release, attenuation.
- Simulate state numerically and log shape transforms per time step.
- Prepare a review packet with still-unrendered JSON, expected behaviors, and Austin questions.

Next visual step after this roadmap: render only the accepted water phrase graphs, one at a time, with large primitive shapes and no field tiling.
