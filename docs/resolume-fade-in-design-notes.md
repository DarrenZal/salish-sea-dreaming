# Resolume fade-in design notes (for Tue morning session with Prav)

Deferred deploying `td_relay_v2.py` + `resolume_fade.py` on 2026-04-20 evening after
discovering the fade behavior would almost certainly misbehave against the
current live composition. Captured findings here so Tuesday morning's session
with Prav can land the feature correctly on the first try.

## What works remotely today (already proven)

- Visitor submits prompt via web app → gallery server (poly) queues it → `td_relay.py`
  polls `/td/next?after=N` → sends OSC `/salish/prompt/visitor <prompt_text>` to
  the 3090 at 127.0.0.1:7000 → TouchDesigner's prompt_sequencer catches it →
  overwrites StreamDiffusionTD's `Promptdict22concept` parameter → StreamDiffusion
  regenerates imagery reflecting the prompt → NDI-streamed to Resolume → wall.
- Prompt -> wall latency ~5s end to end (per today's test with "more oysters
  on the beaches"; user confirmed visible oyster imagery on wall after submit).

**The existing chain works.** We don't need to change any of that.

## What's missing

**Visibility cue.** The wall doesn't obviously *signal* to the visitor that their
prompt landed. The TD layer is blended with Autolume + other content at
whatever opacity Resolume's auto-mode assigns at that moment. Visitors can't
tell "that's my dream on the wall" vs "that's the ambient rotation".

The fix Prav + Darren originally envisioned: when a visitor prompt arrives,
*fade the TD layer to full opacity briefly* so the visitor sees their dream
clearly, then fade it back down to the normal ambient mix.

## Where the fade-in code lives

- `scripts/resolume_fade.py` — `ResolumeFader` class. Sends
  `/composition/layers/{N}/video/opacity` OSC messages to Resolume at 127.0.0.1:7001.
  Arena's OSC input is enabled on port 7001 (verified Mon 2026-04-20 from
  `Preferences/osc.xml`).
- `scripts/td_relay_v2.py` — already wires the fader into the poll loop.
  `fade_in()` fires when a prompt is received (line 329); `fade_out()` fires after
  `FADE_IN_SECS` seconds (line 366).

## The problems we need to resolve with Prav on-site

### Problem 1: fade_out() ramps to 0.0, not a saved baseline

`ResolumeFader.fade_out()` ramps opacity to absolute 0.0 — i.e. invisible.
That's wrong if the TD layer's normal auto-mode opacity is anything non-zero
(a blend with another layer, full opacity for ambient playback, etc.). After
every visitor fade-out the layer would be locked at 0.0 opacity; the wall
would turn black (or show only non-TD layers) until Resolume's auto-mode next
overrode the opacity parameter.

**Fix needed:** before first fade_in, snapshot the current opacity value;
fade_out ramps back to that snapshot. Or have fade_out set opacity based on
a config-specified "baseline" value.

### Problem 2: auto-mode interaction is unknown

Resolume has an "auto mode" for the composition (Autopilot column advance,
clip-level automations, possibly parameter modulation). If the TD layer's
opacity is being driven by an auto-mode parameter modulator, our OSC writes
get overridden on the next tick. We don't know from outside whether the
current composition uses this.

**Need Prav to confirm on-site:** is the TD layer's opacity being driven by
any automation, or is it just a static baseline Resolume doesn't touch?

### Problem 3: which layer is the TD layer?

The composition has 5 top-level Layer slots (per the .avc XML inspection).
All are named generically "LayerView" (UI panel name, not the actual layer
name). All clips are named generically "Clip". NDI source references in the
XML show **TouchDesigner (768×768)** and **Autolume Live (512×512)** are BOTH
used across multiple clips, potentially in multiple layers.

So the TD content isn't a single layer — it's scattered. Setting opacity on
layer 1 (what `resolume_fade.py` defaults to) may not actually affect the TD
content we want to highlight, and may affect Autolume content we *don't* want
to touch.

**Need Prav to confirm on-site:**
- Which layer index (1-5) contains the StreamDiffusion / TD output?
- Is the Autolume output on a separate layer, or the same one?
- Are there any "dedicated visitor reflection" clips/columns in the
  composition, or does visitor content just flow through the same TD layer?

### Problem 4: does Prav want a dedicated "visitor layer"?

A cleaner architecture: add a NEW layer to the composition that's dedicated
to visitor reflections, normally at opacity 0 (invisible), and fade_in brings
it to 1.0, fade_out returns it to 0. Avoids all the auto-mode interaction
because this layer has no auto-mode automation on it.

Trade-off: requires composition edit; Prav would need to route TD NDI into
that new layer (or duplicate an existing TD clip into it); might impact the
existing column automation if present.

## Proposed Tuesday morning session (~30 min with Prav)

1. **Survey** (5 min): Prav shows me the composition in Arena — which layer
   is TD, which is Autolume, what's the auto-mode doing.
2. **Decide** (5 min): pick one of:
   a. Single layer + save-baseline-and-restore (lower effort, may fight with
      auto-mode).
   b. Dedicated visitor layer added to the composition (cleaner, needs
      composition edit).
3. **Implement** (10 min): patch `resolume_fade.py` with the chosen approach.
   Deploy `td_relay_v2.py`. Kill the duplicate td_relay.py instances from
   April 17.
4. **Validate visually** (10 min): submit a test prompt from phone; Prav
   watches wall; confirm fade-in timing feels right + fade-out returns to
   proper baseline.

## Additional cleanup Tuesday

- **Kill 4 duplicate td_relay processes** — there are 2 instances from Apr 17
  (different Python environments: streamdiffusion-env + Program Files/Python310)
  both polling. They don't double-fire prompts today only because the PID lock
  file is respected, but it's messy. After deploying td_relay_v2 cleanly, we
  should have exactly 1 polling instance.

## What I tested tonight and what remains unverified

**Tested tonight:**
- Arena prompt-suppression (launch_resolume.bat v2) — Arena log confirms
  composition auto-loads, no modal. ✅
- Tunnel watchdog recovery — killed ssd_ssh_tunnel.ps1 parent + ssh children,
  watchdog detected within 2 min, auto-restarted SSD-SSH-Tunnel, full outage
  ~2:10. ✅
- TD + Autolume watchdogs v2 — deployed, heartbeats writing. Will be exercised
  the next time either process dies. ✅

**NOT tested / still deferred to Prav visual check Tuesday AM:**
- AHK kick actually toggles Advanced Output (only AHK log confirmed "OK").
- Dongle's EDID emulation vs passthrough mode (requires physically powering
  BenQ off).
- td_relay_v2 fade-in visually correct (requires composition walkthrough
  first — see above).
