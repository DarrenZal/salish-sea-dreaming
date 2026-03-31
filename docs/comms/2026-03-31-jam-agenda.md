# SSD Jam — March 31, 2026

**Time:** 1:00-2:00pm, then 3:00-5:00pm (Prav has Indigenomics meeting 2-3pm)
**Who:** Darren, Prav, Shawn
**Where:** Remote / Prav's studio

---

## What Changed Since Last Message (March 27)

1. **Leo + Prav got StreamDiffusion working at 30fps in TD 2025** — real-time style transfer breakthrough
2. **Shawn posted 16 handoff files** on shared Drive (7 stills, 8 videos) — video 48 is the curator hero
3. **Curator wants to see production quality** to determine exhibition space allocation
4. **Moonfish high-res from Deirdre** — expected any day
5. **Poetry DATs** — Prav drafted two prompt docs for SD in TD
6. **Website** — Shawn proposed landing page, Prav suggests SalishSeaDreaming.MOVE37XR.org

## Decisions Needed

### 1. Is the Briony LoRA actually expressing?
Prav asked if the LoRA contains Briony-specific weight data. It does — but requires:
- Trigger token `brionypenn` in prompt
- 8-20 inference steps (not 4)
- LoRA loaded in StreamDiffusion (not just in the folder)

**Action:** A/B test — run StreamDiffusion with and without `brionypenn` in prompt, screenshot both. If no difference, LoRA isn't loading.

### 2. Curator Demo
- What is video 48? Is it ready to show the curator?
- When is the projection test — Tuesday or Saturday?
- Do we need anything else for the curator beyond video 48?

### 3. Technique Lock
Original plan: Round 1 micro-renders on 3060 → technique pruning gate → lock by April 1.
Reality: StreamDiffusion 30fps working + Shawn's ComfyUI/RAVE outputs exist.

**Proposed lock:**
- **Real-time wall:** StreamDiffusion + Briony LoRA in TD (if LoRA is expressing)
- **Pre-rendered hero sequences:** ComfyUI + LoRA (Shawn's pipeline)
- **Fallback:** Raw Moonfish footage (already beautiful)

### 4. Moonfish High-Res
- Status from Deirdre?
- Pipeline ready to process on arrival (Shawn confirmed ComfyUI warm on Legion)

### 5. Weekend Plan (Fri-Sun at studio)
- Who can make it?
- What must be done in-studio vs remote?
- Priority work for the weekend?

### 6. Website
- Domain: SalishSeaDreaming.MOVE37XR.org? Standalone?
- Phase 1 = landing page? Or interactive from the start?
- Who builds it?

---

## Status Board

| Track | Owner | Status | Blocker |
|-------|-------|--------|---------|
| StreamDiffusion real-time | Prav + Leo | 30fps working | LoRA expression unverified |
| Pre-rendered hero sequences | Shawn | 16 files posted, video 48 = curator hero | — |
| ComfyUI/RAVE pipeline | Shawn | Warm on Legion | Moonfish high-res files |
| Moonfish high-res footage | Deirdre → team | Pending | Waiting on Deirdre |
| Poetry DAT → prompt system | Prav | Two Google Docs drafted | TD integration TBD |
| OSC data engine → TD | Shawn | Built, not integrated | Needs walkthrough with Prav |
| RTX 3090 readiness | Prav + Leo | TD 2025 working (Leo session) | ControlNet + LoRA untested |
| Credits/attribution | Darren | Draft done (`docs/credits-attribution.md`) | Permission confirmations |
| Curator projection test | Prav | Planned Tue or Sat | — |
| TELUS hyperscaler | Shawn | Status TBD | — |

## Technical Verify (at jam or this week)

- [ ] StreamDiffusion + `brionypenn` trigger token — does Briony style appear?
- [ ] Compare with/without trigger — screenshot both
- [ ] Review Shawn's 16 handoff files — which are exhibition-ready?
- [ ] OSC pulse walkthrough (Prav requested from Shawn)
- [ ] RTX 3090 ControlNet + LoRA test
- [ ] Poetry DAT → how poems feed SD prompt system (A/B weighted blending from Leo notes)

---

## Intent Field Concept (for discussion)

Darren wrote up `docs/intent-field-installation.md` — connects directly to ideas from Prav's Leo session:
- "have people who enter the space become part of the dreaming"
- "QR code app using phone as voice/image device"
- "take a selfie and one becomes part of the dreaming"

**The concept:** Visitors voice their care for the Salish Sea. Each voice becomes a herring (Boids algorithm in TD). Herring with related intents school together. Over 16 days, a dark ocean fills with a constellation of collective care.

Technical path: Whisper.cpp (local transcription, ~1s) → TouchDesigner Boids (CHOP or GLSL compute) → Moonfish backdrop + Briony LoRA styling.

**Question for Prav:** Does this serve the artistic vision? What's the minimal proof-of-concept?

---

## Next Actions (assign at jam)

| Action | Owner | By When |
|--------|-------|---------|
| A/B test LoRA with trigger token | ? | Today |
| Confirm Moonfish permission (written) | Prav | This week |
| Confirm Denning permission (written) | Prav | This week |
| Curator projection test | Prav | Tue or Sat |
| Process Moonfish high-res on arrival | Shawn | On arrival |
| OSC → TD integration | Shawn + Prav | Weekend |
| Website domain decision | Team | This week |
| Intent field proof-of-concept? | TBD | TBD |
