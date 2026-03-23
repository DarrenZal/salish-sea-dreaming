# Draft Signal Message to Prav — March 23, 2026

**Status:** READY TO SEND

---

Hey Prav,

Took the day off snowboarding yesterday and got a solid session in on April prep. Here's where things are at.

**Fish model complete — kimg 1000 on Drive:**
The fish model finished training today. Final checkpoint on Drive — load this in Autolume:
- PKL: https://drive.google.com/file/d/1RPb2c_PdKa7oCX---cUBZMq6GljW17la/view
- Fakes grid (what it produces): https://drive.google.com/file/d/1e0NVRR9vvD2iV9GHY1ehrGaHfokfNdhy/view

Trained for 6 days on the TELUS H200, 378 fish images, 1000 kimg. This is the sharpest version.

TELUS is now free for the next training job.

**The strategic shift — one model, not three:**
I've been rethinking the GAN strategy. We were going to train separate fish/whale/bird models — but with only 1 Autolume instance per machine, we'd have to swap checkpoints and cover the gap with Resolume transitions. And even with multi-machine, crossfades between separate models are just pixel dissolves — they don't feel like transformation. Within a single StyleGAN model, you get smooth latent interpolation — a herring can organically morph into a salmon, an octopus dissolves into an anemone. That's the actual dreaming mind. One model where navigating the latent space IS navigating the ecosystem.

I scraped 778 CC-safe intertidal images (octopus, starfish, anemones, urchins, nudibranchs, jellyfish, crabs, kelp, eelgrass, seals — 16 species). Combined with our fish corpus (378) and underwater whale shots, the target is ~800-880 images for a single multi-species "dreaming model."

Full concept: https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/dreaming-model-corpus.md

**Multi-wall architecture:**
Also rethinking the room as a spatial composition, not a single screen:
- **Live wall:** Autolume (fish model for now, dreaming model if it earns it)
- **Briony narrative wall:** Pre-rendered SD 1.5 + LoRA sequences at 30 steps — ecological film poem. The LoRA works beautifully at 30 steps, we just couldn't make it work real-time on SD-Turbo. So pre-render the beautiful stuff, play in Resolume.
- **Atmosphere (floor/ceiling):** OSC data engine — tides, moon, herring spawn
- **Witness layer:** Data visualizations (Geographic Collapse map, Keystone Web) that emerge and recede. Evidence becoming atmosphere.

Four temporal layers: present tense (live GAN), memory (Briony narrative), deep time (data pulse), witness (political testimony).

**QC Review App — could use your eyes:**
http://37.120.162.60:8090/tools/qc-review.html
Login: salishsea / dreaming2026 (open in incognito if it doesn't prompt)

Click an image to reject (pick a reason), click again to un-reject. Even just glancing at one species would help — are these the kinds of images that would be interesting in Autolume?

**Docs (all updated):**
- Team handoff: https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/team-handoff-march-2026.md
- Style transfer guide: https://github.com/DarrenZal/salish-sea-dreaming/blob/main/docs/style-transfer-guide.md
- LoRA eval (Briony's art vs our output): https://darrenzal.github.io/salish-sea-dreaming/briony-lora/eval/compare-v2.html

**What would help from you:**
- Your gut on the multi-wall idea — does it match what you're thinking for the space?
- Any progress on SD 1.5 + LoRA at higher step counts in StreamDiffusion?
- Load the kimg 1000 fish checkpoint in Autolume when you get a chance — how does it look?

I'll be on the mountain most of this week but online evenings — happy to keep things moving.
