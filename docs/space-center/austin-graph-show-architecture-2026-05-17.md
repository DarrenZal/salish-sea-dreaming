# Austin Graph + Show Architecture — 2026-05-17

`[INTERNAL — DO NOT SHARE]`

> Captured 2026-05-16 late evening from operator + Claude creative brainstorm. Documents a major architectural reframe: **the show is a multi-minute live traversal of a graph of Austin's pieces**, embedded in a larger living graph that already exists across the project. Same discipline as the rest of the experiment work: internal-only outputs, per-output Austin OK before any public surface, see `docs/space-center/sunday-internal-experiment-lane-2026-05-17.md` and `docs/space-center/pearl-interior-experiment-spec-2026-05-17.md` for companion policy and pearl-interior work.

---

## The graph through-line — why this is the project's actual architecture

We've been working in this register all along without naming it:

| Existing project graph | What it is | Status |
|---|---|---|
| **salishseadreaming.art exhibit graph** | Visitor dreams visualized as a 3D living point-cloud / graph (April show web app + the `salish_dreamworld` TD scene fetching `/dreams/3d` with music-driven unity → cluster → individual bezier breathing) | LIVE, shipped April |
| **Indigenomics AI knowledge graph** | Concepts/contributors/frameworks for Carol Anne's work; currently rendered on the web app; **being rendered as dome video for IMPACT** (first draft exists, queued for Dan to integrate) | First draft delivered |
| **Bioregional knowledge graph** | Herring → Salmon → Orca → Kelp → Cedar trophic + cultural connections (the Five Threads); concept-level connections from the herring reports + Octo knowledge garden | Conceptually mapped; partially rendered |
| **Austin's pieces graph** (this doc) | Austin's 18 pieces as nodes, morphs as edges; multi-resolution (pieces + decomposed atoms) | **NEW — this spec** |

The IMPACT show makes the graph visible and traversable. **Graphs aren't a stylistic choice we're imposing — they're the architecture the project has been building toward.**

---

## Vision — the show as graph traversal

Not "18-sec pearl loop on repeat." Not "Resolume sequence of pre-rendered clips." The show is a **multi-minute live traversal of the Austin graph**, with the graph itself visible as ambient structure throughout.

- **All 18 Austin pieces laid out in 3D space** as nodes (sphere-shell, constellation, tide-pool, forest, or hanging — see "Graph visualization treatments" below).
- **Edges between pieces visible as luminous threads**, weighted/colored by edge type.
- **At any moment the show is "at" a position** — either on a node (a piece is the primary visual) or on an edge (a morph is playing as the transition).
- **Camera moves between long-shot ("here's the graph") and close-up ("we're inside this edge").**
- **Visited nodes stay lit** — the graph illuminates over the show's duration. Final state is the fully-walked graph.
- **Different traversals = different shows.** Wed and Thu nights don't have to follow the same path; same content, different choreography.
- **The pearl-interior piece (sister spec)** becomes ONE NODE in this larger graph — probably the "essence" or "container" node where the three primitive teachings live.

---

## Nodes — multi-resolution

The graph is hierarchical. Three levels of node:

### Level 1 — Pieces (macro-nodes)

Austin's 18 files as currently registered:
- Animal_Insect_Bee.pdf
- Animal_Insect_Butterfly_Transparent.png
- Animal_Bear_Background.pdf
- Animal_Deer_Background.pdf
- Animal_Wolf_Background.pdf
- Animal_Wolf_Spindle_Whorl.svg
- Animal_Bird_Raven_Background.pdf (or similar — verify exact filename)
- Animal_Bird_Raven_Transparent.png
- Animal_Bird_Raven_Sun.svg
- Animal_Water_Octopus_Transparent.png
- Animal_Water_Orca_Transparent.png
- Animal_Salmon_Spawn_Eggs.svg
- Nature_Cosmic_Sun.svg
- Supernatural_Bird_Thunderbird_Background.pdf
- Supernatural_Human_TheCreator_Background.svg
- (plus ~3 more — verify against `austin-v2-ingest/approved/`)

The **naming convention is itself a taxonomy** — domain (Animal / Nature / Supernatural) → subdomain (Bird / Water / Insect / etc.) → specific piece. This pre-existing structure gives us a free hierarchical clustering for free.

### Level 2 — Atoms (micro-nodes, via decomposition)

Each piece decomposes into formline atoms. A typical Coast Salish composition contains:
- **Outlines (formlines)** — thick contour lines defining shapes
- **Primitives** — crescents, trigons, ovoids (the Coast Salish primitives per `reference_coast_salish_formline_primitives.md`)
- **Eyes / focal-ovals** — central eye-shapes, often heart-of-piece
- **Wings / feathers / fins / fur / body-parts** — figural elements
- **Negative space cutouts** — engineered empty areas
- **Color fields** — palette regions
- **Symmetry axes** — bilateral, rotational, radial

18 pieces × 5-15 atoms each = 100-200+ atoms. **This becomes an Austin-vocabulary atlas.**

### Level 3 — Meta-nodes (clusters / hubs)

Emergent from the graph structure:
- **Communities** — natural clusters (Animal-cluster, Supernatural-cluster, Background-cluster, Transparent-cluster, palette-clusters)
- **Hubs** — pieces with many edges (high centrality); become recurring anchors in show
- **Bridges** — edges connecting otherwise-disconnected subgraphs; "powerful" morphs
- **Spanning tree** — minimal structure connecting all nodes; the "trunk" of the graph

---

## Edge typing — different KINDS of morphs

Not all edges are equal. Each piece-pair can connect along multiple dimensions simultaneously:

| Edge type | What it captures | Examples in Austin's set |
|---|---|---|
| **Form similarity** | shared geometric grammar, viewBox, composition logic | Raven_Sun.svg ↔ Cosmic_Sun.svg (matching 108×108, both radial-icon) |
| **Subject domain** | same naming-taxonomy bucket | Bear_Background.pdf ↔ Deer_Background.pdf |
| **Cross-domain** | edges bridging domains (the *interesting* ones) | Raven (air) ↔ Octopus (sea); Wolf (animal) ↔ Thunderbird (supernatural); Bee (insect) ↔ Butterfly (transformation) |
| **Palette / color** | shared chromatic family | Nam̓gis red/yellow group vs Sḵwx̱wú7mesh palette |
| **Figure / ground** | Transparent (cutout) ↔ Background (scene); a kind of zoom-in/zoom-out edge | Wolf_Spindle_Whorl.svg ↔ Wolf_Background.pdf (icon ↔ context) |
| **Cultural-load weight** | how much trust/blessing this edge needs from Austin | Wolf↔Thunderbird-Background = heavy (Austin's lineage); Bee↔Butterfly = light |
| **Format edge** | technical feasibility class | SVG↔SVG (engine works now); PDF↔PDF (Inkscape decomp first); PNG↔* (raster adapter — not yet built) |
| **Narrative edge** | what does this transition *say*? | Salmon-spawn ↔ Cosmic-sun (sun energy descending as roe) |
| **Bioregional edge** | piece "lights up" when corresponding bioregional data fires | Orca piece ↔ J-pod sighting; Salmon piece ↔ Fraser river flow |
| **Decomposition edge** | piece → its constituent atoms (Level 1 → Level 2) | Wolf_Spindle_Whorl.svg → its wolf-eye + trigon-tongue + crescent-cheek atoms |
| **Recomposition edge** ⚠️ | atoms → new composition (high cultural load) | NOT to be used without Austin co-authorship |
| **Identity / translation edge** | piece → itself under transformation (mirror, rotate, scale, color-shift, etc.) | see "Translation operations" below |

A given piece-pair can have multiple edges of different types active simultaneously. Render each edge type as different color / thickness / material in the visualization layer.

---

## Translation operations — additional soft edges

Beyond piece-to-piece morphs, each piece can have edges to its own transformations:

- **Mirror reflection** — flip on bilateral axis; piece sees itself reflected
- **Rotation** — slowly rotate; treat 2D as 3D, see from different angles
- **Scale shift** — zoom in to detail, zoom out to whole; can be animated as breathing
- **Color shift** — same piece, different palette; teaches what color does
- **Form ↔ ground inversion** — flip positive/negative; what was empty becomes filled
- **Time stretch** — slow-down or speed-up; what does 5 minutes inside a piece reveal?
- **Geometry projection** — project 2D piece onto 3D form (sphere, cylinder, pearl) and watch how it wraps
- **Tessellation** — repeat the piece across a surface; pattern emerges from singleton
- **Caustics** — light passing through the piece projects shifted forms onto another surface

These are EDGES too. A piece connects to its mirror, its rotated version, its color-shifted version — each is a soft transformation that can be a graph traversal step.

---

## Decomposition + recombination discipline (cultural-load tiers)

Decomposing Austin's pieces and using the atoms is genuinely creative territory. Per the project's "experiment broadly, share narrowly, ship only with Austin's explicit OK" policy, internal experimentation is unrestricted — what's gated is what we put in front of audiences or claim authorship of. Tiers:

### Tier D-1 — Decompose for analysis (LOW load, internal-OK)
- Show Austin the atom-level view as "look how we mapped your grammar"
- Frame: he's the expert, we're students learning his vocabulary
- Internal use unrestricted; great as a teaching artifact to share with Austin

### Tier D-2 — Decompose to highlight elements (MEDIUM load)
- Show a single atom (e.g., a specific Crescent) as a focal point, **with provenance** "from Austin's Salmon piece"
- Like a literary anthology pulling specific lines from one author
- Each highlighted atom keeps its attribution
- Internal-OK; public surface needs Austin per-output OK

### Tier D-3 — Atoms in ballet without recombination (MEDIUM load)
- Atoms float and arrange in space but never claim to be a new artwork
- They're material from Austin's work being shown in motion
- "Look at the elements" not "look at our new piece"
- Internal-OK; public surface needs Austin per-output OK

### Tier D-4 — Recombine atoms into NEW compositions (HIGH load for use, but exploration-OK)
- ✅ **Internal experimentation is allowed and encouraged** — that's how we learn the grammar
- Any recombination we think might be interesting for installation **or that Austin might simply find interesting**, we run by Austin
- Anything that goes to audience needs Austin's explicit per-output OK
- AI-assisted recombination is fine for exploration; not fine to ship as authored
- Keep provenance always: every atom in any recombination retains its piece-of-origin label internally so we can trace what we did

**Default discipline:** experiment freely in D-1 through D-4 internally; default-pause for any audience-facing or sponsor-facing use until Austin sees and OKs the specific output.

---

## Atomic experiment menu — ranked, parallelizable for Sunday + Monday

Same ranking system as pearl spec: **S (Signal 1-5)** + **F (Feasibility 1-5)** – **A (Austin sensitivity 1-5)** = priority. Higher = build sooner.

### A. Decomposition experiments (the foundation)

These produce atoms that enable everything else. Mostly parallelizable; mostly desk work.

| ID | Experiment | S/F/A | Priority | Tools | Parallel? |
|---|---|---|---|---|---|
| **A.1** | Manual atomic decomposition of all 18 Austin pieces in Inkscape — split each piece into 5-15 named atoms; produce per-piece atom catalog with provenance | 3/5/2 | **+6** | Inkscape, hand work | Single-stream (operator) — start Sunday AM |
| **A.2** | Automated path-segmentation script — Python + svgpathtools split SVG pieces into connected-component paths; less accurate but fast | 3/3/2 | +4 | Python, svgpathtools | Background — runs while A.1 happens |
| **A.3** | Color-region segmentation — extract each fill-color region as a separate atom (PIL/scikit-image) | 3/4/2 | +5 | Python, PIL | Parallel with A.1, A.2 |
| **A.4** | Symmetry-axis detection — find bilateral / rotational symmetry axes in each piece; decompose into reflective halves | 4/3/2 | +5 | Python, computational geometry | Parallel; depends on having vectorized pieces |
| **A.5** | **Atom catalog visualization (atomic atlas)** — HTML/grid view showing all atoms organized by piece-of-origin, formline-type, color, scale; the catalog IS itself a teaching artifact and a beautiful object | 4/4/2 | **+6** | HTML + Pillow contact-sheet | Depends on A.1; do Sunday PM after A.1 done |
| **A.6** | Hand-traced formline-type labeling — for each atom in catalog, tag with formline grammar class (primary form / secondary U-form / tertiary inner-element) | 4/4/2 | +6 | Manual labeling in catalog | Sunday PM/Monday |

### B. Recombination experiments (now unlocked — internal exploration)

All outputs to `track2-deterministic/morph_outputs_INTERNAL/` with provenance CSV row. Anything we want Austin to see (curious-style or use-style) gets flagged.

| ID | Experiment | S/F/A | Priority | Parallel? |
|---|---|---|---|---|
| **B.1** | **Atom genealogy visualization** — recombinations always show provenance threads back to source pieces (visible silver lines connecting atom to its origin piece). Foundational discipline that makes recombination culturally honest | 5/4/2 | **+7** | Foundational; build first |
| **B.2** | **Atom morphing through 3 Coast Salish primitives** — Crescent atom → Trigon atom → Circle atom in continuous cycle. Teaches the three primitives by direct demonstration | 5/4/2 | **+7** | Uses existing morph engine; Sunday PM |
| **B.3** | **Family album** — atoms briefly assemble back into their original Austin piece, hold for 2-3 sec, then disperse and re-form a different piece's composition. Meditation on origin + multiplicity. Provenance preserved | 4/4/2 | **+6** | Depends on A.1; Sunday PM/Monday |
| **B.4** | **Constellation of atoms** — all 100-200 atoms arranged in 3D space as a constellation; viewer flies through; clusters by formline-class are visible. Sister to the constellation graph viz | 5/3/2 | **+6** | Three.js or TD; Sunday PM |
| **B.5** | **Atomic procession** — single atom moves across screen; others join one at a time; formation slowly builds to a complete original piece OR to a new composition. Slow ceremonial pacing | 4/4/2 | +6 | Sunday PM/Monday |
| **B.6** | **Atom-as-instrument** — each atom triggers a tone when activated (Pravin/Matt territory); recombinations create musical phrases. Visible chord visible AND audible | 5/3/3 | +5 | Needs sound integration; sprint week pair-build |
| **B.7** | **Bioregional-driven recombination** — herring count → number of small atoms; salmon run → 5 large atoms; tide phase → atom orientation. The pearl/graph breathes as the Salish Sea breathes | 5/3/4 | +4 | Uses bioregional_osc_bridge.py; live show use → Austin OK |
| **B.8** | **Atomic field theory** — atoms have "valences": Circle attracts Crescent, Crescent attracts Trigon (per formline grammar rules); let physics arrange them; they emerge into formline-correct compositions | 5/2/3 | +4 | Research project — encode formline rules as physics; ambitious but elegant |
| **B.9** | **Atomic crystallization** — atoms drift in random space → "temperature" drops → snap into formation. Phase transition meditation | 4/3/2 | +5 | Sunday PM/Monday |
| **B.10** | **Cross-fertilization chimera** — combine atoms from different pieces (Wolf eye + Salmon body + Octopus tendrils). Internal exploration only; share curious-style with Austin if interesting | 3/4/4 | +3 | Sunday PM; results stay internal until Austin sees |
| **B.11** | **Visitor-driven recombination** — audience voice or gesture → atoms rearrange in response. Audience participation in cultural learning | 5/2/4 | +3 | Needs interaction infrastructure; sprint week if Tier 1-2 land first |
| **B.12** | **Atom orchestra** — atoms move on choreographed paths creating temporal compositions; each performance is a "piece" composed by motion in time, not space | 4/3/3 | +4 | Choreography work; Monday/sprint |
| **B.13** | **Random shuffle baseline** — randomly arrange atoms; control experiment to see whether constraint-based methods (B.8) actually produce something better than chance | 2/5/3 | +4 | Trivial; Sunday quick test |
| **B.14** | **Genetic-algorithm composition** — evolve compositions toward "interesting" via fitness function (symmetry? balance? formline-rule compliance?). Generative-art classic adapted to Austin's atoms | 3/3/3 | +3 | Research project; sprint week if time |

### C. Atom-level translation operations

Each atom can be transformed (mirror, rotate, scale, invert, etc.) — these are soft edges in the graph.

| ID | Experiment | S/F/A | Priority |
|---|---|---|---|
| **C.1** | **Atom positive ↔ negative inversion** — each atom morphs into its negative-space twin. Buddhist emptiness teaching + Coast Salish positive/negative pedagogy (Austin's grammar already plays here) | 4/4/2 | **+6** |
| **C.2** | Atom at multiple scales simultaneously — same atom at 0.5x / 1x / 2x / 4x rendered side by side; meditation on scale | 3/5/2 | +6 |
| **C.3** | Atom mirroring — atom and its bilateral reflection dance around symmetry axis | 3/5/2 | +6 |
| **C.4** | Atom 360° rotation — slow contemplative full rotation of a single atom; viewer sees its 2D structure as if it were 3D | 3/5/2 | +6 |
| **C.5** | Atom fragmentation/reassembly — atom shatters into smaller fragments, reassembles. Death/rebirth meditation | 3/3/2 | +4 |
| **C.6** | Atom dissolving/coalescing — atom slowly dissolves into noise texture, then re-coalesces. Form/formless boundary | 3/4/2 | +5 |
| **C.7** | Atom-microscope — extreme zoom on a single atom showing its sub-structure (curves, line weights, color gradients); ultra-still | 4/4/2 | +6 |

### Top-10 to build first (sorted by priority across A + B + C)

| Rank | Experiment | Priority | Stream |
|---|---|---|---|
| 1 | **B.1 Atom genealogy visualization** | +7 | Foundation — build first |
| 2 | **B.2 Atom morphing through 3 Coast Salish primitives** | +7 | Pearl spec already overlaps; uses existing engine |
| 3 | **A.1 Manual atomic decomposition** | +6 | Sunday AM operator hands |
| 4 | **A.5 Atom catalog visualization** | +6 | Sunday PM after A.1 |
| 5 | **A.6 Formline-type labeling** | +6 | Sunday PM/Monday after A.5 |
| 6 | **B.3 Family album** | +6 | Sunday PM/Monday — beautiful + culturally honest |
| 7 | **B.4 Constellation of atoms** | +6 | Sunday PM (Three.js or TD prototype) |
| 8 | **B.5 Atomic procession** | +6 | Sunday PM/Monday |
| 9 | **C.1 Positive/negative inversion** | +6 | Sunday quick experiment |
| 10 | **C.7 Atom-microscope** | +6 | Quick stillness experiment |

Many of these are **independent and parallelizable** — see execution plan below.

---

## Sunday + Monday parallel execution plan

Realistic operator availability: Sun AM = Dance Temple + MemEx call (low operator hands), Sun PM = Pravin check-in + work, Mon = full day at home before Tue travel. Three concurrent streams possible:

### Stream A — Operator hands-on (single-threaded)

**Sun AM (limited):**
- MemEx Victoria call (11 AM – 6 PM window; phone-confirm hours)
- If MemEx open → Victoria pickup run
- Otherwise: read this spec + pearl spec + decide morning sketch priorities

**Sun PM (full):**
- A.1 manual Inkscape decomposition of 5-6 Austin pieces (start with SVG pieces — easier)
- Pearl spec Tier 0 sanity check (open existing .ply in Blender)
- Pearl spec Tier 1.1 pearl material pass (start material tuning)
- Pravin check-in: discuss this graph architecture spec; get his read

**Mon:**
- Finish A.1 (remaining pieces, including PDF decomp via Inkscape Trace Bitmap)
- A.5 atom catalog visualization (HTML grid + Pillow contact sheet)
- A.6 formline-type labeling (annotate catalog)
- B.2 atom morphing through 3 primitives (uses existing morph engine — fast)
- B.3 family album prototype (animation work)
- C.1 positive/negative inversion experiment
- C.7 atom-microscope (very fast — single atom + zoom)
- Travel prep

### Stream B — Background / automated (parallel to A)

**Sunday-Monday:**
- A.2 automated path-segmentation script runs in background on all pieces
- A.3 color-region segmentation runs in background
- A.4 symmetry detection runs in background
- These output to a `_AUTOMATED/` subfolder of atoms; manual A.1 takes precedence where they conflict
- B.13 random shuffle baseline (trivial; quick) — produces baseline videos to compare B.8/B.14 against

### Stream C — Heavier creative experiments (any time CPU/GPU is free)

**Sunday PM or Monday:**
- B.1 atom genealogy visualization (foundational — pair with A.5)
- B.4 constellation of atoms (Three.js or TouchDesigner prototype)
- B.5 atomic procession (animation work)
- B.9 atomic crystallization (physics sim experiment)
- Pearl spec Tier 1.2 + 1.3 (pearl-still + slow motion fixes)
- Graph layout sketch (paper or Excalidraw — what does the Austin graph LOOK like?)

### Stream D — Wait-and-see (no operator hands required)

- Arshia GAN-axis reply (sent tonight)
- Pravin reflection reply (sent tonight)
- TELUS H6 kelp upscale (in_progress per session task #3)
- Pravin agent's NVIDIA Upscaler TOP claim — could be verified passively if anyone has time (verify it exists, check TD docs)

### Sprint-week pair-builds (Tue-Fri at Pravin's studio)

- B.6 atom-as-instrument (Matt + Pravin pair on sound integration)
- B.7 bioregional-driven recombination (wire to OSC bridge)
- B.8 atomic field theory (formline rules as physics — research-y, may not land in time)
- B.11 visitor-driven recombination (interaction infrastructure)
- B.12 atom orchestra (choreography pair)
- Graph visualization treatment selection + TD prototype (Pravin's native domain)
- Austin in-person check-ins (every day) — share atom catalog (A.5/A.6), get reactions, see what he wants to co-author from D-4 / recombination space

### Things to defer

- B.14 genetic algorithm composition (research project; sprint week IF time)
- D-4 recombinations destined for show use (defer to Austin pair-work in sprint week)
- Anything else not on this list — this is already 20+ experiments; we'll have plenty

---

## Path-selection modes — who chooses the traversal

Four candidate modes, increasing in complexity:

1. **Deterministic curated path** — Pravin + Darren pre-design the optimal walk; same every show; tight artistic control
2. **Random walk** — at each node, randomly pick an edge weighted by edge-strength; different show every time; surprise + emergence
3. **Bioregional-data-driven** — current live tide / salmon count / orca sighting biases which edges activate; **show responds to what's actually happening outside in the Salish Sea right now**
4. **Audience-influenced** — visitor presence detection / voice contributions / movement tilt the walk; quieter room → contemplative edges; vocal room → dramatic edges

**Recommendation: (3) + (4) combined.** Bioregional data + audience presence together choose the show. That's the project's deepest thesis made architectural — the Salish Sea and the audience together determine the journey. Deterministic (1) as fallback if live data is flaky.

---

## Graph visualization treatments — how the graph LOOKS

The graph layout deserves its own design treatment, not just as scaffolding. Options:

| Treatment | Aesthetic | Pros | Cons |
|---|---|---|---|
| **Sphere-shell** | All 18 pieces float on the surface of a giant translucent sphere; edges arc through the interior; viewer is inside looking out at constellations | Pearl-resonance; viewer-as-witness; works with the pearl-interior piece as the "essence sphere" at center | Risk of feeling like 3D star map cliché |
| **Constellation** ★ | Pieces are points of light against deep-blue Salish Sea night sky; edges are constellations drawn in faint silver between them | Indigenous astronomy resonance; stillness-rewarding (the longer you look, the more constellations resolve); ambient + foreground compatible | Need careful color/contrast tuning |
| **Tide-pool** ★ | Pieces float on a still water surface; edges are ripple-connections that propagate when an edge activates | Bioregional grounding; calm pool aesthetic invites stillness; ripples make edge activation visceral | Reflection complicates camera work |
| **Forest** | Pieces are leaves/blossoms on a slowly-growing tree; edges are branches; growth over show duration | Most ambitious — the show literally grows the tree; final state contains all of Austin's work | High render cost; Cedar-thread resonance |
| **Hanging** | Pieces are luminous medallions hanging from invisible threads in a 3D volume; gentle gravitational drift | Mobile-like; meditative; easy to render | May feel too "art gallery" |
| **Anatomy** | Pieces arrayed around a central form (body, longhouse, cedar, pearl); edges are pathways/meridians | Anchoring center provides composition; central form has its own meaning | Cultural-load of central form choice is high |
| **Force-directed** | Standard graph-viz layout; nodes repel, edges attract; settles into emergent shape | Self-organizing; reveals graph structure honestly | Risk of generic "tech demo" aesthetic |

**Top picks: Constellation + Tide-pool.** Both reward stillness, both embed bioregional themes, both leave room for the morph videos as foreground content while keeping the graph ambient. Could even alternate — show opens as constellation, evolves to tide-pool for water-piece moments, returns to constellation for sky/sun moments.

---

## Place-anchored Salish Sea substrate (peer-review addition, 2026-05-17 AM)

**This may be the strongest visualization treatment, but it's also more than a treatment — it's a deeper architectural substrate.** Surfaced by peer-agent review of the original visualization options.

### The observation peer raised

All the visualization treatments above (constellation, tide-pool, forest, sphere-shell, hanging, anatomy, force-directed) are **abstract-space architectures**. They borrow nature as metaphor but float in design space. That carries a real risk: "generic graph-viz made spiritual." Especially given the project's depth, an abstract treatment can read as decorative rather than load-bearing.

### The alternative — make the Salish Sea itself the traversal medium

Not a literal cartographic map UI (which would feel like a navigation tool, not art). A visual field built from:

- **Coastline geometry** — actual Salish Sea outlines (Strait of Juan de Fuca + Strait of Georgia + Puget Sound), abstracted/stylized but recognizable
- **Bathymetry** — depth contours and underwater terrain (lit from below; shapes the spatial topology)
- **Tide / current vectors** — live or pre-recorded current patterns; visible as gentle flow lines
- **Watershed mouths** — Fraser, Skagit, Cowichan, Nanaimo (with the major rivers feeding in)
- **Island and inlet geometry** — Salt Spring, the Gulf Islands, Howe Sound, Burrard Inlet, the San Juans
- **Light geography** — where the sun rises/sets through the show, where shadows fall

Austin's pieces and bioregional threads then sit **in relation to place** rather than in abstract layout:

- Salmon-edge morphs move through river-mouth / current-path geometries
- Orca-edge morphs follow water corridors (the actual J/K/L pod travel routes)
- Cedar / forest-edge morphs rise from watershed contours upland
- Sun / Raven-Sun edges occupy sky reflection over the same geography
- Octopus / Water-being edges live in deep-water bathymetric zones
- Wolf / land-being edges arrange along coastal forest interface
- Thunderbird-Background occupies sky over specific mountain peaks (the actual peaks visible from key sites)
- The Creator-Background as encompassing field across the whole substrate

### Why this is structurally stronger

1. **It IS the project thesis made architectural.** "The Salish Sea using technology to perceive itself" is not metaphorical here — the Salish Sea's actual geography is the canvas; everything sits in it.
2. **It removes the "abstract spiritual graph" risk.** Even subtle place-references ground the work in real territory.
3. **It composes with the bioregional data driver** — tide vectors aren't just decoration, they're the same live OSC feed already validated in `scripts/bioregional_osc_bridge.py`. Real tide moves through visible current paths.
4. **It composes with the existing dome rendering** — Dan/John's dome work is already place/sky-anchored; the Hubble Space installation could rhyme with that geometry.
5. **It honors xʷməθkʷəy̓əm / Sḵwx̱wú7mesh / səlilwətaɬ territory acknowledgment** structurally, not just in opening copy. Place visibility makes territory legible.
6. **Visitor dreams subgraph from April show already had position semantics** — visitor contributions could anchor to where the visitor said they were from, or to a Salish Sea coordinate they choose.

### Why it's a substrate, not just a layout option (refined per peer 2026-05-17 AM)

Constellation, tide-pool, etc. are visual STATES — how the graph appears at any moment. Place-anchored is different: it's the underlying **coordinate system** that those visual states sit on top of. Position has meaning. Distance has meaning. Direction has meaning (current direction, prevailing wind, salmon-run upstream).

**This is a fork in the coordinate system, not a fork in the whole show aesthetic.** Peer-review refinement: we can still BE in constellation mode, tide-pool mode, pearl-interior mode, or map-field mode at any moment, while the underlying substrate is place-anchored throughout. The visualization treatments become VIEWS of the same substrate, not competing alternatives. The substrate can also be hidden vs visible — sometimes ambient coastline glow under a constellation field; sometimes explicit when narrative calls for it.

This is a deeper architectural commitment than choosing a layout, but it's NOT a commitment to a single aesthetic. If we adopt it, other things follow:
- Path-selection modes get a fifth option: **(5) place-walking** — traverse the graph along actual geographic routes (J-pod's morning travel, salmon's natal-stream return, the dawn light's path across the sea)
- Edge typing gets a new dimension: **geographic adjacency edges** (Austin pieces whose place-anchoring is physically near each other)
- The Indigenomics AI graph layer (per Dan's dome work) can co-locate
- The visitor-dreams layer gets a literal home (a visitor's dream pins to a coordinate)

### Ranking

**S5 / F3 / A2 = priority +6** as a visualization treatment. As an architectural substrate (deeper), it's effectively a fork in the project's path — either we commit to place-anchoring or we don't. Worth surfacing to Pravin in the 4pm check-in.

### Feasibility notes

- Coastline geometry: free, open-data (OpenStreetMap, NOAA shorelines). Could be vectorized for use in TouchDesigner / Blender / Three.js.
- Bathymetry: NOAA + CHS Canadian Hydrographic Service open data; we already use IWLS for tides.
- Tide vectors: same OSC bridge, just exposing more.
- Render: TouchDesigner native; could use NDI / Spout to Resolume composition.
- Sunday prototype: an HTML+canvas sketch showing just the coastline + a few Austin pieces anchored to plausible places would be a 60-90 min experiment to test whether the visual reads.

### Open question for Pravin

- Does this resonate, or does it pull the work toward "geographic visualization" in a way that doesn't fit the meditative / pearl / stillness aesthetic we've been developing?
- If yes: explicitly visible coordinate system, or ambient/hidden one? (Per refinement above, both are possible — the substrate doesn't dictate the surface aesthetic.)

---

## The pearl-bead-on-edges concept (operator-originated 2026-05-17 AM)

**This may be the most important visual idea in this whole spec.** Surfaced by Darren in dialogue.

### The concept

The graph isn't displayed as a static structure with morphs played in some other window. Instead, **the graph IS alive with moving beads (pearls)**, each one a morph-in-flight:

- Every node = an Austin piece, displayed as its own visual (image / texture / 3D form) at the node's position
- Every edge = a possible morph route between two pieces
- **Pearls (or beads) travel along edges** — small spherical entities, each carrying a real-time morph
- Where a pearl sits on an edge determines what it shows: at edge-start it looks exactly like the source piece, at edge-end it looks exactly like the destination piece, in between it shows the morph at that interpolated moment
- When a pearl reaches its destination node, it **performs a designed aesthetic dissolve into that node** — peer-review note: a video-textured lit sphere will NOT visually match a flat node thumbnail unless we either (a) render the node thumbnails as sphere-textured too, OR (b) treat docking as a deliberate crossfade with its own visual logic. Don't promise a "perfect literal match"; design the docking as its own moment.
- New pearls spawn from nodes and begin journeys; the graph is constantly flowing

### Why this is the unifying move

It solves a structural problem none of the other treatments solved cleanly: **how does the graph stay visually coherent while morphs happen?** Previous proposals had the graph as one thing and the morph clips as another — they coexisted but weren't a unified visual logic. Pearl-on-edges makes them ONE THING: **the morph IS the bead's journey across the edge**. The graph isn't background context; the graph is animate, and the animation IS the morphs.

It also recovers the pearl from earlier work — the pearl isn't replaced by the graph architecture. Instead, **the pearl becomes the visual carrier-form that journeys between pieces**, holding a continuous visual relationship between them as it travels. The pearl-interior spec's central concept (pearl as container) is preserved AND extended (now the pearl literally moves between forms). **Cultural-language caveat per peer review:** "teaching carried between forms" is internally useful framing but is interpretive and possibly culturally heavy; for any external surface or Austin/Carol-Anne-facing description, use neutral language like "visual relationship" or "morph carrier" until Austin blesses the teaching framing.

### Visual mechanics

- **Pearl appearance:** a small luminous sphere (iridescent, per the pearl-interior material spec) carrying a real-time-rendered or video-textured surface that morphs from source-piece to destination-piece based on edge position
- **Multiple simultaneous pearls:** several pearls can be in flight on different edges at once; some on the same edge at different positions (staggered starts) creates a procession effect
- **Pearl speed:** different pearls can travel at different speeds — contemplative slow ones, livelier quick ones; mix creates rhythmic counterpoint
- **Birth/death:** pearls spawn from nodes, journey, dock at destinations and merge. Empty graph (no flying pearls) would feel still and quiet — could be used as a punctuation
- **Pearl trails:** optional luminous fade-trail behind moving pearls; show recent activity in the graph
- **Pearl convergence:** when several pearls dock at the same node within a short window, the node briefly intensifies — visible moments of concentration

### Naming caveat (one minor pushback)

There's a potential name collision: we have a **pearl-interior piece** (the Circle + Crescent + Trigon container concept) AND we'd have **pearls** as the traveling beads. Either:
- Lean into it: the traveling beads ARE pearls. The pearl-interior piece is one specific pearl (the largest, the "essence-pearl") that all other pearls return to or emerge from
- Separate the names: traveling units = "beads," pearl-interior piece keeps "pearl" — clearer but loses the resonance

**Lean toward "lean into it" with controlled language** (peer-refined 2026-05-17 AM): use **"source pearl"** for the pearl-interior piece and **"traveling pearls"** for the beads moving along edges. Internally we can describe the source pearl as an "origin or reservoir node from which traveling pearls are spawned and to which they may return" — but do NOT claim it is "the cosmological center" to Pravin / Austin / Carol Anne. That's interpretive mythology we haven't earned. Safer framing for external conversation: "the pearl-interior piece becomes the origin/reservoir node, if that framing lands with Austin." The mechanic is strong without locking mythology prematurely.

### Technical implementation — and honest scope distinction (peer-review 2026-05-17 AM)

**This reduces CONCEPTUAL scope (collapses graph + morphs + pearl into one logic) but it does NOT reduce TECHNICAL scope to zero.** Important distinction Pravin will likely catch:

- **What we don't need to redo:** the morph clips we already have (Exp 2 Raven_Sun→Cosmic_Sun, Exp 2b Wolf↔Salmon, future edge morphs) become **texture data sources** for the corresponding edge's pearls. No new morph rendering pipeline.
- **What we DO need to build:** a new TouchDesigner visualization layer that does the compositing (sample morph clip at pearl's edge-position, map onto pearl sphere, manage multiple pearls in flight, handle docking dissolves, optionally pearl trails / node convergence).

Scope reality:
- **One pearl on one edge, textured by one morph video, no special docking:** plausibly 1-2 hr in TouchDesigner — a real "is this worth it" prototype
- **Production pearl-graph:** multiple pearls with independent scrub positions, trails, designed dockings, convergence behavior at nodes, place-substrate paths — sprint-week-scale work (Tue-Fri territory)

**Critical pre-prototype unknown — legibility risk:** Austin's pieces have detailed linework. Mapping a video texture onto a lit sphere may render that linework as a *beautiful but illegible marble* at projection distance. The prototype MUST test legibility at actual projection scale, not just in motion charm. Three mitigations to have ready if it fails:
- Render pearls larger relative to node size; lose some "marble" character but preserve linework
- Treat the pearl as a translucent shell with the morph as the inner surface (less foreshortening distortion)
- Crossfade between two flat-quad orientations of the morph rather than spherical mapping at all (loses 3D charm; preserves legibility)

In TouchDesigner this maps to:
- Geometry COMP for each node (the piece's visual at fixed position)
- Particle / instance system for pearls moving along edges
- Movie File In TOP per edge (the morph clip)
- For each pearl: sample the edge's morph clip at `t = pearl_position_on_edge` and map onto the pearl sphere texture
- Docking = designed crossfade, not "perfect dissolve"
- Legibility test: render one pearl + one edge + one morph + one Austin-piece node at projection resolution before scaling up

In Blender:
- Same idea: animated UV texture on a sphere mesh
- More render cost but full 3D control
- Same legibility caveat

### Ranking

**S5 / F4 / A2 = priority +7** — top-of-stack. Unifies graph + morphs + pearl into one visual logic. Doesn't require new pipeline work. Recovers and extends the pearl. Pravin's TouchDesigner domain.

### Implications for the larger architecture

If we adopt pearl-on-edges:
- The "show as graph traversal" framing gets a visible mechanic. Pravin asked "how do we make the graph visible without it feeling like a tech demo" — pearls flowing IS the answer.
- Multiple simultaneous pearls = the show is polyphonic. Several morphs can be in flight at once; the audience can choose what to track or just feel the overall flow.
- The pearl-interior piece is no longer competing with the graph — it's the source/center. Reframes both specs as a single architecture.
- Place-anchored substrate (from peer): pearls flow along geographically meaningful paths (salmon-pearls along Fraser → ocean; orca-pearls along travel corridors)
- Bioregional data driver: live data influences which pearls spawn (high tide spawns more sea-being pearls; salmon-run season spawns more salmon-related pearls)
- Visitor dreams: a visitor's input could spawn a pearl that travels to the dream-relevant node

This is the kind of unifying move that retroactively makes everything else feel obvious in hindsight. Strongly recommend bringing to Pravin at 4pm as a centerpiece.

---

## Specific edge inventory — Austin's pieces

These are edges worth queuing as Tier 1 morph experiments, independent of cultural load (we apply that filter separately). Ordered roughly by tractability:

| Edge | Edge types | Status | Why it matters |
|---|---|---|---|
| Raven_Sun.svg ↔ Cosmic_Sun.svg | form + palette + narrative | Already rendered (Exp 2 today) | Proven; short high-confidence edge; good show warmup |
| Cosmic_Sun.svg ↔ Salmon_Spawn_Eggs.svg | narrative + cross-domain (Nature↔Animal) | Queued for tonight's overnight (per pearl spec) | Sun-energy-descending-as-roe = trophic narrative edge |
| Wolf_Spindle_Whorl.svg ↔ Salmon_Spawn_Eggs.svg v2 | narrative + format match (SVG↔SVG) | Exp 2b rendered; needs v2 fix | Internal v2 fixes the egg-field problem from first attempt |
| Bee.pdf ↔ Butterfly.png | narrative (transformation) + cross-format | Needs PDF decomp first | Life-cycle teaching; bridges PDF↔PNG (tests format-edge feasibility) |
| Bear_Background.pdf ↔ Deer_Background.pdf | scene similarity + format match | Needs PDF decomp | Background-cluster edge; soft palette-cleanser between bigger transitions |
| Wolf_Spindle_Whorl ↔ Wolf_Background | figure-ground (icon ↔ context) | Needs PDF decomp | "Zoom-out" edge; same subject, different scale |
| Octopus.png ↔ Orca.png | subject domain + format match | Needs raster adapter | Sea-being continuity; intra-water-cluster edge |
| Raven.png ↔ Octopus.png | cross-domain (air↔sea) + format match | Needs raster adapter | High-narrative edge (T'lep + corvid intelligence dialogue) |
| Cosmic_Sun ↔ Raven_Sun ↔ Salmon_Spawn ↔ Cosmic_Sun (triangle) | closed-cycle subgraph | Composable from existing | Cycle subgraph = meditation on return-to-source; could be a structural motif in the show |
| Wolf_Background ↔ Thunderbird_Background | cross-cluster (Animal↔Supernatural) | **HIGH cultural load — Austin's lineage** | Touches Austin's actual Sḵwx̱wú7mesh Wolf + Nam̓gis Thunderbird lineage; per existing policy, render only after trust conversation |

### Special status — TheCreator_Background.svg
- Treat as **central hub / frame node**, not as morph endpoint
- Many incoming edges ("pieces gesture toward Creator"); zero outgoing edges
- Other pieces may "point at" Creator visually, but no piece morphs INTO or OUT of Creator
- The Creator node *contains* / *frames* the graph

---

## Cross-graph connections — joining the larger living graph

This Austin-pieces graph is a subgraph of the project's full living graph:

```
SALISH SEA DREAMING LIVING GRAPH (sketch — Phase 2 architecture)
│
├── Austin's pieces subgraph (18 piece nodes + 100+ atom nodes — this spec)
│   ├── Animal cluster
│   ├── Nature cluster
│   ├── Supernatural cluster
│   └── morph + translation + decomposition edges within and across
│
├── Bioregional data subgraph
│   ├── Herring, Salmon, Kelp, Orca, Cedar nodes (the Five Threads)
│   ├── Tide, river-flow, light, weather edges (LIVE via scripts/bioregional_osc_bridge.py)
│   └── Connects to Austin's pieces via subject affinity
│       (Salmon thread ↔ Salmon_Spawn_Eggs piece; Orca thread ↔ Orca piece; etc.)
│
├── Indigenomics AI knowledge graph (Carol Anne / Dan / web app)
│   ├── Concepts, frameworks, contributors, principles
│   ├── First dome-render draft delivered (queued for Dan integration)
│   └── Connects to Austin's pieces via "this piece embodies this concept"
│
├── salishseadreaming.art exhibit graph (April show LIVE artifact)
│   ├── Visitor dreams as a 3D living point-cloud
│   ├── salish_dreamworld TD scene with /dreams/3d live fetch + music-driven breathing
│   ├── Connects to Austin's pieces via dream-content affinity
│   └── Grows in real time during shows
│
└── Pearl-interior subgraph (sister spec)
    ├── Pearl-as-essence node containing Circle / Crescent / Trigon primitives
    ├── Connects to Austin's pieces via "every piece contains these primitives at the atom level"
    └── Companion content: pearl-interior-experiment-spec-2026-05-17.md
```

**The Hubble Space installation could literally render this whole graph as the show's architecture.** Three projector panels: one for graph long-view (constellation/tide-pool), one for active morph close-up, one for bioregional data + visitor dreams (the live feeds). Show is the navigation of all three together.

---

## Implementation arc

This is not "rendered video by Tuesday." It's an **architecture decision** that informs everything downstream:

### Sunday AM (30-60 min thinking exercise)
- Sketch the graph on paper or Excalidraw
- Decide: which pieces are Tier 1 nodes (most show-worthy)? Which edges are interesting first?
- Decide: which edge types matter for IMPACT (form? narrative? bioregional?)?
- Output: a 1-page hand-sketch + a Tier 1 edge list of 5-7 morphs to actually render

### Sunday PM
- The 5-7 Tier 1 edges become the actual morph video assets queued for production
- Pearl-interior work (sister spec) shifts framing from "the show" → "rendering one node of the graph really well"

### Mon-Tue
- Decide graph-visualization treatment (constellation? tide-pool? force-directed?)
- Prototype the chosen layout in a small TouchDesigner scene (Pravin pair)
- Verify visual reads at projection scale before going deeper

### Tue-Fri sprint (in person at Pravin's studio)
- Pair-build TD real-time graph visualization
- Wire morph videos as edge-traversal triggers
- Connect to existing `scripts/bioregional_osc_bridge.py` for live tide/river data
- Connect to existing salishseadreaming.art dreams API for live visitor-dreams overlay
- Test path-selection modes (deterministic vs random vs data-driven vs audience-driven)

### Show — May 27-28
- Multi-minute graph traversal as primary architecture
- Bioregional + audience influences active
- Different nights, different traversals
- The graph IS the show

---

## What this changes about other plans

If we commit to graph-as-architecture, these prior commitments shift framing (not necessarily content):

| Prior commitment | New framing |
|---|---|
| Pearl-interior piece is "the show" | Pearl-interior is *one node* of the graph (the essence / container node) |
| Tier 1 motion render = 18-sec loop = sneak-peek to Pravin | Tier 1 motion render is *one edge* of the graph (the proof that edges work) |
| Render every morph experiment | Render every morph that's also a *useful edge*; prune morphs that don't fit the graph |
| Closing-panel dome short = standalone 10-22 sec piece | Closing-panel dome short = a *path through* the bioregional + Austin + Indigenomics-AI subgraphs — graph traversal becomes the dome content too |
| 5090 = "second machine for theater" | 5090 = "graph-rendering engine for the live show" |

These reframings *increase coherence* across previously-separate threads. They don't add scope; they reveal the structure that was already there.

---

## Cultural floor (applies same as everywhere else)

- Per `feedback_austin_consent_trust_floor.md`: per-output OK is the floor for anything carrying Austin's vocabulary
- Decomposition discipline (Tier D-1/D-2/D-3 only for IMPACT; D-4 deferred)
- Cross-cluster cultural edges (Wolf↔Thunderbird-Background, anything touching specific lineage) require trust conversation with Austin before render
- Graph visualization treatments that anchor on cultural forms (longhouse, drum, button-blanket) are HIGH-A; safer to start with universal forms (sphere-shell, constellation, tide-pool)
- Internal-only outputs to `track2-deterministic/morph_outputs_INTERNAL/` with provenance CSV row

---

## Open questions (DEFERRED — for Sunday or sprint week)

1. Does Pravin/Austin want the graph layout to be *fixed* (every show looks the same shape) or *dynamic* (layout recomputes each show based on live data)?
2. How explicit should the graph structure be to the audience? Visible all-the-time vs revealed-at-moments?
3. Does the salishseadreaming.art dreams graph join in for IMPACT or stay April-show-specific?
4. Does Carol Anne / Dan want the Indigenomics AI graph integrated into the Austin-pieces graph (one unified show) or kept as separate dome content?
5. What's the show's start-state and end-state? (All nodes dim → all nodes lit? One node bright → graph illuminates? Etc.)
6. Multi-show graph state persistence — does Thu's graph remember Wed's traversal, or reset?
7. How does the graph handle Austin sitting in the room? (Special edge activation when he's present?)

---

## References

- Operator + Claude brainstorm 2026-05-16 late evening
- Companion: `docs/space-center/pearl-interior-experiment-spec-2026-05-17.md` — sister spec for the pearl-interior node
- Companion: `docs/space-center/sunday-internal-experiment-lane-2026-05-17.md` — cross-creature experiment policy with shared discipline
- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/feedback_austin_consent_trust_floor.md` — per-output OK floor
- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/project_austin_pearl_vision.md` — Austin's own framing
- `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/reference_coast_salish_formline_primitives.md` — Circle/Crescent/Trigon as Coast Salish primitives
- `scripts/bioregional_osc_bridge.py` — live tide + river OSC feeds (existing, validated)
- `austin-v2-ingest/approved/` — the 18 Austin pieces (currently in private/internal ingest)
- April show artifacts — `salish_dreamworld` TD scene + salishseadreaming.art web app — for graph-visualization architecture reference
