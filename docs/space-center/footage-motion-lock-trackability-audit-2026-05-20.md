# Footage Motion-Lock Trackability Audit - 2026-05-20

Status: INTERNAL Agent A audit. Not Austin-approved, not public-use guidance,
not a cultural claim. Companion to the v004 -> v005 motion-lock R&D thread.

## Purpose

v004 proved the frame-synchronous motion-lock mechanism works (phrases advected
by per-frame optical flow), but Darren's review found the dense salmon-school
footage (`P1099653.mp4`, t=160s) too complex for the lock to *read*: hundreds
of near-identical fish at many depths, no distinct landmark for the eye to see
a primitive glued to.

This audit inspects the available Moonfish and Evan footage and ranks short
windows by **trackability** -- how clearly a 2D image-space motion lock would
read on them -- so the v005 proof can be rendered on the best one.

## The 3D Caveat (why the salmon school failed)

Optical flow measures **2D apparent image-space motion** only. We do **not**
claim to extract 3D motion from this monocular footage, and v005 will not.

The dense salmon school fails because it is a 3D volume of overlapping,
semi-transparent fish at many depths. Its 2D image projection is a tangle of
competing motions with no stable figure-ground -- the per-frame flow is real
but visually illegible, and there is no still anchor to read a lock against.

Footage is *trackable* for a 2D motion lock when its motion is legible in the
image plane. Three good cases:

- **Rigid-scene camera parallax** -- the camera moves past a solid, feature-rich
  subject (a reef). The whole scene translates coherently; optical flow is
  clean and consistent; distinct features let the eye verify the lock.
- **Distinct in-plane-moving features** -- elements that sway or drift roughly
  parallel to the image plane (kelp blades), each individually trackable.
- **A clear directional current** -- a visible, coherent flow with a static
  frame around it (a stream), giving an unambiguous figure-ground.

## Method

- Motion probe across all candidate clips: per-window mean frame-difference
  (`motion`), spatial non-uniformity of that motion (`structure`), and the
  fraction of the frame that stays near-still (`still_frac` -- a proxy for
  "are there stable anchors?"). Probe at 160x90, 8fps, 4s windows.
- Visual inspection of representative frames and short consecutive-frame
  sequences for each promising window.
- Trackability is a visual judgement; the probe only narrows where to look.

## Footage Inventory

| Clip | Res / fps | Dur | Content |
|---|---|---|---|
| `moonfish-video/underwater/P1099653.mp4` | 1920x1080 / 60 | 428s | dense salmon school (v003/v004 -- rejected) |
| `moonfish-video/underwater/P1111509.mp4` | 1920x1080 / 60 | 19s | reef-garden boulder + kelp (= hero `H5_reef_garden`) |
| `moonfish-video/underwater/P1111785.mp4` | 1920x1080 / 60 | 90s | kelp forest (= hero `H3_kelp_cathedral`) |
| `moonfish-video/underwater/P1077716.mp4` | 1920x1080 / 60 | 148s | busy mid-water school |
| `moonfish-video/underwater/P1111707.mp4` | 1920x1080 / 60 | 82s | mid-water, low anchor content |
| `moonfish-video/underwater/P1000011.mp4` | 1920x1080 / 60 | 63s | murky reef/bottom, sun rays |
| `moonfish-video/longform/DSC_9313_HD.mp4` | 1920x1080 / 30 | 762s | eelgrass bed + thin schools + reef |
| `moonfish-video/drone/DJI_0022,0045,...` | 1920x1080 / 30 | ~100s | aerial water surface (near-static) |
| `hero-subclips/H2_herring_in_kelp.mp4` | 1920x1080 / 60 | 64s | herring school in kelp |
| `austin-reference/.../evan_vancouver_island_4096x2160_20sec.mp4` | 4096x2160 / 24 | 20s | forest stream (t0-4.5) then dissolve to rocky coast |

Note: `H5_reef_garden` is the hero subclip of `P1111509`; `H3_kelp_cathedral`
is the hero subclip of `P1111785` (identical probe signatures). The audit
references the underwater source files.

## Ranked Windows

### 1. P1111509 reef garden, t = 1.0-7.0s -- TRACKABILITY: HIGH  [chosen for v005]

An encrusted reef boulder -- vivid orange and yellow sponges, anemones,
encrusting life -- with kelp stipes rising behind it; the camera moves steadily
past it. Probe: motion 4.8-7.1, structure 2.9-4.6, still_frac 0.23-0.33.

Why it is the best window:

- **Distinct high-contrast features.** The orange/yellow sponges are
  individually trackable -- the eye can verify "that glyph stayed on that
  sponge." This is the direct fix for v004's no-landmark failure.
- **Rigid-scene camera parallax** is the cleanest case for optical flow: the
  reef translates coherently, so the per-frame flow is consistent and reliable
  (no froth, no overlapping-layer tangle, no fish-school chaos).
- Near foreground (reef) and farther background (kelp, green water) move at
  different parallax rates -- legible depth ordering *in the image plane*,
  with no 3D claim required.
- 6 s of continuous clean footage; marine; on the Salish Sea theme.

### 2. Evan Vancouver Island stream, t = 0.0-4.5s -- TRACKABILITY: HIGH motion, MIXED

A forest stream: white water flowing over mossy rocks. Probe: the highest
motion of any candidate (6.8-11.3) with strong structure (3.9-8.2).

- Strong, coherent, directional, in-plane current; static mossy-rock anchors;
  unambiguous figure-ground. The single most *dramatic* motion available.
- Limits: it is a **freshwater forest creek, off the Salish Sea marine theme**;
  only ~4.5 s is clean before the clip dissolves to a coastal scene; and
  white-water froth violates brightness-constancy, so the flow is noisier than
  rigid parallax and the water itself has no distinct trackable feature (it is
  a flow-field lock, not a feature lock).
- Best runner-up; strongest choice if a pure "current" demonstration is wanted
  over a marine/feature one.

### 3. P1111785 kelp cathedral, t = 70.0-76.0s -- TRACKABILITY: MEDIUM-HIGH

Kelp forest -- large elongated blades, gentle in-plane sway, sun behind. Probe:
motion ~3.1, structure ~2.9, still_frac 0.32 (the best stable-anchor fraction
of the underwater clips). Individual blades are distinct, trackable, and move
mostly parallel to the image plane. Marine, on-theme. Motion is gentler than
the reef; an alternative higher-motion kelp window is t=28-34s (motion 4.25).

### 4. DSC_9313 longform, t = 597.0-603.0s -- TRACKABILITY: MEDIUM

Eelgrass bed with a thin mid-water fish school and reef at the bottom. Probe:
motion ~5.6, structure ~5.0, still_frac 0.38. The eelgrass blades and reef are
usable anchors, but the fish school partially reintroduces the multi-small-
mover problem. Workable, not ideal.

### 5. P1000011 underwater, t = 48.0-54.0s -- TRACKABILITY: MEDIUM-LOW

Murky reef/bottom with sun rays and an orange element (possible lone fish).
Probe: motion ~4.3, structure ~3.1. Low water clarity reduces feature contrast;
anchors are present but soft. A fallback only.

## Rejected

- **P1099653 dense salmon school** -- the v004 failure case; 3D volume, no
  anchors. Do not reuse for a lock test.
- **P1077716, P1111707, H2_herring_in_kelp** -- busy schools, still_frac
  0.04-0.12: almost no stable anchors.
- **Drone DJI_0022 / DJI_0045** -- near-static aerial (motion 0.5-1.5); too
  little movement to lock to.
- **Evan coastal scene (t=7-20s)** -- a wider, more complex frame (foreground
  wind-blown pine + distant waves + rocky coast); the clear in-plane motion
  (branch sway) is only partial. Usable but not as clean as the stream or reef.

## Not Found

No window with a clear **lone fish** or **seal** as a single dominant trackable
subject turned up in the sampled footage. If such a shot exists in unsampled
longform material it would be an excellent future lock subject; this audit did
not locate one.

## Recommendation

Render the v005 proof on **P1111509 reef garden, t = 1.0-7.0s**. It is the best
all-around window: it directly fixes v004's diagnosed no-landmark failure
(distinct high-contrast features), gives the cleanest and most reliable optical
flow (rigid-scene parallax, not froth or schooling chaos), provides a full 6 s
clean window, and is marine and on-theme.

The Evan stream is the strongest pure-motion alternative but is freshwater,
short, and froth-featureless -- noted for the operator in case a "current"
demonstration is preferred over a marine feature-lock one.

Footage does support a clearer motion-lock test than the salmon school. v005
renders the proof; this audit is the footage-selection record behind it.
