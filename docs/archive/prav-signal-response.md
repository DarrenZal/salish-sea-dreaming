# Draft: Signal Response to Prav re: Autolume + TELUS GPUs + TD

*Draft for Darren to review, edit, and send via Signal*

---

## Option A — Brief initial response (if wanting to confirm understanding first)

---

Prav — yes, I'm in on this. Before I start setting things up, want to make sure we're aligned on the tool.

Are you referring to **Autolume** from SFU's MetaCreation Lab? (https://github.com/Metacreation-Lab/autolume — the StyleGAN2-ada-based generative visual system with OSC/MIDI support.) Or something else?

Also: what OS are you on, and do you have an NVIDIA GPU? Autolume is Windows/Linux only — no macOS — so I want to confirm who hosts it (your machine, TELUS, or my Linux server) before diving in.

If it is the MetaCreation Lab tool, I've got the integration architecture worked out and can walk you through the TD/OSC/MIDI setup.

---

## Option B — Full architecture response (if you want to lead with the plan)

---

Prav — yes, let's do this. I've done a deep dive on Autolume and I think the integration architecture is clear. Here's what I've worked out:

**What Autolume does:**
StyleGAN2-ada generative visual system from SFU's MetaCreation Lab. Designed for live performance — real-time latent space navigation, audio-reactive, OSC + MIDI controllable, NDI video output. The marine imagery from iNaturalist (128 species already downloaded) is potential training data.

**The constraint:**
Autolume is Windows/Linux only — no macOS, so it can't run directly on my MacBook. I do have access to a Linux server though, so I can host it on my end if needed. Or we run it on your machine, or on TELUS.

**The TELUS GPU role:**
Most valuable for **training** — a StyleGAN2-ada run that takes 1–3 days on a desktop RTX takes a few hours on an H200. The workflow:
- Submit training job to TELUS → export checkpoint
- Run inference locally on your machine for live performance (lower latency)

Is Carol Anne the access point for TELUS, or do you have direct credentials?

**TD integration:**
```
MIDI controller
      │
      ▼
  Autolume (your machine) ←── OSC ──→ TouchDesigner
       │
       └── NDI video stream ──────────→ TD (NDI In TOP)
```

In TD: OSC In CHOP to receive latent parameters, NDI In TOP to receive the generated video as a texture. Two-way — TD can also send OSC back to drive Autolume from audio analysis or ecological data.

**MIDI options:**
A) Direct MIDI → Autolume's Network Bending (faders map to latent PCA directions — semantic image manipulation like morphing between species)
B) MIDI → TD → OSC → Autolume (TD as hub — controls both at once)

Is Max for Live already in your signal chain? If so it's a natural OSC bridge.

**Training data strategy:**
I'm thinking Five Threads models — separate StyleGAN checkpoints for herring, salmon, orca, kelp forest, and deep water. Latent interpolation between models = the cascade feels alive. The marine images already cover these. Let me know if you want more images scraped (I can pull 1024px versions for better training).

**A few things I need from you to move forward:**
1. Confirm: MetaCreation Lab's Autolume repo?
2. Your OS + GPU (for local inference)
3. TELUS access path (Carol Anne or direct?)
4. MIDI controller — which one?
5. Is this for Nicholas's LED volume, or a smaller rig for Salt Spring?
6. Timeline — do you want something testable before Herring Fest (March 6–8)?

I can build the TD patch and get the training pipeline ready once I know your setup. Happy to jump on a quick call too if easier.

---

*Notes for Darren:*
- Option B is more useful to Prav since it gives him something concrete to react to
- The macOS constraint is the single most important thing to surface early — it reframes who hosts Autolume
- If Prav confirms it's the MetaCreation Lab tool, next step is: test with a pre-trained checkpoint before any custom training
- The Five Threads model idea maps to the Five Threads framework from Darren's perspective dump — worth emphasizing this as the semantic layer of the installation
