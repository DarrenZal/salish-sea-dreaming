# Style-Transfer Pilot — Austin's Register

**Status:** STAGED 2026-05-13. Awaiting 3090 reachability for execution.

**Origin:** Prav's 2026-05-13 06:51 PDT email — *"Please get started on still and motion with Austin's style. We need teasers for the social media and this is the make or break for this version. ... We really need to get the Style Transfer into the TD stream diffusion. Ie that cannot look like generic."*

## Posture

- **Internal experiments only** until Austin's curated Drive folder lands AND/OR Austin OK's specific outputs per `austin-consent-map.md`. Source = `austin-reference/` (127 images scraped 2026-05-04 from indigitaldesign.ca public portfolio).
- **No public-facing render OR social-media post** without Austin per-piece OK, even if the output looks good.
- **Cultural floor:** treat experiments as design sketches, not finished work. Show Austin via Signal screenshare before any external use.

## Hero pieces selected for pilot (5)

Drawn from austin-reference/ subdirectories. Choice criteria: visually self-explanatory crests + commercial/public provenance (not clan-restricted) + structural variety to test morph anchors.

| # | Piece | Folder | File(s) | Why chosen |
|---|---|---|---|---|
| 1 | **Salish Spirit @ VanLive!** | `salish-spirit/` | RobsonLive_SalishSpirit_01–04.jpg | Closest SSD precedent — Austin's own large-format projection work; 4 sequence frames are gold for morph-anchor extraction |
| 2 | **Westridge Orca** | `westridge-elementary/` | (15 files) | Orca = Phase 1 audience favorite; commercial school commission; clean primitives |
| 3 | **Whitecaps Sínulhka** (Two-Headed Serpent) | `whitecaps/` | (10 files) | Public commercial crest (FC Vancouver); high recognition; strong serpentine line work |
| 4 | **KwiKwi (Thunderbird)** | `kwikwi/` | (17 files) | Largest piece set; relates to pearl-vision Thunderbird; ceremonial weight — flag for explicit Austin OK |
| 5 | **MST Justice Centre — Plant series** | `mst-justice-centre/` | ChocolateLillies, RedCedar, StingingNettle, Wapato (8 files) | Plant motifs add ecological/bioregional bridge to Salish Sea theme; matched description+design pairs |

## Two pipelines to spike in parallel

### Pipeline A — img2img + ControlNet over Austin's vectors (fast, no train)
- Pass Austin source image as ControlNet lineart conditioning at high weight (0.8–1.0)
- SD prompt: bioregional content (kelp forest / herring cloud / orca pod) in Austin's register (color palette extracted from his pieces; line treatment cued by ControlNet)
- Denoise sweep: 0.25 / 0.35 / 0.45 / 0.55 — find the point where bioregional content emerges while formline structure stays legible
- Expected outputs: 5–10 still teaser candidates per hero piece, generated in ~30s/frame on 3090
- **Hardware:** 3090 with existing SDTD stack; ControlNet model needs verification (may need to pull)
- **Risk:** "generic" failure mode that Prav explicitly called out. Mitigation: keep line conditioning weight high; don't let SD invent new formline shapes.

### Pipeline B — LoRA training on Austin's portfolio (slow, higher fidelity)
- Train SD 1.5 LoRA (rank 16, ~1000 steps, kohya_ss) on `austin-reference/` images
- Mirror the Briony LoRA recipe (proven on H200 March 31 — "AMAZING" verdict per Prav)
- Trigger: `austinharrystyle` or similar; weight 0.7–1.0 in prompts
- **Hardware preferred:** TELUS H200 (parallel Jupyter notebooks per the proven March pattern) — Carol Anne provisions access; deadline EOD today
- **Fallback:** 3090 overnight train; lower batch size, slower convergence
- **Cultural note:** Austin's curated Drive set, once it lands, is the canonical training source. Pilot trains on `austin-reference/` to prove the pipeline; full quality run waits for Austin's set + his per-output OK.

## What can be done locally now (Mac, no GPU)

- ✅ Asset selection + cropping/squaring to 512×512 (matches existing Briony LoRA prep)
- ✅ Caption file authoring for LoRA training (BLIP captioning + manual edits)
- ✅ ControlNet-input preparation: convert hero pieces to lineart maps via existing `tools/` scripts
- ✅ Prompt library drafting: bioregional content × Austin register

## What requires 3090 (BLOCKED on tunnel)

- ❌ img2img + ControlNet runs (SDTD stack lives on 3090)
- ❌ Local LoRA training (CUDA + ample VRAM)
- ❌ Live TD StreamDiffusion integration test
- ❌ Real-time preview iteration

## TELUS H200 — actually our primary execution path

**Correction 2026-05-13:** TELUS access has been in hand since early March. Token in `.env:Jupyter_REST_API`, 3 H200 nodes at `*-0b50s.paas.ai.telus.com`, full setup pipeline at `scripts/telus-style-transfer-setup.sh` + `scripts/telus-training-setup.sh` + `scripts/telus_style_server.py`. The "wait for Carol Anne to provision" framing from yesterday was stale — that provisioning happened months ago.

**What to do to use it:**
1. Go to `console.ai.telus.com` → start the pod(s) (auto-stopped to save credits)
2. SSH or web-terminal into pod → run `bash scripts/telus-training-setup.sh` to rehydrate ephemeral env (PyTorch + CUDA + compilers)
3. Upload austin-reference/ via the Jupyter REST API (`telus-style-transfer-setup.sh` template)
4. Run LoRA training + ControlNet img2img experiments in parallel across 3 nodes
5. Download outputs (storage is ephemeral — pull before pod restart)

**Capabilities once pods up:**
- ✅ Parallel Jupyter notebook LoRA training across 3 H200s (per March recipe — 600+ experiments in 4 days)
- ✅ Production-quality 30-step renders for hero motion clips
- ✅ Multiple concurrent experiments (img2img sweep + LoRA train + ControlNet validation in parallel)
- ✅ ControlNet + LoRA batch pipeline (proven primary path per `docs/style-transfer-guide.md` Option A)

**This means the 3090 is NOT a blocker for the style-transfer pilot's core work** — only for the *live TD SDTD integration* step (Days 5–7). Pre-rendered hero stills + motion clips can flow entirely through TELUS.

## Blockers + escalations

1. **3090 SSH tunnel down** as of 2026-05-13 09:30 — both `windows-desktop` (local) and `windows-desktop-remote` (poly reverse tunnel) refused connection. Last known good: scripts deployed 2026-05-03. Likely cause: tunnel task not running after a reboot, or poly forwarder issue. **Escalation:** Signal Prav to ask him to verify 3090 is powered + run `schtasks /run /tn "SSD-SSH-Tunnel"`. If unrecoverable, defer pilot execution until 3090 reachable.
2. **TELUS H200 access** — Carol Anne to provision. Plan deadline = EOD Day 3 (today). Worth a direct ask via Prav today.
3. **Austin curated Drive set** — pending Austin's compile per his May 11 email. Pilot can proceed on `austin-reference/` in the meantime; outputs internal-only.

## Acceptance criteria (Day 5 review with Prav + Austin)

- 5 still teaser candidates per hero piece (25 total) generated via Pipeline A
- LoRA from Pipeline B trained on `austin-reference/` (if TELUS unblocked) OR trained on first batch of Austin's Drive set (if it lands by Day 4)
- 2–3 motion clip drafts (5–10s each) showing Austin-register applied to bioregional content (kelp, herring, orca pod)
- **Quality bar:** outputs visibly carry Austin's line/color treatment, not "generic Coast Salish-ish" (Prav's explicit failure mode). Three independent reviewers (Darren + Prav + 1 other) agree on quality before showing Austin.
- All outputs internal; ZERO public-facing posts until Austin per-output OK.
