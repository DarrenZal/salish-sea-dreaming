# SSD IMPACT — Resolume Compositing Cheat-Sheet

**For Pravin's Sunday composition + Monday live performance.**
**Built 2026-05-24 Sunday morning.**

One-page reference for layer blending, alpha-channel handling, and the Alley → AVC pipeline. Keep this beside the Resolume comp.

---

## Quick layer stack (suggested starting point)

```
TOP    →  Primitive ripples / field overlays    [Add or Screen blend]
          Water flow phrases (alpha versions)   [Alpha blend if HAP/ProRes]
          ────
MIDDLE →  Autolume "dreaming" baseline 22-min   [Multiply or Add or normal]
          ────
BOTTOM →  Moonfish hero footage (H1 Salmon etc) [Normal / base]
```

Adjust to taste. The dreaming layer is YOUR signature — give it visual primacy.

---

## File-naming convention → which blend mode

| Filename pattern | Resolume blend mode | Notes |
|---|---|---|
| `*_overlay_black.mp4` | **Add** or **Screen** or **Lighten** | Black background drops out; bright primitives composite onto layer below |
| `*_over_moonfish-water.mp4` | (don't blend — preview only) | These are pre-composited PREVIEWS showing how the layer feels. Not for compositing yourself. |
| `*.mov` ProRes 4444 (alpha) | **Alpha** | True alpha channel; cleanest transparency, biggest files |
| `*.mp4` HAP Alpha (post-Alley) | **Alpha** | Resolume-native alpha codec; cleaner than `_overlay_black` Add/Screen |
| `H1_salmon_school_4k_lanczos.mp4` etc | **Normal** | Base footage layer |
| `autolume_baseline_22min_4k_lanczos.mp4` | **Normal**, **Multiply**, or **Add** depending on intent | Try Multiply first for ghostly underlay; Add for energetic surface |
| `autolume_baseline_44min_halfspeed_4k.mp4` | same as above | Half-speed variant — closer to April show's morph pace |

---

## Layer-by-layer recommendations from current asset set

### Primitive ripples
- `abstract_radiating_primitive_ripples_v001_1_orientation_polish_overlay_black.mp4` → **Add** blend. Black drops, ripples emerge over footage below.
- For cleanest result: convert to HAP Alpha via Alley first, then use **Alpha** blend. Worth the extra step.

### Water flow (waterfall, transpiration, current)
- `waterfall_vertical_phrase_v002_60s.mp4` (the longer 60s version Pravin loved) → use the **ProRes 4444 alpha** version in `04_ProRes_Alpha/` if Resolume handles it on Windows; else HAP Alpha via Alley.
- Companion `__over_moonfish-water.mp4` files are previews — don't composite, just reference how it looks.

### Primitive field (flocking)
- `primitive_field_v002_flocking_dark_palette_overlay_black.mp4` → **Add** at low opacity (0.3-0.5).
- `primitive_field_v002_flocking_light_palette_overlay_black.mp4` → **Lighten** at low opacity.
- Use sparingly — these are texture, not focal.

### Autolume dreaming baseline
- Try **Normal** blend at full opacity first — let it be the dreaming layer it is.
- If too dominant, drop to 0.6-0.8 opacity OR switch to **Multiply** for ghostly underlay reading.
- Speed: try the original 22-min first. If morph feels too fast vs the April show, switch to `autolume_baseline_44min_halfspeed_4k.mp4` (half-speed, closer to April pace).

### H1 Salmon + other hero clips
- Bottom of stack, **Normal** blend.
- These are the source-of-life layer — primitives and dreaming go ON TOP, not under.

---

## Alley → HAP Alpha workflow (for alpha-channel layers)

Pravin's pipeline: Mac composition → Alley transcoding → Windows for the live performance because of NVIDIA GPU dependency.

**For alpha layers via Alley:**

1. Open Alley, drag in the source (ProRes 4444 alpha .mov OR `_overlay_black.mp4`)
2. **Output codec: HAP Alpha** (NOT HAP — that's no-alpha)
3. **Resolution**: 3840×2160 (or match Resolume composition target)
4. **Quality preset**: usually highest available
5. Test one short clip end-to-end before committing the whole set:
   - Alley → output `.mov` (HAP Alpha)
   - Drop into Resolume → Alpha blend mode → verify transparency reads correctly over a test footage layer
6. If it looks right, batch the rest

**Edge cases / pitfalls:**
- HAP Alpha files can look slightly different on Apple vs Windows due to gamma handling — preview on the Windows machine before committing
- If `_overlay_black` source is used (no real alpha), Alley generates synthetic alpha from luminance — works but not pixel-perfect
- Resolume has occasionally been finicky with HAP Alpha at 4K — if a layer reads black or flickers, fall back to **Add** blend on the `_overlay_black` MP4

**For opaque layers (Autolume baseline, hero footage):**
- AVC (H.264) via Alley is fine. Source files already H.264 4K — Resolume will transcode to DXV natively on import or you can pre-bake via Alley to HAP for fastest playback.

---

## Speed adjustment in Resolume (if Autolume morph is too fast)

Right-click the Autolume clip → properties → **Playback Speed** slider → drop to 0.5x or 0.4x. Same effect as the half-speed re-encode but in real-time + adjustable.

The half-speed file `autolume_baseline_44min_halfspeed_4k.mp4` is the pre-baked option — slightly cleaner playback at the trade of a bigger duration.

---

## Common pitfalls + fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| Black halos around primitive shapes | Add/Screen blend on `_overlay_black` source (not pure-black background) | Use HAP Alpha version via Alley → Alpha blend |
| Primitive ripples too dim | Add blend at low opacity | Bump opacity; or switch to Lighten |
| Autolume looks "alive" but flickers | noise_anim=True doing its job; OR codec stutter | Frame mutation is intentional. If it's actually playback stutter, transcode to HAP via Alley for smooth 30fps |
| Water flow reads wrong way | Wrong "crescentup" vs default version | Check filename — `crescentup` rises toward sky, default flows down |
| Resolume crash on 4K HAP Alpha | Memory or GPU pressure | Try lower-bitrate HAP Alpha; or fall back to Add-blend on MP4 |

---

## File index quick-reference

| Asset class | Folder / file | Format | Blend |
|---|---|---|---|
| Autolume dreaming | `autolume_baseline_22min_4k_lanczos.mp4` (or half-speed sibling) | MP4 H.264 | Normal / Multiply / Add |
| Hero footage | `H{1,2,3,4,5,6,7,8}_*_4k_lanczos.mp4` (H6 is native 4K from John-test) | MP4 H.264 | Normal |
| Primitive ripples | `abstract_radiating_primitive_ripples_v001_1_*` | MP4 black-bg OR ProRes alpha | Add / Alpha |
| Water flow (waterfall, transpiration, current) | `waterfall_vertical_phrase_v002_*`, `transpiration_*`, `current_streamline_field_*` | MP4 black-bg OR ProRes 4444 RGBA | Add / Alpha |
| Primitive field (flocking) | `primitive_field_v002_flocking_*_overlay_black.mp4` | MP4 black-bg | Add / Lighten |
| Austin spine endpoint | `anchor_graph_spine_v004_1_raven_collapse_polish.mp4` | MP4 | Normal (full screen, intercut) |
| Briony drawings | `Briony-Penn-Archive-for-Pravin-2026-05-23.zip` (9 categories) | Still images | (load as Resolume sources OR for reference palette) |

---

## When you're stuck, the simplest stack that always works

1. Hero footage (Moonfish) — bottom, Normal
2. Autolume dreaming — middle, Normal at 0.7 opacity
3. ONE overlay layer (water flow or primitives) — top, Add at 0.5 opacity

That's it. Three layers. Read it. Add fourth/fifth ONLY if Resolume's running smooth.
