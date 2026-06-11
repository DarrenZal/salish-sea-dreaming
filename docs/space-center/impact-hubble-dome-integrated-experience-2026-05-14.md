# IMPACT Hubble + Dome Integrated Experience — 2026-05-14

Purpose: correct the Phase 2 framing around IMPACT 2026. The Hubble Space installation and the Dome cosmic journey are two surfaces in one event arc, not separate projects.

Status: working integration brief. Public language remains subject to Austin / Carol Anne / Pravin review.

Update from Kurt reply, 2026-05-13 evening: Dan is the Dome specifications lead for tomorrow's call. IMPACT survey / polling / word-cloud support is Whova-backed and projects to a standard screen, not the Dome projection. Treat custom survey intake and live analytic visualization as out of scope for SSD unless reopened after the Whova conversation next week.

## Corrected Event Shape

| Surface | Location | Date / window | Lead context | Primary content |
|---|---|---|---|---|
| Salish Sea Dreaming Phase 2 | Hubble Space | install May 22-24, doors May 25 | Pravin / Austin / Darren | triptych pearl installation, Austin-reviewed visual language, visitor app |
| Living Intelligence cosmic journey | Dome | IMPACT 2026, May 27-28 | Carol Anne / Shawn / Darren | knowledge graph constellation journey, concept Dome visuals, Donna Sound interview material if ready; survey support handled by Whova/screen |

Both surfaces are at HR MacMillan Space Centre. The integration question is real scope because the meeting record frames MOVE37XR and Indigenomics as integrated production contexts, not loosely affiliated partner orgs.

## One Experience, Two Rooms

The visitor should feel one arc:

1. **Hubble Space: enter the pearl.** The visitor encounters the Salish Sea through water, lineage, and live ecological signal. The visitor app collects a short offering / query and lets them explore the graph behind the installation.
2. **Between rooms: carry the thread.** The QR/app surface becomes the connective tissue. It can point visitors from the Hubble pearl to the Dome cosmic journey without requiring the Hubble show to explain the Dome.
3. **Dome: expand into constellation.** The same graph substrate opens at cosmic scale: relationships become stars, interview fragments become orbits, and Living Intelligence appears as a navigable field. Survey/polling support remains in Whova unless that scope changes.

This keeps the Hubble installation culturally specific and Austin-governed while letting the Dome carry the larger Living Intelligence / Indigenomics graph story.

## Visitor App Integration

Existing app facts:

- `web/visitor.html` already links to the dreamworld and knowledge graph.
- `scripts/gallery_server.py` already frames chat responses with markdown links into the graph.
- Static graph assets exist at `static/ssd-data-map.json`, `static/ssd-data-map.html`, `static/ssd-data-export.jsonld`, and `static/dreamworld.html`.

Recommended v5 refresh scope for IMPACT:

| App surface | Hubble role | Dome / Living Intelligence role | Day 4 action |
|---|---|---|---|
| Offering / dream intake | visitor leaves a Salish Sea reflection | can become a graph event if persisted | keep, but update copy only after public-language approval |
| Knowledge Graph link | shows what powers the installation | portal to Living Intelligence constellation | rename / position as a bridge, not a side link |
| Dream Field Query | visitor asks the sea / graph | can route through the same sovereign model layer if available | spec now, implement only if model path is confirmed |
| Dome teaser | tells visitors there is a larger journey nearby | moves Hubble traffic toward the Dome surface | add as optional card / link once Carol Anne approves wording |
| Survey launch | out of scope for Hubble app | Whova-backed polling/survey/word-cloud on screen | do not build custom survey UX unless scope is reopened |

## Content Boundaries

Do not collapse the two rooms into one story.

Hubble Space can say:

- this installation has a knowledge graph behind it
- visitor offerings can enter a shared dream / graph field
- the Dome presentation expands related Living Intelligence work at IMPACT

Hubble Space should not say without approval:

- that Austin's pearl is the same thing as the Living Intelligence graph
- that Coast Salish teachings are being generalized into the Dome system
- that the Indian Act survey is part of Austin's visual world
- that visitor submissions become economic survey data

Dome can say:

- knowledge graph cosmic journey
- Whova-backed survey / polling / word-cloud support if Carol Anne wants it framed
- pre-recorded primary demo, live backup if Wi-Fi cooperates

Dome should be careful with:

- implying full live functionality by May 27 if only concept visuals exist
- implying custom survey analytics are being built by SSD when Whova owns the intake/display path
- borrowing Austin / Coast Salish visual language unless explicitly approved
- using Hubble pearl language as Carol Anne's framework without review

## Pre-Recorded First

Per the May 8 strategy, pre-recorded video is the primary demo. The live demo is backup because Space Centre Wi-Fi is unreliable.

Practical implication:

- Friday deliverable should be concept visuals / GIFs / title cards, not a fragile live prototype.
- Dan's Dome specs should determine native render format before final delivery.
- The Whova survey conversation is next week; the presentation path should not depend on custom survey buildout.
- If a live graph view exists, screen-record it and treat the recording as the thing that must work.

## Friday Asset Target

Minimum useful package for Carol Anne's AI presentation:

- 10 concept visuals or GIFs
- each with a clear title
- each rooted in the KG cosmic journey direction
- no claim that the full survey visualization is implemented
- no Austin-derived forms or unapproved cultural motifs

Asset brief lives at `docs/space-center/dome-cosmic-journey-friday-asset-brief-2026-05-14.md`.

Do not send the staged package as final Dome media until Dan confirms projection format / resolution / timeline. It remains useful as concept material and can be re-rendered once specs are known.

## Dan Call Ask

Dan is the specs lead copied by Kurt. Tomorrow's call should cover the render pipeline first:

1. Dome projection specs: resolution, format, fisheye/equirectangular requirements, frame rate, audio, file delivery, test window.
2. Playback strategy: preferred format for pre-recorded demo assets in the Dome if live is not reliable.
3. Realistic delivery window if the team can author to Dan's render pipeline.
4. Whether concept stills/GIFs are useful for Carol Anne before native Dome assets are rendered.

Survey/app questions should stay narrow because Whova owns polling/survey/word-cloud: only ask whether any Hubble QR/app handoff is useful, not whether SSD should build survey intake.

## Design Principle

Use one substrate, two visual grammars:

- Hubble: water / pearl / triptych / approved Austin lineage layer.
- Dome: constellation / graph / cosmic journey / participation-as-signal.

The connection is the knowledge graph and visitor pathway, not visual sameness.
