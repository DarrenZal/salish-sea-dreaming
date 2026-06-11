# Motion / Physics To Primitive Grammar - 2026-05-20

Status: INTERNAL Agent C spec for Agent A/B support. No rendering. Not Austin-approved. Not public-use guidance. Not a cultural-meaning claim. Not a literal physical model unless a separate simulation says so.

Read with:

- [primitive-pattern-language-canon-2026-05-20.md](primitive-pattern-language-canon-2026-05-20.md)
- [primitive-grammar-visual-acceptance-criteria-2026-05-20.md](primitive-grammar-visual-acceptance-criteria-2026-05-20.md)
- [smooth-fluid-primitive-grammar-prototype-2026-05-20.md](smooth-fluid-primitive-grammar-prototype-2026-05-20.md)
- [primitive-topology-grammar-cymatics-2026-05-20.md](primitive-topology-grammar-cymatics-2026-05-20.md)
- [overnight-visual-review-notes-2026-05-20.md](overnight-visual-review-notes-2026-05-20.md)

## Purpose

Define how footage motion, optical flow, and simple field quantities map to circle / crescent / trigon grammar for internal prototypes. Footage supplies apparent image-plane motion and confidence cues. Primitive grammar uses those cues for placement, orientation, timing, scale, opacity, and debug labels. The result is a visual mapping, not a claim about real water physics, cultural meaning, or Austin approval.

## 1. What We Can Infer From Footage

| Signal | Estimate | Use in grammar | Limits |
|---|---|---|---|
| Apparent velocity | Optical flow `flow(x, y) = (u, v)` between frames. | Local tangent, downstream direction, speed-ranked placement, common-fate drift, streamlines, wake traces, low-opacity footage alignment. | Image motion only. It can include camera motion, parallax, reflection, shadow, exposure flicker, specular highlights, occlusion, and blur unless compensated. |
| Divergence / expansion-contraction proxy | `div = du/dx + dv/dy`. | Positive: expansion, opening, pulse, ripple birth, spacing increase. Negative: contraction, compression, return, fade, tightening. Near zero: stable drift/current hold. | Not literal pressure, compression wave, or density change. |
| Curl / vorticity proxy | `curl = dv/dx - du/dy`. | High magnitude suggests circle/oval eddy knot or pivot. Sign controls clockwise/counter-clockwise side choice after coordinate convention. Surrounding tangent drives crescent orbit; downstream exit drives trigon release. | Not a physical vortex unless a separate simulation or measurement pipeline supports it. |
| Strain / shear proxy | Flow-gradient tensor `J = [[du/dx, du/dy], [dv/dx, dv/dy]]`; use `shear_xy = du/dy + dv/dx`, `stretch = du/dx - dv/dy`. | Oval stretch, crescent thickening/thinning, phrase spacing compression at bends/constrictions, boundary-conflict warning. | Say "shear proxy" or "stretch cue", not measured stress or force. |
| Wake / path traces | Advect seeds through smoothed flow, integrate streamlines, or retain short high-confidence persistence trails. | Hidden guides, faint line primitives, path IDs for phrase placement. Rank by stability, length, curvature, and boundary fit. | Do not replace primitive phrases with dense particle trails. |
| Confidence / occlusion | Forward/backward flow disagreement, mask quality, texture, blur, cut detection, camera stabilization residuals. | Gate primitive birth/death, opacity, fallback to authored splines, rejected-shape counts. | Low confidence includes occlusion/reveal, cuts, low texture, reflections/highlights, blur, uncompensated pan, fast foam/mist. Do not invent strong grammar from weak motion data. |

## 2. What We Must Not Claim

Do not claim:

- literal compression waves in water from optical-flow divergence;
- literal pressure, force, density, turbulence, or CFD unless simulated and labeled as simulation;
- literal fluid-particle tracking from RGB footage;
- cultural meaning, Coast Salish grammar, traditional interpretation, or ceremonial symbolism;
- Austin authorship, Austin approval, or public readiness;
- that circle / crescent / trigon mappings are approved meanings.

Allowed language: "apparent motion proxy", "field-driven placement", "internal primitive grammar sketch", "water-flow review question", "debug overlay shows the mapping used by the renderer."

## 3. Primitive Mapping

| Primitive | Motion-derived roles | Controls | Reject when |
|---|---|---|---|
| Circle / oval | Impact or origin where divergence opens; eddy knot / pivot where curl magnitude is high; pressure-like visual node at bends, rocks, wakes, waterfall lips, or authored path nodes; antinode body in standing-wave extraction; low-motion hold point. | Radius from speed/divergence/antinode area; oval stretch from strain; opacity from confidence and age; pulse before downstream crescents. | It becomes an unlabeled dot, eye, roe, decorative particle, or false physical-pressure claim. |
| Crescent | Wavefront arc around impact/origin; current-following arc; wake arc; orbit arc around eddy/pivot; shear arc on water-sheet or membrane edge. | Tangent follows velocity/path; concavity cups origin, eddy center, or previous phrase state; thickness changes slowly with shear/strain; related crescents share common fate. | It faces away from its origin, flips randomly, reads as a moon stamp, or decorates empty space. |
| Trigon | Downstream exit; radial release from impact/ripple; waterfall descent tip or spray edge; terminal point of wake/path trace; three-region topology or standing-wave cell. | Point follows flow, radial release, or fall axis; rear base attaches to crescent/path/membrane/cell; endpoint scale and opacity usually decrease. | It reads as generic triangle, arrow, spike, detached point, or second origin. |

Default water/motion phrase:

```text
circle/origin -> crescent/phase -> crescent/wake-or-return -> trigon/release
```

Valid variants:

- `line/path -> circle -> crescent -> crescent -> trigon` for streamlines;
- `crescent crest -> circle fold -> crescent trough -> trigon spill` for pressure-ridge studies;
- `outline -> filled cell -> outline -> inverse cell` for standing-wave phase inversion;
- partial `crescent -> faint crescent` for mist only when origin loss is intentional and low-contrast.

Orientation rules:

- Define coordinate convention once per renderer; image-space y often points down, so curl sign must be consistent.
- Circle has no heading unless oval stretch or pulse direction is declared.
- Crescent cup normal points toward origin, eddy center, membrane pressure point, or previous phrase state.
- Flow-following crescents must still read as holding, following, or phasing around a local relation.
- Trigon point follows downstream flow, radial release, fall axis, or terminal path tangent.
- Never randomize orientation to add visual energy.

Opacity / scale / timing rules:

- Confidence gates opacity and birth/death.
- Speed controls travel rate and phrase delay, not density by itself.
- Positive divergence can increase scale, spacing, or opacity after a pulse.
- Negative divergence can tighten spacing, reduce scale, or fade.
- Curl magnitude can increase orbit amount, but cap rotation speed.
- Strain/shear can stretch ovals and crescents, but primitive identity must remain clear.
- Minimum lifetimes and fade ramps prevent frame-to-frame flicker.

## 4. Standing-Wave / Phase-Inversion Mapping

Use this as field/topology animation only unless real audio or membrane simulation is implemented.

| Field element | Primitive grammar mapping |
|---|---|
| Nodal line | Outline, membrane, clip contour, or graph path. It is the stable boundary layer, not decorative line art. |
| Antinode / filled body | One closed lobe maps to circle/oval; pinched or two-arc lobe maps to crescent/lune/lens; three-way lobe or triangular gap maps to trigon. |
| Positive phase | Fill one selected cell family as the primary fill channel. Color/fill choice carries no cultural meaning by itself. |
| Negative phase | Fill the inverse or complementary cell family as negative space, alternate fill, or lower-opacity echo. |

Recommended loop:

```text
nodal outline -> positive fill -> nodal outline -> negative/inverse fill -> nodal outline
```

Transitions should read as breathing/phasing, not strobe. At zero crossing, outlines may remain while filled bodies fade out.

## 5. Review Rubric

Good Agent A water v001/v002 render:

- current, river, or waterfall phrases follow stable apparent flow or authored paths;
- origins, streamlines, flow vectors, confidence, and phrase IDs are visible in debug stills;
- some phrases clearly read as `circle -> crescent -> crescent -> trigon`;
- crescents cup correctly and trigons release downstream/outward/downward;
- low-confidence footage regions are masked, faded, or spline-replaced;
- motion has common fate and does not jitter independently.

Good Agent B field-cycle v003 render:

- many phrase units cycle cleanly at field scale without becoming scatter;
- each phrase keeps stable origin/path and readable primitive identity;
- clean v002 single-shape morph quality combines with richer v001/v002 field behavior;
- births, transitions, and fades are phase-locked to a field, path, or phrase clock;
- debug metadata names primitive role and parent phrase.

Good standing-wave / topology v001 render:

- debug overlay shows nodal outlines, antinodal cells, phase sign, and selected region types;
- filled cells classify cleanly into circle/crescent/trigon-like bodies;
- final layer is sparse and emergent, not a full lattice or mandala;
- outline/fill/inverse-fill transitions are legible and non-flickering.

Fails:

- random crescents or trigons over footage;
- generic triangles, arrows, spikes, crescent-moon stamps, or decorative dots;
- wrong crescent concavity relative to origin/path;
- camera pan or reflection treated as water truth;
- no confidence mask, debug overlay, or rejected-shape count;
- dense particle trails replacing primitive phrases;
- physics language overclaiming footage;
- any Austin approval, cultural meaning, or public-ready claim.

## 6. Implementation Hints

Optical flow:

- Start with OpenCV Farneback for fast iteration.
- Try TV-L1 / Dual TV-L1 when slower, sharper, piecewise-stable flow is worth the cost.
- Downsample for estimation and upsample vectors smoothly.
- Use stable luminance; avoid heavy color dependence.
- Stabilize or subtract global camera motion before interpreting water motion.
- Use forward/backward flow disagreement as confidence.

Smoothing and gradients:

- Spatially smooth flow before gradients.
- Temporally smooth vectors with EMA or windowed median.
- Use Sobel or finite differences for `du/dx`, `du/dy`, `dv/dx`, `dv/dy`.
- Normalize div/curl/strain by robust percentiles, not raw max values.
- Clamp outliers near cuts, flashes, occlusions, and frame edges.

Streamlines and paths:

- Seed only inside high-confidence masks.
- Integrate through smoothed flow with fixed arc-length sampling.
- Rank by length, stability, curvature, and boundary fit.
- Prune aggressively; one strong phrase beats a screen full of traces.
- Keep a sidecar path ID for every phrase.

Avoiding flicker:

- Use hysteresis for birth/death thresholds.
- Give each phrase a minimum lifetime.
- Fade in/out over several frames.
- Track origins and streamlines across frames instead of redetecting from scratch.
- Low-pass orientation with angle unwrapping.
- Quantize phrase clocks lightly so related marks pulse together.

Debug overlays:

- source frame;
- flow vectors or streamlines;
- confidence/occlusion mask;
- divergence, curl, and strain proxy views;
- selected origins and paths;
- primitive IDs, roles, phrase order, and orientation arrows;
- rejected-shape counts and reasons.

Recommended sidecar fields: `phrase_id`, `source`, `origin_xy`, `path_id`, `confidence`, `mean_speed`, `divergence_proxy`, `curl_proxy`, `strain_proxy`, `primitive_order`, `cultural_status`.

## Bottom Line

Use footage and fields to make primitive phrases move with believable common fate. Do not let proxy math become a physics claim, and do not let internal grammar become a cultural or approval claim.
