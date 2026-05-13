# Deep Research Prompt #3 — Multi-Projector Composition + 3-Wall Narrative

**Best tools:** ChatGPT Deep Research, Claude.ai web-research, Gemini Deep Research.

**Decision unblocked:** How content is authored against the 3-wall canvas. Asset aspect ratios. Resolume composition layout.

**Deadline:** 2026-05-14 (T+3 days). Blocks asset production.

---

## Prompt (paste verbatim)

```
I'm designing a 3-projector installation in the Hubble Space at HR MacMillan
Space Centre, Vancouver, late May 2026. Existing venue projectors are 720p
and being replaced with 1080p (possibly 4K) units we'll rent. Single RTX 3090
desktop drives the stack: TouchDesigner + StreamDiffusion + Autolume + Resolume
Arena with Advanced Output. Audience is in transit (anteroom to a dome
theater), dwell times 30 seconds to 8 minutes.

Research and report on:

1. Triptych vs edge-blended panorama for 3-projector walls. Composition
   theory (retable / altar / triptych art history; contemporary public LED
   art; Austin Harry's own Salish Spirit @ VanLive! on the Robson/Granville
   LED screen). When does each work?

2. Resolume Arena Advanced Output configuration for 3-projector triptych
   and edge-blending. Concrete walk-through with screenshots. REST API +
   Windows COM API options for remote automation.

3. Spout vs NDI for 3-output rigs on a single GPU at 1080p × 3 and 4K × 3.
   Latency, bandwidth, fps under typical load. Best practices for
   multi-Spout-stream stability.

4. Inter-projector motion synchronization — timecode source, single-clock
   controllers, OSC heartbeat patterns, how to prevent visible drift
   between surfaces in a triptych composition.

5. Anteroom audience gaze choreography — research on transit-audience
   attention patterns (museum studies, retail signage, transit-space art).
   Where does the eye land in a triptych for an audience walking past?

6. Edge-blend calibration in practice — color matching, luminance matching,
   geometric alignment for mismatched-projector situations and for matched-
   projector situations.

7. Single-GPU multi-output limits for 3090-class hardware running
   Resolume + TouchDesigner + StreamDiffusion concurrent.

Deliverable: 8–12 page report with fps-budget tables, Resolume screenshots,
inter-projector sync diagrams, and a one-page recommendation summary
covering: triptych or edge-blend; target resolution per projector; sync
strategy; calibration workflow.
```
