# Lane 1 v002 — Atom-level endpoint fix (spec)

Written 2026-05-17 PM after peer-agent diagnosis of v001 visual review.
v001 was image/luma-mask level; the real problems are atom-level. v002
goes there directly.

## What v001 cannot fix

1. **Start-frame z-order wrong** — raw and v001 both open with the sun
   layered on top of the raven's head. Austin's source SVG has raven
   layered on top of sun. v001 only touches the last 18 frames so
   cannot address.
2. **Destination eye/pivot color reads worse than raw** — luma-mask blend
   averages morph residue with destination, diluting exact fills.
3. **Straight diagonal seams persist** — large background-field polygons
   are being interpolated as morph atoms, causing linear artifacts
   cutting through the composition.

Diagnosis: these are atom-selection and layer-ordering problems, not
endpoint timing problems. v002 must operate on the atom set, not on
output pixels.

## Three concrete fixes

### Fix 1 — Background-field exclusion

**Symptom:** straight diagonal/linear seams cutting through morph frames.

**Cause:** the morph engine treats every SVG path equally. Background
rectangles, large field polygons, and underlying color blocks get
interpolated alongside foreground figures, producing wrong-shape
intermediates that look like geometric seams.

**Fix:**
- Use existing `atom_metadata.csv` per piece (already classified — 504
  atoms, 179 primitives, plus `background-field` and `negative-space`
  labels)
- Modify `morph_engine.py` to accept an `--exclude-atom-types` flag
  (default: `background-field,negative-space`)
- Background atoms render as STATIC UNDERLAY composited under the morph
  frames — no interpolation, no shape-warping
- Foreground atoms (circle-oval, crescent, trigon, formline-primary,
  eye-focal-oval, wing-feather, fin-tail, body-element, etc.) morph as
  before

**Implementation sketch:**
```python
# In morph engine, before path resampling
src_atoms = load_atom_metadata(source_svg)
dst_atoms = load_atom_metadata(dest_svg)

src_fg = [a for a in src_atoms if a.ai_label not in EXCLUDED_TYPES]
src_bg = [a for a in src_atoms if a.ai_label in EXCLUDED_TYPES]
dst_fg = [a for a in dst_atoms if a.ai_label not in EXCLUDED_TYPES]
dst_bg = [a for a in dst_atoms if a.ai_label in EXCLUDED_TYPES]

# Render bg underlay (cross-fade source bg → dest bg over duration)
bg_underlay = render_bg_layer(src_bg, dst_bg, n_frames)

# Morph only foreground atoms
fg_morph = run_path_interpolation(src_fg, dst_fg, n_frames)

# Composite
for i in range(n_frames):
    final[i] = bg_underlay[i].copy()
    final[i].paste(fg_morph[i], mask=fg_morph[i].alpha)
```

### Fix 2 — Z-order preservation via direct-render endpoints

**Symptom:** start frame has wrong layer order (sun on top of raven).

**Cause:** path resampling at t=0 produces an interpolation of source
paths in their pre-shuffled order; original SVG draw order is lost.

**Fix:**
- First 3 frames = direct SVG render of source piece (correct z-order)
- Frame 3 → frame 6: cross-fade from direct render to engine's first
  output frame (smooth transition into morph)
- Frames 6 to N-7: pure engine output (the primitive-motion middle that
  operator likes)
- Frame N-7 → frame N-3: cross-fade from engine output to direct dest
  SVG render
- Last 3 frames: direct SVG render of dest piece (correct z-order +
  exact palette)

This trades 6 frames of "engine middle" on each end for clean endpoints
with source-of-truth z-order. Total middle motion: N-12 frames instead
of N, still ~90% of the duration. The cross-fades are short enough
(125ms each at 24fps) that they read as "frame-edge settling" rather
than as a fade transition.

**Why this is different from v001:** v001 luma-blended dest INTO engine
residue. v002 cuts to direct SVG render at endpoints, preserving exact
palette + layer order. Engine output is bracketed by ground-truth
frames, not blended with them.

### Fix 3 — Palette-aware emergence (deferred to v003)

If Fix 1 + Fix 2 don't fully resolve eye/pivot color: v003 would
implement true per-atom snap where remaining foreground morph atoms in
final 10 frames move to nearest destination atom position + adopt that
atom's exact fill color. This requires per-frame shape data from the
morph engine, which it doesn't currently emit. Defer until v002 visual
review.

## Output naming

```
raven_sun_to_salmon_spawn_atom_level_v002.mp4
cosmic_sun_to_salmon_spawn_atom_level_v002.mp4
```

Frame directories same convention:
`<pair_id>_atom_level_v002/frame_NNNN.png`

## Effort estimate

- Fix 1 (bg exclusion + underlay composite): 2-3 hrs (touches morph
  engine internals)
- Fix 2 (direct-render endpoints): 1-1.5 hrs (post-process; engine output
  already saved, just need pre/post composite)
- Test + iterate: 1-1.5 hrs

Total: 4-6 hrs. Achievable Mon-Tue between LoRA work and Salt Spring
prep.

## Decision gate

Before promoting v002 to canonical, side-by-side review with:
- raw (current canonical, drifty endpoints)
- endpoint_emerge_v001 (image-level attempt, control)
- atom_level_v002 (proper fix)

If v002 looks right on Raven/Salmon, apply same approach to Cosmic/Salmon
+ any future cross-scale pairs. If still wrong, iterate to v003 with
per-atom palette snap.

## Open question for Pravin (not for 4pm — Salt Spring sprint)

Should background-field be:
- (a) static underlay (current spec) — keeps source bg through middle,
  cross-fades to dest bg
- (b) blank (white) underlay — eliminates ALL bg, shows pure foreground
  morph on white
- (c) destination bg from frame 0 — composition lands "in" the
  destination world from the start

Each gives a different feel. (a) preserves visual context; (b) is
exhibition-honest about the transformation being abstract; (c) reads
as the destination "coming into being" rather than morphing FROM
source. Decide by trying all three on one pair.
