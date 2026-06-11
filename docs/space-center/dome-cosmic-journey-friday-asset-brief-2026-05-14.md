# Dome Cosmic Journey — Friday Asset Brief

Purpose: define the concept-quality visuals needed for Carol Anne's Friday 2026-05-15 AI presentation.

Status: internal production brief. These assets are for concept communication, not proof of full functionality.

Update from Kurt reply, 2026-05-13 evening: do not treat these as final Dome deliverables until Dan confirms native projection specs. Survey / polling / word-cloud support is Whova-backed on a standard screen; this package should frame survey-related visuals as concept atmosphere only unless Carol Anne requests otherwise.

## Source Direction

Meeting record direction:

- IMPACT 2026 Dome direction: knowledge graph "cosmic journey" through a 3D constellation.
- Indian Act economic survey: Whova-backed survey / polling / word-cloud on screen; not a custom SSD survey app or native Dome projection unless scope changes.
- Demo strategy: pre-recorded video is primary; live demo is backup if Space Centre Wi-Fi cooperates.

## Delivery Target

By Friday:

- 10 concept-quality visuals or GIFs
- clear titles embedded or paired in manifest
- coherent visual language across all 10
- no unapproved Austin / Coast Salish visual borrowing
- no claim that survey analytics are live or custom-built by SSD

Recommended output folder:

```text
output/dome-cosmic-journey-2026-05-15/
  00_manifest.md
  stills/
  gifs/
```

## Visual Set

| # | Title | Concept | Source / substrate |
|---:|---|---|---|
| 01 | Enter the Living Graph | audience enters a constellation of relationships | existing SSD graph |
| 02 | From Pearl to Constellation | Hubble pearl experience expands into Dome-scale graph | bridge visual, no Austin motifs |
| 03 | People, Places, Agreements | graph clusters around participants, venues, and commitments | KG node categories |
| 04 | Survey Becomes Signal | participation / polling appears as light in the graph | concept atmosphere, not Whova replacement |
| 05 | Questions Find Relations | survey questions connect to themes and evidence | concept |
| 06 | Voices in Orbit | interview / testimony material as orbiting paths | Donna Sound placeholder only if approved |
| 07 | Sovereign AI Layer | TELUS / sovereign model layer as computation field | technical partner visual |
| 08 | Economic Patterns Emerge | graph clusters reveal patterns without reducing them | analytics concept |
| 09 | Hubble Visitors Join the Field | visitor app offerings can become graph events | only if framed as optional/consented |
| 10 | IMPACT Constellation | closing title: one event arc, two rooms | Hubble + Dome integration |

## Style Rules

Use:

- dark Dome-safe background
- star / node / edge language
- slow camera drift or pulse
- clear large titles
- enough contrast for projection
- abstract color families distinct from the Hubble pearl/Austin layer

Avoid:

- Coast Salish formline, ovoids, U-forms, crescents, Thunderbird, pearl-teaching claims
- AI-generated Indigenous motifs
- survey UI screenshots unless the survey app exists
- "live" wording unless a live path has been tested
- any implication that SSD replaces Whova polling/survey/word-cloud
- dense text in Dome visuals

## Suggested Title Copy

Use short title-only copy on images. Put explanations in the presenter notes, not the Dome frame.

1. Enter the Living Graph
2. From Pearl to Constellation
3. People, Places, Agreements
4. Survey Becomes Signal
5. Questions Find Relations
6. Voices in Orbit
7. Sovereign AI Layer
8. Economic Patterns Emerge
9. Visitors Join the Field
10. IMPACT Constellation

## Asset Generator

A deterministic local generator is available:

```bash
python3 scripts/generate_dome_cosmic_journey_assets.py
```

It reads `static/ssd-data-map.json` and renders concept stills/GIFs into `output/dome-cosmic-journey-2026-05-15/`.

Generated package status:

- `output/dome-cosmic-journey-2026-05-15/00_manifest.md`
- `output/dome-cosmic-journey-2026-05-15/stills/` - 10 PNGs at 1920x1080
- `output/dome-cosmic-journey-2026-05-15/gifs/` - 10 GIFs at 960x540
- `output/dome-cosmic-journey-2026-05-15/contact_sheet.png` - quick visual review sheet
- `output/dome-cosmic-journey-2026-05-15.zip` - 23 MB handoff package, SHA256 `59e69436bbb29b1179cc428600c032cfb099dd20009fe23cd11fa7e6ab56269a`
- total package size: about 30 MB

Generator boundary:

- uses existing graph structure as visual substrate
- generates abstract constellation visuals only
- does not use Austin source imagery
- does not claim live survey functionality or replace Whova

## Presenter Framing

Suggested spoken frame:

> These are concept visuals for the IMPACT Dome direction: a knowledge graph as a cosmic journey. The pre-recorded assets show how interviews, people, places, commitments, and audience participation can become a navigable constellation. Whova owns survey / polling / word-cloud support; these visuals are not a custom survey system.

## Decision Still Needed

- Who owns final title wording: Carol Anne, Shawn, Darren, or Pravin?
- Can "survey" appear on slides, or should visuals say "participation" / "audience signal" because Whova owns the actual survey tool?
- Is Donna Sound named in Friday materials, or kept as "interview voices" until approved?
- What Dome aspect/resolution does Dan require?
