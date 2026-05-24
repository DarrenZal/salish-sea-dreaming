# Bob Turner — Priority Theme Subclip Cut List

**Source:** Chapter markers (5 videos) + auto-captions (3 unchaptered) + Bob's annotated docx.
**Built:** 2026-05-23 morning, while 3090 was offline + before scrape kicked off.
**Purpose:** When source files land (after the scrape, ~2-4h pull), go straight to `ffmpeg -ss …` cuts. No scrub-under-pressure on Saturday.

## How to read this

- ⭐ = Pravin's explicit ask / Bob's flagged hero moment
- HH:MM:SS = source video timestamp
- "Skip" = section of source video to omit from theme cuts
- "Blend candidate" = neighboring clip that should cross-dissolve smoothly with next

---

## Theme 1 · Humpback whale surface activity ✅ STRONGEST COVERAGE

### Source A — XvCuL-coVOM (17:45, **native 4K** ⭐ no upscale needed)
*"Humpback Comeback - The Return of Humpback Whales to the Salish Sea"*

| In | Out | Chapter | Use | Notes |
|----|-----|---------|-----|-------|
| 1:04 | 3:28 | Whales in the Bay | YES | "Three young whales, playing in the bay" per description — close-up surface play |
| 3:28 | 6:48 | The Humpback Comeback | MAYBE | Likely narrative/historical. Visual TBC; may have museum footage. Watch first. |
| 6:48 | 9:24 | Tidal Rapids | YES | Tidal current + whale interaction. Visual interest. |
| **9:24** | **17:45** | **Herring Feeding** | ⭐⭐ HERO OF HEROES | Bob's own description: "feed on surface schools of herring using lunges, traps and other acrobatics." This 8-min segment is the Priority One asset. |

**Recommended cut sequence (theme 1 spine):**
1. 1:04 → 2:30 (whales playing, intimate)
2. 6:48 → 8:30 (tidal rapids interaction)
3. 9:24 → 17:00 (herring feeding hero — sustain)

### Source B — AmIpFWfjS2I (12:09, 1080p)
*"The Return of Humpbacks - Howe Sound/Atl'ka7tsem"*

| In | Out | Chapter | Use | Notes |
|----|-----|---------|-----|-------|
| 0:00 | 3:08 | Introduction | Skip | Likely talking head intro |
| 3:08 | 4:19 | Hot Island | MAYBE | Unknown content — depends on visual |
| **4:19** | **6:29** | **Humpback** | ⭐ YES | Direct close-up, named after chapter |
| 6:29 | 7:18 | Glaciers | Skip | Landscape, off-theme |
| **7:18** | **10:21** | **Yogi** | ⭐ YES | Named individual whale — intimate, ~3 min |
| 10:21 | 12:09 | Conclusion | Skip | |

**Use as supplement to A.** Source A's 4K + 8-min hero segment is the primary; B adds intimate close-ups if more material needed.

---

## Theme 2 · Orca hunts and closeups ✅ RESOLVED — ACCEPT 1080p + UPSCALE

**Pravin 2026-05-23 ~12:05 PDT (Signal):** *"Orca there is an entire video about an Orca Hunt — I believe included some key moments however there are lots in there. just try to get it higher res and cool in terms of the spatial dynamics... I may overlay effect like Edge on it via resolume."*

Decision: accept the 1080p source, upscale to 4K via Real-ESRGAN x4plus, focus selection on **spatial-dynamics moments** (the boat-side encounter + close approaches where motion through the frame is most legible). Pravin will Edge-effect in Resolume — that further hides any residual upscale softness.

### Source — 3NCuLawvQaE (11:14, 1080p)
*"Orcas on the Hunt! Howe Sound"* — Bob's "low res" caveat was relative self-criticism, source is 1080p HD.

Auto-caption timeline (paraphrased from Bob's voiceover):

| In | Out | Visual content (inferred from captions) | Use |
|----|-----|------|-----|
| 0:00 | 1:00 | Outdoor school intro setup | Skip (talking head) |
| **1:00** | **2:30** | "Tail flippers… sea lion is vertical, standing on…" — **the actual attack moment** | ⭐ HERO |
| **2:30** | **4:30** | Boat encounter: "sea lion coming right at me, right there at the side of my boat… I'm doing 360s in the boat… buffeted by all these pressure waves" | ⭐ HERO (intimate) |
| 5:00 | 5:30 | [Music interlude, transition] | Maybe (transition shot) |
| **5:30** | **7:00** | Orca identification: T99 and three offspring (named matriarch + family) | YES (close-up dorsals) |
| 7:00 | 8:00 | Migration context: spotted off Pender Gulf Islands 200km away next day | Skip (talking head) |
| **9:30** | **10:30** | "I look out and realize the orcas… exhausted" — close approach to boat | YES |
| 10:30 | 11:14 | Music/wrap | Maybe (musical tail) |

**Recommended cut sequence:**
1. 1:00 → 2:30 (attack moment)
2. 2:30 → 4:30 (boat-side encounter)
3. 5:30 → 7:00 (identified individuals)
4. 9:30 → 10:30 (close approach)

**Total hero material: ~5:30 from this single source.** Combined with rhythmic music + atmospheric blending, can sustain a ~3-4 min orca theme sequence.

**Upscale strategy:** Real-ESRGAN x2plus → 4K via H200. Bob's "low resolution" was likely self-critical; 1080p source upscales cleanly.

---

## Theme 3 · Human impact ✅ EXPANDED — 3 sources, ferry + harbour + ship traffic now covered

**Pravin 2026-05-23 ~12:08 PDT (Signal):** *"Human impact: there is tons of footage ferries / freighters / harbour / cargo in the videos — they are short but well shot clips."*

Confirmed via auto-caption scan: 3 of Bob's videos contain embedded ferry/harbour/ship-traffic moments. Theme upgraded from fishery-only to a full industrial spectrum.

### Source A — 6EzO5wugg4Y (10:40, 1080p) — "Herring Roe Fishery, Strait of Georgia 2020"

Expanded timeline (re-scanned with captions):

| In | Out | Visual content | Use |
|----|-----|------|-----|
| 0:00 | 0:55 | Herring ecology intro | Skip (narration) |
| 0:55 | 1:00 | "herring 2 are a foundation of our industrial fisheries" | Maybe (text card moment) |
| **2:53** | **3:08** | **"whoa I better get going so half an hour later I'm on the next ferry to Denman"** | ⭐ FERRY HERO (Pravin's ask) |
| **3:08** | **3:30** | "along the Denman shore the fishing fleet far ahead of me" — **fleet visible from ferry** | ⭐ HERO continuation |
| **3:58** | **4:30** | "after about half an hour I reached the southern end of the fleet" — arrival at fleet | ⭐ HERO |
| **4:30** | **5:00** | "binoculars out and take a look at the fleet I prop myself on a rock" — fleet vista | ⭐ HERO |
| **5:00** | **6:00** | "I watch one boat lay out its net" — net deployment | ⭐ HERO |
| **5:35** | **6:15** | "all around the fleet the ocean is alive with wheeling gulls" — peak action | ⭐ HERO (gulls overlap with T5 birds!) |
| 6:15 | 7:00 | Nets being hauled in | YES |
| 7:30 | 8:30 | Consequence narrative (ground into fishmeal) | YES (contemplative) |
| **9:04** | **9:30** | **"a few hours later I ponder it all from a ferry heading back to Hornby"** | ⭐ FERRY HERO (return leg) |
| 9:30 | 10:40 | Final hope / music | Maybe (musical tail) |

**Cut sequence (departure → industrial peak → consequence → return):**
1. 2:53 → 3:30 (ferry out, fleet sighted) — NEW CUT
2. 3:58 → 5:00 (arrival, scale)
3. 5:00 → 7:00 (extraction in motion)
4. 7:30 → 8:30 (consequence)
5. 9:04 → 9:30 (ferry home) — NEW CUT

### Source B — pg3SPTI0A28 (9:26, 1080p) — "HERRING: Why Kill the Foundation" 🆕 PROMOTED FROM EXTRAS

Caption-driven scan reveals strong harbour + boat-harbour content:

| In | Out | Visual content | Use |
|----|-----|------|-----|
| 0:00 | 1:00 | Intro: "commercial fishery every March" | Maybe (establish) |
| 1:22 | 1:50 | Looking for herring spawn | Skip |
| **1:59** | **2:30** | **"I get to French Creek boat harbour"** | ⭐ HARBOUR HERO (Pravin's ask) |
| 2:30 | 4:00 | Investigates | Maybe |
| **4:33** | **5:00** | **"I head for the harbour mode"** | ⭐ HARBOUR HERO |
| **5:04** | **5:30** | **"net fleet I watched the boats come in"** | ⭐ HARBOUR + BOATS HERO |
| 5:30 | 6:30 | Narrative on fishery management | Skip |
| 6:30 | 8:30 | Closing arguments / data | Skip |
| 8:30 | 9:26 | Music tail | Maybe |

**Cut sequence (harbour-focused supplement to Source A's fleet scene):**
1. 1:59 → 2:30 (French Creek boat harbour arrival)
2. 4:33 → 5:30 (harbour + boats coming in)

### Source C — oneCVfKdI9I (12:31, 1080p) — "The Extraordinary Salish Sea"

Single embedded shipping-traffic beat per caption scan:

| In | Out | Visual content | Use |
|----|-----|------|-----|
| **10:35** | **11:00** | **"this big population is growing fast and so is industry ship traffic"** | ⭐ CARGO/SHIPPING HERO |

**Cut: 10:35 → 11:00** — likely shows shipping lanes, freighter shots, or harbour-traffic time-lapse. Worth pulling and watching first before locking in.

### Total expanded T3 material: ~7-8 min across 3 sources

Coverage now spans the full Pravin brief: ferry transit (Source A 2:53, 9:04), commercial fishery (Source A 3:58-7:00), industrial harbour with moored boats (Source B 1:59-5:30), cargo/shipping traffic (Source C 10:35).

---

## Theme 4 · Intertidal life ⭐ STRONG MATCH

### Source — F2LRC7mMres (9:39, 1080p)
*"Tide Pool! Atl'ka7tsem/Howe Sound"* — "My hour-long float in a big tidepool reveals a world of tiny wonders."

| In | Out | Chapter | Use | Notes |
|----|-----|---------|-----|-------|
| 0:00 | 2:18 | <Untitled 1> | Maybe | Likely setup / arrival |
| **2:18** | **4:23** | **Purple Sea Stars** | ⭐⭐ HERO | Direct match to Pravin's "sea stars close-up / ultra close-up" |
| 4:23 | 5:37 | Green Sea Urchin | YES | Bonus species (urchin not in Pravin's list but contextually fits) |
| **5:37** | **6:12** | **Sea Slug** | ⭐⭐ HERO | Direct match to Pravin's "sea slugs" ask |
| 6:12 | 6:52 | Sea Stars | YES | Additional star material |
| **6:52** | **9:39** | **Purple Sea Star** | ⭐ HERO (long form) | Sustained sea star content — ~2:45 |

**Recommended cut sequence (life-tour through tidepool):**
1. 2:18 → 4:23 (purple sea stars, ~2:00)
2. 4:23 → 5:37 (urchin transition, ~1:15)
3. 5:37 → 6:12 (sea slug, ~0:35)
4. 6:52 → 9:39 (sustained purple star, ~2:45)

**Total: ~6:30 of hero material.** Strongest match in the entire catalog to Pravin's brief — sea-stars + sea-slug both explicitly delivered.

---

## Theme 5 · Birds ✅ EXPANDED — 3 sources, rich species variety

**Pravin 2026-05-23 ~12:08 PDT (Signal):** *"Birds: there are seagulls. → all noted in the excel spread sheet. you can supplement as well however Bob does have a good eye."*

Confirmed via caption scan: Bob's videos contain rich bird content beyond just the standalone snow geese video. Eagles, gulls, mergansers, herons appear across multiple videos.

### Source A — XJ4WyRy0oQg (11:01, 1080p) — Snow geese (primary)
*"Snow Geese! Fraser and Skagit River deltas, Salish Sea"*

| In | Out | Chapter | Use | Notes |
|----|-----|---------|-----|-------|
| 0:11 | 0:49 | Snow Geese | YES | Species intro |
| **5:21** | **11:01** | **Abundant Winter Food** | ⭐ HERO | 5:40 of feeding flocks |
| **9:17** | **9:30** | **Dramatic liftoff** | ⭐⭐ HERO MOMENT | Bob's docx flagged |

**Cut sequence:**
1. 0:11 → 0:49 (species intro)
2. 5:21 → 9:17 (feeding flocks)
3. 9:17 → 9:30 ⭐ (dramatic liftoff)

### Source B — oneCVfKdI9I (12:31, 1080p) — Dunlin fragment
*"The Extraordinary Salish Sea"*

| In | Out | Content | Use |
|----|-----|---------|-----|
| **6:02** | **6:16** | **Dunlin murmuration** | ⭐ HERO (Bob's docx annotation) |

### Source C — V4dMyHzz_80 (9:20, 1080p) 🆕 PROMOTED FROM HERRING SECTION
*"Herring Spawn! Serengeti of the Sea"* — bird-rich beyond just herring

Caption-driven scan reveals strong eagle / gull / heron / merganser content within the herring spawn footage:

| In | Out | Bird content | Use |
|----|-----|------|-----|
| **3:13** | **3:45** | **"then an eagle… bathed in a level of animal energy"** | ⭐ EAGLE HERO |
| **5:20** | **5:45** | **"I see a gull dive in and come up with a heron"** | ⭐ GULL + HERON HERO |
| **6:11** | **6:30** | **"there are also fleets of merganser another fish eating duck"** | ⭐ MERGANSER HERO |
| **7:07** | **7:30** | **"sea lions approach and the eagle moves on"** | YES (multi-species interaction) |
| **7:40** | **8:00** | **"many of the gulls have settled on the shore, a heron heading off"** | ⭐ GULLS + HERON HERO |

**Cut sequence (multi-species feeding spectacle):**
1. 3:13 → 3:45 (eagle)
2. 5:20 → 5:45 (gull-heron interaction)
3. 6:11 → 6:30 (merganser flock)
4. 7:40 → 8:00 (gulls + heron at shore)

### Total expanded T5 material: ~9 min across 3 sources, 6+ species (snow goose, dunlin, eagle, gull, heron, merganser)

---

## Assembly notes (for Pravin's rhythmic / atmospheric blend)

Pravin's email: *"composite clips blended together rhythmically and atmospherically — avoiding hard jump cuts wherever possible."*

Cross-dissolve / atmospheric blending candidates within themes:

- **Theme 1 humpback:** XvCuL-coVOM 9:24 herring feeding → AmIpFWfjS2I 4:19 close-up *(cross-fade through water surface)*
- **Theme 2 orca:** 1:00 attack → 2:30 boat-side → 5:30 family identification → 9:30 close approach. Each cut is *time-progressed* in Bob's storyline; blends naturally chronologically.
- **Theme 4 intertidal:** Cuts within F2LRC7mMres are already adjacent — minimal blending needed. Color-bias correction may help (kelp green / tidepool blue → unified palette).
- **Theme 5 birds:** Snow geese feeding → liftoff is a natural visual rhythm peak; the dunlin fragment is a totally different register and should be its own beat.

**Recommendation:** assemble per-theme sequences at 1080p first (Source B humpback + all others), then upscale the final mixed sequences once to 4K via H200 — uses upscale compute most efficiently. The native-4K XvCuL-coVOM hero stays at native 4K throughout.

---

## ffmpeg cut commands (ready to execute when sources land)

```bash
SRC=/Users/darrenzal/projects/salish-sea-dreaming/bob-turner-corpus
OUT=/Users/darrenzal/projects/salish-sea-dreaming/bob-turner-cuts
mkdir -p "$OUT"/{01_humpback,02_orca,03_human_impact,04_intertidal,05_birds}

# THEME 1 — Humpback hero (4K source, no transcode)
ffmpeg -ss 00:09:24 -i "$SRC/01_humpback/humpback_hero_4k__XvCuL-coVOM.mp4" \
  -t 00:07:36 -c copy "$OUT/01_humpback/01_herring_feeding_hero.mp4"
ffmpeg -ss 00:01:04 -i "$SRC/01_humpback/humpback_hero_4k__XvCuL-coVOM.mp4" \
  -t 00:01:26 -c copy "$OUT/01_humpback/02_whales_in_the_bay.mp4"
ffmpeg -ss 00:06:48 -i "$SRC/01_humpback/humpback_hero_4k__XvCuL-coVOM.mp4" \
  -t 00:02:36 -c copy "$OUT/01_humpback/03_tidal_rapids.mp4"
ffmpeg -ss 00:04:19 -i "$SRC/01_humpback/howe_sound_humpbacks__AmIpFWfjS2I.mp4" \
  -t 00:02:10 -c copy "$OUT/01_humpback/04_humpback_chapter.mp4"
ffmpeg -ss 00:07:18 -i "$SRC/01_humpback/howe_sound_humpbacks__AmIpFWfjS2I.mp4" \
  -t 00:03:03 -c copy "$OUT/01_humpback/05_yogi.mp4"

# THEME 2 — Orca (4 cuts from single source)
ffmpeg -ss 00:01:00 -i "$SRC/02_orca/orca_sea_lion_howe_sound__3NCuLawvQaE.mp4" \
  -t 00:01:30 -c copy "$OUT/02_orca/01_attack_moment.mp4"
ffmpeg -ss 00:02:30 -i "$SRC/02_orca/orca_sea_lion_howe_sound__3NCuLawvQaE.mp4" \
  -t 00:02:00 -c copy "$OUT/02_orca/02_boat_side_encounter.mp4"
ffmpeg -ss 00:05:30 -i "$SRC/02_orca/orca_sea_lion_howe_sound__3NCuLawvQaE.mp4" \
  -t 00:01:30 -c copy "$OUT/02_orca/03_t99_family.mp4"
ffmpeg -ss 00:09:30 -i "$SRC/02_orca/orca_sea_lion_howe_sound__3NCuLawvQaE.mp4" \
  -t 00:01:00 -c copy "$OUT/02_orca/04_close_approach.mp4"

# THEME 3 — Human impact / fishery (3-cut arc)
ffmpeg -ss 00:04:00 -i "$SRC/03_human_impact/herring_roe_gill_net_fishery__6EzO5wugg4Y.mp4" \
  -t 00:01:00 -c copy "$OUT/03_human_impact/01_fleet_arrives.mp4"
ffmpeg -ss 00:05:00 -i "$SRC/03_human_impact/herring_roe_gill_net_fishery__6EzO5wugg4Y.mp4" \
  -t 00:02:00 -c copy "$OUT/03_human_impact/02_nets_in_motion.mp4"
ffmpeg -ss 00:07:30 -i "$SRC/03_human_impact/herring_roe_gill_net_fishery__6EzO5wugg4Y.mp4" \
  -t 00:01:00 -c copy "$OUT/03_human_impact/03_consequence.mp4"

# THEME 4 — Intertidal (chapter-aligned, 4 cuts)
ffmpeg -ss 00:02:18 -i "$SRC/04_intertidal/tide_pool_atlkatsem__F2LRC7mMres.mp4" \
  -t 00:02:05 -c copy "$OUT/04_intertidal/01_purple_sea_stars.mp4"
ffmpeg -ss 00:04:23 -i "$SRC/04_intertidal/tide_pool_atlkatsem__F2LRC7mMres.mp4" \
  -t 00:01:14 -c copy "$OUT/04_intertidal/02_green_sea_urchin.mp4"
ffmpeg -ss 00:05:37 -i "$SRC/04_intertidal/tide_pool_atlkatsem__F2LRC7mMres.mp4" \
  -t 00:00:35 -c copy "$OUT/04_intertidal/03_sea_slug.mp4"
ffmpeg -ss 00:06:52 -i "$SRC/04_intertidal/tide_pool_atlkatsem__F2LRC7mMres.mp4" \
  -t 00:02:47 -c copy "$OUT/04_intertidal/04_purple_sea_star_long.mp4"

# THEME 5 — Birds (2 sources)
ffmpeg -ss 00:00:11 -i "$SRC/05_birds/snow_geese_fraser_skagit__XJ4WyRy0oQg.mp4" \
  -t 00:00:38 -c copy "$OUT/05_birds/01_snow_geese_intro.mp4"
ffmpeg -ss 00:05:21 -i "$SRC/05_birds/snow_geese_fraser_skagit__XJ4WyRy0oQg.mp4" \
  -t 00:03:56 -c copy "$OUT/05_birds/02_winter_food_flocks.mp4"
ffmpeg -ss 00:09:17 -i "$SRC/05_birds/snow_geese_fraser_skagit__XJ4WyRy0oQg.mp4" \
  -t 00:00:13 -c copy "$OUT/05_birds/03_dramatic_liftoff_HERO.mp4"
ffmpeg -ss 00:06:02 -i "$SRC/05_birds/extraordinary_salish_sea_full__oneCVfKdI9I.mp4" \
  -t 00:00:14 -c copy "$OUT/05_birds/04_dunlin_murmuration.mp4"
```

**Total subclips: 20.** Total cut material across themes: ~33 min from 196 min source (17% selection ratio — well above the rough "1 minute of hero per 10 minutes of source" rule of thumb for nature footage).

## Open questions — RESOLVED

(From the variant Signal sent 11:18am)

1. ~~Orca: 1 clip only, Bob flagged as low-res.~~ ✅ **RESOLVED 2026-05-23 ~12:05 PDT** — accept 1080p + upscale + Pravin Edge-effect in Resolume. Focus on spatial dynamics.
2. ~~Human impact: 0 ferries / freighters / harbour.~~ ✅ **RESOLVED 2026-05-23 ~12:08 PDT** — Pravin: "tons of footage in the videos, short but well shot." Re-scan via captions surfaced 3 sources with ferry (Source A 2:53, 9:04), boat harbour (Source B 1:59, 4:33-5:30), ship traffic (Source C 10:35).
3. Intertidal: strong coverage, no gap. Still no formal Pravin OK on this theme but the brief is exactly delivered.
4. ~~Birds: 1 standalone + 1 fragment.~~ ✅ **RESOLVED 2026-05-23 ~12:08 PDT** — Pravin: "seagulls all noted in the excel spread sheet; supplement as well however Bob does have a good eye." Caption scan added Source C `V4dMyHzz_80` with eagles, gulls, mergansers, heron across 4:30 of bird-rich content.

## Supplemental sourcing — GREENLIT WITH CONSTRAINT

**Pravin 2026-05-23 ~12:08 PDT:** *"you could source supplemental as well we just need to be aware of copyright and usage."*

If after pulling Bob's videos the thematic sequences need more material, supplement from CC-licensed / public-domain sources only:
- **iNaturalist** (with `license` filter for CC0 / CC-BY / CC-BY-SA) — already proven path via `tools/scrape_inaturalist_guide.py`
- **NOAA / NPS** — public domain, often has shipping-lane and harbour footage
- **Wikimedia Commons** — per-file license verification required
- **Pexels / Pixabay** — CC0 video
- **Coast Salish or BC-specific archives** — verify license per source

**Rule:** every supplemental clip gets license + source URL logged in the cut list. No "found on Google" or YouTube downloads from non-Bob channels (those are presumed copyrighted unless explicit license).

## Updated theme totals

| Theme | Sources | Cut material | Coverage |
|-------|---------|-------------:|----------|
| 1 · Humpback | 2 (1 native 4K) | ~12 min | ⭐⭐ Strongest, 4K hero |
| 2 · Orca | 1 | ~5:30 | ✅ Resolved (accept + upscale + Resolume Edge) |
| 3 · Human impact | 3 (was 1) | ~7-8 min | ✅ Expanded — ferry/harbour/cargo now covered |
| 4 · Intertidal | 1 | ~6:30 | ⭐⭐ Direct brief match (sea stars + sea slug) |
| 5 · Birds | 3 (was 2) | ~9 min | ✅ Expanded — 6+ species |
| **Total** | **10 source videos** | **~40 min** | from 196 min source (20% selection ratio) |
