# Transition Candidate Round - 2026-05-18

Internal offline morph exploration after the TouchDesigner mudra scrubber
checkpoint. No more TD work in this pass.

## New Renderer

`scripts/morph_atom_recomposition_candidate.py`

Purpose: quick candidate generation for piece-to-piece transitions using
verified training JPG endpoints plus available decomposed atom masks.

Algorithm:

- force exact source JPG at frame 0
- force exact destination JPG at final frame
- convert atom masks into transparent source/destination sprites
- assign source atoms to destination atoms by centroid, color, and area cost
- move source atoms on curved paths with particle flow
- assemble destination atoms in place
- use only a short final endpoint settle for exact fidelity

## Rendered Candidates

### Bee -> Cosmic Sun v001

- MP4: `track2-deterministic/morph_outputs_INTERNAL/bee_to_cosmic_sun_atom_recomposition_v001.mp4`
- Folder: `track2-deterministic/morph_outputs_INTERNAL/bee_to_cosmic_sun_atom_recomposition_v001/`
- Read: useful control; too much late Bee ghosting.

### Bee -> Cosmic Sun v002 earlier reassembly

- MP4: `track2-deterministic/morph_outputs_INTERNAL/bee_to_cosmic_sun_atom_recomposition_v002_earlier_reassembly.mp4`
- Folder: `track2-deterministic/morph_outputs_INTERNAL/bee_to_cosmic_sun_atom_recomposition_v002_earlier_reassembly/`
- Read: cleaner than v001; Cosmic structure asserts earlier, but the transition still reads as a burst into the sun rather than a deeply authored morph.

### Bee -> Raven Sun v001

- MP4: `track2-deterministic/morph_outputs_INTERNAL/bee_to_raven_sun_atom_recomposition_v001.mp4`
- Folder: `track2-deterministic/morph_outputs_INTERNAL/bee_to_raven_sun_atom_recomposition_v001/`
- Read: strongest of this round. The winged source and Raven/sun destination share enough mass, palette, and silhouette that the atom routing has visual continuity.

## Caveats

- Bee atom labels are currently unclassified, so routing is visual rather than
  grammar-aware.
- These are automatic visual correspondences, not Austin-authored semantic
  mappings.
- All outputs are INTERNAL ONLY and require Austin per-output OK before any
  public, sponsor-facing, or show-staged use.

## Next Offline Direction

Use Bee -> Raven as the better candidate for v002 if this branch continues:

- fade source sprite residue earlier
- give wing/leg atoms distinct destination classes instead of one global solver
- consider a short Raven wing unfurl at the end rather than a static endpoint
- keep Bee -> Cosmic as a control, not the lead
