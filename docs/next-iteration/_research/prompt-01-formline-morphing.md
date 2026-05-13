# Deep Research Prompt #1 — Coast Salish Formline Morphing Techniques

**Best tools:** ChatGPT Deep Research, Claude.ai web-research, Gemini Deep Research. Run on 2+ and triangulate; save outputs as `prompt-01__chatgpt.md` / `__claude.md` / `__gemini.md` in this directory.

**Decision unblocked:** Which morphing technique we ship for May (recommend manual decomposition + TD interpolation as primary) and what we explore for MOVE37XR (October).

**Deadline:** 2026-05-13 (T+2 days from sprint start).

---

## Prompt (paste verbatim)

```
I'm a technologist collaborating with a Coast Salish digital artist (Austin Harry,
INDIGITAL Vancouver — Sḵwx̱wú7mesh Wolf Clan + Nam̓gis Thunderbird Clan) on a
3-projector installation at HR MacMillan Space Centre in Vancouver, late May 2026.
The piece will show morphing transitions between his Coast Salish crests (Wolf,
Whale, Eagle, Thunderbird, Salmon, Sínulhka/Two-Headed Serpent, etc.) using shared
formline primitives (crescents, ovoids, U-forms, split-Us, tertiary lines,
salmon-trout's-head) as morphing anchors. Cultural integrity is non-negotiable —
every intermediate morph frame must be composed of primitives that exist in the
source/target vectors; no AI-hallucinated shapes.

Research and report on:

1. Coast Salish formline grammar as a named, finite, combinatorial system
   (Bill Holm, Steve Brown, Cheryl Shearar as starting references). What are
   the exact named primitives, their compositional rules, and how does
   contemporary scholarship treat AI / generative-art uses?

2. State of the art in line-aware video metamorphosis (2025–2026) for
   "structure-aware" morphing where intermediate frames must respect a
   restricted shape vocabulary. Specifically:
   - SAGE (Structure-Aware Generative vidEo transitions) — Hungarian-algorithm
     line matching + B-spline trajectories
   - VTG (Versatile Transition Generation)
   - CHIMERA / FlowEdit (h-space directional analysis, selective masking)
   - CoDeF canonical content field
   - TouchDesigner SVG/SOP-based primitive interpolation
   - Blender Grease Pencil + SVG morph workflows

3. ControlNet lineart conditioning at low denoise strengths (0.25–0.45) for
   preserving formline integrity while allowing color/texture drift. Does
   SDXL ControlNet preserve Coast Salish line weights and crescent
   terminators, or does it smear them?

4. Cultural-protocol precedents — Indigenous artists who've worked with AI
   on their own iconography (positively or critically). What attribution,
   consent, and reversibility frameworks have they used? (Marvel/Kabam
   Chee'ilth precedent with Squamish Lil'wat Cultural Centre is one example
   to look up.)

5. Recommend a primary morphing technique + 1 fallback for a 2-week sprint,
   given the constraint that experiments stay internal until per-piece artist
   approval.

Deliverable: 8–12 page report with citations, worked examples where possible
(screenshots, code snippets), and a one-page decision summary at the top.
```
