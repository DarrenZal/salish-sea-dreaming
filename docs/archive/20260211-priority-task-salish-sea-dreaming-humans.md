# Feb 11 Priority Task - "Salish Sea Dreaming Humans" Still for Raf

**Date:** February 11, 2026  
**Deadline context:** Raf still-image selection due by February 13, 2026  
**Owner:** Darren (with Prav/Natalia review)

## Request We Are Responding To

From the M37 Signal export:
- `/Users/darrenzal/Documents/Notes/M37 Salish Sea Dreaming Chat.md:307`
- `/Users/darrenzal/Documents/Notes/M37 Salish Sea Dreaming Chat.md:309`

Prav asked to explore a compelling still image for Raf around:
- "the Salish Sea dreaming humans"
- using the attached photo of his sons as a test
- aiming for something gentle and dreamy
- intermixed with Briony's styling and marine imagery

Source image currently available at:
- `/Users/darrenzal/signal-chats-salish-sea/M37SalishSeaDreaming/media/2026-02-11T00-34-58.821_00_IMG_0517.jpg`

## Why We Are Doing This

1. It is the most recent explicit creative direction from Prav for the Feb 13 deliverable.
2. It creates a concrete still candidate for Raf's poster/public engagement review.
3. It tests a human-centered composition while staying inside the project's contemplative visual language.
4. It helps answer a practical storytelling question: how to include human presence without collapsing into generic AI portrait aesthetics.

## Creative Constraints

1. Keep the mood gentle, dreamlike, and contemplative.
2. Integrate marine imagery as relational context, not decorative overlay.
3. Keep visual relation to Briony's language (line, color restraint, ecological tenderness).
4. Maintain Raf's constraint: output must be distinct enough from Briony's originals to avoid confusion.
5. Avoid spectacle-heavy effects and avoid literal "AI demo" look.

## Ethical and Usage Guardrails

1. Treat the sons photo as sensitive input and confirm usage scope with Prav before any public posting.
2. Keep generated outputs in internal review folders until approved.
3. Preserve attribution notes in metadata sidecars for reproducibility and provenance.

## Technical Approach (How)

Primary path for today:
1. Use `scripts/dream_gemini.py` with multi-reference conditioning.
2. Input references:
   - Prav's sons photo (subject anchor)
   - 2-4 Briony paintings (style anchor)
   - optional marine anchor image if needed
3. Generate 8-12 still candidates across two aspect ratios:
   - `3:2` for poster exploration
   - `4:5` for IG/public engagement fallback
4. Curate down to 3 strongest candidates with short rationale notes.

Suggested command pattern:

```bash
python3.11 scripts/dream_gemini.py \
  --model pro \
  --aspect 3:2 \
  --size 4K \
  --refs "/Users/darrenzal/signal-chats-salish-sea/M37SalishSeaDreaming/media/2026-02-11T00-34-58.821_00_IMG_0517.jpg" \
         "assets/reference/briony-watercolors/2026-02-07T21-29-28.416_01_IMG_1474.jpg" \
         "assets/reference/briony-watercolors/2026-02-07T21-29-28.416_03_IMG_1476.jpg" \
         "assets/reference/briony-watercolors/2026-02-07T21-29-28.416_05_IMG_1478.jpg" \
  --prompt "<prompt variant>" \
  --name "raf-still-dreaming-humans-v1" \
  --notes "Feb11 priority task: Salish Sea dreaming humans"
```

## Prompt Direction (Initial)

Use prompt variants around this structure:
- "Two young humans held within a gentle Salish Sea dream."
- "Marine life and currents are present as soft relational layers, not sharp montage elements."
- "Watercolor-informed edges, restrained palette, subtle bioluminescent accents."
- "No hard realism, no synthetic glossy skin, no text, no poster typography."
- "Quiet, tender, protective, intergenerational feeling."

## Acceptance Criteria for Today's Task

1. At least 8 viable still candidates generated.
2. At least 3 curation-ready stills selected for Raf review.
3. Each selected still has:
   - prompt provenance (JSON sidecar),
   - aspect ratio noted,
   - one-line rationale.
4. Clear recommendation sent: "best poster candidate" + "best social candidate".

## Out of Scope Today

1. Final motion/video pipeline decisions.
2. Installation interaction logic changes.
3. Full dataset integration for Five Threads behavior.

## Task Checklist (Feb 11)

- [ ] Confirm permission scope with Prav for sons-photo usage context.
- [x] Generate first 4 candidate stills (3:2).
- [x] Generate second 4+ candidate stills (4:5 or 3:2 alternates).
- [x] Curate top 3 and write rationale notes.
- [ ] Package and share candidate set with Prav/Natalia for Feb 13 decision flow.

## Results (Generated Feb 11)

Output directory:
- `assets/output/experiments/raf-still-dreaming-humans/`

Generation summary:
- 12 PNG stills generated
- 12 JSON metadata sidecars generated
- Aspect coverage:
  - 8 x `3:2` (`5056x3392`)
  - 4 x `4:5` (`3712x4608`)

### Top 3 Curated Stills

1. `assets/output/experiments/raf-still-dreaming-humans/20260211-122523_raf-still-dreaming-humans_v06_3x2_kelp-cathedral-soft.png`
- Rationale: strongest poster readability and environmental framing; children remain clear emotional center while marine context is immersive and legible at distance.

2. `assets/output/experiments/raf-still-dreaming-humans/20260211-123004_raf-still-dreaming-humans_v11_4x5_mixed-hero.png`
- Rationale: clean vertical composition for social/public channels; gentle and restrained, with good balance between human tenderness and sea motifs.

3. `assets/output/experiments/raf-still-dreaming-humans/20260211-122912_raf-still-dreaming-humans_v10_3x2_mixed-quiet-glow.png`
- Rationale: good emotional fidelity to source photo and convincing “dreaming” mix of herring + kelp without becoming visually noisy.

### Recommendation

- **Best poster candidate:**  
  `assets/output/experiments/raf-still-dreaming-humans/20260211-122523_raf-still-dreaming-humans_v06_3x2_kelp-cathedral-soft.png`

- **Best social candidate:**  
  `assets/output/experiments/raf-still-dreaming-humans/20260211-123004_raf-still-dreaming-humans_v11_4x5_mixed-hero.png`

### Notes

- All generated files include provenance metadata via `scripts/dream_gemini.py` + `scripts/image_metadata.py`.
- Before external publication, confirm explicit usage scope with Prav for the sons photo.

## Results (Tide Pool Refinement Pass - Generated Feb 11)

Output directory:
- `assets/output/experiments/raf-still-dreaming-humans-tidepool-pass1/`

Proof sheet:
- `assets/output/proof-sheets/20260211_raf-still-dreaming-humans-tidepool-pass1_contact-sheet.png`

Generation summary:
- 8 PNG stills generated
- 8 JSON metadata sidecars generated
- Aspect coverage:
  - 5 x `3:2` (`5056x3392`)
  - 3 x `4:5` (`3712x4608`)

Drive packaging (internal review):
- Main folder: `https://drive.google.com/drive/folders/1NpnraarzsZd-vwQLBC0OEErKPwHMQdTV`
- Metadata folder: `https://drive.google.com/drive/folders/1n3BXRzvJF7htCW8qpCVbwaB0tsbyDb-E`

### Top 3 Curated Stills (Tide Pool Pass)

1. `assets/output/experiments/raf-still-dreaming-humans-tidepool-pass1/20260211-143835_raf-still-dreaming-humans-tidepool_v03_3x2_reflection-window.png`
- Rationale: strongest “nested reality” read; reflection device is immediately legible and emotionally coherent while staying gentle.

2. `assets/output/experiments/raf-still-dreaming-humans-tidepool-pass1/20260211-143800_raf-still-dreaming-humans-tidepool_v02_3x2_cosmic-shallows.png`
- Rationale: best balance of shoreline realism with underwater dream depth; very good poster readability in landscape.

3. `assets/output/experiments/raf-still-dreaming-humans-tidepool-pass1/20260211-144030_raf-still-dreaming-humans-tidepool_v06_4x5_tidal-memory.png`
- Rationale: strongest vertical social/public candidate; clear figure-ground separation and calm, tender atmosphere.

### Recommendation (Tide Pool Pass)

- **Best poster candidate (3:2):**
  `assets/output/experiments/raf-still-dreaming-humans-tidepool-pass1/20260211-143835_raf-still-dreaming-humans-tidepool_v03_3x2_reflection-window.png`

- **Best social candidate (4:5):**
  `assets/output/experiments/raf-still-dreaming-humans-tidepool-pass1/20260211-144030_raf-still-dreaming-humans-tidepool_v06_4x5_tidal-memory.png`

## Results (Briony Photo Replacement Pass - Generated Feb 13)

Context update from Prav:
- Briony photo permission approved (source: David Denning article image)
- New priority: generate "Salish Sea Dreaming Briony" options using same styling
- Keep technology motifs subtle (network diagrams, DNA/chem, spacetime physics)
- Boys can be considered later as optional secondary weave-in

Input source image:
- `assets/reference/people/briony-denning-20260213_signal-2026-02-12-233158.jpeg`

Output directory:
- `assets/output/experiments/raf-still-dreaming-briony-pass1/`

Proof sheet:
- `assets/output/proof-sheets/20260213_raf-still-dreaming-briony-pass1_contact-sheet.png`

Generation summary:
- 8 PNG stills generated
- 8 JSON metadata sidecars generated
- Aspect coverage:
  - 5 x `3:2` (`5056x3392`)
  - 3 x `4:5` (`3712x4608`)
- Motif spread:
  - 3 network-thread variants
  - 3 DNA/organic-chem variants
  - 2 spacetime/field variants

Drive packaging (photos-only):
- `https://drive.google.com/drive/folders/1yLO8SoCDjXjzIU1KaJ7A8SA8RgiB4PQB`

### Top 3 Curated Stills (Briony Pass)

1. `assets/output/experiments/raf-still-dreaming-briony-pass1/20260213-092048_raf-still-dreaming-briony_v01_3x2_network-tide-threads.png`
- Rationale: strongest overall balance of Briony subject clarity, marine tenderness, and subtle tech-thread integration without visual noise.

2. `assets/output/experiments/raf-still-dreaming-briony-pass1/20260213-092549_raf-still-dreaming-briony_v08_4x5_quantum-shore-breath.png`
- Rationale: best vertical social/public candidate; readable composition with gentle field motifs and strong emotional focus.

3. `assets/output/experiments/raf-still-dreaming-briony-pass1/20260213-092454_raf-still-dreaming-briony_v07_3x2_spacetime-tide-curvature.png`
- Rationale: quiet, coherent spacetime motif treatment; keeps the science layer poetic and secondary to the intertidal portrait.

### Recommendation (Briony Pass)

- **Best poster candidate (3:2):**
  `assets/output/experiments/raf-still-dreaming-briony-pass1/20260213-092048_raf-still-dreaming-briony_v01_3x2_network-tide-threads.png`

- **Best social candidate (4:5):**
  `assets/output/experiments/raf-still-dreaming-briony-pass1/20260213-092549_raf-still-dreaming-briony_v08_4x5_quantum-shore-breath.png`
