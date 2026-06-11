# Prompt 06 Addendum - Pearl-as-Container Triptych + Dome Migration

Source report: `/Users/darrenzal/Downloads/Visual Precedents for "Inside" an Object.docx`

## Bottom line

The report partially fills the gap identified in `synthesis-2026-05-13.md`: it gives useful compositional and asset-authoring guidance for making three discrete 1080p screens feel like one interior volume, and for later migrating the work to dome/360. It does not fully solve the cultural meaning of the pearl for SSD. Claims about Coast Salish pearl/shell cosmology are not backed by a Coast Salish-specific source in the report and should go to Austin, not into wall copy.

## Useful findings to apply

### Three screens can read as one interior if authored as one space

The report's most actionable recommendation is to build the pearl interior as one unified 3D/spherical environment and derive the three triptych views from that source. It says to "align all geometry in one 3D scene" and render three side-by-side virtual cameras so the content stitches itself across screens without physical edge blending (`Visual Precedents for "Inside" an Object.docx`, "Compositional Strategies (3x1080p Triptych)"). This directly supports the existing 3 x 1080p triptych decision while changing how assets should be authored.

Concrete May recipe:

- Treat the center screen as the primary view into the pearl; side screens are peripheral facets of the same interior, not separate scenes (`Visual Precedents...`, "Strategic Focal Panel").
- Use shared perspective cues, horizon/arc lines, particle flow, and matched motion across panel boundaries (`Visual Precedents...`, "Continuous Perspective"; "Shared Motifs at Edges"; "Unified Motion and Sound").
- Keep detailed symbolic content away from panel boundaries; use lower-detail gradients, fields, particles, or darkness at seams (`Visual Precedents...`, "Avoid Hard Cuts").
- Use synchronized audio/motion to reinforce the single-volume read (`Visual Precedents...`, "Unified Motion and Sound").

### The strongest technical migration pattern is spherical-first

The report recommends authoring as 360/spherical content first, then extracting triptych segments for May. It specifically suggests building the pearl interior in Unreal, Unity, Blender, or equivalent; placing a virtual camera at the pearl center; rendering equirectangular/fisheye or 360 source; and extracting three 120-degree-ish segments for the triptych (`Visual Precedents...`, "Triptych-to-Fulldome Migration").

Concrete migration recipe:

- Source scene: high-resolution 3D/spherical pearl interior.
- May output: three 1920 x 1080 perspective crops or camera views from the same scene.
- Dome output: re-render the same scene as fisheye/equirectangular at dome resolution.
- Asset rule: keep background, midground, and formline/shape elements as separate passes so dome distortion can be corrected later (`Visual Precedents...`, "Use Independent Layers").
- QA rule: test in VR or dome-preview software before committing the panel seams (`Visual Precedents...`, "Test with Dome Preview").

### Precedents support multi-panel continuity, not the pearl itself

The report names several precedents whose relevance is mainly compositional:

| Precedent | What it contributes | Caution |
|---|---|---|
| Cellscape / XVIVO | Strong "inside a living object" reference via VR cellular interior (`Visual Precedents...`, "Cellscape") | VR, not flat triptych; useful for spatial feeling, not panel method |
| The Singleton Whisky Triptych / Found Studio | Three panels used to visualize unseen interior/molecular process (`Visual Precedents...`, "The Singleton Whisky Triptych") | Commercial launch reference; verify before public citation |
| Charles Atlas, About Time | Multi-channel screens as facets of one choreographed environment (`Visual Precedents...`, "Charles Atlas - About Time") | Not specifically inside-object |
| Richard Mosse, Incoming | Three large adjacent screens unified through darkness, scale, and recurring imagery (`Visual Precedents...`, "Richard Mosse - Incoming") | Heavy subject matter; cite only for display grammar |
| Steven Eastwood, The Interval and The Instant | Multi-screen continuity and repeated motif tying panels together (`Visual Precedents...`, "Steven Eastwood") | Source is a Medium article, not primary documentation |
| Virginia Tech Cube | Discrete projected surfaces forming one immersive volume (`Visual Precedents...`, "Virginia Tech Cube") | CAVE/lab scale, not transit triptych |

For SSD, these should be used as design references, not public-facing cultural precedent.

## Weak or unsafe findings

### Coast Salish pearl claims are not source-safe

The report says that in Coast Salish cosmology, pearl images "have specific mythic meanings" and later describes a "Coast Salish pearl of knowledge" (`Visual Precedents...`, "Pearl/Sphere Motifs"; "Risks and Pitfalls"). The cited examples in that section are Wunambal Gaambera and Torres Strait / Aboriginal pearl shell projects, not Coast Salish sources. This is a category jump. Do not use those claims in wall card, sponsor copy, or plan prose without Austin explicitly grounding them.

Safe framing:

- "Austin's pearl vision" is source-safe because it comes from Austin's May 11 email.
- "Pearl/shell as a vessel of story in other Indigenous Pacific contexts" is report-backed but not Coast Salish-specific.
- "Coast Salish pearl cosmology" is not established by this report.

### Some precedents need citation verification before public use

The report cites live project pages, but this addendum has not independently verified them. Before procurement/public claims, verify at least:

- The Singleton Whisky Triptych / Found Studio / D1S1 page.
- The Richard Mosse and Steven Eastwood claims, because the report cites a Medium article rather than primary exhibition documentation.
- Any quotation attributed to Austin's Senakw profile before using it in sponsor materials.

### The report overstates "10-15 precedents"

The prompt asked for 10-15 concrete precedents. The report gives about nine substantive examples plus a general note on altarpieces. It is enough to act on composition, but not enough to claim broad art-historical coverage.

## Decisions ready to make

1. **Author spherical-first.** Use a unified pearl interior scene as the source of May triptych renders and future dome renders.
2. **Do not edge-blend.** The report's continuity strategies work with discrete panels and support the existing triptych choice.
3. **Make panel seams low-information zones.** Do not let core formline teachings, Thunderbird, or the three shapes cross seams in a way that requires exact projector matching.
4. **Keep pearl language Austin-led.** Use Austin's own "pearl" / "teachings" language only after he approves how explicit the public framing should be.

## Recommended May composition recipe

Build a "pearl interior" TouchDesigner/Blender/Unreal scene with the virtual camera at the center of a translucent spherical/vessel space. Render three camera views from one rig:

- Left: peripheral scientific/bioregional texture entering the pearl.
- Center: primary teaching view, where Thunderbird / pearl / three shapes are legible.
- Right: water-memory field, sharing particles and light motion with the other panels.

The screens should share one motion clock. A spiral/particle current can traverse all three panels, but symbolic figures should either live fully within one panel or cross only during slow, low-detail transitions. Add moments of stillness/rest frames so "inside the pearl" does not become constant rotation or visual fatigue (`Visual Precedents...`, "Risks and Pitfalls").

## Plan edits to propose

- **Section 1:** Add "pearl interior is authored as one continuous volume, viewed through three windows" as the operational translation of Austin's vision.
- **Section 2:** Add the three-screen continuity rules: shared virtual camera system, shared motion clock, low-information seams, center-panel hierarchy.
- **Section 3:** Keep the three shapes as the central characters; do not let particle effects dominate them.
- **Section 4:** Add spherical-first asset authoring to the pipeline: one source scene, triptych crops for May, fisheye/equirectangular render for dome later.
- **Consent map:** Add a required approval field for any public wording that interprets the pearl's cultural meaning.

## What to do next

Do not run another broad deep-research report for this. The remaining gap is not research volume; it is Austin's meaning. Take the report's technical recipe into the next design review, then ask Austin:

- Does "inside the pearl" for May mean a literal spherical interior, or a suggested interior?
- Are the three shapes meant to move across all three panels or stay centered?
- What language can be used publicly around "pearl," "teaching," and "Thunderbird passing down"?
- Should other Indigenous pearl/shell precedents be avoided entirely so this stays grounded in his own framing?
