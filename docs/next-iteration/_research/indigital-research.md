# INDIGITAL — Research Dossier

> Single source of truth for the Austin Harry / INDIGITAL collaboration brief, scraper input list, and roadmap citations. Compiled 2026-05-04 from in-session research (WebFetch + WebSearch). Verify against live pages before any external use.

---

## Artist Identity

| Field | Value |
|---|---|
| Name | Austin Aan'yas Harry (also seen "Austin B. Harry") |
| Studio | INDIGITAL (Indigital Design) |
| Location | Vancouver, BC |
| Tagline | "Modern design anchored in ancient culture" |
| Mission | "Bring traditional Coast Salish heritage and culture to a modern audience through digital media" |
| Email | austin@indigitaldesign.ca |
| Phone | (778) 994-9464 |
| Hours | Mon–Fri 10am–8pm |

**Cultural lineage:**

- Wolf Clan, **Sḵwx̱wú7mesh** (Squamish Nation)
- Thunderbird Clan, **Nam̓gis Nation** (Kwakwaka'wakw, northern Vancouver Island)

**Tools in stack:** Autodesk Maya, ZBrush, Substance Painter, 3D printing (used at Banff Centre residency), digital compositing. Game-industry background. **No public mention of TouchDesigner / Unreal / Unity / AR.**

---

## Family Lineage

```
Xwalacktun (Rick Harry, O.B.C.) — master Coast Salish carver, lifetime achievement award recipient
   ├── Austin Aan'yas Harry      — INDIGITAL (digital / 3D / formline)
   └── James Harry                — sculptor (jamesharry.ca)

KwiKwi Collaborations = Austin + James + Lauren Brevner (painter, laurenbrevner.com)
```

**Three-generation exhibition:** "Balanced Forms: Xwalacktun, James Harry, and Austin Harry" at the West Vancouver Art Museum.

---

## Pages to Scrape (input for `tools/scrape_indigital.py`)

All on `https://www.indigitaldesign.ca/`:

| Slug for folder | Page path |
|---|---|
| `studio-home` | `/` |
| `about` | `/about` |
| `media` | `/media` |
| `portfolio-index` | `/portfolio` |
| `salish-spirit` | `/portfolio/project-salishspirit` |
| `whitecaps` | `/portfolio/whitecaps-fc-indigenous-celebration-game` |
| `arcteryx` | `/portfolio/arcteryx` |
| `mst-justice-centre` | `/portfolio/project-one-ephnc-ml4je` |
| `vch` | `/portfolio/vancouver-coastal-health` |
| `westridge-elementary` | `/portfolio/westridge-elementary-school` |
| `nelson-elementary` | `/portfolio/nelson-elementary` |
| `cheeilth-marvel` | `/portfolio/cheeilth` |
| `kalkalilh-banff` | `/portfolio/kalkalilh-banff-centre-residency` |
| `kwikwi` | `/portfolio/kwikwi-projects` |

CDN host for image assets: `images.squarespace-cdn.com/content/v1/649b573464526506c600f7f1/`. Append `?format=2500w` for highest practical resolution.

---

## Project Catalogue

| Project | Year | Medium | One-line |
|---|---|---|---|
| **Salish Spirit at VanLive!** | 2024 | LED screen, 3D Thunderbird composited over Vancouver footage | City of Vancouver Public Art commission, Robson/Granville screen, Jan 1–Feb 26 2024, 10-month production with Jonas Jones; closest precedent to SSD |
| **Whitecaps FC Indigenous Celebration Game** | — | Logo / kit / scarf | Two-Headed Serpent (Sínulhka) reimagining of Whitecaps mark; jersey + scarf merchandise |
| **Arc'teryx Indigenous Métis Inuit Belonging Council** | — | Brand identity | Raven-in-transformation carrying sun, medicine wheel, North Shore connection |
| **MST Indigenous Justice Centre** | — | Architectural artwork | Downtown Vancouver; Thunderbird House Post + plant-medicine icons; co-installed with Musqueam + Tsleil-Waututh artists |
| **Vancouver Coastal Health (VGH)** | — | Vinyl wall murals (×5) | Soar (Burn Ward), Spirit, Care, Calm, Acute Care Thunderbird Talking Stick |
| **Westridge Elementary** | 2024 | Mural + 2-day workshops | Burnaby; Bobcat / Orca / Spukwus crests; teaching Coast Salish design to kids |
| **Nelson Elementary** | — | Logo redesign | Burnaby; Nighthawk crest |
| **Chee'ilth (Marvel Contest of Champions)** | — | Game character design | "First truly Coast Salish superhero" with Kabam Games + Squamish Lil'wat Cultural Centre; tattoo designs, Guardian Spirits (Bear, Eagle), axe with Salish Eyes |
| **Kalkalilh — Banff Centre Residency** | — | 3D sculpture + animation | Akunumusǂitis: Ecological Engagement Through The Seasons; Coast Salish "child-eating old woman" cautionary tale rendered in 3D print |
| **KwiKwi Collaborations** | ongoing | Public-space art | Partnership with brother James Harry + Lauren Brevner |
| **Spirit Shell TTRPG** | in dev | Tabletop RPG | Listed on `/media` — Coast Salish TTRPG |

Permanent installation: a 3D-printed **Sínulhka** (two-headed serpent) at Vancouver International Airport.

---

## URL Inventory (Squarespace CDN)

> ~70 unique image URLs across 11 portfolio pages. The scraper re-parses pages live (don't trust this list as a stale URL set). Listed here for sanity-check during dry-run.

**Studio identity (homepage / portfolio index)**
- `Indigital_HorizontalText.png` (`/8bc077ab.../`)
- `Indigital_HorizontalIcon.png` (`/e937f726.../`)
- `WebsiteBanner_Transparent.png` (`/190ec6fc.../`)
- `Thunderbird_Kamloops.jpg` (`/ba4c2d5d.../`)
- Hero/promo: `20231123_145554.jpg` (`/1705731892368.../`), `4ft2mm_Unceded_04.png` (`/1705769906516.../`)

**About**
- `AboutImage.jpg` (`/5917c678.../`) — Austin portrait

**Salish Spirit (most-relevant precedent)** — page is image-light; pull from page + go to YouTube reel
- `RobsonLive_SalishSpirit_01.jpg` (`/1705906503541.../`)
- `Spirit_Installed.jpg` (`/add271c5.../`)
- YouTube reel: `https://youtu.be/ZRs-4Ocm7r8`

**Whitecaps FC** (~12 URLs)
- `Text_Logo_WhiteOutline@3x.png` (`/5b35dcc2.../`)
- `drxir5hsxdknk7faodua.jpg` (`/bacc94df.../`)
- `image_WFC2416x9scarfindigenous.jpg` (`/71e30107.../`)
- (additional jersey + scarf + crest variants)

**Arc'teryx** (~10 URLs)
- `TitlePage` (`/a43c5e44.../`)
- `ArcTeryx_Logo` (`/49b15f7c.../`)
- `Concept_Transformation` (`/1192c32e.../`)
- `MedicineWheel` (`/27f544a7.../`)
- `Raven_Wheel` (`/f6071738.../`)

**MST Justice Centre** (~8 URLs) — plant-medicine icon set
- `RedCedar` (`/88d0fc98.../`)
- `StingingNettle` (`/99cc60fa.../`)
- `Wapato` (`/0674b0a9.../`)
- `ChocolateLillies` (`/00d8a9fb.../`)

**Vancouver Coastal Health** (~6 URLs)
- `Soar_Installed` (`/cd69e047/21591e09.../`)
- `EagleCaretaker_Monotone_Egg` (`/f4b46171.../`)
- `Spirit_Installed` (`/529a2f12.../`)
- `Care_Installed` (`/340aae43.../`)
- `AccuteCare_Paralax` (`/94e6d753.../`)

**Westridge Elementary** (~10 URLs)
- `Bobcat_TwilightFog` (`/5709d73e.../`)
- `Orca` (`/ade4390f.../`)
- `Spukwus_Summer_Crest` (`/4ac019ee.../`)

**Nelson Elementary** (~11 URLs) — full Nighthawk logo system breakdown

**Chee'ilth Marvel** (~7 URLs) — tattoo + Guardian Spirit designs

**Kalkalilh Banff** (~7 URLs) — 3D-print drafts + final + wall print

**KwiKwi** — page is image-light; one hero `Screenshot_2.png` (`/c07da421.../`); go to Instagram for more

**Total expected: ~70 unique image URLs.** Sanity-check threshold for dry-run: ≥50, ≤120.

---

## External Sources & Citations

| Source | Use |
|---|---|
| `https://www.indigitaldesign.ca/about` | Primary bio, mission, lineage, tools |
| `https://www.indigitaldesign.ca/portfolio/*` | Project descriptions verbatim |
| `https://en.wikipedia.org/wiki/Xwalacktun` | Father's lineage, awards |
| `https://www.squamishchief.com/in-the-community/squamish-nation-family-passing-down-stories-through-art-3348433` | Family / lineage feature |
| `https://www.squamishchief.com/local-arts/putting-coast-salish-art-on-the-map-globally-5482882` | Austin's broader practice |
| `https://www.squamishchief.com/local-news/i-just-do-the-work-renowned-artist-xwalacktun-receives-prestigious-lifetime-achievement-award-7668548` | Father's lifetime achievement award |
| `https://granvilleisland.com/news/artist-xwalacktun-obc-born-rick-harry-national-indigenous-peoples-history-month` | Father feature |
| `https://westvancouverartmuseum.ca/exhibitions/balanced-forms-xwalacktun-james-harry-and-austin-harry` | Three-generation exhibition |
| `https://preview-art.com/highlight/balanced-forms-xwalacktun-james-harry-austin-harry/` | Balanced Forms gallery review |
| `https://ourcityourart.wordpress.com/2024/01/05/platforms-nine-places-for-seeing-austin-harry-jonas-jones-artworks-installed/` | Salish Spirit / VanLive! installation context |
| `https://vancouver.ca/parks-recreation-culture/platforms-nine-places-for-seeing.aspx` | City of Vancouver Public Art Board program |
| `https://www.vch.ca/en/about-us/indigenous-health/indigenous-art-vancouver-coastal-health/indigenous-art-vancouver-general` | VGH installation context |
| `https://www.jamesharry.ca/` | Brother's practice |
| `https://www.laurenbrevner.com/` | KwiKwi collaborator |
| `https://www.instagram.com/indigital.design/` | Studio social |
| `https://www.instagram.com/austinbharry/` | Austin's personal social |
| `https://www.instagram.com/pechakuchavancouver/p/DAtnYnlydfn/` | PechaKucha Vancouver 2024 talk |
| `https://x.com/VGHFdn/status/1876740697790779685` | VGH Foundation thank-you |
| `https://youtu.be/ZRs-4Ocm7r8` | Salish Spirit motion reel |

---

## Style / Motif Inventory

**Recurring crests / animals:**
Thunderbird (Nam̓gis clan crest — appears repeatedly), Two-Headed Serpent / **Sínulhka** (signature, 3D-printed at YVR), Wolf, Eagle, Orca, Salmon, Bear, Hummingbird, Raven, Nighthawk, Bobcat, Spukwus.

**Plant medicines:** Red Cedar, Stinging Nettle, Wapato, Chocolate Lilies (MST Justice Centre series).

**Visual language:** Classical Coast Salish formline (trigons, crescents, ovoids, Salish eyes) rendered through vector / 3D / digital compositing rather than carved or painted. Symmetrical heraldic compositions (logos). Color palettes range from monochrome black/white-on-color crests to full-spectrum sky/sunset gradients (VGH "Spirit"). Production-grade clean line — closer to brand-system polish than gestural watercolor.

**Bridging concept** (Austin's own words, Kalkalilh page): bridging digital art and sculpture, character design and Coast Salish design, supernatural and natural worlds.

---

## SSD Species Library Overlap

The current SSD species/dreaming corpus already includes (per `project_gan_strategy.md` memory): salmon, herring, orca, whales, sea birds, cetaceans, intertidal life, kelp.

**Direct overlap with Austin's existing crest repertoire:** Orca, Salmon, Eagle, Bear, Hummingbird (Westridge + VGH installations).

**Concept hook:** Austin's crests as **togglable cultural-lens overlay** on iNat species — Western-science image + Coast Salish formline rendition of the same animal — directly maps to SSD's "three-eyed seeing" thesis (Western science + Indigenous knowledge + the land itself).

---

## Cultural Protocol — Items to Verify with Austin

These are open questions to raise on the first call. Do **not** assume.

1. **Which motifs are open vs ceremonial?** Sínulhka (two-headed serpent) — already public via YVR install, but is replication acceptable? Thunderbird is his clan crest; what's the protocol for AI-generated derivatives? Are there motifs entirely off-limits to AI training/img2img?
2. **AI training acceptability** — would Austin consent to a Briony-style LoRA fine-tune on his work? Or is direct compositing / IP-Adapter / img2img the only acceptable path?
3. **Attribution model** — credits, residual rights, revenue share if the work tours. Marvel/Kabam precedent (with Squamish Lil'wat Cultural Centre as cultural partner) is the template to mirror.
4. **Cultural-centre partnership** — should Squamish Lil'wat Cultural Centre be looped in as advisor for this collaboration, mirroring the Marvel precedent?
5. **Halact / Squamish elders** — Austin's relationship to Halact, who Prav named as Squamish-territory collaborator for MOVE37XR. Does Austin want a joint conversation or sequential intros?
6. **Family network** — interest in looping Xwalacktun (father) or James Harry (brother) into Phase 2 venues for tactile/sculptural counterpoint?

---

## Web / Press Context (collaboration-relevant signals)

- **Squamish Chief** has at least three feature articles on Austin / family — strong local journalist relationships exist; useful for any media plan around Indigenomics Impact / DEVCON.
- **West Vancouver Art Museum** — three-generation Balanced Forms exhibition establishes Austin in fine-art gallery context, not just commercial design.
- **City of Vancouver Public Art Board** — Austin is in their active public-art stable (Platforms: Nine Places for Seeing 2024).
- **PechaKucha Vancouver** — speaker in 2024.
- **VGH & UBC Hospital Foundation** has publicly thanked him on X.
- **Banff Centre Indigenous Arts** — Akunumusǂitis residency cohort.
- **Arc'teryx Backcountry Academy / Whistler Art Show** — listed Indigenous artist roster.
- **No public commission rate sheet.** No awards-list page on his own site.

---

## Collaboration-Relevant Observations

1. **Strongest conceptual bridge for the pitch:** Salish Spirit / VanLive! framing — "screens as windows into the supernatural" — is essentially a one-line cousin of SSD's "Salish Sea using technology to perceive itself." Lead with that.
2. **He has done one large-scale screen installation** (VanLive! Robson, 10-month production) but **not yet a generative / real-time / AI / interactive sensor piece.** SSD would be a step up in technical ambition for him; opportunity (he's likely hungry for it given the gaming background) and flag (timeline assumptions need to account for first-time tooling).
3. **Cultural protocol gravity is real.** The Marvel/Kabam project shows he's comfortable with high-profile commercial licensing, but always with a cultural-centre partnership (Squamish Lil'wat).
4. **Existing repertoire overlaps SSD species list almost perfectly** (Orca, Salmon, Eagle, Bear, Hummingbird) — cultural-lens overlay concept maps cleanly to "three-eyed seeing."
5. **Family network multiplier:** engaging Austin opens Xwalacktun + James Harry — relevant if Phase 2 wants tactile/sculptural counterpoint.
6. **Carol Anne / Indigenomics fit:** Austin's MST Justice Centre work means he has already collaborated under Sḵwx̱wú7mesh + Musqueam + Tsleil-Waututh shared-territory protocols on a marquee Vancouver project — directly relevant to Indigenomics Impact framing.
7. **Watch-outs:** No TD / Unreal / Unity / AR experience visible; pricing not public; runs solo (M–F 10–8) so capacity is bounded; one-page projects suggest the studio is < ~3 years old.

---

## Provenance

- Compiled: 2026-05-04 by Darren via in-session research agent (`general-purpose`) using WebFetch + WebSearch on the URLs listed under External Sources.
- Verification status: **NOT yet verified against live pages by Darren**. Verify before any external use of citations in `austin-collab-brief.md`.
- This file is intentionally not pruned — it carries more than the brief needs, so the brief can be terse while still being defensible.
