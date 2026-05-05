# Salish Sea Dreaming — Venue / Phase 2 Strategy

> Drafted 2026-05-04 from project `CLAUDE.md`, post-show meeting notes, and the auto-memory file. Sequences the four-venue trajectory Prav has named and the touring kit needed to make it real.

## The arc

```
2026-04 Mahon Hall (DONE) → 2026-05 Indigenomics → 2026-10 MOVE37XR → 2026-11 DEVCON → 2027 Life at the Center
   proof of concept         soft re-deploy         full installation     ceremony chamber    flagship
```

Each venue answers a different question:

- **Mahon Hall** — *can we run an autonomous gallery installation reliably for 3 weeks?* (Yes, mostly.)
- **Indigenomics** — *can we re-deploy in <4 weeks with minimal rebuild?*
- **MOVE37XR** — *can we ship a full installation with Indigenous co-authorship in territory?*
- **DEVCON** — *can the three-layer architecture (Brad agentic + Darren KOI + Shawn blockchain) hold up under live demo?*
- **Life at the Center 2027** — *can the work hold a year-long flagship gallery context?*

---

## 1. Indigenomics Impact Summit (May 2026)

**Curator:** Carol Anne Hilton.
**Runway:** ~3–4 weeks from today (2026-05-04).

**Recommended shape: ~~full installation~~ → sample reel + talk + interactive 1-projector demo.**

Rationale: 3–4 weeks is below the floor for a full re-deploy. The 3090 is currently in dev mode (`installation-archive/` contains the Mahon config; restoring is ≥2 days but the touring kit is uncalibrated for a new room). Better play: ship the Mahon Hall hero reel + a stripped-down single-projector autonomous mode + a Carol-Anne-framed talk. **Austin's involvement is contingent**: if the first call lands well and he's available, integrate one of his Salish Spirit-style overlays into the demo loop.

**Decisions needed by 2026-05-08:**

- Full installation vs reel + talk? (Recommend reel + talk.)
- Is Austin in for May, or is May the discovery call only?
- Does Carol Anne want the *Kwaxala* economic framing (forage-fish-worth-more-swimming) foregrounded, or kept in the artist statement?

**Assets ready today:** Mahon Hall hero reel (Moonfish + Denning + GAN composites), gallery server (poly), three TD scenes from 2026-04-23, visitor web app.

---

## 2. MOVE37XR Symposium (October 2026)

**Territory:** Sḵwx̱wú7mesh (Squamish).
**Runway:** ~5 months. The big one for a full multi-track build.

**Recommended shape: full installation with Coast Salish co-authorship.**

This is where Tracks A/B/C/D (technical roadmap) all land:

- **Track A** (touring resilience) — must be locked.
- **Track B** (visitor memory) — Mahon dreams continue here; visible cross-venue continuity.
- **Track C** (VVVV) — decision made by mid-summer; whichever tool wins, the build is on it.
- **Track D** (Austin + Halact) — Austin's consent map is in hand; Halact's relationship is established by Prav; the cultural-lens overlay is real, not speculative.

**Cultural protocol weight:** highest of any venue. Squamish territory + Squamish artist + Squamish collaborator named (Halact). Non-negotiable: every motif used has explicit consent; every elder named has been consulted; the show opens with proper protocol if Halact and Austin direct it.

**Open questions for Prav:**

- Is Halact's relationship Prav-direct, or routed through Austin?
- Is the symposium venue indoor / outdoor / dome / multi-room? (Affects projector count, audio, and whether DEVCON's "ceremony chamber" framing applies here too.)
- Funding: which of {MOVE37XR org, Indigenomics, Canada Council mid-cycle, sponsorship} covers the gap?

---

## 3. DEVCON ETH Mumbai — Indigenous Technology House (November 2026)

**Runway:** ~7 months.

**Recommended shape: ceremony chamber stress-test of the three-layer architecture.**

This is the venue where Brad's agentic storytelling engine + Darren's KOI + Shawn's blockchain memory substrate (per 2026-02-27 architecture conversation) finally meet under live load. ETHCON crowd reads "blockchain memory" with the technical literacy to actually engage with what's happening, which makes it the right venue to risk that integration.

**Open questions:**

- Does Indigenous Technology House have curatorial alignment with the bioregional thesis, or is it primarily an Indigenous-tech showcase?
- Is the "ceremony chamber" a dome / blackbox / AV-tracked stage?
- Does Shawn's cards ontology need on-chain anchoring by then, or are testnet artifacts enough for the demo?

**Assets new for this venue:** Brad's storytelling engine integration; Shawn's cards ontology surface; KOI ingest of accumulated visitor prompt memory (Track B harvest).

---

## 4. Life at the Center 2027

**Runway:** ~12+ months.

**Recommended shape: full year-out flagship; site-grounded; grant-funded.**

Three planned site visits (per `CLAUDE.md` and `project_exhibition_pivot.md`):

1. **Salmon run** (autumn) — Moonfish underwater cinematography continues.
2. **Nettie Wiles event** — community-facing.
3. **Briony rewilding drawings** — new corpus material.

**Grant targets:** Canada Council for the Arts, Canadian Media Foundation. Pre-application work begins **now** (typical CCFA cycle is 6–9 months).

**Architectural commitments by end of 2026:**

- Three-layer stack (Track D + DEVCON learnings) is production-grade.
- Cultural protocol map is canon (every motif, every collaborator, every territory).
- Touring kit MVP (§5) is documented to the point a third party could redeploy it.

---

## 5. Touring kit — minimum viable spec

What must move with us across venues; what gets re-rented; the deploy-in-<8-hours runbook.

### Travels with us (in custody of Darren / Prav)

| Item | Why | Notes |
|---|---|---|
| **3090 desktop (current build)** | StreamDiffusion + Autolume + auto-heal stack | `installation-archive/` is the canonical config; restore via task-scheduler re-enable |
| **`installation-archive/` snapshot** | re-deployable Task Scheduler XMLs + scripts + .toe lineage tips | Already at commit `ba94a83`; back this up off-Mac too |
| **Visitor web app codebase** | gallery server on poly | poly is internet-hosted, doesn't move physically, but the code does |
| **iNat + Briony + Moonfish corpora** | dreaming model inputs | `images/`, `training-data/`, `briony-lora/` (gitignored mostly) |
| **Reverse-tunnel config** | remote ops from anywhere | WireGuard primary, poly:2222 fallback |

### Re-rented per venue

- Projectors (count varies by room — 1 for Indigenomics, ≥2 for MOVE37XR)
- Speakers + audio interface (3090 has no mic, audio must come from venue PA or rented)
- Blackout fabric / staging / rigging
- BenQ EDID dongle (THWT 4K-EWD) for any troublesome HDMI path — see `project_edid_dongle_model.md`

### Deploy-in-8-hours runbook (target)

The Mahon deploy was multi-day. The MVP target for any subsequent venue is **8 hours from gear-on-floor to running autonomous loop**:

1. **Hour 0–1:** unpack 3090, mount projectors, run cabling, verify HDMI/EDID.
2. **Hour 1–2:** boot, verify Task Scheduler tasks fire (auto-launch + auto-heal).
3. **Hour 2–4:** color/keystone calibration; Resolume Advanced Output mapped to room.
4. **Hour 4–6:** audio level check (WASAPI loopback monitor — Track A); visitor-app QR test from venue Wi-Fi.
5. **Hour 6–8:** soak run with synthetic visitor prompts; verify auto-heal triggers and recovers.

This is aspirational; achieving it depends on Track A landing.

---

## 6. Cultural protocol per venue

Different territories, different protocols. Not a generic touring problem.

| Venue | Territory | Protocol owner | Notes |
|---|---|---|---|
| Mahon Hall | WSÁNEĆ / Salt Spring | Curator (Raf) + Briony's land relationships | Already navigated |
| Indigenomics | TBD (Northeastern University setting) | Carol Anne Hilton | Indigenomics framing carries the protocol |
| MOVE37XR | Sḵwx̱wú7mesh (Squamish) | Halact + Austin + Squamish Nation | Highest weight; opens with elder protocol if directed |
| DEVCON | Mumbai (no Indigenous-bioregional protocol native to the work) | Indigenous Technology House curator | Cultural translation for non-Coast-Salish audience |
| Life at the Center 2027 | TBD by site | Site-specific | Grant proposals must name protocol owner explicitly |

**The non-negotiable:** every venue's intro/announcement names the territory, the artists, and the collaborators, in that order. No exceptions.

---

## What needs to happen this week (2026-05-04 → 2026-05-11)

1. Send the Austin brief (`austin-collab-brief.md`) to Prav for review.
2. Decide Indigenomics shape (full / reel+talk / pass).
3. Confirm Austin's availability for May vs October-only.
4. Start Track A (Resolume automation) — even if Indigenomics is a reel-only show, the touring kit starts here.
5. Carol Anne intro: confirm Indigenomics dates + venue spec.

## Out of scope

- Booking flights / shipping logistics (Prav drives).
- New venue prospecting beyond the four named.
- Any commercial licensing of the work (this is a research / cultural project).
