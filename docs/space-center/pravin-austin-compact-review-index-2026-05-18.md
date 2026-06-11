# Compact review index — Pravin / Austin

**INTERNAL ONLY. Per Austin consent floor: per-output OK required before any audience-facing use.**

Suggested framing: *"We have been experimenting internally. Nothing here is approved or proposed as final. We want to ask: does any of this feel interesting, useful, or worth developing with you?"*

---

## Top 6 — show in this order

### 1. Pearl-bead single-edge traversal

**File:** `track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4`

**Demonstrates:** the pearl-bead-on-edges concept — a graph edge carrying a real-time morph along its path. Foundational visual mechanic for a multi-piece graph traversal show.

### 2. Three-shapes primitive field

**File:** `track2-deterministic/morph_outputs_INTERNAL/primitive_field_v001.mp4`

**Demonstrates:** Coast Salish primitive vocabulary (Circle / Crescent / Trigon) at compositional scale — 40 phase-offset cycles sweeping diagonally. Zero cultural load (no Austin assets). Anchors the "primitive cycle as bridge grammar" conversation.

*Alt for darker projection contexts:* `primitive_field_v002_flocking_dark.mp4` — 60 atoms on deep-blue BG, curl-noise drift.

### 3. Raven→Cosmic endpoint-correct v001

**File:** `track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4`

**Demonstrates:** clean same-viewBox (108×108) cross-piece morph with endpoint-correction. Both source and destination resolve to the verified training-JPG frames. Strongest deterministic cross-piece morph candidate so far.

### 4. Cosmic→Salmon v006

**File:** `track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4`

**Demonstrates:** cross-piece, cross-scale morph (108×108 → 1500×1500) with v006-fix that removes the destination background-rect "expanding square" artifact. Endpoint-assisted. The frame for asking Austin: which atom-to-atom relationships are meaningful, which are noise?

*Newer sibling:* `cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007.mp4` — applies Lane 2E routing rule, smoother final settle.

### 5. Salmon in-place v005 — canonical "alive within the piece"

**File:** `track2-deterministic/morph_outputs_INTERNAL/salmon_in_place_v005.mp4`

**Demonstrates:** "the figures come alive without leaving the artwork." Both salmon in their yin-yang positions, counterphase swim via continuous body deformation (cv2.remap traveling wave), subtle eye pulse. Respects the piece's geometry — no straightening, no translation, no extraction.

### 6. SD/LoRA affordance excerpt (Austin v2 LoRA controlled test)

**File:** `track2-deterministic/morph_outputs_INTERNAL/austin-abstract-t2i-affordance-2026-05-18-austin-review-excerpt/`

Open `ONE_PAGE_SUMMARY.md` first; then the two paired JPG comparisons:
- `p01_pearl_interior_three_primitives__C_scaffold_no_lora.jpg` (scaffold only)
- `p01_pearl_interior_three_primitives__B_scaffold_lora025.jpg` (scaffold + LoRA 0.25)
- `p03_tide_current_field__C_scaffold_no_lora.jpg`
- `p03_tide_current_field__B_scaffold_lora025.jpg`

**Demonstrates:** controlled affordance test — can SD/LoRA add surface/light to hand-authored primitive scaffolds while geometry stays locked? Frame as: *"the model is not composing the cultural geometry; it can only add surface/light where the geometry is already locked."* Excludes all animal/clan/supernatural/Austin-creature prompting. LoRA 0.25 only (0.35 excluded).

---

## Ask-first — only if conversation has room for rough experiments

| Artifact | Path | Demonstrates |
|---|---|---|
| Multi-pearl 3-node composite | `morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/04_multi_pearl_animation.mp4` | Polyphonic pearl-bead — 3 graph nodes, 2 simultaneous pearls. Rough; inherits edge-transition artifacts. |
| TheCreator pearl-bridge composite | `morph_outputs_INTERNAL/thecreator-pearl-bridge-composite-2026-05-17/thecreator_pearl_bridge_composite_v001.png` | Visual resonance observation: atom_0114 (sphere) + atom_0117 (figure) in TheCreator structurally echoes our pearl-bead. **Ask Austin to interpret — NOT a cosmological claim.** |
| Cosmic_Sun breathing v003c | `morph_outputs_INTERNAL/austin_piece_breathing_nature_cosmic_sun_v003c_strong.mp4` | "Alive within the piece" mechanic for radial pieces. Companion to Salmon v005. Sister artifact, not as strong on its own. |
| Raven→Salmon raw morph | packet `02_promising_rough_ask_first/02_raven_sun_to_salmon_raw_shape_morph_rough.mp4` | Cross-piece raw morph; known start-z-order, endpoint drift, seam artifacts. |
| Wolf↔Salmon high-load | packet `02_promising_rough_ask_first/04_wolf_whorl_to_salmon_high_load_do_not_lead.mp4` | **HIGH cultural load on both sides.** Ancestor (Wolf) ↔ provider (Salmon). Discuss BEFORE showing. |
| Bee-alive v001 (decomposition proof) | `morph_outputs_INTERNAL/bee_alive_v001.mp4` | Validates PDF→SVG→decomposition pipeline on a low-cultural-load piece. Motion is subtle, not show-worthy by itself. |
| Bee atom catalog (new SVG-geometry masks) | `austin-v2-ingest/decomposed/Animal_Insect_Bee/_atom_contact_sheet_labeled_v2_new_masks.png` | 53 atoms with sub-agent labels + bilateral symmetry + new color-independent masks. Show to validate decomposition + labeling approach. |

---

## Do NOT show

| Artifact | Why excluded |
|---|---|
| `*_CURRENT_*_crossdissolve-regressed.mp4` (Cosmic→Salmon + Raven→Salmon) | Cross-dissolve regression preserved as anti-pattern control — illustrates "what we don't want to do." Confusing out of context. |
| `cosmic_sun_to_salmon_spawn_endpoint_emerge_v001.mp4` | Image-level luma blend; didn't solve atom-level z-order issues. Failed control. |
| `cosmic_sun_to_salmon_spawn_roe_particle_field_v00X.mp4` | Wrong architecture (whole-piece crossfade). Codex worker owns v003 per spec. |
| `salmon_line_swim_v00X.mp4`, `salmon_rectify_v00X` | Salmon free-swimming: TPS, rectification, column-median all FAILED. Architectural lesson: Austin's formline salmon isn't a continuous tube. |
| `salmon_circle_chase_v001.mp4` | Geometry mismatch (body length vs orbit radius). |
| `bee_alive_v002_wing_flutter.mp4` | Wing masks were empty (cream-on-white decomposition limitation, now fixed but THIS clip was rendered before the fix). |
| `austin_006_salmon_body_articulation_v002.mp4` and other "big-shapes" variants | Sprite-based body articulation. Operator review: "disconnected tails, sliding chunks." Failed architecture. |
| `lane_2e_atom_primitive_bridge_poc_v001/v002` | Lane 2E mechanism works but too few atoms to communicate visually. Concept locked as routing RULE (not visual artifact). |
| Anything in `morning-demo-folder-2026-05-18/4_failed_controls/` | All labeled controls; preserved for internal reference only. |
| Supernatural pair morphs (TheCreator-x, Snake_Serpent, Thunderbird, Transformer) | VERY HIGH cultural load. Do not render or show until Austin guides supernatural pieces. |
| Wolf↔Thunderbird-Background pair | Operator-restricted explicitly. |

---

## Cultural guardrails (apply everywhere)

- Per-output Austin OK required before any audience-facing use.
- Treat "Heron↔Salmon" as "ecological adjacency candidate" framing, NOT interpretive claims like "fishes the spawning ground" (peer caution 2026-05-18).
- TheCreator pearl-bridge composite = OBSERVATION, not cosmological claim.
- Wolf↔Salmon = discussion-first before showing.
- LoRA affordance test = "adds surface/light to locked geometry, does not compose."

---

## Reference

- Full packet v1 (source of truth): `morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/README.md`
- Packet v2 (thumbnails + HTML): `morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/index.html`
- Morning demo folder (4 categories, 27 symlinks): `morph_outputs_INTERNAL/morning-demo-folder-2026-05-18/index.html`
- Morning checklist: `docs/space-center/morning-checklist-2026-05-18.md`
- Decomposition mask upgrade report: `docs/space-center/pdf-to-svg-conversion-report-2026-05-18.md`
