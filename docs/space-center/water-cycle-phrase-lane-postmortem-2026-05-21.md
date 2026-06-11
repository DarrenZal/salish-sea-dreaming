# Water-Cycle Phrase Lane Postmortem - 2026-05-21

Status: INTERNAL ONLY. Postmortem of two internal R&D probes (v001, v002).
No cultural-meaning claim. No Coast Salish grammar claim. No traditional-
meaning claim. Not Austin-approved. Not public, show, projector, sponsor,
social, or press cleared. This document recommends a lane disposition; it
does not commission v003.

## Scope

This is a paper review of two probes in the water-cycle phrase lane:

- v001: [water_cycle_anchor_phrase_probe_v001 README](../../track2-deterministic/morph_outputs_INTERNAL/water_cycle_anchor_phrase_probe_v001_2026-05-21/README.md)
  ([contact sheet](../../track2-deterministic/morph_outputs_INTERNAL/water_cycle_anchor_phrase_probe_v001_2026-05-21/water_cycle_anchor_phrase_probe_v001_contact_sheet.png),
  [recipe](../../track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v001.json))
- v002: [water_cycle_anchor_phrase_probe_v002_loop_closure README](../../track2-deterministic/morph_outputs_INTERNAL/water_cycle_anchor_phrase_probe_v002_loop_closure_2026-05-21/README.md)
  ([contact sheet](../../track2-deterministic/morph_outputs_INTERNAL/water_cycle_anchor_phrase_probe_v002_loop_closure_2026-05-21/water_cycle_anchor_phrase_probe_v002_loop_closure_contact_sheet.png),
  [recipe](../../track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v002_loop_closure.json))

Read with [installation-anchor-graph-architecture-2026-05-21.md](installation-anchor-graph-architecture-2026-05-21.md),
which classifies phrase-to-phrase / water-cycle as edge type F (INCONCLUSIVE)
at synthesis time. This postmortem confirms F's reading with v001 and v002
evidence and recommends the lane's disposition going forward.

## What Improved: Scalar-Field Continuum to Phrase Composition

The lane's pivot was from `water_cycle_continuum` (scalar-cell phase studies
classified through cymatic field topology) to authored parametric primitives
moving through a phrase chain. The prior continuum lane passed every
mechanical Section 9 criterion (frame counts, caps, untouched upstream, clean
loop) and still read as "instrument readouts" on inspection, not as water.

Concrete improvements the phrase-composition pivot delivered:

- **Mark scale**: large, deliberate, role-coloured primitives instead of a
  sparse cymatic field on near-black. The water phases are visibly water-like,
  not sensor traces.
- **Vocabulary discipline**: one primitive set (circle, crescent, trigon)
  carries every phase. Role mutates through motion + color + composition
  context, not through inventing a new motif per phase.
- **Attachment over scatter**: trigons attach to parent forms; crescents cup
  an origin or follow a path. The arc-bounded-region attachment rule (see
  [arc-bounded-region-rendering-notes-2026-05-21.md](arc-bounded-region-rendering-notes-2026-05-21.md))
  held in both probes; nothing reads as detached arrow clip-art.
- **Field engine demoted to atmosphere**: the v003 wave/interference engine
  is used only in phase 4 (ripple) as a low-opacity background shimmer
  underneath authored concentric crescents. The wave field is not classified,
  contoured, or used as geometry. The earlier continuum lane's failure mode -
  "field becomes the marks" - is gone.

The pivot was the right call. The lane became visually water-like instead of
instrument-like. That is real progress and worth preserving as reusable craft
even though the lane itself does not promote to spine.

## What v001 Got Right

From the v001 self-assessment and the contact sheet:

- **Phase 1 (sun)**: warm-amber origin with three asymmetric soft release-
  trigons attached to the disc. Reads as a quiet origin, not a clip-art sun.
- **Phase 4 (ripple)**: the strongest still in the lane. A bright impact
  circle with concentric ring crescents over the v003 wave-field shimmer
  atmosphere sells "rain hits water" unambiguously. This is the only phase
  where the wave engine and the authored phrase composition compose cleanly.
- **Anchor chain through color and motion**: the dim amber origin circle
  persists as a "memory of the sun" through phase 3 (rain) and reappears
  faintly at the end of phase 5 (wave -> return). Color carries continuity
  the geometry alone could not.
- **No glyph scatter**: each phase has 1-8 deliberate primitives, every one
  with a role and a parent-form attachment. The composition discipline held
  across all five phases.

v001's self-verdict was "mid / passable". The contact sheet confirms it:
phases 1, 4, and 5 read; phase 2 (vapor) and phase 3 (rain) are the weaker
beats.

## What v002 Fixed

v002 extended to 36 s, added two loop-closure phases (6 wave -> vapor, 7
vapor -> sun), and addressed v001's two named failure modes plus the
mono-cool palette.

- **Phase 1 saturation spot resolved**: v001's three perimeter release-
  trigons produced a faint additive saturation spot inside the orb where
  they overlapped the disc's halo. v002 replaced them with one eclipse-
  partial crescent that cups the orb plus one small attached release-
  trigon at the cusp, and switched the orb to replace-mode compositing.
  The amber-on-amber white-spot is gone.
- **Phase 3 shower-head silhouette resolved**: v001's concave-up trail
  crescent above each raindrop produced an unintended shower-head read.
  v002 dropped the trail crescent, added an elongated vertical fall streak
  below each drop head, and clustered drops into three spatial groups
  (left, center, right). Rain now reads as a group event, not isolated
  splashes with hardware above them.
- **Per-phase chromatic identity introduced**: v001 was mono-cool with a
  single warm sun. v002 gave each phase a palette signature - warm amber
  (sun), pale lavender-blue (vapor), deeper steel-blue (rain), ivory +
  pale cyan (ripple), deep teal (wave), lavender-blue (spray, matching
  vapor for visual continuity), lavender-blue -> amber (closure mix).
  Chromatic variation does some of the role-mutation work motion alone
  was carrying in v001.
- **Loop closure plausibly implemented**: spray crescents in phase 6 are
  parented to phase-5/6 sine-peak x-coordinates of the lead wave band, so
  spray is born at wave peaks rather than floating above them. Phase 7
  converging vapor crescents are parented to a center origin with a
  progress-driven warmth mix. Closure step B (vapor -> sun) is the
  clearest of the two new phases.

## What Still Failed

From v002's self-assessment plus the contact sheet, the remaining weaknesses
are real and block the lane from promoting to a spine role.

- **Rain identity is not yet legible**. v002 fixed the shower-head silhouette
  but dropped v001's wide soft glow + 3 sine-arc cloud-streak lines in favor
  of a single concave-DOWN inverted-arc hint, which is barely visible in the
  key still. Rain reads as falling from empty sky. The operator brief said
  "do not reach for cloud clip art" and that constraint held - but the result
  is that rain has no atmospheric source. A reviewer without the constraint
  context will see "where is this rain coming from?". This is the lane's
  most visible failure mode going into any review.
- **Loop closure is composition-loop, not identity-loop**. t=0 and t=36
  both show a warm amber orb at center, but phase 1 opening has the orb +
  eclipse-partial crescent + attached trigon while phase 7 final has only
  the orb. Watching the master end-to-end reads as "we came back to the
  warm orb", not "we came back to the exact same opening composition".
  The v002 worker chose not to revive the phase-1 companions in the
  closing beat to avoid making phase 7 feel busy/forced. The trade-off is
  honest, but the loop is not a true seamless cycle.
- **Phase 6 wave amplitude fades too fast in mid-phase**. Wave bands are
  barely visible at t=28s while spray droplets rise above them, weakening
  the "the wave releases upward" physical anchor. The wave needs to remain
  visibly present underneath the rising spray.
- **Phase 6 late (t=31s) is dead air**. A few faint droplets and a near-
  invisible wave at the phase 6 -> phase 7 boundary. The transition into
  closure has no carrier.
- **Mono-cool palette is reduced, not eliminated**. v002's per-phase palette
  signatures are subtle: sun is the only chromatically distinct beat;
  vapor, rain, ripple, wave, and spray all sit within a blue/teal/lavender
  range. A reviewer scanning the contact sheet still reads "cool sequence
  with one warm bookend", not "five chromatically distinct water states".
- **Overall verdict: mid / passable**. Both probes self-assessed as mid;
  the contact sheets confirm it. The lane is not visually broken, but it
  is not wall-worthy and does not read as a water cycle without watching
  the full master in order. A still-frame review packet would not carry
  the chain on its own.

## Reusable Elements (Keep)

Several pieces of craft are worth preserving even though the lane parks.
These are the artifacts of the postmortem that can be reused as support
texture, references, or schema in adjacent lanes.

- **Phase 4 ripple composition**. The only phase that composes the v003
  wave-field shimmer + authored impact circle + concentric ring crescents
  into a single legible water moment. Reusable as a stand-alone ripple
  beat or as background texture under other lanes' water moments.
- **Wave engine as background shimmer (not geometry)**. The `evaluate_field`
  + low-opacity multiplier pattern is a clean way to use the v003 wave
  field without letting it become the marks. The boundary held in both
  probes. Reusable wherever a water-surface atmosphere is wanted under an
  authored composition.
- **Role-mutation schema**. The vocabulary discipline of one primitive set
  (circle, crescent, trigon) mutating role through motion + color +
  composition context is reusable as a renderer contract for any phrase
  composition work. Documented in both READMEs' "Primitive Vocabulary And
  Roles" sections.
- **Recipe JSON shape**. The scene-recipe pattern
  ([v001](../../track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v001.json),
  [v002](../../track2-deterministic/scene_recipes/water_cycle_anchor_phrase_probe_v002_loop_closure.json))
  - per-phase windows, frame ranges, anchor-chain banner, and primitive
  parameter exposure - is the right shape for any future phrase-composition
  probe even if the contents change.
- **Attached crest detail (phase 5 wave)**. The small attached release-
  trigon at the lead wave crest is a clean example of the arc-bounded-
  region attachment rule producing a non-arrow trigon read. Reusable as
  reference geometry for any wave or crest composition.
- **Phase 6 spray-parented-to-wave-peak mechanic**. Even with the wave
  amplitude weakness, the implementation of "spray is born at the wave
  peaks rather than floating above them" is the right physical anchor
  pattern. Reusable in any future water-release composition.
- **Phase 7 convergence + warmth-mix pattern**. Per-crescent convergence
  vectors plus a progress-driven palette mix (lavender-blue -> amber) is
  the closest the lane came to a clean cycle-closure mechanic. Reusable
  in any composition that needs an atmospheric form to converge into a
  point/orb destination.

The v001 and v002 renderer scripts
(`scripts/water_cycle_anchor_phrase_probe.py`,
`scripts/water_cycle_anchor_phrase_probe_v002.py`) are kept reproducible
as the source of these reusable pieces.

## Recommendation: Park the Lane

**Park the water-cycle phrase lane as a spine candidate.** Use it only as
support texture, phrase reference, or atmosphere under other lanes.

This matches edge F (phrase -> phrase / water cycle) in
[installation-anchor-graph-architecture-2026-05-21.md](installation-anchor-graph-architecture-2026-05-21.md):
"Phrase -> phrase should not carry a lead installation role until it has a
complete evidence packet and reads without labels." v001 and v002 now have
complete evidence packets, but they still do not read as a water cycle
without label scaffolding (anchor-chain banners, phase captions, watching
the full master in order).

The right next test for the broader water-flow question is not v003 of this
lane. The right next test is **an authored water-flow GIF node** - a whole-
source water composition that participates in the anchor graph through the
same collapse/reveal contracts the Austin artwork nodes use (see
[installation-anchor-graph-architecture-2026-05-21.md](installation-anchor-graph-architecture-2026-05-21.md)
Section "Canonical Transition Pattern"). That is a different category of
node (closer to the Austin artwork nodes than to phrase studies) and should
be tested on its own terms, not by continuing to iterate this lane.

Until the authored water-flow GIF node has been tested, the phrase lane's
role is:

- **Phase 4 (ripple)** is keepable as a stand-alone ripple beat or as
  background texture under another lane's water moment.
- **Phase 5 (wave)** attached-crest detail is reusable as reference
  geometry.
- **Recipe JSON shape + role-mutation schema** are reusable as renderer
  contracts for any future phrase-composition work.
- **The wave-engine-as-shimmer pattern** is reusable wherever an
  authored composition wants a water-surface atmosphere underneath.

Do not commission v003 of the water-cycle phrase chain. If, after the
authored water-flow GIF node has been tested, there is still a need for a
phrase-cycle composition in the installation, revisit this lane then with
the GIF node's evidence in hand.

## Cultural Boundary

This postmortem describes internal R&D probes carrying the status
`primitive-like water-cycle phrase study pending cultural review`. No
"Austin-approved" claim. No "Coast Salish" claim. No traditional-meaning
claim. No ceremonial reference. The arc-bounded-region attachment rule
that held across both probes is a renderer rule, not a cultural rule, and
nothing in this postmortem promotes any generated output to externally
shareable status.

Generated visuals must not be described as Coast Salish designs. Generated
fields may be described only as abstract cymatic fields, water geometry,
primitive-like studies, or atmospheric support. Cultural content must come
from Austin-authored or Austin-approved works.

## Boundary

Internal only. No public, show, projector, sponsor, social, or press use.
Pending Austin review for any onward use of the lane's outputs, even as
support texture.
