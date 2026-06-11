# John Install Checklist — Salish Sea Dreaming @ HRMSC Hubble Space

**Status: DRAFT — for joint Darren + Prav editing on the 2026-05-14 evening call.**
Not a locked plan. Tiers and gates below are a *proposed* starting point to react to, not decisions.

---

## How to read the tiers

The tiers are an **install-risk sequence**, not a value or priority ranking.

John's philosophy (2026-05-14 call): *secure a base that cannot fail, then build up
level by level — if everything craps out, the base still runs.* So Tier 0 is the
floor you stand up first because it has the fewest dependencies, **not** because it
is the most important part of the show.

In particular: **the visitor app + MediaPipe mudra system are primary show surfaces**,
core to the "Salish Sea perceiving itself" interactive vision (Prav-confirmed). They
appear at Tier 3 only because they carry the most live dependencies and are sequenced
last for install safety — that is risk-ordering, not a demotion.

**Key dates**
- John on-site at HRMSC for projector test: **Tue 2026-05-19**
- Install window: **May 22–24** · Doors: **~May 25** · IMPACT: **May 27–28**
- Austin curated assets expected to the team: **~Mon 2026-05-18**

---

## Tier 0 — MVP base (the must-not-fail floor)

A single projected video loop + stereo sound. No live systems, no network, no GPU at
show time. This is what runs if literally everything else falls over.

| Item | Detail | Owner | Status |
|---|---|---|---|
| Hero loop video | Seamless loop, exhibition-safe. Candidate: `H1_salmon_school.mp4` (1080p) or a styled loop | Darren | clip in hand; loop/grade TBD |
| Ambient audio | Stereo loop, length-matched or independently looping | Prav / Darren | source TBD |
| Playback method | Resolume on the show machine, or a dead-simple media player as ultimate fallback | Prav + John | decide on call |
| One projector, known-good | Whatever the venue can reliably give us first | John (on-site) | May 19 test |
| Run-to-run survival | Loop + audio auto-start, survives reboot | Darren | proven pattern from Phase 1 |

**Gate to Tier 1:** Tier 0 plays unattended for a full day without intervention.

---

## Tier 1 — Proper projection

The "blame the projectors if it's blurry, then fix the projectors" layer. Real
resolution, real mapping, multi-projector if the wall needs it.

| Item | Detail | Owner | Status |
|---|---|---|---|
| Projector test | Resolution / colour / geometry characterised on the real units | John | **test pack ready** — see below |
| Rent vs bring-own | Venue 720p was unacceptable; resolution issue reportedly now resolved (Tobias) — reconfirm | Prav / John | open |
| Projection mapping | Resolume Advanced Output for the wall | Prav | Phase 1 stack intact |
| 4K content path | Do we need true-4K masters for May, or is 1080p upscaled acceptable? | **decide on call** | open |
| Union install coordination | Venue uses union crews — schedule into May 22–24 | Prav / venue | open |

**Test pack for John (ready now):** `austin-reference/john-test-pack_2026-05-14/` (+ `.zip`)
- `calibration/synthetic_projector_test_4k.png` — 4K calibration baseline
- `video/H1_salmon_school.mp4` — real show footage, **1080p not 4K**
- Pending: a true-4K landscape stand-in (friend's "Vancouver Island 4K" — not yet in hand / licence-cleared)
- Optional on request: AI stress plates from `john-projector-test-pack-v1_2026-05-13/`

**Gate to Tier 2:** projectors mapped, a real clip looks good on the wall.

---

## Tier 2 — Austin content + curated show sequence

Austin's formline work, the pearl / Thunderbird teaching framing, Track 2
deterministic morphs, style-transfer v2 LoRA outputs. This replaces the Tier 0
placeholder loop with the actual curated show.

| Item | Detail | Owner | Status |
|---|---|---|---|
| Austin curated drive | Vector files / isolated forms | Austin → Prav/Natalia | contract in progress; ~Mon May 18 |
| v2 LoRA pipeline | `scripts/austin_v2_pipeline.py` — operator-ready, ~45 min to evaluated LoRA once files land | Darren | rehearsed, waiting on drive |
| Track 2 morph engine | `track2-deterministic/` — deterministic primitive morphs | Darren | dry run complete |
| **Per-output consent gate** | **Nothing public without Austin's per-output sign-off — this is the floor, not a milestone (per `feedback_austin_consent_trust_floor`)** | Darren + Prav | standing rule |
| Public-facing language | "pearl", "teaching", "three shapes" framing also needs Austin review | Prav | drafts pending |

**Gate to Tier 3:** a curated, Austin-approved sequence runs as the base loop.

---

## Tier 3 — Interactivity (PRIMARY show surface — sequenced last for install safety only)

The visitor app and MediaPipe mudra system. Core to the show's vision; sequenced here
because they carry the most live dependencies (GPU on-site, network, OSC, real-time AI).

| Item | Detail | Owner | Status |
|---|---|---|---|
| Visitor web app | QR → browser → prompt → OSC → live visuals | Darren | v5 spec exists; **code review for IMPACT context not yet done** |
| MediaPipe mudra system | Hand-tracking → live visual control | Darren | Phase 1 `hand_pos` bridge proven |
| Live AI layer | Autolume + StreamDiffusion | Darren | Phase 1 stack intact, dormant |
| On-site GPU box | 3090 (currently at Prav's Salt Spring studio) travels to Vancouver? Or 5090 build? | **decide — see hardware** | open |
| Auto-heal / resilience | Self-healing chain from Phase 1 | Darren | proven ~99% |

**Gate:** interactivity layered on top of an already-proven base — never replacing it.

---

## R&D / field-research layer (genuine stretch / next iteration)

Live bioregional data feeds (`scripts/bioregional_osc_bridge.py`), the full cybernetic
"Dreaming Mind" vision. Explicitly not May-critical — protect the lower tiers first.

---

## Hardware decision (cross-cutting)

- Tiers 0–2 run off **pre-rendered video — no GPU at show time.**
- Tier 3 needs a **GPU box on-site in Vancouver.** The 3090 is at Prav's studio on
  Salt Spring. Options: transport the 3090, or the 5090 build (sponsor-framed,
  ~$11.7K CAD turnkey — procurement would need to move immediately for a May soak).
- **Decide on call:** is the 5090 May-primary, Phase 2.1, or sponsor-R&D narrative only?

---

## Open decision points for tonight's call

1. **Video set for John** — H1 (1080p) + calibration plate now; 4K stand-in pending. Send curated or "the whole thing"?
2. **1080p vs 4K** for the May underwater material — acceptable upscaled, or do we need 4K masters?
3. **John's contact channel** — how does the pack physically reach him? (he's now on the email thread: john@desnoyers.ca)
4. **Friend's "Vancouver Island 4K"** — quick written-permission ask, or keep it test-only?
5. **3090 vs 5090** for on-site Tier 3 — and does the 3090 travel?
6. **Two Friday calls** — does today's SSD-install call merge with the Austin/Dan/Darren/Pravin dome-Longhouse call?
7. **John's "render lag"** (raised in the Longhouse thread) — what is actually rendering slow, in what software? Resolve *what it is* before offering render infrastructure.

## What John needs from us / what we need from John

- **To John:** the test pack (Tier 1), the install checklist (this doc), clarity on what the May show actually is
- **From John:** projector characterisation from the May 19 test, his read on rent-vs-bring-own, what his render-lag bottleneck actually is
