# Pearl Interior — Vision + Experiment Spec — 2026-05-17

`[INTERNAL — DO NOT SHARE]`

> Captured 2026-05-16 late evening from a creative exploration between operator and Claude. **All outputs go to `track2-deterministic/morph_outputs_INTERNAL/`** with provenance CSV entry per the policy in `docs/space-center/sunday-internal-experiment-lane-2026-05-17.md`. Nothing here ships, nothing here goes to Austin without per-output OK. We're playing in the Coast Salish formline grammar (Circle / Crescent / Trigon = Coast Salish primitives per `reference_coast_salish_formline_primitives.md`) — our compositions are our own design choices, but we're still in the cultural lineage.

---

## Vision direction (the creative through-line)

A still, iridescent **oyster pearl** that the viewer is inside. The pearl does not rotate. The **shapes move inside it** — Circle, Crescent, Trigon — in slow breath-cycle motion, composing and re-composing in classic Coast Salish radial grammar. Shapes have **volume** (half-spheres, not flat overlays). Motion is **slow, smooth, eased** — pearl breathes; shapes orbit each other; nothing flickers.

This is also a re-statement of Austin's Pearl Vision (May 11 email): "Thunderbird passes down a pearl with 3 shapes morphing inside; viewer is inside the pearl receiving the teaching." Our experiments converge on his framing while remaining internal-only until he sees and reacts.

---

## Architectural pivot (the tooling reframe)

SD img2img through Austin v2 LoRA is **not the right primary engine** for structural pearl-interior work. It has temporal-coherence problems (flicker) and material-fidelity problems (sphere ≠ pearl). It's good at atmospheric style passes; it's wrong for geometry.

Revised track architecture for the pearl-interior piece:

| Track | Tool | Role |
|---|---|---|
| **Track 2 — structural** (expands) | **Blender (Cycles + Principled BSDF + thin-film iridescence)** as primary; TouchDesigner as live-performance alternative | Pearl material, primitive geometry (incl. half-spheres), camera, motion control, breath-cycle timing, native 5120×1600 render |
| **Track 1 — style** (narrows) | SD + Austin v2 LoRA | Thin atmospheric pass over rendered 3D **only** for moments where painterly texture is wanted. Not the structural engine. |
| Autolume (unchanged) | StyleGAN2 + Real-ESRGAN x4 + Resolume composition | Abstract organic background atmosphere only (still the Arshia question) |

**The unlock:** we already have `track2-deterministic/morph_outputs/exp4_hybrid_pearl_container_model_2026-05-16.ply` — a real 3D mesh on disk. Sunday morning we open it in Blender, apply proper pearl material, re-animate. No SD required for the structural pass.

---

## Aesthetic specs

### Pearl material (oyster pearl, not grey sphere)
- **Base:** Principled BSDF
- **Transmission:** 0.8–0.95 (translucent depth, not opaque)
- **Roughness:** 0.05–0.15 (soft satin, not mirror)
- **IOR:** 1.53–1.56 (real pearl nacre range)
- **Thin-film interference:** enabled, thickness 350–600nm range (gives the pinkish-blue-green nacre shimmer)
- **Subsurface:** light scattering enabled with warm pink-cream tint (depth)
- **Coat layer:** thin clear coat for surface bloom
- **Lighting:** soft ambient + 1 key light + 1 subtle rim light (no harsh shadows)
- **Reference images:** real oyster pearl photos for color reference (operator can pull a few from web)

### Motion (slow, smooth, eased)
- **Base rate:** 360° rotation over 36 sec (half the speed of current Exp 4)
- **Easing:** ease-in-out on all transforms (no linear motion anywhere)
- **Frame rate:** 24fps render (smoother than 12fps)
- **Breath cycle:** 5–6 sec inhale, 5–6 sec exhale (matches resting human breath rate, induces parasympathetic response in viewer)
- **Optional polish:** RIFE or FILM frame interpolation to 48fps for ultra-smooth motion

### Half-sphere primitive geometry
- **Circle/Oval:** full sphere or sphere with subtle vertical flatten (egg shape), high SSS scattering for soft glow
- **Crescent:** half-sphere arc, concave inward (like a bowl facing the Circle), thin shell mesh
- **Trigon:** 3 half-spheres meeting at apex (tetrahedral arrangement), or single bevelled triangular prism with rounded edges

All shapes get the same iridescent material as the pearl (with slightly different IOR per shape so they're distinguishable but coherent).

---

## Experiment tiers (Sunday + Tue-Fri sprint)

### Tier 0 — Sanity check (10 min Sunday AM, first thing)

**Exp 0.1 — Open existing .ply in Blender, confirm asset is sound.**
- File: `track2-deterministic/morph_outputs/exp4_hybrid_pearl_container_model_2026-05-16.ply`
- Check: mesh is manifold, normals consistent, scale reasonable, primitives separable
- If broken: regenerate via `track2-deterministic/scripts/exp4_hybrid_pearl_container.py`
- Output: confirmation only; no render
- Blocks: everything below

### Tier 1 — Material + motion fix (Sunday AM, 1–2 hr)

**Exp 1.1 — Pearl material pass.** Re-render Exp 4 geometry with proper iridescent pearl material per spec above. Same motion as original (just better material). Output: 1 video, 18 sec, 1080p test.
- Validates: oyster-pearl quality, lighting, material
- If good: scale to 5120×1600 final render later
- Effort: 30–60 min material tuning

**Exp 1.2 — Pearl still, shapes orbit.** Same geometry, but pearl static, shapes do their own rotation inside. Camera also static.
- Validates: the architectural inversion (Austin's Pearl Vision rendering literally)
- Effort: 30 min (re-rig Blender scene)

**Exp 1.3 — Slow + eased motion.** Same as 1.2 but at 24fps with ease-in-out, 36-sec rotation, breath cycle.
- Validates: motion quality fix for the flicker / too-fast complaint
- Effort: 15 min (keyframe + curve tweak)

### Tier 2 — Compositional grammar (Sunday PM, 2–3 hr)

**Exp 2.1 — Operator's 5-element radial: C + 2Cr + 2Tr.** Circle at center, 2 Crescents cupping it (mirror pair), 2 Trigons outside (mirror pair). Static composition first (single frame), then slow rotation animated.
- Validates: the operator's compositional vision; "two hands cupping" read
- Effort: 1 hr scene build + render

**Exp 2.2 — 3-element triangle.** C + Cr + Tr equidistant in equilateral triangle, slow rotation around pearl center.
- Validates: minimal viable Coast Salish triad composition
- Effort: 30 min

**Exp 2.3 — Concentric Russian-doll.** C inside Cr inside Tr inside larger Cr inside larger Tr (5 nested primitives).
- Validates: nested-grammar reading; depth perception inside pearl
- Effort: 45 min

**Exp 2.4 — Half-sphere geometry test.** Render Trigon as 3 half-spheres meeting at apex, Crescent as half-arc bowl, Circle as full sphere. Single static frame to confirm the geometry reads as intended before animating.
- Validates: half-sphere primitive design
- Effort: 30 min

### Tier 3 — Motion-relative dynamics (Tue-Fri sprint, 2–4 hr each)

**Exp 3.1 — Saturn-rings orbital.** Shapes orbit pearl center at different speeds (Circle slow center, Crescents medium, Trigons fast outer).
- Validates: differential motion creates depth illusion
- Effort: 1–2 hr

**Exp 3.2 — Heartbeat synchrony.** All shapes expand/contract together on shared breath cycle, gentle pulse.
- Validates: meditative rhythm; pearl "breathes" as one organism
- Effort: 1 hr

**Exp 3.3 — Procession through center.** Shapes pass through pearl center one at a time in sequence (Circle → Crescent → Trigon → Circle...), like a procession.
- Validates: narrative-time inside the pearl; teaching-sequence reading
- Effort: 1–2 hr

**Exp 3.4 — Camera-around-pearl.** Pearl + shapes all static; camera slowly arcs around the pearl, revealing different faces of the composition.
- Validates: viewer-as-witness positioning; pearl as object being beheld
- Effort: 30 min camera animation

**Exp 3.5 — Shape-becoming.** One shape morphs through another (e.g., Circle expands → becomes Crescent → contracts to Trigon → re-expands to Circle) — temporal version of the morph engine but in 3D.
- Validates: continuous-transformation reading; cyclical teaching
- Effort: 2–3 hr (geometry morph in Blender geometry nodes is non-trivial)

### Tier 4 — Style pass (Tue-Fri sprint, optional)

**Exp 4.1 — Thin Austin LoRA style pass over Blender render.** Take a Tier 1/2/3 output, run it through SD + Austin v2 LoRA at very low strength (0.10–0.15) just for atmospheric texture. Compare to raw Blender output.
- Validates: whether LoRA-as-style-finisher adds anything vs Blender alone
- Effort: 30 min (we have the pipeline)
- Risk: may add flicker back; if so, skip

### Tier 5 — Live performance (Tue-Fri sprint, only if Tier 1-3 land)

**Exp 5.1 — TouchDesigner real-time port.** Port the best Tier 1-3 Blender experiment to TouchDesigner Geometry COMP for real-time render at 5120×1600 → Resolume composition.
- Validates: live-performance viability for IMPACT show
- Effort: 2–4 hr (Pravin's domain — pair-build during sprint)

---

### Tier 6 — Open-ended exploration menu (NOT committed; feeding pool for future tiers)

> Captured from operator + Claude creative brainstorm 2026-05-16 late evening. These are ideation, not execution commitments. Sunday-AM-Darren reads, picks 1-3 that resonate enough to graduate into Tier 1-3 status. Most will stay parked.

#### 6.A — Topology and geometry play

- **6.A.1 Concentric-fold layered pearl** (operator's original): pearl as onion of teachings. Outer skin → inner skin folds into Trigons → Trigons surround inner sphere → inner sphere has Crescent meridians → Circle at center. Animation: pearl exhales = layers separate visibly; pearl inhales = layers collapse back to smooth sphere. "Shapes are the pearl's own anatomy at different depths."
- **6.A.2 Klein-bottle pearl**: non-orientable surface. Inside connects to outside without crossing. Symbol: non-duality / no-self.
- **6.A.3 Möbius Crescent**: Crescent twisted into a half-twist strip, one continuous edge. "Embrace that has no inside or outside."
- **6.A.4 Voronoi shell tessellation**: pearl surface tiled with organic Voronoi cells, each cell is a tiny primitive composition. Self-similar / fractal at multiple zoom levels.
- **6.A.5 Phi-spiral interior**: golden ratio spiral of Crescents winding into Circle center, Fibonacci timing on which Crescent illuminates.
- **6.A.6 Origami / lotus pearl**: pearl unfolds petal by petal, each petal reveals a primitive composition, refolds. Each blooming is a new teaching surfacing.

#### 6.B — Cosmology and symbolism (our own interpretation, NOT claiming Coast Salish meaning — Austin's territory)

- **6.B.1 Pearl as cosmos**: Circle = sun, Crescents = moons in their phases (literally cycling through phases as motion), Trigons = star-points / galactic spirals. Connects to Indigenous astronomy traditions and bioregional scope.
- **6.B.2 Pearl as seed / womb / egg**: shapes are genetic code of a being unfolding inside. Time-lapse gestation. Pearl grows; at moments shapes "complete" and a new cycle starts.
- **6.B.3 Three temporalities**: Crescent (waning, past), Circle (full, present), Trigon (rising, future). Time as composition.
- **6.B.4 Three relations**: Circle (being itself), Crescent (being-with-other), Trigon (being-toward-purpose). Buber-meets-pearl.
- **6.B.5 Land / Sea / Sky**: Circle = earth/stone/center, Crescent = wave/concave/water, Trigon = mountain or upward-light-ray. Bioregional pearl.

#### 6.C — Dynamics and rhythm

- **6.C.1 Polyrhythm**: Circle in 4/4, Crescent in 6/8, Trigon in 3/4. Visible chord, coherent at every measure but never repeating identically. Music made geometric. Pravin's Ableton + Max background = right pair for rhythm design.
- **6.C.2 Resonance ringing**: one shape "strikes" and others respond in harmonic ratios. Cymatics inside the pearl, visible standing waves.
- **6.C.3 Phase transition**: at sacred moments all shapes simultaneously change state (solid → liquid → gas → plasma) while their fundamental geometry persists. Pearl as alchemical vessel.
- **6.C.4 Procession**: shapes pass through center one at a time. Each at center = "teaching of this moment." Other two wait at periphery, witnessing.
- **6.C.5 Mirror exchange**: shapes pass through each other rather than around. Crescent passes through Circle and emerges as Circle; identity is borrowed and returned.

#### 6.D — Live-reactive (Tue-Fri sprint territory)

- **6.D.1 Audience breath driver**: pearl breathes at rate of room's collective breath (mic input averaged into long moving average). Slow induction of shared parasympathetic rhythm.
- **6.D.2 Bioregional data driver** **★ strongest for SSD thesis**: herring count → Circle size; tide phase → Crescent angle; salmon return → Trigon rotation. Pearl breathes to the Salish Sea's actual heartbeat. Wire to existing `scripts/bioregional_osc_bridge.py` (IWLS tide + Fraser river OSC feeds already validated).
- **6.D.3 Heartbeat sync**: visitor wears HRV sensor or webcam pulse detection; pearl pulses with them. One person at a time, intimate.

#### 6.E — Multi-pearl and meta-structures

- **6.E.1 Pearl cluster**: 3 pearls of different sizes, each contains all 3 shapes but one is dominant. They dance around each other. Triangulation.
- **6.E.2 Pearl chain**: string of pearls; awareness/light passes from pearl to pearl in sequence. Procession at meta-scale.
- **6.E.3 Pearl-in-pearl-in-pearl**: Russian-doll structural recursion. Zoom-in reveals new worlds; zoom-out reveals containment.

#### Tier 6 selection — what to graduate first (Claude's vote, operator decides)

After 2026-05-16 late-eve expansion (62 ideas total), top candidates by S+F-A ranking (see scoring system below):

1. **6.D.2 Bioregional data driver** (S5/F4/A2 = +7) — strongest symbolic claim for SSD's bioregional thesis; OSC bridge tooling already exists. Could be the show's signature moment.
2. **6.F.7 Tide cycle compression** (S5/F4/A2 = +7) — 18-sec pearl breathes one tidal cycle. Real bioregional time made visible.
3. **6.F.1 Bioluminescent pearl** (S5/F4/A2 = +7) — primitives fire/glow like jellyfish/neurons; SSD has bioluminescence in core motifs.
4. **6.F.12 Schooling-fish primitives** (S5/F3/A2 = +6) — Boids flocking; herring/salmon school resonance.
5. **6.F.30 Pearl rewards attention** (S5/F3/A2 = +6) — detail increases with viewer stillness; directly aligns with SSD's "stillness rewarded" principle (per CLAUDE.md).
6. **6.F.31 Pearl listens** (S5/F3/A2 = +6) — primitives respond to room sound; whisper makes them lean in.
7. **6.F.16 Pearl-as-sonic-instrument** (S5/F3/A2 = +6) — strikes produce real tones; visible chord made audible.
8. **6.F.17 Cymatic primitives** (S5/F3/A2 = +6) — Matt-driven; sound vibration shapes formations.
9. **6.F.18 Whale-song driver** (S5/F3/A2 = +6) — orca/humpback recordings shape primitive motion.
10. **6.F.27 Triptych within triptych** (S5/F4/A3 = +6) — 3 simultaneous angles; matches Hubble triptych spec.

**Pattern observed:** the highest-scoring ideas are bioregionally live-reactive (#1, #2, #9), stillness/attention-rewarding (#5, #6), and sound-coupled (#7, #8, #9). That's a real signal — SSD's strongest mode is when the audience is in dialogue with living systems through stillness and sound.

#### Ranking system (apply to any future addition)

Each idea gets three 1-5 scores:
- **S (Signal):** how strongly does this resonate with SSD's core themes — bioregional consciousness, three-eyed seeing, stillness rewarded, Indigenous worldview, living-systems dialogue. 5 = bullseye.
- **F (Feasibility):** can we actually execute this with our tools by May 27-28? 5 = trivially doable now, 1 = requires significant new tooling or research.
- **A (Austin sensitivity):** how much does this need Austin's input or blessing before any public surface? 5 = Austin's call entirely (e.g. anything touching specific cultural symbols), 1 = pure abstract / technical / universal phenomena.

**Priority = S + F - A.** Higher = graduate faster. Tied ideas: prefer **lower A** (lower Austin lift — less culturally heavy, safer for solo experimentation) for Sunday solo execution; prefer higher S for sprint pair-work with Pravin when he and/or Austin are present. Bug fixed 2026-05-17 AM after peer review caught the inversion.

---

#### 6.F — Extended brainstorm menu (2026-05-16 late eve expansion)

All scored with S/F/A. Sorted within each sub-theme by priority.

##### Material / texture (the pearl itself as story)

- **6.F.1 Bioluminescent pearl** — primitives glow when they "fire" like neurons or jellyfish; dark pearl punctuated by light pulses. SSD bioluminescence motif. **S5/F4/A2 = +7**
- **6.F.2 Pearl with surface caustics** — interior light projects water-reflected patterns on outer surface; pearl wears the dance inside. S4/F3/A2 = +5
- **6.F.3 Pearl-as-bubble** — soap-film iridescence, fragility implied; pearl could pop. S3/F4/A2 = +5
- **6.F.4 Pearl with rain on it** — water drops refract what's seen inside; weather as participant. S4/F2/A2 = +4
- **6.F.5 Pearl that ages** — surface patina deepens over the 18 sec; teaching matures. S3/F4/A3 = +4
- **6.F.6 Pearl as ice that thaws** — opens frozen, melts to reveal interior; winter teaching. S4/F3/A3 = +4

##### Time / narrative arcs

- **6.F.7 Tide cycle compression** — 18-sec pearl breathes one full tidal cycle. **S5/F4/A2 = +7**
- **6.F.8 Lunar phases** — Crescents cycle through 28-day moon phases in 18 sec; each Crescent is a different night. S4/F4/A2 = +6
- **6.F.9 Seasons** — pearl color/temperature: spring (chartreuse) → summer (gold) → fall (amber) → winter (silver-blue). S4/F4/A2 = +6
- **6.F.10 Day cycle** — dawn → noon → dusk → night light qualities. S3/F4/A2 = +5
- **6.F.11 Memory cascade** — shapes leave luminous trails (long-exposure), composition writes itself in light. S4/F3/A1 = +6
- **6.F.11b Time reversal** — pearl runs forward, then reverses, "unlearning"; impermanence meditation. S3/F4/A2 = +5

##### Movement type

- **6.F.12 Schooling-fish primitives** — Boids flocking algorithm on shapes; herring/salmon school resonance. **S5/F3/A2 = +6**
- **6.F.13 Brownian/thermal jitter** — primitives subtly tremble as if molecular; aliveness at small scales. S3/F4/A1 = +6
- **6.F.14 Magnetic field motion** — primitives orbit along invisible field lines. S3/F3/A1 = +5
- **6.F.14b Gravitational dance** — primitives attract/repel each other with continuous gravity sim. S3/F3/A1 = +5
- **6.F.15 Liquid pearl** — interior is fluid sim (zero-g water), primitives float. S3/F3/A2 = +4
- **6.F.15b Smoke pearl** — volumetric smoke interior, primitives are denser regions. S3/F2/A2 = +3

##### Sound / synesthesia (Pravin / Matt territory)

- **6.F.16 Pearl-as-sonic-instrument** — each primitive strike = real tone; Circle fundamental, Crescent third, Trigon fifth. Drone music. **S5/F3/A2 = +6**
- **6.F.17 Cymatic primitives** — shapes form according to sound vibration patterns; literal music-to-form. **S5/F3/A2 = +6**
- **6.F.18 Whale-song driver** — actual orca J/K/L pod or humpback recordings shape primitive motion. **S5/F3/A2 = +6**

##### Inversion / negative space

- **6.F.19 Hollow pearl** — shapes are voids cut from solid space; pearl is empty room, shapes are the negative. Buddhist emptiness. S4/F4/A2 = +6
- **6.F.20 Anti-pearl** — pearl invisible; only shapes visible, pearl implied by their constraint. S4/F4/A2 = +6
- **6.F.21 Mirror pearl** — interior reflects viewer's space back via camera-as-mirror. Self-witnessing. S4/F3/A2 = +5
- **6.F.22 Sphere eversion** — pearl turns inside-out continuously (Smale-Boy topology); mathematically gorgeous. S3/F2/A1 = +4

##### Composition / scale / camera

- **6.F.23 Macro pearl** — POV so close only one primitive visible at a time; pearl is vast. S3/F4/A2 = +5
- **6.F.24 Micro pearl** — pearl is tiny speck in vast void; meditation on scale. S3/F4/A2 = +5
- **6.F.25 Scale-shifting** — 18-sec zoom from far → inside pearl looking out. Cinematic. S4/F3/A2 = +5
- **6.F.26 Infinite recursion** — pearl reflected in 6 mirrors → Indra's Net. S4/F3/A2 = +5
- **6.F.27 Triptych within triptych** — 3 simultaneous angles of same composition; matches Hubble triptych spec. **S5/F4/A3 = +6**

##### Cross-species / bioregional embodiment

- **6.F.28 Pearl as kelp forest** — primitives as holdfast/stipe/blade anatomy. S5/F3/A3 = +5
- **6.F.29 Pearl as herring school** — primitives as fish-flock formations. S5/F3/A3 = +5
- **6.F.29b Pearl as salmon life cycle** — primitives morph egg→fry→smolt→adult→spawn over 18 sec. S5/F3/A3 = +5
- **6.F.29c Pearl as cedar growth rings** — primitives as ring/branch/needle anatomy. S5/F3/A3 = +5
- **6.F.29d Pearl as orca pod** — primitives as J/K/L pod members. S5/F3/A3 = +5
- **6.F.29e Pearl as octopus / T'lep teaching** — primitives as arms/suckers/beak; touches T'lep cultural framing already in CLAUDE.md. S5/F3/A4 = +4
- **6.F.29f Pearl as moon jellyfish** — bell/oral-arms/tentacles. S4/F3/A2 = +5

##### Philosophical / experiential (stillness-rewarding — direct SSD principle fit)

- **6.F.30 Pearl rewards attention** — detail increases with viewer stillness; if room moves, pearl simplifies. Shapes audience posture. **S5/F3/A2 = +6**
- **6.F.31 Pearl listens** — primitives respond to room sound; whisper makes them lean in. **S5/F3/A2 = +6**
- **6.F.32 Pearl as silence** — no music, just visual rhythm; intentionally creates room quiet. Bold. S4/F5/A3 = +6
- **6.F.33 Pearl as witness** — primitives slowly turn to face the longest-still observer. Returns gaze. S5/F2/A3 = +4

##### Indigenous / cultural (high A — our exploration, needs Austin scrutiny)

> All flagged as OUR creative exploration; would require Austin's review before any public surface; some may be inappropriate even internally — operator/Austin judgment call.

- **6.F.34 Pearl as longhouse interior** — primitives as architectural elements. S5/F3/A5 = +3
- **6.F.35 Pearl as drum** — primitives as patterns on drumhead; beats as pulses. S5/F3/A5 = +3
- **6.F.36 Pearl as canoe** — primitives as paddles/passengers. S4/F3/A5 = +2
- **6.F.37 Pearl as button blanket** — primitives as buttons in formline pattern. S4/F3/A5 = +2
- **6.F.38 Pearl as woven cedar** — primitives as warp/weft/binding. S4/F3/A5 = +2

##### Scientific phenomenon (abstract but resonant)

- **6.F.39 Pearl as cell** — primitives as nucleus/mitochondria/organelles. S4/F3/A1 = +6
- **6.F.40 Pearl as atom** — primitives as orbital electrons; shells = onion layers. S3/F4/A1 = +6
- **6.F.41 Pearl as galaxy** — primitives as arms/core/halo. S4/F3/A1 = +6
- **6.F.42 Pearl as neural net** — primitives fire like neurons, connections visible. S3/F3/A1 = +5
- **6.F.43 Pearl as standing wave** — primitives are nodes/antinodes of wave function. S3/F3/A1 = +5

##### Mathematical / formal (pure geometry)

- **6.F.44 L-system generative** — primitives grow algorithmically via Lindenmayer system. Botanical grammar. S4/F3/A1 = +6
- **6.F.45 Subdivision animation** — pearl alternates discrete polyhedron ↔ smooth sphere over breath cycle; discrete↔continuous teaching. S3/F4/A1 = +6
- **6.F.46 Strange attractor orbits** — primitives follow Lorenz/Rössler chaotic-but-bounded paths. S3/F3/A1 = +5
- **6.F.47 Hyperbolic pearl** — non-Euclidean interior bigger than exterior (Escher-like). S3/F2/A1 = +4
- **6.F.48 Toroidal pearl** — donut topology, primitives orbit through the hole. Flow teaching. S3/F2/A1 = +4

##### Inter-pearl relationships (next-level structural)

- **6.F.49 Two pearls in dialogue** — shapes pass between them along invisible thread; conversation visualized. S4/F2/A2 = +4
- **6.F.50 Pearl mitosis** — pearl divides into two, primitives redistribute by symmetry. S3/F2/A2 = +3
- **6.F.51 Pearl fusion** — two pearls merge, primitives reorganize. S3/F2/A2 = +3
- **6.F.52 Pearl family** — small pearls bud from main pearl, each a child-teaching. S3/F2/A3 = +2

---

---

## Symbolism framing discipline

For ANY symbolic interpretation we layer onto the primitives (cosmos, time, relations, land/sea/sky, etc.), the discipline is:

- **We frame it as OUR interpretation, not Coast Salish meaning** — Austin owns the Coast Salish symbolic register; we explore our own. If a meaning we propose happens to align with what he teaches, great; if it diverges, ours is clearly labeled as ours.
- **Wall card / public framing copy stays minimal on symbolism** until Austin reviews. Internal experimentation can be rich in our own meanings; what reaches the audience needs Austin's voice.
- **The Coast Salish primitive vocabulary itself** (Circle, Crescent, Trigon) IS shared cultural lineage. Using the primitives is OK; assigning fixed Coast Salish meanings to them is Austin's call.

---

## Tonight's vision capture vs Sunday execution

This doc is **the spec**, not the execution. Sunday-AM-Darren opens this, picks Tier 0 + Tier 1 first (sanity check + material + motion fix), produces 3 output videos, judges quality, then either proceeds to Tier 2 or iterates on Tier 1.

**Critical sequencing:** Do not skip Tier 0. Do not jump to Tier 3 before Tier 1 lands. Tier 4 only after Tier 1-3 have something worth styling. Tier 5 only after Tier 1-3 have something worth porting.

---

## Discipline (carried from sunday-internal-experiment-lane doc)

- All outputs to `track2-deterministic/morph_outputs_INTERNAL/`
- Each output gets a `provenance.csv` row (date, exp_id, tools_used, cultural_load=internal-experiment, sharing_status=internal-only, notes)
- Each output gets a `.consent.txt` sidecar with INTERNAL header
- Per-output Austin OK required before any external share
- The Coast Salish primitive vocabulary we're using IS Austin's cultural lineage — even though these are our compositions, the grammar is borrowed. Treat with the same trust floor.

---

## What we are NOT doing in this spec

- Not retraining any model
- Not re-rendering anything in SD as a primary engine
- Not claiming any of these experiments as authorized meaning until Austin OKs
- Not shipping any of this to Pravin / John / Dan externally without per-output review
- Not committing to all 13 experiments — this is a menu, Sunday-AM-Darren prunes

---

## References

- Operator + Claude creative exploration session 2026-05-16 late evening
- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/project_austin_pearl_vision.md` — Austin's pearl framing
- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/reference_coast_salish_formline_primitives.md` — Circle/Crescent/Trigon as Coast Salish primitives
- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/feedback_austin_consent_trust_floor.md` — per-output OK is the floor
- `docs/space-center/sunday-internal-experiment-lane-2026-05-17.md` — companion experiment policy (cross-creature pairs); same discipline
- `track2-deterministic/morph_outputs/exp4_hybrid_pearl_container_model_2026-05-16.ply` — existing 3D mesh, starting point for Tier 1
- `track2-deterministic/scripts/exp4_hybrid_pearl_container.py` — generator if mesh needs regen
- `track2-deterministic/scripts/exp5_carved_pearl_hull.py` — alternative 3D approach
