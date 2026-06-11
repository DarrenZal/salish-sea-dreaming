# Austin-Informed Water Phrase Recipes - 2026-05-19

Scope: Agent C internal recipe pass only. No rendering, no clips, and no edits to Agent A/B/D outputs.

Status: internal Austin-review sketches based on observed compositional logic. These are not traditional meanings, not approved Coast Salish grammar, not Austin-authored outputs, and not public-use guidance.

Machine companion: `track2-deterministic/primitive_grammar/water_phrase_recipes_v001.json`

## Sources Read

- `docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md`
- `docs/space-center/austin-fish-bird-sun-primitive-reference-brief-2026-05-19.md`
- `docs/space-center/primitive-grammar-contract-2026-05-19.md`
- `/Users/darrenzal/Documents/Notes/media/2026-05-18-ssd-meeting-2/03-austin-course01-phase05-water-shapes.png`
- `/Users/darrenzal/Documents/Notes/media/2026-05-18-ssd-meeting-2/05-austin-phase05-loopingscreen.png`
- `/Users/darrenzal/Documents/Notes/media/2026-05-18-ssd-meeting-2/06-austin-vancity-slides-crescent-circle-trigon.png`

## Darren Critique Incorporated

- Heightfield/SDF v002 may be technically interesting, but it is visually wrong for this next step.
- Ripple clips lost the primitive shapes.
- Field clips became grid-like, generic, and too far from Austin's primitive phrase logic.
- The next step is clear primitive phrase units first, then animation.
- Avoid Cartesian tiling, eye-like paired circles, generic triangles, and random orientation changes.
- Keep shapes relational: circle, crescent, and trigon must sit close enough and be oriented clearly enough to read as phrase grammar.

## Shared Recipe Rules

- Author recipes in normalized scene or plane coordinates, with origin at center and positive `y` up, matching `primitive-grammar-contract-2026-05-19.md`.
- Use the core water phrase as a design anchor: `circle -> crescent -> crescent -> trigon`.
- Use circles as impact or knot origins, not repeated eyes.
- Use crescents as close relational bodies, cupping by origin or following the flow tangent.
- Use trigons as attenuation or flow-tip marks, not generic triangles.
- Keep phrases sparse. A useful unit can be three to five visible marks, plus an optional hidden flow spine.
- Prefer hand-authored splines, water paths, impact sites, rocks, bends, and eddies over field fills.
- Preserve common-fate motion: marks in one phrase move, pulse, fade, or drift as one related event.
- Treat perspective, mist, and heightfield/SDF behavior as review questions, not as solved style.

## Recipe 01: Pond Ripple

Intent: a still-water impact that keeps Austin's circle, crescent, crescent, trigon phrase readable.

- Shape order: `circle impact_anchor`, `crescent inner_ripple`, `crescent outer_ripple`, `trigon attenuation_tip`.
- Relative positions: circle at phrase origin. First crescent close to the circle on the travel/ripple axis. Second crescent farther out on the same axis. Trigon at the far edge, still close enough to read as the same phrase.
- Rotation/orientation rules: crescents cup back toward the circle unless Austin says the cup should face travel. Trigon points away from the circle along the radial axis. No random flips.
- Scale relationships: first crescent about 1.15x to 1.4x circle diameter. Second crescent about 1.35x to 1.75x circle diameter. Trigon slightly smaller than the second crescent so it reads as attenuation.
- Spacing rules: spacing starts compressed at the circle and opens outward. Total phrase length should stay compact; do not spread marks so far that the order disappears.
- Animation behavior: circle appears first, crescents phase in after it with a small outward drift, trigon appears last and fades first. The phrase breathes once or twice; it does not become a tiled field.
- What this asks Austin: should water crescents cup toward the impact origin, face the direction of ripple travel, or vary by water state?
- What not to do: do not use concentric generic rings, dense ripple shaders, paired circles that read as eyes, or heightfield effects that erase the circle/crescent/trigon shapes.

## Recipe 02: River Bend / Eddy Cluster

Intent: a sparse cluster at a bend or rock interaction, matching the observed river path logic in Austin's water examples.

- Shape order: optional hidden `line flow_spine`, `circle current_knot`, `crescent bend_cup`, `crescent eddy_return`, `trigon downstream_tip`.
- Relative positions: place the circle near the inside of the bend or rock-contact compression point. First crescent sits just downstream on the outside edge of the bend. Second crescent curls back toward the inside lane. Trigon exits along the downstream tangent.
- Rotation/orientation rules: all non-circle marks follow the local river tangent, with the second crescent allowed to rotate slightly against the tangent to imply eddy return. Trigon points with downstream flow.
- Scale relationships: circle is small and not dominant. First crescent is largest. Second crescent is smaller and tighter. Trigon is narrow and tapered.
- Spacing rules: marks compress near the bend or rock, then open downstream. Use one cluster per bend; do not cover the whole river surface.
- Animation behavior: phrase slides around the bend with shared timing. The eddy crescent lags or counter-rotates subtly while remaining locked to the same cluster.
- What this asks Austin: can a river bend phrase bend the ripple order around topology, or should it remain closer to a straight circle-to-trigon sequence?
- What not to do: do not make a Cartesian lattice across the river, do not populate every open water area, and do not let eddy marks rotate independently like decorative particles.

## Recipe 03: Waterfall Vertical Phrase

Intent: a vertical falling-water unit based on the observed stacked waterfall marks.

- Shape order: optional hidden `line fall_axis`, `circle lip_or_drop_origin`, `crescent falling_body`, `crescent falling_body_lower`, `trigon downward_attenuation`.
- Relative positions: circle sits near the waterfall lip or a visible drop origin. Crescents stack below it on the fall axis, with slight horizontal offsets only when the fall sheet bends. Trigon sits at the lower end of the unit.
- Rotation/orientation rules: fall axis is primary. Crescents cup upward toward the origin or sideways into the fall sheet as an Austin review question. Trigon points down.
- Scale relationships: vertical phrase uses narrower marks than pond ripple. Circle is modest. Lower crescent may stretch slightly in the fall direction. Trigon is long enough to read as descent, not a generic triangle.
- Spacing rules: tighter spacing near the lip or rock break, looser spacing down the fall. Keep large blank water sheets between vertical phrases.
- Animation behavior: circle pulses at the lip, crescents descend with slight stretch/fade, trigon drops and dissolves. All marks share downward common fate.
- What this asks Austin: is vertical stacking an acceptable extension of the pond ripple grammar for falling water?
- What not to do: do not turn the waterfall into a full column of repeated symbols, do not use random sideways orientations, and do not rely on particle spray alone.

## Recipe 04: Current Knot

Intent: a compact turbulence unit where two current paths meet without becoming an eye-like pair of circles.

- Shape order: `circle knot_anchor`, `crescent incoming_cup`, `crescent crossing_cup`, `trigon release_tip`.
- Relative positions: circle sits at the knot center. First crescent sits close on the dominant incoming tangent. Second crescent sits close on the crossing tangent, offset enough to avoid bilateral eye symmetry. Trigon exits on the strongest release direction.
- Rotation/orientation rules: each crescent aligns to its own tangent and cups toward the knot. Trigon points away from the knot along the release tangent.
- Scale relationships: circle is the smallest or tied with trigon. Crescents are similar scale but not mirrored. Trigon is slim and directional.
- Spacing rules: keep the phrase tight. The two crescents should overlap in neighborhood but not form a regular X or compass rose.
- Animation behavior: incoming crescent brightens first, crossing crescent follows, circle briefly holds, then trigon carries the release outward.
- What this asks Austin: can a circle serve as a current knot where water paths meet, or should circles remain primarily droplet/ripple origins?
- What not to do: do not use two circles, symmetric eye pairs, four-way compass layouts, or generic triangle bursts.

## Recipe 05: Rain Impact

Intent: many possible small impacts, but authored as sparse individual phrases rather than a wallpaper of droplets.

- Shape order: `circle droplet_origin`, `crescent tiny_ripple`, optional second `crescent faint_ripple`, optional `trigon faint_attenuation`.
- Relative positions: each impact is a miniature pond ripple. The visible crescent should sit within one to two circle diameters of the origin. Use the trigon only for a few stronger impacts.
- Rotation/orientation rules: orientation is radial from each impact. If several rain phrases are visible, their axes may differ because origins differ, but each individual phrase must remain internally coherent.
- Scale relationships: all shapes are smaller and lower contrast than the main pond ripple recipe. Strong impacts can scale up slightly; quiet impacts should stop at circle plus one crescent.
- Spacing rules: sparse stochastic placement is allowed only at the phrase-origin level. Avoid grid spacing and avoid uniform density. Leave large quiet water areas.
- Animation behavior: impacts pop in quickly, expand a short distance, then fade. Stronger impacts may show the trigon late; most should remain partial phrases.
- What this asks Austin: should rain-over-pond use the same circle-to-crescent-to-trigon phrase, or should rain stay quieter and more partial?
- What not to do: do not make a raindrop grid, do not convert circles into roe-like particles, and do not show so many origins that circles read as many eyes.

## Recipe 06: Wave Crest / Trough Duality

Intent: a paired crest/trough water phrase that expresses a wave relation without using paired circles.

- Shape order: optional hidden `line wave_spine`, `crescent crest`, `circle pressure_anchor`, `crescent trough_return`, `trigon spill_tip`.
- Relative positions: crest crescent rides slightly above the wave spine. Circle sits near the pressure point where the crest begins to fold, not mirrored across the trough. Trough crescent sits below and downstream. Trigon sits at the spill or attenuation edge.
- Rotation/orientation rules: crest crescent follows wave tangent and cups into the wave face. Trough crescent follows the same tangent but lower and slightly phase-offset. Trigon points along spill direction.
- Scale relationships: crest crescent is largest. Trough crescent is slightly smaller and dimmer. Circle is small to medium. Trigon is small and sharp.
- Spacing rules: keep the crest and trough close enough to read as one dual phrase. Do not repeat the pair at regular wave intervals.
- Animation behavior: crest leads, circle pulses at folding pressure, trough follows with delayed fade, trigon releases at the end.
- What this asks Austin: can a water phrase express crest/trough duality while keeping the circle as a pressure anchor rather than an eye?
- What not to do: do not make sinusoidal wallpaper, paired eyes, generic triangle foam, or mirrored decorative crescents.

## Recipe 07: Mist Partial Phrase

Intent: a low-contrast in-between water state that keeps primitive logic partial and reviewable.

- Shape order: `crescent soft_arc`, optional `crescent echo_arc`, optional `trigon faint_tip`, optional absent `circle hidden_origin`.
- Relative positions: start from an implied origin outside or just beyond the visible mist bank. One or two crescents sit along the mist flow. Trigon appears only as a faint terminal cue.
- Rotation/orientation rules: crescents follow the slow drift tangent and remain gently related to the hidden origin. Trigon, if used, points with drift.
- Scale relationships: crescents are larger, softer, and lower opacity than ripple marks. Trigon is smaller and faint. Circle is usually omitted or hidden to avoid turning mist into impacts.
- Spacing rules: partial phrases should be isolated. Do not use dense fog fields made from repeated crescents.
- Animation behavior: slow fade, slight drift, and soft reveal. No hard pulsing. Partial phrases can appear and disappear before completing the full sequence.
- What this asks Austin: should mist/fog/cloud states use partial primitive phrases, or should explicit crescents/trigons stay out of mist until more guidance exists?
- What not to do: do not treat mist as generic particles, do not fill the frame, do not add random rotations, and do not imply this is approved cloud grammar.

## Recipe 08: Perspective Water-Plane Phrase

Intent: a tilted-plane version of pond/current grammar, kept as a clear Austin review question.

- Shape order: `circle plane_origin`, `crescent near_body`, `crescent far_body`, `trigon far_attenuation`.
- Relative positions: author all positions in water-plane UV space first. Circle anchors the origin. Crescents and trigon advance along the UV radial or flow path. Projection to screen happens after phrase placement.
- Rotation/orientation rules: orientation is computed in plane space from origin or flow tangent, then projected. Do not fake depth with random scale changes.
- Scale relationships: scale falls off according to the plane projection only. Near/far differences should preserve phrase legibility; the trigon must not vanish before it can be read.
- Spacing rules: UV spacing remains compressed near origin and opens outward. Screen-space spacing may compress because of perspective, but the phrase should still read.
- Animation behavior: animate in plane space as a coherent phrase, then project. The whole unit can drift across the water plane, but marks do not jitter independently.
- What this asks Austin: can the same primitive water phrase live on a tilted water plane, or should review stay flat/head-on for now?
- What not to do: do not use heightfield/SDF depth effects that hide primitive identity, do not scatter perspective sprites, and do not treat this as approved 3D relief or carved grammar.

## Implementation Notes For Later Renderers

- Start with one phrase on black or a plain water field before adding footage, heightfields, or SDF materials.
- Render phrase labels or debug guides only in internal review tooling, not in Austin-facing visual exports unless requested.
- Validate shape order and orientation before style. If the phrase cannot be read in a still frame, animation will not fix it.
- Keep all generated outputs under `internal` status until Austin reviews the specific use.
