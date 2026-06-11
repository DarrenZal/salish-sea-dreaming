# Fact-checks (2026-05-13)

> Targeted verification of 4 claims that have been load-bearing in plans, research prompts, or sponsor-facing docs. Captured here so future-me doesn't have to re-search; flagged where reality differs from internal claims.
>
> Triggered by `feedback_verify_pricing_before_sponsor_facing.md` discipline — verify before relying.

## 1. Orbbec Femto Bolt + TouchDesigner 2025 — ✅ CONFIRMED

**Claim:** Orbbec Femto Bolt is a usable Azure Kinect replacement in TouchDesigner 2025.

**Verified:** Yes, well-supported. Two integration paths:

- **Native Orbbec TOP / Orbbec Select TOP**: streams color, depth, and point cloud from Femto Bolt and most other Orbbec cameras
- **Kinect Azure TOP / CHOP** with `Hardware = Orbbec`: routes Femto Bolt through Microsoft's Body Tracking SDK for skeleton tracking + player index

**Caveat (don't miss this in implementation):**
> "It is not recommended to use the Kinect and native Orbbec nodes together in the same project. If you need skeleton tracking, use only Kinect Azure nodes to access the Orbbec cameras." — Derivative docs

**Implication:** if mudra/skeleton work is planned (it is — visitor MediaPipe is primary per `feedback_visitor_interactivity_primary.md`), pick the Kinect Azure node path *up front* and don't mix.

**Source:** [Orbbec Femto Bolt product page](https://www.orbbec.com/products/tof-camera/femto-bolt/) · [Derivative — Orbbec docs](https://docs.derivative.ca/Orbbec) · [Forum thread](https://forum.derivative.ca/t/orbbec-femto-bolt/446371) · [Kinect Azure TOP docs](https://docs.derivative.ca/Kinect_Azure_TOP)

---

## 2. Autolume Spout / NDI output support — ⚠️ DOES NOT EXIST UPSTREAM

**Claim (in `docs/autolume-integration.md` lines 17, 23, 60-63, 77, 95+):**
> "NDI video output: streams generated frames to other apps (TouchDesigner, OBS)"
> "Autolume (Fish Model) ──► NDI In TOP — TouchDesigner Compositor"

**Reality:** Upstream Autolume (`Metacreation-Lab/autolume` on GitHub) has **zero references** to Spout, NDI, or Syphon in its source code or documentation:

```
$ github code-search spout repo:Metacreation-Lab/autolume  →  0 matches
$ github code-search ndi   repo:Metacreation-Lab/autolume  →  0 matches
$ docs check (Getting Started page) → no mention of any video output protocol
```

The README, getting-started docs, and live-module pages mention OSC for *control input* but no video output mechanism beyond display-on-screen.

**What Apr-20 ops history says:** `docs/apr-20-onsite-walkthrough-plan.md` line 15 says "patched Autolume `visualizer.py`, fixed NDI hostname binding" — implying that during the April exhibition, Prav had a working NDI path **via a custom patch or fork**, not via upstream Autolume.

**Archive check 2026-05-13 PM:** `installation-archive/scripts/autolume_launch.bat` and `installation-archive/scripts/patch_instance.py` confirm the production launcher patched `modules/visualizer.py` per instance for unique `self.ndi_name` and OSC ports. The patched `visualizer.py` implementation itself is not present in `installation-archive/`, so the exact NDI sender mechanism still needs recovery from the 3090 or Pravin.

**Implications:**
- Don't promise Autolume NDI output to anyone (Prav, sponsors, John, venue) without first confirming what patch/method made it work in April
- If Spout was being assumed for the Phase 2 stack — re-verify whether Autolume is the right tool, or whether a Spout-capable alternative (TouchDesigner-native StyleGAN, OBS+Spout source, NDI screen-capture, or a SDTD-fork) is needed
- The Phase 1 production stack archived in `installation-archive/` may contain the actual `visualizer.py` patch — check there first if rebuilding the integration

**Action item:** before next Phase 2 sync that touches Autolume, ask Pravin or inspect the 3090's installed Autolume folders (`C:\Users\user\autolume*`) for the patched `modules\visualizer.py` implementation.

**Source:** [Metacreation-Lab/autolume README](https://github.com/Metacreation-Lab/autolume/blob/main/README.md) · [Autolume official docs (Getting Started)](https://metacreation-lab.github.io/autolume/) · [Metacreation Autolume project page](https://www.metacreation.net/projects/autolume-automating-live-music-visualisation-technical-report/)

---

## 3. CHS IWLS Vancouver station 07735 — ✅ CONFIRMED

**Claim:** Station 07735 = Vancouver tide gauge, accessible via CHS IWLS REST API.

**Verified:** Both correct.

- **Station 07735** = Vancouver, BC. Located at 49.2863, -123.0997. Permanent operational tide gauge owned by Canadian Hydrographic Service.
- **API endpoint:** `https://api-iwls.dfo-mpo.gc.ca/swagger-ui.html` (public REST API, JSON)
- **Alternate endpoint:** `https://api-sine.dfo-mpo.gc.ca/swagger-ui/index.html`
- 9 endpoints exposed, GET-only data retrieval
- Python wrapper available: `chs-tides` on PyPI / GitHub (RonSchofield)

**Implication:** if Phase 2 ambient layer needs live tide data for the Hubble Space show (Vancouver harbour breath cycle = a tonally appropriate data source given the venue), this is reachable with no auth required. Cache behavior + rate limits not yet checked.

**Source:** [CHS web services overview](https://tides.gc.ca/en/web-services-offered-canadian-hydrographic-service) · [Station 07735 page](https://www.tides.gc.ca/en/stations/7735) · [chs-tides Python wrapper](https://github.com/RonSchofield/chs-tides)

---

## 4. SAGE / VTG citations — ✅ BOTH EXIST, SLIGHTLY DIFFERENT FROM CLAIMED

**Context:** referenced in research prompts (`docs/next-iteration/_research/`) as candidate techniques for video transition / motion generation.

**SAGE** = "Structure-Aware Generative video transitions between diverse clips"
- Paper: arxiv `2510.24667`
- October 2025 publication
- **Scope:** video-to-video transitions (taking 2 video clips and synthesizing motion between them) — NOT image-to-video generation
- **Strength claimed:** highest flow similarity to ground truth, validates motion consistency for transitions; #2 on FID and FVD vs other transition methods
- **Benchmark introduced:** TransitBench (2 task families: concept blending + scene transition)

**VTG** = "Versatile Transition Generation with Image-to-Video Diffusion"
- Paper: arxiv `2508.01698` (HuggingFace mirror)
- August 2025 publication
- **Scope:** image-to-video transitions (generating motion bridging 2 keyframe images)
- **Methods:** dual-directional motion fine-tuning + representation alignment regularization

**Implication:** If our research prompts framed SAGE and VTG as interchangeable text-to-video models, that's wrong — they're both *transition* models specifically. Useful for the morphing/breath cycles in the pearl interior, NOT for generating standalone hero clips. Reference these correctly when next round of research prompts goes out.

**Source:** [VTG arxiv 2508.01698 (HuggingFace mirror)](https://huggingface.co/papers/2508.01698) · [SAGE arxiv 2510.24667 (referenced via search)](https://arxiv.org/html/2510.24667) · [Awesome-Video-Diffusion list](https://github.com/showlab/Awesome-Video-Diffusion)

---

## Summary

| # | Claim | Status | Action |
|---|---|---|---|
| 1 | Orbbec Femto Bolt + TD 2025 | ✅ Confirmed | Pick Kinect Azure node path up front if skeleton needed; don't mix node families |
| 2 | Autolume NDI output | ⚠️ Not in upstream | Ask Pravin or check `installation-archive/` for the April patch before re-promising NDI |
| 3 | CHS IWLS station 07735 = Vancouver | ✅ Confirmed | Endpoint usable, no auth required for reads |
| 4 | SAGE / VTG citations | ✅ Both exist, both *transition* models | Don't conflate with text-to-video models in next research prompt round |

## Discipline note

Per `feedback_verify_pricing_before_sponsor_facing.md`: applies beyond pricing. Anything that goes into a sponsor doc, venue email, contract, or external-facing planning artifact gets web-verified first. The Autolume-NDI claim has been in our docs since March without verification — exactly the failure mode the discipline rule is meant to catch.
