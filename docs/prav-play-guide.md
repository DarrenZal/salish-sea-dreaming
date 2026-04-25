# Prav's Play Guide — Salish Dreamworld for Saturday's Set

A 1-page how-to for the Hakini-herring scene running on Darren's MacBook,
streamed to your Resolume rig via NDI. Everything you need to play with the
piece during the set.

---

## What's running on Darren's Mac

A TouchDesigner scene called **`salish_dreamworld`** that renders every visitor's
submitted dream as a fish-shape in 3D space, colored by its meaning-cluster. The
scene has three states the audience can summon with their hands:

1. **Idle** — fish drift in semantic space (UMAP projection), gently breathing.
   The cloud rotates slowly on the Y axis.
2. **One-hand pinch (Chin Mudra)** — a single visitor pinches thumb-to-index.
   All fish collapse to a single point (unity).
3. **Two-hand Hakini** — two visitors touch all 5 fingertip pairs across each
   other, OR one visitor does it alone across their own body. The fish
   reorganize into the slowly-rotating shape of a **herring**, with warm-colored
   dreams in the tail and dorsal stripe, blues in the body, greens in the fins.

Release any gesture: the fish spring back to UMAP positions.

---

## How you get the visual into Resolume

Darren's TD has an **NDI source** named `salish_dreamworld_mac`. In Resolume:

1. Open the Sources panel (top-left of Resolume's UI).
2. Find **NDI** in the source list.
3. Look for `salish_dreamworld_mac` — it should be there if Darren and you are
   on the same LAN.
4. Drag it onto any Resolume layer.

If it doesn't appear, ask Darren to plug Mac → his ethernet hub directly via
USB-C cable (NDI sometimes needs same-subnet for auto-discovery).

---

## What you can do during the set

### Mix the dreamworld in and out

Treat `salish_dreamworld_mac` like any Resolume video source: crossfade with
your other layers, blend modes, FX chains, the works.

### Cue the herring transformation

You don't need to do anything technical to trigger the herring — visitors do
it with their hands in front of Darren's webcam. But you can **time your set
around it**. When you want the herring moment:

- Cue Darren (or a visitor) to do Hakini in front of the camera
- The transition from cloud → herring takes ~1 sec
- The herring rotates slowly (~45 sec for a full revolution) — perfect for a
  long held note or a pad
- When the gesture releases, the dreams swim home over ~1.5 sec

### Drive the rotation rate (if Darren has time)

The cloud rotates at 8°/sec by default. If you want faster/slower for
performance, ask Darren to flip a knob in TD textport:

```
op('/project1/salish_dreamworld/dream_cloud').par.ry.expr = 'absTime.seconds * 16'
```

(16°/sec = 22.5 sec full rotation; 4°/sec = 90 sec; etc.)

---

## Kill switches — if anything looks wrong

Three optional behaviors are layered on top of the basic Hakini-herring. If
any of them misfires under venue lighting, Darren can disable that one only,
keeping the rest working. From TD textport:

```python
# Turn OFF B-light asymmetric break (most likely to misfire)
op('/project1/salish_dreamworld').store('hakini_bilateral', 0)

# Turn OFF per-fish orientation (if fish are facing weird directions)
op('/project1/salish_dreamworld').store('orient_fish', 0)

# Turn OFF swim wiggle (if it looks too jittery)
op('/project1/salish_dreamworld').store('swim_wiggle', 0)
```

Each toggle takes effect within 1 frame (~17 ms).

To turn them back ON, replace `0` with `1`.

---

## What NOT to touch

- **Don't save the .toe file.** When closing TD, click "Don't Save." The patreon
  source file must stay clean for Sunday's exhibition cleanup.
- **Don't move the MacBook during the set** — it's hand-tracking via webcam, so
  the camera angle matters.
- **Don't change `hakini_bilateral` to 1 unless Darren has run the morning
  preflight.** The asymmetric-break detection requires MediaPipe at
  num_hands=4 / num_faces=2 which can drop FPS in some configurations.

---

## If TouchDesigner crashes

Darren has a recovery script. Total time from crash to restored visual: **~30
seconds**. He'll handle this; don't touch his Mac unless he's away.

If he's away and you have to: paste the recovery snippet from
`~/projects/salish-sea-dreaming/scripts/dreamworld_callback/RESTART.md`.

---

## The deeper version, for the talk

If audience members ask you what's happening:

> The fish are visitor dreams from the whole exhibition — every prompt
> someone wrote during the run, embedded into 3D semantic space. When two
> visitors do the Hakini mudra together, the dreams briefly arrange themselves
> into a herring — the keystone forage species of the Salish Sea, the body
> that holds the food web together. The mudra is sympoiesis: making-with.
> The dreams are still themselves; they have just briefly been arranged in a
> way that lets them also be a herring.

There are three writeups in `docs/digital-ecologies/`:
- `mudra-as-sympoiesis.md` — the full essay
- `mudra-relational-map.md` — how the gesture relates to everything else
- `mudra-and-joint-commitment.md` — the philosophical trajectory

The chat agent at `salishseadreaming.art` can answer visitor questions from
those.

---

## Contact

If anything goes wrong during the set: Darren is on stage with you. If he's
not reachable: text the Salish Sea Dreaming Signal group.

— Have a beautiful set, Prav.
