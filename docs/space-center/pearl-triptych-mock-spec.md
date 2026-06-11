# Pearl Triptych Mock — One-Page Recipe

> Phase 2 production architecture: spherical-first authoring (per `project_spherical_first_authoring` memory + plan addendum Update C). One unified pearl-interior 3D scene → three 1080p triptych views for May → fisheye/equirectangular re-render for fulldome at MOVE37XR Oct.

## Source scene (one continuous volume)

Build in TouchDesigner, Blender, or Unreal — whichever the team picks. The scene is a translucent spherical interior with a virtual camera at the center.

**Scene contents (separate passes / layers):**

1. **Background** — interior shell of the pearl. Soft nacreous gradient (warm white → mother-of-pearl iridescent → deep blue at the base). Slow internal rotation (~0.5 deg/sec). Gentle volumetric haze.
2. **Midground (particle current)** — slow spiral particle current traversing the volume. Particles tinted in Austin's palette (red / black / blue / gold). Used as the through-line that visually unifies all three triptych views.
3. **Foreground (formline / symbolic)** — Thunderbird and the three primitive shapes (crescent / ovoid / U-form, pending Austin clarification). Lives at the center of the volume so it reads from all three camera views, with stronger weight to the center camera.

## Three camera rig (May triptych)

| Camera | Pose | What it sees |
|---|---|---|
| **Left** | Yaw −60°, slight upward tilt | Peripheral facet — mostly background nacre + edge of particle current. Symbolic content visible faintly at the right edge of frame. |
| **Center** | Yaw 0°, level | **Primary teaching view.** Thunderbird + three shapes legible front-and-center. Highest information density. |
| **Right** | Yaw +60°, slight downward tilt | Water-memory facet — particle current dominant, symbolic content visible faintly at the left edge of frame. |

**FOV per camera:** ~50° horizontal (matches typical 1080p projector throw geometry; not so wide that perspective distortion gets surreal).

**Continuity rules:**
- All three cameras share **one motion clock** — the spiral current and pearl rotation are the same world-time across panels.
- Particle current is **traversable across panel boundaries** — particles flow off the right edge of Left into the left edge of Center, etc. (At seam render time, render Left+Center+Right as one wide frame and slice; particles cross seam smoothly.)
- **Symbolic content (Thunderbird, three shapes) lives within one panel** OR crosses only during slow low-detail transitions. Don't let a half-Thunderbird straddle a seam during a high-information moment.
- **Low-information seams** — within ±100 px of each panel edge, keep imagery to background gradient + particle pass only. No detailed line work or text in seam zones.

## Render outputs

### May (triptych)
- 3× 1920×1080 PNG sequence per camera, 24/30 fps
- Asset rule: keep background / midground / foreground as **separate render passes** (alpha-channeled PNGs or EXR) so Resolume can composite or restage independently
- Frame rate sync via TouchDesigner master clock or Resolume timeline

### Oct (fulldome) — same scene, different camera
- One fisheye (180° hemispherical) OR equirectangular (360×180) render at dome native resolution
- Same per-pass separation; dome distortion correction applied per-pass

## Mock implementation steps (today/tomorrow, before Austin's curated set lands or in parallel)

A simple TouchDesigner mock to validate the recipe:

1. **Geometry COMP** — sphere SOP (radius 5 m), normals flipped (inside-out), translucent material
2. **Camera** at world origin, three Camera COMPs at yaw -60° / 0° / +60°
3. **Particle COMP** — bound to a noise-driven spiral; emit in volume; particles tinted via ramp
4. **Foreground placeholder** — abstract shapes for Thunderbird + 3 primitives (use simple geometry until Austin's actual vectors are ready)
5. **Render TOPs** — three Render TOPs, one per camera, output to three separate texture slots
6. **Composite check** — wire all three to one wide TOP arranged side-by-side, scrub through time, verify particle current crosses seams cleanly + symbolic content stays within Center panel

This mock can ship to Resolume as 3 NDI inputs OR pre-rendered sequences. Either path validates whether the spherical-first approach reads as "one volume, three windows" before we invest in higher-fidelity assets.

## Open questions for Austin (next Signal screenshare)

These should drive how we author the foreground pass:

1. The "three shapes swirling and morphing" — which three specifically? (Default working assumption: crescent, ovoid, U-form — but he may have a specific set in mind)
2. Is the Thunderbird the sole pearl-passer, or do other crests share the role?
3. Should the three shapes stay centered (visible primarily in Center panel) OR move across all three panels? Affects seam-handling rules above.
4. How explicit can the "teaching" framing be in wall card / panel description?
5. Anything else from his "ideas surrounding the animation" he didn't put in the May 11 email?

## Cultural-protocol notes

- Per `project_spherical_first_authoring` memory: Coast Salish pearl claims in the prompt-06 research report were NOT source-safe. Public framing stays "Austin's pearl vision" only, until Austin grounds any broader cultural meaning.
- Per `feedback_austin_consent_trust_floor`: per-output approval is the floor, not a milestone. Default-pause, not default-ship. The mock is internal; only Austin-OK'd content reaches the projectors.

## Estimated effort to first watchable mock

- Bare-bones TD scene + 3 Render TOPs + abstract foreground: 2–3 hours
- Particle current tuning + nacre material: another 2–3 hours
- Seam-crossing test + slice-and-display in Resolume: 1–2 hours
- Total: ~6–8 hours of TD work, achievable in a day once 3090 access is back

## Hand-off

Once Austin's curated assets land, the foreground placeholder gets swapped for:
- His three actual shapes (whatever they turn out to be)
- His Thunderbird vector art (rendered as 3D extruded panels OR 2D sprite layered into the volume)
- His color palette refined per his curated set (override the current "red / black / blue / gold" working palette if he prefers different)
