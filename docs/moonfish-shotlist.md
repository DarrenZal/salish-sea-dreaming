# Moonfish + Denning Shotlist — Exhibition Hero Segments

**Created:** 2026-03-27
**Lock target:** Wednesday, April 1, 2026
**Goal:** 3-5 locked Briony-styled exhibition sequences from 5-8 hero segments

## Video Inventory

| File | Duration | Category | Content | FPS | Hero? |
|------|----------|----------|---------|-----|-------|
| P1099653.mp4 | 7:08 | Underwater | Salmon schools, kelp forest, varied | 60 | YES |
| P1077716.mp4 | 2:28 | Underwater | Herring in golden kelp bed | 60 | YES |
| P1111785.mp4 | 1:30 | Underwater | Bull kelp canopy, golden light | 60 | YES |
| P1111707.mp4 | 1:22 | Underwater | Herring schools through kelp | 60 | YES |
| P1111509.mp4 | 0:19 | Underwater | Colorful reef/intertidal (short) | 60 | YES |
| P1000011.mp4 | 1:03 | Underwater | Kelp with small herring, intimate | 60 | maybe |
| DSC_9313_HD.mp4 | 12:42 | Underwater | Shallow reef/kelp, nearshore | 30 | review |
| DJI_0022.mp4 | 1:39 | Drone | Sea lions + birds in spawn water | 24-30 | witness |
| DJI_0045.mp4 | 2:02 | Drone | Aerial spawn, milky water, boats | 24-30 | witness |
| DJI_0009 2.mp4 | 1:57 | Drone | TBD | 24-30 | review |
| DJI_0811.mp4 | 0:46 | Drone | TBD | 24-30 | review |
| DJI_0848.mp4 | 0:45 | Drone | TBD | 24-30 | review |
| DJI_0857.mp4 | 1:21 | Drone | TBD | 24-30 | review |

## Hero Segments

### Tier 1 — ControlNet + LoRA pre-render candidates

**H1. "Salmon School" — P1099653 ~1:40–2:30**
Dense salmon/herring school moving through green water with dramatic light from above. The 2:00 mark has an extraordinary dense formation. Powerful, dynamic — "salmon power" motif.
- Role: Translation/Dream
- Technique: ControlNet + Briony LoRA (preserve schooling motion, apply watercolor)
- Notes: The density of fish here is ideal for style transfer — strong edges for ControlNet

**H2. "Herring in Kelp" — P1077716 ~0:00–1:00**
Herring schools swimming through a golden kelp/eelgrass bed. Beautiful natural composition — golden vegetation in foreground, silver fish in midground, green water background. Steady, flowing motion.
- Role: Translation
- Technique: ControlNet + Briony LoRA, possibly selective masking (style fish more than kelp)
- Notes: The kelp provides beautiful natural structure. This is the heart of the exhibition.

**H3. "Kelp Cathedral" — P1111785 ~0:00–1:00**
Golden bull kelp canopy with light filtering through from above. No fish — pure kelp forest, swaying. Contemplative, slow, the "stillness" moment.
- Role: Translation → Witness (raw→styled dissolve candidate)
- Technique: Light LoRA (strength 0.35) to preserve the golden kelp texture, or raw→styled dissolve
- Notes: This clip has the strongest contemplative quality. A freeze/bloom/release moment here.

### Tier 2 — img2img or hybrid candidates

**H4. "Dense School" — P1111707 ~0:40–1:10**
Herring school becomes very dense at ~60s, flowing behind and through kelp fronds. More dramatic than H2 — the school dominates the frame.
- Role: Translation/Dream
- Technique: img2img + LoRA (fast iteration), promote to ControlNet if results are strong
- Notes: Good fallback if H1 doesn't style well (different scale of fish)

**H5. "Reef Garden" — P1111509 ~0:00–0:19**
Only 19 seconds but extraordinary: colorful reef with sponges, anemones, coralline algae in vivid reds/oranges/yellows/pinks, kelp forest rising behind. The most color-rich frame in the entire collection.
- Role: Dream (full Briony transformation)
- Technique: ControlNet + LoRA at higher strength (0.55) — this wants full painterly treatment
- Notes: Short clip = entire thing is a hero. Ask Deirdre if she has more of this reef.

**H6. "Kelp Forest Floor" — P1099653 ~3:40–4:20**
Vertical kelp forest scene (the 240s preview). Different spatial grammar from the school shots — looking up through kelp toward surface light. Fish visible in mid-distance.
- Role: Structure (motion grammar for TD, kelp sway as flow field)
- Technique: Light LoRA or raw, extract kelp motion for TD boid/flow field drivers

### Tier 3 — Drone as witness layer (raw, not Briony-styled)

**H7. "Spawn Feast" — DJI_0022 ~0:00–0:40**
Sea lions/seals (dark shapes) and seabirds (white dots) feeding in milky herring spawn water. The ecological event from above — predators converging. This is pure witness material.
- Role: Witness
- Technique: **Raw footage, no style transfer.** This is documentary truth.
- Notes: Could be used as a data layer underneath styled content. The milky green is beautiful.

**H8. "Milky Water" — DJI_0045 ~0:00–0:30**
Aerial herring spawn — milky turquoise water along beach, boats present. The spawn event at landscape scale.
- Role: Witness
- Technique: Raw or very light treatment. The aerial perspective provides counterpoint to underwater immersion.

## Denning Photo Heroes

| Image | Content | Resolution | Exhibition Role |
|-------|---------|------------|-----------------|
| jpeg_064.jpg | Underwater reef — vivid sponges, coralline algae on dark background | 3264x2448 | ControlNet apparition reveal |
| jpeg_071.jpg | Sunflower sea star (Pycnopodia) — dramatic on dark background | 3264x2448 | ControlNet apparition reveal |
| jpeg_056.jpg | Purple ochre sea star (Pisaster) — bold color on rock | 4000x3000 | ControlNet + LoRA, freeze/bloom |
| jpeg_059.jpg | Tidepool — urchins, coralline algae, encrusting organisms | 4000x3000 | Full Briony transformation |
| jpeg_061.jpg | Sea star wasting / textured surface | 4000x3000 | Documentary/witness |

## Deirdre Request List

Send to Prav for Deirdre:

1. **P1099653** — timecodes 1:35–2:35 and 3:35–4:25 (two segments). Mezzanine/ProRes 422 preferred. Slowed version of the 1:35–2:35 segment especially.
2. **P1077716** — timecodes 0:00–1:05. Full clip essentially. Slowed version.
3. **P1111785** — full clip (only 1:30). Slowed version — this kelp footage will be beautiful slow.
4. **P1111509** — full clip (only 0:19). This is the reef — ask if she has more footage of this location.
5. **P1111707** — timecodes 0:35–1:15.

Format: ProRes 422 HQ or high-bitrate H.264. A few seconds of handles on each side.
For P1099653 salmon school segment (H1): RAW if willing — this is likely the single strongest exhibition frame.

Also: any bird murmuration/flocking footage she mentioned was coming.

## Technique Decisions (to be updated after testing)

| Segment | Round 1 Test | Round 2 Test | Production Decision |
|---------|-------------|-------------|---------------------|
| H1 Salmon School | img2img s=0.45 | ControlNet+LoRA | TBD |
| H2 Herring in Kelp | img2img s=0.45 | ControlNet+LoRA | TBD |
| H3 Kelp Cathedral | img2img s=0.35 | raw→styled dissolve | TBD |
| H4 Dense School | img2img s=0.45 | — | TBD |
| H5 Reef Garden | img2img s=0.55 | ControlNet+LoRA | TBD |
| H6 Kelp Forest Floor | extract motion | — | TD flow field? |
| H7 Spawn Feast | raw | — | Witness layer |
| H8 Milky Water | raw | — | Witness layer |

**Pruning gate:** After Round 1-2, lock 2 primary + 1 fallback techniques. Drop the rest.

## Next Steps

1. [x] Extract preview frames from all 13 videos
2. [x] Review and identify hero segments
3. [x] Trim hero subclips (video-to-video, fast) — 8 subclips in media/hero-subclips/
4. [ ] Send Deirdre request to Prav
5. [ ] Round 1 micro-render tests on Prav's 3060
6. [ ] Round 2 ControlNet+LoRA on 3090 (if ready) or 3060
7. [ ] Creative technique tests (dissolves, freeze/bloom, Denning apparitions)
8. [ ] Technique pruning gate
9. [ ] Lock 3-5 production sequences
10. [ ] Final pre-renders and Resolume export
