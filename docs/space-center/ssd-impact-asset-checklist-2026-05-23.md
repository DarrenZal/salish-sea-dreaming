# SSD Phase 2 IMPACT 2026 — Asset Checklist

**For Pravin's compositing + the Monday May 25 install at HRMSC Hubble Lounge.**
**Built 2026-05-23 evening.** Pravin's ask: *"I guess I should have created a check list."*

Show event: **IMPACT 2026, HR MacMillan Space Centre — May 27-28**.
Install window: **Monday May 25, 3pm onward** (preferred); Tuesday 10pm-midnight (backup if needed).

---

## Status legend

- ✅ Ready, on Drive, Pravin can grab now
- 🟡 On Mac, needs upload (in progress or queued)
- 🔧 Being processed
- ❌ Not done / blocked

---

## Layer 1: Autolume "dreaming" video master (20-min continuous, non-repeating)

The primary single-layer asset Pravin's recording his 20-min performance against. One continuous loop, no visible repeat.

| Variant | Resolution | Duration | Codec | Location | Status |
|---|---|---|---|---|---|
| **baseline_20min** psi=0.8 + noise_anim=True | 3840×2160 (pillarbox from 512²) | 22:22 | H.264 / CRF 18 / ~50 Mbps | `/tmp/4k-heroes/autolume_baseline_22min_4k_lanczos.mp4` (7.9 GB) | 🟡 done, needs upload |
| baseline_20min @ 512² native (pre-upscale) | 512×512 | 22:22 | mpeg4 | `/tmp/autolume_20min_20260523_1336_baseline.mp4` (2.62 GB) | 🟡 master source, archive copy |
| 5-variant 4K sweep (30s loops each) | 3840×2160 | 30s × 5 | H.264 | Google Drive `02_Autolume_4K_Sweep_5_Variants` | ✅ already mirrored |
| wild_psi120 30s in 2 framings (centered + cropped) | 3840×2160 | 30s | H.264 | Google Drive `01_Autolume_4K_Wild_30s` | ✅ already mirrored |

**Note on the 22-min lanczos**: Source was rendered at 512² on the 3090 with the 120-kimg PKL (preserves intentional abstract aesthetic). Upscale path is lanczos (not ESRGAN AI) because BOTH H200 pods wedged tonight after ~1000 frames. ESRGAN can be retried tomorrow if Pravin wants a sharper version, but Resolume transcodes to DXV anyway and lanczos at CRF 18 / 50 Mbps is projection-grade.

**Backup wild_psi120 22-min**: rendered at same time, on 3090 at `C:\Users\user\autolume_20min\20260523_1222\wild_psi120_20min.mp4` (1.69 GB 512² master). Can lanczos-upscale on request if Pravin prefers it over baseline.

---

## Layer 2: Moonfish hero subclips at 4K (composable underwater footage)

The "running footage" Pravin uses underneath the Autolume + water flow layers in his composite.

| Hero | Subject | Source FPS | Duration | 4K Status | Location |
|---|---|---|---|---|---|
| H1 Salmon school | dense fish school | 60fps | 60s | ✅ 4K lanczos done | `/tmp/4k-heroes/H1_salmon_school_4k_lanczos.mp4` (319 MB) |
| H2 Herring in kelp | herring through kelp forest | 60fps | 64s | 🔧 firing now | `/tmp/4k-heroes/H2_herring_in_kelp_4k_lanczos.mp4` |
| H3 Kelp cathedral | tall kelp light beams | 60fps | 90s | 🔧 queued | `/tmp/4k-heroes/H3_kelp_cathedral_4k_lanczos.mp4` |
| H4 Dense school | tightly packed fish | 60fps | 40s | 🔧 queued | `/tmp/4k-heroes/H4_dense_school_4k_lanczos.mp4` |
| H5 Reef garden | reef life close-up | 60fps | 19s | 🔧 queued | `/tmp/4k-heroes/H5_reef_garden_4k_lanczos.mp4` |
| H6 Kelp forest floor | kelp seabed dappled light | native 4K | 50s | ✅ already 4K (John-test) | `/Users/darrenzal/projects/salish-sea-dreaming/media/hero-subclips/H6_kelp_forest_floor_4k.mp4` (217 MB) |
| H7 Spawn feast | salmon spawn frenzy | 60fps | 39s | 🔧 queued | `/tmp/4k-heroes/H7_spawn_feast_4k_lanczos.mp4` — **Pravin's "original 4K 7 S salmon"?** |
| H8 Milky water | particulate plume in water | 60fps | 29s | 🔧 queued | `/tmp/4k-heroes/H8_milky_water_4k_lanczos.mp4` |

**1080p originals** (always available, in case any 4K upscale is wrong): `~/projects/salish-sea-dreaming/media/hero-subclips/H{1,2,3,4,5,6,7,8}.mp4`.

**On Google Drive** under Shawn's SSD parent (`1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr`) → folder `18ld1BmLePz8…` has the 512/768 processed versions (smaller, not show-ready) + originals.

---

## Layer 3: Water flow grammar (alpha-channel composable phrases)

These overlay on the hero footage via Resolume Add/Screen/Lighten blend. Black-background MP4 versions OR ProRes 4444 RGBA versions.

| Layer | Description | Status | Location |
|---|---|---|---|
| `waterfall_vertical_phrase_v002_60s.mp4` | waterfall, 60s extended (Pravin loved the original 6s, wanted longer) | ✅ on Google Drive | `1xP0dzNpibCJet…/03_Water_Flow_MP4/` |
| `waterfall_vertical_phrase_v002_60s__over_moonfish-water.mp4` | composite preview over underwater | ✅ on Google | same folder |
| Transpiration (inverse waterfall) — crescent up | rises from earth toward sky | ✅ on Proton 2026-05-22 update | Proton `SSD Phase 2 - Pravin Internal Update - 2026-05-22` |
| Transpiration (inverse waterfall) — crescent down | catches vapor from below | ✅ on Proton | same |
| Current streamline field | horizontal flow | ✅ on Proton | same |
| ProRes 4444 RGBA alpha versions | for cleaner compositing | ✅ on Google Drive | `1xP0dzNpibCJet…/04_ProRes_Alpha/` |

**Cymatic / topology R&D**: see Proton `SSD Phase 2 - Pravin Internal Update - 2026-05-20` for early sun-portal water-field experiments. Not lead show material per operator's own notes; useful as variety if Pravin wants.

---

## Layer 4: Primitive ripples + flocking field (Coast Salish primitive grammar)

| Layer | Description | Status | Location |
|---|---|---|---|
| `abstract_radiating_primitive_ripples_v001_1_orientation_polish_overlay_black.mp4` | composable primitive-ripple layer, black bg | ✅ on Proton WEB SMALL | `02_Primitive_Ripples_MP4/` |
| `abstract_radiating_primitive_ripples_v001_1_orientation_polish_over_moonfish-water.mp4` | preview over underwater | ✅ on Proton | same |
| `primitive_field_v002_flocking_dark_palette_overlay_black.mp4` | dark-palette flocking primitives | ✅ on Proton | `06_Primitive_Field_MP4/` |
| `primitive_field_v002_flocking_light_palette_overlay_black.mp4` | light-palette flocking | ✅ on Proton | same |

---

## Layer 5: Austin authored spine + figural endpoints

The lead Austin/Pravin artifact passage.

| Asset | Status | Location |
|---|---|---|
| `anchor_graph_spine_v004_1_raven_collapse_polish.mp4` (Nature Cosmic Sun → Raven Sun → cymatic loop) | ✅ on Proton WEB SMALL | `01_Spine_Endpoint/` |
| Contact sheet for the spine | ✅ on Proton | same |
| `figural_orca_fluid_silhouette_reveal_v001.mp4` (orca silhouette prototype) | ✅ also on Google Drive as zip | Google `1EEr7JJyyVf8kcv-9ABxyh6hfZiCLUiRC` |

---

## Layer 6: Briony Penn drawings (palette enrichment)

Pravin: *"we may wish to get Briony's drawings on the pallet as well - they add alot"*

| Asset | Size | Status | Location |
|---|---|---|---|
| `Briony-Penn-Archive-for-Pravin-2026-05-23.zip` (9 categories, 206 files: Field-Journals, Illustrated-Maps, Illustrations, Nudibranch/camas, Paintings, Paintings-cleaned, Pen-and-Ink, Signage-and-Murals, Watercolour-Mandalas) | 91 MB | 🟡 zip ready, needs upload | `/tmp/Briony-Penn-Archive-for-Pravin-2026-05-23.zip` |
| 22-image Briony LoRA training pairs (subset, with horizontal/vertical crops) | 335 MB | 🟡 if useful | `~/projects/salish-sea-dreaming/briony-lora/*.png` |

---

## Layer 7: Bob Turner thematic source footage (Saturday assembly target, NOT Monday-blocking)

Pravin's "annotated film list" email from May 22 — Priority One: 5 thematic 4K sequences.

| State | Reality |
|---|---|
| Catalog | ✅ All 18 URLs cataloged at `docs/space-center/bob-turner-youtube-catalog-2026-05-23.md` |
| Subclip cut list | ✅ 20 subclips across 5 themes, ~40 min hero material, ffmpeg commands ready at `docs/space-center/bob-turner-subclip-cut-list-2026-05-23.md` |
| Source pulls | ❌ YouTube 403'd all 13 attempts today (my IP rate-limited). Retry tomorrow with `yt-dlp --cookies-from-browser safari` |
| 4K upscale | ❌ Blocked on source pulls |

**Note**: Orca gap resolved (accept 1080p + upscale + Pravin's Resolume Edge effect). Human-impact + birds gaps resolved (Bob's videos have embedded ferry/harbour/cargo/birds content per Pravin's clarification). Catalog updated accordingly.

---

## Layer 8: Audio

| Asset | Status | Location |
|---|---|---|
| Ableton project `SSD_ABLETON_V2_PERFORMANCE` | ✅ on Google | `1XLfLWr3Ws3037Y57kg…` (Exhibition Files) |
| Matt's `file 2.mp3` (sole audio source) | ✅ on 3090 | `C:\Users\user\` (per memory `project_ableton_audio_source.md`) |
| `Singing Male Humpback Whale Mar 5, 2019.mp3` | ✅ on Google Drive | parent `11lrwgmLjnfN…` |

---

## Source-of-truth Drive locations (3 places things live)

| Drive | URL | What's there |
|---|---|---|
| **Google Drive — Shawn's SSD shared** (canonical) | `https://drive.google.com/drive/folders/1UvJ6G65FbSRngtCy0hMFpUwqhadfywFr` | SSD1 originals, Exhibition Files (Ableton), the May 22 internal-update folder, demo materials, figural orca zip, SSD-Senakw-Data-Package |
| **Operator's Proton Drive — SSD Phase 2 Live Installation Review WEB SMALL** | (Proton link in Signal 13:18 PDT) | spine endpoint, primitive ripples, water flow layers, orca silhouette, primitive field, R&D — operator's curated review folder |
| **Operator's Proton Drive — SSD Phase 2 Pravin Internal Updates** | (Proton links in Signal May 20, 22) | MVP fallback + R&D lane experiments + cymatic water field work — earlier Phase 2 work |

**Workflow tip per Pravin's preference** (May 22 14:19): *"I'll continue to work through google drive."* — when you can't preview on Proton, fall back to Google. The May 22 packet IS mirrored to Google in the `02_Autolume_4K_Sweep_5_Variants` / `01_Autolume_4K_Wild_30s` folders under `1xP0dzNpibCJet…`.

---

## What's NOT yet on a Drive Pravin can navigate

These all need upload (operator action tonight or tomorrow AM):

1. `H1_salmon_school_4k_lanczos.mp4` (319 MB) → Google
2. `autolume_baseline_22min_4k_lanczos.mp4` (7.9 GB) → Google (slow upload; consider re-encode to CRF 23 first to halve size to ~4 GB)
3. H2-H8 4K lanczos clips (firing now; will land ~22:00-22:45 PDT) → Google
4. `Briony-Penn-Archive-for-Pravin-2026-05-23.zip` (91 MB) → Google
5. **May 20 Proton packet contents** (coastline footage + H6 4K + Moonfish salmon school 4K) → Google. Pravin's Proton preview was broken; mirroring solves it.

---

## Show logistics summary

| Date | What |
|---|---|
| **Sun May 24** (tomorrow) | Operator at Pravin's all day, in-person walk-through, compose 20-min loop, finalize all hero clips. Maybe retry ESRGAN if pods cooperate. |
| **Mon May 25 — first ferry AM** | Operator + Pravin travel YVR together |
| **Mon May 25 3pm** | Both at HRMSC Hubble Lounge with tech folks. Carol Anne booked Airbnb Mon-night YVR. |
| **Mon May 25 night** | Operator sleeping at the Airbnb |
| **Tue May 26 10pm-midnight** | Backup install window if Mon doesn't finish |
| **Wed May 27** | IMPACT opens AM |
| **Wed May 27 + Thu May 28** | IMPACT runs |

---

## Open coordination items

- [ ] Mehul + Clare attending IMPACT — Pravin: "They should!". Needs operator follow-through (logistics, VIP, etc.)
- [ ] Austin check-in (Pravin wanted Friday; slipped — Sunday or Monday?)
- [ ] Ari's talk notes for Pravin (Pravin asked operator to take notes; operator at talk now)
- [ ] Dixy live-footage handoff (Indigenomics + M37 socials featuring Darren/Austin/Matt/Pravin) — will fall out of Pravin's Saturday performance recording
- [ ] Dome short for Dan Tell — separate workstream, Pravin in flight, mastering Monday
- [ ] NVIDIA server pitch this week (Pravin's GPU meeting play) — not your immediate action
- [ ] Pravin's mum (ER visit May 21) — emotional context overlay

---

## What I (operator's Claude assistant) am doing autonomously while operator is at Pravin's

- H2-H8 4K lanczos (firing now serial, ~30-60 min total)
- Monitor any signal of pod 1 or pod 2 recovering (would let us retry ESRGAN)
- Hold the queued status Signal draft for Pravin (variant + 7 S salmon question)
- Stay ready to fire Bob Turner scrape retry with Safari cookies once IP block lifts
