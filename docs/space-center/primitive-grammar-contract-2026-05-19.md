# Primitive Grammar Contract Syntax Draft - 2026-05-19

Machine contract: `track2-deterministic/primitive_grammar/grammar_v001.json`

Accepted internal grammar-correct v002 baseline: `track2-deterministic/primitive_grammar/water_phrase_layouts_source_grounded_v002.json`

Status: INTERNAL Darren syntax draft, Austin-review-needed, not Austin-approved. Darren accepted v002 only as an internal grammar-correct baseline. This does not approve public use, does not claim Austin authorship of generated outputs, does not assign traditional meanings to primitives, and is not a general Coast Salish grammar claim. It gives Python, TouchDesigner, Blender, and future web demos the same parameter names, roles, palettes, projection rules, and cultural gates.

## Explicit Warning

This document is a Darren/internal/Austin-review-needed working contract. It is a technical syntax draft for coordinating experiments in this project only.

It must not be represented as:

- A general Coast Salish visual grammar.
- Austin's approved grammar.
- A public-use cultural style guide.
- A claim that circles, crescents, trigons, ovals, outlines, figures, or topology marks have fixed traditional meanings.

Every public-facing use, exact-source use, figure use, palette-reference use, or Austin-derived semantic claim still needs Austin review and a separate approval record.

## Purpose

The shared grammar solves the coordination problem surfaced in the research synthesis: water, fish, bird/flocking, sun/sky, and future review demos need one reusable primitive vocabulary instead of independent renderer-specific guesses.

The contract defines:

- Primitive parameters for `circle`, `crescent`, `trigon`, `oval`, and `line`.
- Source-grounded v002 syntax rules for valid/invalid adjacency.
- Shape-quality rules for circle, crescent, trigon, and oval/outline use.
- Motion semantics for water phrases, figure construction, and topology placement.
- Palette roles and blend-mode constraints.
- Projection modes for flat 2D, flow-aligned 2D, perspective planes, heightfield/SDF water, mesh-normal instancing, relief/3D, and exact Austin source use.
- Role bindings for water, fish, bird, sun/sky, exact Austin source, and blocked subjects.
- Cultural-status fields: `internal`, `Austin-review-needed`, and `public-blocked`.

## Source Basis

The contract is distilled from:

- `docs/space-center/deep-research-fluid-grammar-synthesis-2026-05-19.md`
- `docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md`
- `docs/space-center/austin-fish-bird-sun-primitive-reference-brief-2026-05-19.md`
- `docs/space-center/source-grounded-water-phrase-layout-correction-v002-2026-05-19.md`
- `track2-deterministic/primitive_grammar/water_phrase_layouts_source_grounded_v002.json`

Key synthesis points:

- Use a real shared `grammar.json`.
- Treat water as the safest lead and move toward heightfield/SDF glyph embedding.
- Preserve Darren-accepted v002 rules: crescent cupping, trigon specificity, gap discipline, boundary discipline, and phrase order.
- Keep fish, bird/flocking, sun/sky, and exact-source animation independently reviewable.
- Keep every generated primitive output internal until Austin reviews the specific use.

## Cultural Status

`internal` means private technical sketching and review preparation only. It does not allow public projection, publication, recording, or audience-facing use.

`Austin-review-needed` means the idea may be worth exploring internally, but requires Austin review before any public use. Most figure, sun, exact-source, palette-reference, and perspective/3D use lands here.

`public-blocked` means blocked under this contract. Named people, chiefs/specific persons, Thunderbird, double-headed serpent, supernatural beings, crest/clan-specific scenes, James Harry relief/wrapped-sculpture translation, and unreviewed visitor-prompt figures are all blocked unless a separate explicit approval path is created.

The JSON has a strict `public_export_rule`: no instance or role in this contract is public-approved by default.

The v002 baseline is accepted only as Darren's internal grammar-correct geometry baseline. It is still not Austin-approved and cannot be promoted into public use by this document.

## Interop Rules

All runtimes should use normalized scene coordinates:

- Origin: center.
- `x`, `y`, `z`: `-1.0` to `1.0`.
- Positive `y`: up.
- Rotation: radians, counterclockwise.
- Scale: fraction of the short axis.
- Transform order: translate, rotate, scale, project.

Every shape instance should carry:

```json
{
  "id": "water_phrase_001_circle",
  "primitive": "circle",
  "x": 0.0,
  "y": 0.0,
  "scale": 0.1,
  "rotation": 0.0,
  "opacity": 0.6,
  "palette_role": "water_light",
  "role": "water_impact_anchor",
  "cultural_status": "internal"
}
```

Optional fields include `z`, `phase`, `velocity`, `flow_tangent`, `parent_phrase_id`, `projection_mode`, `sdf_parameters`, `stroke_parameters`, and `metadata`.

## Primitive Parameters

`circle` is a round focal, origin, impact, pivot, joint, eye, body-center, roe-like, or orb shape depending on role. It supports `radius`, `inner_radius_ratio`, `edge_feather`, and `stroke_width`.

`crescent` is a curved cupping shape for ripple bodies, current bands, body marks, wing arcs, wakes, rotation phases, or cloud/mist arcs. It supports `outer_radius`, `inner_radius_ratio`, `inner_offset_ratio`, `arc_angle`, `tip_sharpness`, `cup_direction`, and `edge_feather`.

`trigon` is a three-pointed tapered primitive for ripple release, attenuation, flow tips, heads, tails, fins, beaks, feather cuts, and rays. It supports `radius`, `concavity`, `base_flatness`, `corner_rounding`, `point_direction`, and `edge_feather`.

`oval` is a stretched circle or outline field for eyes, body cores, sun face details, eddies, membranes, boundaries, and soft orbs. It supports `radius_x`, `radius_y`, `aspect_ratio`, `inner_radius_ratio`, and `edge_feather`.

`line` is a stroke/curve used as a flow spine, flock path, skeleton, horizon, or construction guide. It supports `length`, `width`, `curvature`, `cap_style`, `dash_ratio`, and `edge_feather`.

## Shape-Quality Rules

### Circle

- Must read as a deliberate origin, pivot, impact, joint, eye, or anchor; not as accidental empty space.
- In water phrases, the circle is the focal origin held by adjacent crescents.
- Paired or clustered circles are high-risk because they can read as eyes, roe, bubbles, or creature bodies. Use only with explicit role labels and internal review.
- Hollow circles are allowed only when the `inner_radius_ratio` is intentional and the role explains whether the mark is a ring, boundary, eye, or impact.

### Crescent

- The concave side cups the circle/origin by default.
- A flow-following crescent may rotate with a current, path, wing, wake, or body only if it still reads as holding, following, or phasing around the local origin.
- Crescent tips should feel shaped, not like an arbitrary crescent moon stamp. `tip_sharpness`, `arc_angle`, and `inner_offset_ratio` should be controlled per role.
- Backwards crescents, isolated decorative crescents, and crescents that face away from their origin are invalid unless the instance is explicitly marked as a review question.

### Trigon

- The trigon must read as a curved pointed primitive with a crescent-like or flat/rounded rear base, not a generic triangle.
- The point direction is the release, ray, fin, head, tail, attenuation, or path direction.
- The rear base should connect visually to the previous crescent, line, body, or membrane without creating an accidental circle-sized void.
- Sharp equilateral triangles, UI arrows, and generic play-button shapes are invalid.

### Oval / Outline

- Ovals and outlines must declare whether they are body core, eye, eddy, membrane, boundary, or soft anchor.
- Outline marks may contain motion or topology but should not become unreviewed crest, mask, face, or animal-body claims.
- An oval may substitute for a circle only when elongation is semantically meaningful: eye direction, current stretch, body axis, eddy shear, or membrane pressure.
- Accidental oval gaps between crescents/trigons are invalid; fill or close them as documented anchors.

## Valid Adjacency Rules

The accepted internal water baseline is:

```text
circle/origin -> crescent -> crescent -> trigon/release
```

Valid adjacency patterns:

- `circle -> crescent`: valid when the crescent cups the circle/origin.
- `crescent -> crescent`: valid when the pair reads as phase, wake, ripple body, cupping sequence, body articulation, or rotation around the same local origin.
- `crescent -> trigon`: valid when the trigon point releases outward/downstream and its rear base closes the crescent transition without a circle-like gap.
- `line/path -> circle/crescent/crescent/trigon`: valid when the line is a flow spine, eye path, skeleton, or construction guide and instances remain flow-aligned.
- `circle/oval -> crescent`: valid for joints, eyes, eddies, body points, or water impacts when role labels make the anchor explicit.
- `oval/outline -> internal primitives`: valid for membranes, body fields, eddy fields, or bounded water areas when child primitives remain inside the boundary.
- `trigon -> trigon`: valid for rays, fin arrays, attenuation marks, or feather-like cuts only when alignment, spacing, and role labels prevent random scatter.

Every valid adjacency must preserve:

- A declared local origin or path.
- Directionality: cupping, flow, release, rotation, or containment.
- Cultural status on each instance.
- Boundary discipline for water, bodies, membranes, and review-only source areas.

## Invalid Adjacency Rules

Invalid or blocked by default:

- `circle -> crescent` where the crescent faces away from the circle/origin.
- `crescent -> trigon` with a circle-sized accidental void between them.
- `crescent -> trigon` where the trigon reads as a generic triangle, UI arrow, or random spike.
- Repeated primitives scattered without a path, origin, topology, or role.
- Random orientation flips in flow-aligned phrases.
- Primitive marks drifting outside a water band, figure body, membrane, or declared boundary unless explicitly marked as foam/spray/review.
- Eye-like paired circles or oval/circle pairs without a figure/eye role and Austin-review-needed status.
- Figure assembly from joints, fins, ribs, wings, or eyes without a review-needed status.
- Exact Austin-source atom adjacency reused as generic grammar.
- Any adjacency that claims a traditional meaning, crest/clan reference, supernatural subject, named person, or public approval.

## Motion Semantics

Motion must follow the primitive's declared role. It should not be generic particle drift when the scene claims grammar.

### Circle

`circle` means origin, pivot, impact, or joint:

- Origin: the local focal point that crescents cup and trigons release away from.
- Pivot: a rotation center for wings, fins, joints, eddies, or rays.
- Impact: a contact event where water, body, or path force enters the scene.
- Joint: a hinge or articulation point in a figure, body, wing, rib, or fin system.

Valid motion: pulse, hold, orbit center, impact expansion, hinge rotation, or anchored drift with a path.

### Crescent

`crescent` means phase, wake, cupping, or rotation:

- Phase: sequential state in a phrase or body articulation.
- Wake: a trailing water/current mark.
- Cupping: a holding relationship around a circle/origin.
- Rotation: a curved sweep around a pivot, joint, eddy, wing, or membrane.

Valid motion: cup-and-follow, ripple propagation, rotational sweep, wake decay, body/wing arc deformation, or current-aligned drift.

### Trigon

`trigon` means release, point, fin, ray, or attenuation:

- Release: end of a phrase moving away from the origin.
- Point: directional emphasis for head, beak, tail, path, or flow.
- Fin: tapered body appendage or water-body interaction mark.
- Ray: radial emission, sun/sky review branch, or attention line.
- Attenuation: diminishing endpoint of ripple/current energy.

Valid motion: point-leading translation, downstream release, radial pulse, fin sweep, tail flick, or fade/scale attenuation.

## Figure Semantics

Figure use is Austin-review-needed by default. These rules are only internal hypotheses for keeping experiments coherent; they do not approve fish, birds, people, masks, crests, or public scenes.

- Joints: usually `circle` or small `oval`, used as pivots or hinges. They must articulate something and should not become decorative dots.
- Fins: usually `trigon` or tapered crescent/trigon combinations, pointing with body motion or water release.
- Ribs: repeated `crescent`, `line`, or narrow `oval` marks following a body axis or membrane.
- Wings: `crescent` arcs around circle/oval pivots, possibly with trigon cuts or tips. Raven-specific silhouettes remain review-needed or exact-source only.
- Eyes: `circle` or `oval` anchors with high cultural/figure sensitivity. Paired eyes, face structures, and mask-like arrangements require review.
- Rays: radial `trigon` or line/trigon sequences from a circle/orb. Austin-derived sun behavior is review-needed.
- Water marks: `circle -> crescent -> crescent -> trigon` phrases, eddies, wakes, impacts, and boundary-contained flow marks. Water remains the safest internal lead but still not public-approved.

## Topology Semantics

Topology placement controls where grammar events are allowed to appear.

- Bends: phrase events can emerge where a path, river, body, or membrane changes direction. Crescents should respond to the bend and trigons release with the exit direction.
- Eddies: circles/ovals mark local rotation centers; crescents orbit or cup the center; trigons attenuate along the outgoing current.
- Constrictions: narrowed boundaries can compress scale, spacing, and opacity; marks should not spill outside the membrane or water body.
- Paths: lines or implicit spines define order, timing, and tangent orientation. Phrases should follow the path rather than scatter across a Cartesian grid.
- Membranes: ovals/outlines or water masks contain child primitives. Motion can press, ripple, or shear along the membrane, but crossing the boundary needs an explicit role.
- Boundaries: water bands, figure silhouettes, source planes, and review masks are hard constraints unless a mark is explicitly labeled as edge foam, spray, ray spill, or review exception.

## Palette Contract

The default output layer is RGB on black for `Add` or `Screen` in Resolume. Alpha is allowed when needed, but black-background additive clips remain the most portable fallback.

Palette roles:

- `water_light`: cool luminous water marks, internal.
- `water_depth`: deeper blue water field, internal.
- `sun_warm_internal`: warm sun/ray colors, Austin review needed.
- `salmon_reference_internal`: Austin salmon-source reference colors, Austin review needed.
- `bird_silhouette_internal`: bird/raven-source reference colors, Austin review needed.
- `review_neutral`: white/gray review marks, internal.

Do not use palette roles to imply cultural approval or Austin authorship. Exact-source colors require review before public use.

## Projection Contract

`flat_2d` is the simplest internal projection: normalized primitives on a 2D plane.

`flow_aligned_2d` rotates primitives by `flow_tangent`, phrase origin, spine tangent, flock heading, or radial vector. Random orientation flips are invalid.

`perspective_plane` authors primitives in UV plane space and projects them by homography or camera matrix. This is a review-needed branch before public use.

`heightfield_sdf` embeds primitive SDF into a water height/normal field before shading. This remains internal/review-needed and should not override the source-grounded v002 water phrase rules.

`mesh_normal_instance` is for Blender/3D placement on displaced surfaces. It needs review before public use.

`relief_or_wrapped_3d` is public-blocked here because it approaches carved/relief and James Harry reference territory.

`exact_source_projection` means using Austin source SVG geometry or decomposed atoms directly. It requires source usage clearance and per-output review.

## Role Bindings

Water is the safest internal lead. The core phrase is:

```text
circle -> crescent -> crescent -> trigon
```

Circle marks origin or current knot; crescents carry ripple/current body; trigon marks attenuation or flow tip; line carries flow spine; oval can mark eddies or soft anchors.

Fish is review-needed. Generic internal fish should not copy Austin's exact salmon. The proposed internal hypothesis is:

```text
line spine -> trigon head -> crescent gill/body -> oval/circle eye or body point -> crescent body -> trigon tail
```

Bird is review-needed. Generic flock birds should not copy the raven silhouette. The proposed internal hypothesis is:

```text
crescent wing arc -> oval body core -> trigon head/beak
```

Sun/sky is review-needed when it uses Austin-derived sun/ray behavior. Generic internal fields can test circle/orb plus radial trigon/ray motion, but exact `Nature_Cosmic_Sun` face animation requires review.

Exact Austin source is review-needed and not enabled for generic grammar work. Use the three SVG paths only when the task is explicitly exact-source analysis or Austin-approved animation.

## Runtime Guidance

Python renderers should load `grammar_v001.json`, validate `primitive`, `palette_role`, `projection_mode`, and `cultural_status`, then dispatch to SDF or vector functions by `sdf_function`. Renderers using this draft should also enforce the v002 syntax rules for crescent cupping, trigon specificity, gap discipline, and boundary discipline.

TouchDesigner should map each primitive instance to CHOP/TOP rows with stable channels: `x`, `y`, `z`, `scale`, `rotation`, `opacity`, `phase`, `primitive`, `role`, `palette_role`, `cultural_status`, and SDF parameter columns. The heightfield/SDF path should fold glyph fields into the heightmap before normal generation.

Blender should map primitive instances to Geometry Nodes attributes. Use normalized coordinates on a plane or UV surface, then project/instance on mesh normals only when the scene role permits it.

Web demos should consume the same JSON scene-graph shape instances. SDF shaders should use the same parameter names as the contract to avoid divergent browser-only behavior.

## Validation Expectations

Minimum scene contract:

```json
{
  "schema_version": "primitive_grammar_v001",
  "syntax_draft": "v002_internal",
  "instances": []
}
```

A public export validator must fail if:

- Any instance is `public-blocked`.
- Any instance is `Austin-review-needed` and no Austin approval record exists.
- Any exact Austin source geometry is used without source clearance.
- Any generated output claims Austin authorship or cultural approval.
- Any blocked subject appears in scene metadata or role labels.
- Any output claims this contract is a general Coast Salish grammar or Austin-approved grammar.

An internal syntax validator should flag:

- Crescents that face away from their declared origin.
- Trigons that use generic triangle geometry.
- Circle-sized accidental voids between crescent and trigon forms.
- Primitive marks outside declared water/body/membrane boundaries.
- Figure semantics without `Austin-review-needed` cultural status.

An internal review export should preserve source paths, role labels, cultural status, adjacency notes, topology notes, and review questions so Austin can critique the specific behavior.

## Implementation Notes

This syntax draft extends the conservative v001 machine contract with Darren-accepted internal v002 geometry rules. It is broad enough for Python, TouchDesigner, Blender, and web demos, but it does not bless any output.

Future machine changes should add `grammar_v002.json` and keep this companion doc versioned if Austin clarifies primitive roles, figure boundaries, palette usage, projection permissions, or public-use limits.
