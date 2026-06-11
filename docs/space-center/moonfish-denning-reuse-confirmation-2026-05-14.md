# Moonfish / Denning Reuse Confirmation — 2026-05-14

Purpose: turn the Phase 1 footage/photo reuse assumption into a written Day 4 confirmation path before any sponsor-facing or projector-ready package depends on it.

Status: pending outreach. `docs/space-center/credits-and-licenses-2026-05.md` currently marks both Moonfish Media and David Denning as "Phase 1 verbal — re-confirm for sponsor-facing reuse."

## Why This Matters Now

Prav's 2026-05-13 directive shifted Phase 2 away from new shoots and toward reusing Phase 1 underwater footage. That makes Moonfish / Denning permissions part of the production floor, not a courtesy cleanup.

Until written confirmation exists:

- use hero clips internally for technical planning and test exports only
- do not send them as public show previews
- do not frame them as cleared sponsor-facing materials
- do not include them in a projector-ready show package except as "pending reuse confirmation"

## Ready Hero Clips Inventory

All current `media/hero-subclips/` files are H.264, 1920x1080.

| Clip | Duration | Frame rate | Likely show role | Permission status |
|---|---:|---:|---|---|
| `H1_salmon_school.mp4` | 60.02s | 59.94 fps | salmon / school motion | pending written reuse |
| `H2_herring_in_kelp.mp4` | 64.03s | 59.94 fps | strongest left/right underwater structure candidate | pending written reuse |
| `H3_kelp_cathedral.mp4` | 90.09s | 59.94 fps | slow kelp architecture / pearl interior texture | pending written reuse |
| `H4_dense_school.mp4` | 40.02s | 59.94 fps | dense fish movement / visual complexity | pending written reuse |
| `H5_reef_garden.mp4` | 19.02s | 59.94 fps | reef texture / temporal-style smoke candidate | pending written reuse |
| `H6_kelp_forest_floor.mp4` | 50.03s | 59.94 fps | lower-energy habitat texture | pending written reuse |
| `H7_spawn_feast.mp4` | 39.04s | 29.97 fps | high-energy ecological moment | pending written reuse |
| `H8_milky_water.mp4` | 29.06s | 29.97 fps | pearl-water atmosphere / low-detail seam candidate | pending written reuse |

Production note: the source set mixes 59.94 fps and 29.97 fps. Normalize exports to one show rate before Resolume packaging.

## Confirmation Needed

Ask for explicit written confirmation on:

1. **Event scope**: Indigenomics IMPACT at HR MacMillan Space Centre, May 2026.
2. **Use scope**: projection installation, internal testing, sponsor/program documentation, and still/video excerpts if needed for recap.
3. **Edit scope**: trimming, color correction, cropping/slicing into triptych panels, looping, compositing with particles/data layers.
4. **AI/style scope**: whether footage may be used as source motion for style-transfer tests or only as raw/edited footage.
5. **Attribution**: exact credit line and placement.
6. **Compensation**: whether Phase 1 honorarium covers Phase 2 reuse or whether Phase 2 needs a new payment.
7. **Time/territory**: whether permission is limited to the May installation or also covers later MOVE37XR / DEVCON / Life at Center contexts.
8. **Archive**: whether the project can retain source and derived files after the event for documentation and future consented development.

## Recommended Default Terms To Request

Keep the ask modest for May:

- allow use in the May 2026 HR MacMillan Space Centre triptych installation
- allow internal technical testing and rehearsal exports
- allow editing needed for projection: crop, loop, color, composite, speed/rate conversion
- allow credit in wall card / program / internal deck
- ask separately before public social, press, or future-event reuse
- ask separately before AI style-transfer publication or reuse beyond internal tests

This gives the team enough clearance for the sprint without silently expanding into the longer MOVE37XR / DEVCON / 2027 arc.

## Draft Ask — Moonfish Media

Subject: Confirming Phase 2 reuse of Moonfish underwater footage

Hi [name],

For Phase 2 of Salish Sea Dreaming, we are preparing a three-projector installation for Indigenomics IMPACT at the HR MacMillan Space Centre in late May 2026. Prav has asked that we reuse the Phase 1 underwater material rather than schedule new shoots.

Can you confirm in writing whether Moonfish Media is comfortable with us using the Phase 1 underwater footage for this May installation and its technical rehearsals? The expected edits are projection-oriented: trimming, looping, color correction, cropping/slicing into left/center/right panels, and compositing with abstract particles or live tide/river data. We will credit Moonfish Media in the program / wall-card materials.

Separate question: are you comfortable with the footage being used as source motion for internal style-transfer tests? Nothing from that process would be shown publicly without a separate review/approval step.

Please also confirm the preferred credit line and whether Phase 2 reuse needs a new fee or falls under the Phase 1 arrangement.

## Draft Ask — David Denning

Subject: Confirming Phase 2 reuse of Phase 1 bioregional images

Hi David,

For Phase 2 of Salish Sea Dreaming, we are preparing a three-projector installation for Indigenomics IMPACT at the HR MacMillan Space Centre in late May 2026. The current plan reuses selected Phase 1 bioregional imagery as part of the water/ecology layer and technical testing path.

Can you confirm in writing whether you are comfortable with us using the Phase 1 photo selections for this May installation and its technical rehearsals? The expected edits are projection-oriented: cropping, scaling, color correction, looping/motion treatment, and compositing with water, particle, or live-data layers. We will credit you in the program / wall-card materials.

Separate question: are you comfortable with selected images being used as source material for internal style-transfer tests? Nothing from that process would be shown publicly without a separate review/approval step.

Please also confirm the preferred credit line and whether Phase 2 reuse needs a new fee or falls under the Phase 1 arrangement.

## Package Rule

Before any Moonfish or Denning file enters `show-package-space-centre-vYYYYMMDD/02_panel_clips/`, add a provenance row with:

- source contributor
- exact source file
- confirmation date
- allowed use scope
- credit line
- compensation status
- whether AI/style-transfer use is allowed or excluded

If confirmation is still pending, keep the clip outside the show package or label it `pending_reuse_confirmation`.
