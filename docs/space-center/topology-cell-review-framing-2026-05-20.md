# Topology-Cell Review Framing - 2026-05-20

Status: internal team-alignment doc for Darren and Pravin, with recommended Austin-facing language. No rendering. Not Austin-approved, not public-use guidance, not a traditional-meaning claim, not a general Coast Salish grammar claim. This doc is not itself sent to Austin - section 2 is a proposed script only, and any actual Austin outreach goes through normal Pravin proofing and the send-verification gate.

Purpose: align Darren and Pravin on how to bring the new topology-cell direction to Austin - what to say, what not to claim, what order to review, and whether it can sit on the Hubble wall as an internal R&D layer.

Read with:

- `docs/space-center/topology-cell-interaction-input-design-2026-05-20.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/primitive-tiling-topology-grammar-2026-05-20.md`
- `docs/space-center/hubble-wide-wall-resolume-assembly-2026-05-19.md`
- `docs/space-center/mvp-fallback-resolume-package-2026-05-19.md`
- `docs/space-center/austin-consent-map.md`
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_standing_wave_phase_inversion_v002_2026-05-20/README.md`

## 1. Plain-Language Explanation (for Pravin)

Static salmon replication is parked. The new lead direction:

A hidden mathematical construction - overlapping circles in the seed-of-life / flower-of-life pattern - is used only as a **generator**. We do not show the circles. We show the grammar that emerges where they overlap.

The visible layer reveals:

- a center circle / origin;
- radial curved trigons and rays;
- crescent / lens / lune fields;
- falling snowflake primitive cells;
- water / ripple / sun relationships.

Why this is the lead direction: one math system produces many looks (water, sun, snow, ripple, network), it can react to sound and touch, it animates fluidly, and - unlike static salmon - it barely depends on copying Austin's exact artwork. It is internal R&D. Nothing here is approved or public.

One guardrail: the visible layer must not read as a generic sacred-geometry mandala or a wallpaper lattice. It should read as sparse, emergent water/sun/snow forms. The construction circles stay hidden.

## 2. Austin-Facing Framing (claim-free)

When Pravin or Darren brings this to Austin, frame it as an open question, not a result. Recommended language:

> "We found a mathematical construction that can reveal circle / crescent / trigon-like forms."
>
> "Does this feel like a useful internal grammar direction?"

Posture around those two lines:

- Present it as internal exploration in progress, not a finished thing.
- Ask, do not tell. Default-pause: we are not proceeding to anything public on the strength of his answer alone.
- Show one or two short loops, then ask one clear question per item (section 5). Do not narrate the math.
- Per-output sign-off is the floor, not a milestone (`austin-consent-map.md`).

Internal note (not for Austin): the three forms - circle, crescent, trigon - happen to coincide with the primitives of Coast Salish formline. We deliberately do **not** lead with "these are your formline primitives." That would be a claim. We present it as abstract math and let Austin draw any connection himself if he sees one. That gap is exactly why this goes to Austin before it goes anywhere.

## 3. What Not To Claim

- **Not traditional meaning.** Circle / crescent / trigon are math topology classes here. We make no claim about cultural or traditional meaning.
- **Not Austin-approved.** Nothing in this lane is approved. The v002 packet is explicitly `INTERNAL ONLY. Austin-review-needed`.
- **Not public-ready.** No topology-cell or cymatic output goes on a public wall without an Austin per-output review record.
- **Not sacred geometry as the final aesthetic.** Seed-of-life / flower-of-life is a hidden generator and a tool, not the show's look. We do not frame the piece as "sacred geometry" and do not render the full lattice.

## 4. Review Order

Review in this order; do not reorder under time pressure.

1. **Cymatic topology-cell v003/v004 - the seed-to-sun/trigon reveal.** (Next render pass; not yet produced - the lane is currently at v002.) This is the single clearest demo of the whole thesis: the hidden seed construction resolving into an emergent radial field of curved trigons, rays, and crescent arcs. Lead with it because it is the most legibly abstract and the lowest cultural load.
2. **The falling-snow layer.** The rectangular falling-snow layer of many small topology snowflakes (designed in `topology-cell-interaction-input-design-2026-05-20.md`; also a not-yet-produced render). Review second.
3. **Defer salmon.** Static salmon / figure work stays parked. Do not put salmon ahead of items 1-2. Salmon is the highest approval-load path and the topology direction is the stronger near-term route; salmon waits until the abstract topology direction has had an Austin pass.

## 5. Exact Austin Questions

Keep these tight and genuinely answerable:

1. Does this mathematical construction - hidden circle overlaps revealing circle/crescent/trigon-like cells - feel like a useful internal grammar direction to keep exploring?
2. Is the seed-to-sun/trigon reveal acceptable as an abstract water-and-light study, or does it already read as something specific we should pause on?
3. Is a falling-snowflake primitive-cell layer acceptable as abstract winter-water, or off-limits?
4. Are there forms in here we should not pursue even internally?
5. What language should we use - and avoid - when describing this? Is naming the shapes "circle / crescent / trigon" itself sensitive?
6. Should figure and salmon work stay parked until this abstract topology direction has had your review?
7. For per-output review: what do you need to see for each clip, and in what form, to give or withhold a sign-off?

## 6. Pravin Questions - Projection / Resolume Usefulness

1. As a black-screen additive layer (Screen/Add, low opacity) over the Moonfish/H6 water footage, does the topology-cell layer actually read on the Hubble wide wall, or does it get lost?
2. Is the v002 phase-inversion loop legible at projection scale in venue lighting - or too subtle, or too busy?
3. Of the five modes - seed, snow, sun, water_ripple, network - which are worth keeping as Resolume layers for the show, and which to drop?
4. For IMPACT: pre-rendered loops, or a live TouchDesigner generator? (The interaction design treats the live generator as TD-stability-gated.)
5. What opacity / blend range works for this layer over the fallback footage floor?
6. Does it belong as its own layer group with a dedicated solo-mute kill-switch, alongside the existing wide-wall groups?
7. Operator load: is one more internal layer group manageable on the 3090, and on the 5090 when it lands?

## 7. Can This Sit On The Hubble Wide Wall As An Internal R&D Layer?

**Yes - as an internal R&D layer only, not as public content.**

Structurally it fits the deck that already exists:

- The wide-wall stack already reserves a slot for exactly this: `mvp-fallback-resolume-package-2026-05-19.md` lists "Layer 5 - (reserved) Primitive grammar layer, Screen/Add, opacity 8-22%". The `hubble-wide-wall-resolume-assembly-2026-05-19.md` deck already runs an internal-only Group 2 ("Water grammar (v004)", ARMED at low opacity) in the same shape.
- The topology-cell / cymatic layer slots in as its own internal-only layer group: ARMED at low opacity (or LOADED + MUTED), Screen/Add over the fallback footage floor, with its own solo-mute kill-switch separate from any Austin-derived group.
- The v002 clips are 1920x1080; they scale-to-fit the 3840x2160 canvas the same way the v004 clips do - no letterbox, black background renders transparent under Screen/Add.

But the boundary is firm:

- Internal / Pravin-review use during build and rehearsal is fine. **Public showing at IMPACT is not** - the v002 packet is `Austin-review-needed`, identical to the v004 water grammar.
- Default deck state for this group is muted / kill-switched. Turning it on for a public audience is a **content-review decision owned by Austin**, not an engineering decision.

So: build it into the wide-wall deck now as a kill-switched internal R&D layer; rehearse with it Pravin-only; do not put it in front of a public audience until Austin has a per-output sign-off on the specific clips.

---

## Path Verification

All paths referenced in this document were verified to exist on 2026-05-20.

Read for this framing:
- `docs/space-center/hubble-wide-wall-resolume-assembly-2026-05-19.md`
- `docs/space-center/mvp-fallback-resolume-package-2026-05-19.md`
- `track2-deterministic/morph_outputs_INTERNAL/cymatic_standing_wave_phase_inversion_v002_2026-05-20/README.md`

Cross-referenced and verified:
- `docs/space-center/topology-cell-interaction-input-design-2026-05-20.md`
- `docs/space-center/cymatics-interaction-input-design-2026-05-20.md`
- `docs/space-center/primitive-topology-grammar-cymatics-2026-05-20.md`
- `docs/space-center/primitive-tiling-topology-grammar-2026-05-20.md`
- `docs/space-center/cymatic-standing-wave-algorithm-brief-2026-05-20.md`
- `docs/space-center/primitive-grammar-contract-2026-05-19.md`
- `docs/space-center/interactive-dream-to-primitive-architecture-2026-05-19.md`
- `docs/space-center/resolume-wide-wall-composition-plan-2026-05-18.md`
- `docs/space-center/austin-consent-map.md`
- `docs/space-center/austin-review-packet-2026-05-14.md`

Note: cymatic topology-cell renders v003/v004 (section 4, item 1) and the rectangular falling-snow layer (section 4, item 2) are next-pass renders and do not exist yet; the cymatic phase-inversion lane is currently at v002. No rendering was performed for this document.
