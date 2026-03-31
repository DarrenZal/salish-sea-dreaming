# Intent Field: Voiced Commitments as Herring

A design concept for an interactive layer of the Salish Sea Dreaming installation where visitors voice their care for the Salish Sea and watch it swim — as herring — into a living school of collective intent.

**Status:** Concept draft — for discussion with Pravin, Carol Anne, and team
**Date:** 2026-03-30
**Author:** Darren Zal

---

## The Core Elegance

An intent is care as a vector — something matters enough to someone that they give it direction. A herring is a vector — a body moving through water with direction and purpose. In this installation, they are the same thing.

Visitors speak into a microphone. They voice what they care about, what they can offer, what they need, what they want for the Salish Sea. Their voice is transcribed. Their care becomes a herring — a living vector that enters the water and begins to swim.

Each herring carries the direction of someone's care. An offer of restoration labor swims toward an unmet need for restoration — vectors composing. Related intents school together — care aligning. When enough vectors converge around a shared need, a pool forms — a spawning event. The water brightens.

This is not a metaphor. Herring school because each fish senses its neighbors and responds — local rules producing collective movement without central coordination. Commitments pool because each one modifies the landscape for others — local care producing collective action without hierarchy. The algorithm is the same. The installation makes that identity visible.

Over the 16-day exhibition, the installation accumulates the collective intent field of everyone who visits. The schools grow. The pools form. The Salish Sea fills with the vectors of the community's care, swimming as herring.

---

## Two Frontiers

### The epistemic frontier — what IS

The water itself is rendered from real ecological data. Moonfish underwater footage grounds the visual — real herring, real kelp, real bioluminescence from the Salish Sea. Overlaid: ecological data from DFO herring spawn surveys, salmon counts, water quality monitoring, the Kwaxala model ("worth more swimming" — forage fish valued for ecosystem services, not extraction).

Where herring actually spawn, the water is alive with light and movement. Where spawning has collapsed, the water is dark and still. Visitors experience the current state of the waters before they say anything.

### The normative frontier — what people WANT

Each voiced intent adds to a constellation of desired futures. "Herring spawning in Tod Inlet again." "Food forests in every neighborhood." "Youth learning watershed monitoring." "Clean water in the Gorge." The constellation grows across the exhibition — a living map of what this community wants for the Salish Sea.

### Intent pressure — the gap

The visible distance between the dark water (where herring should be but aren't) and the bright constellation above (what people want) IS the central tension of the piece. The herring swim in that gap — each one a vector of care trying to bridge the distance between what is and what matters. Intent pressure, made visible as the space the herring are swimming through.

---

## Boids as Commitment Dynamics

Craig Reynolds' Boids algorithm (1986) produces emergent schooling from three local rules: separation, alignment, cohesion. No central coordinator tells the herring where to go. Each fish senses its local neighborhood and responds.

Commitment pooling works the same way. Each commitment modifies the landscape for future commitments. No central planner decides what's needed. The network learns through its own activity. This is stigmergic coordination — indirect coordination through environment modification. The same mechanism that allows herring to school, fungal networks to route nutrients, and communities to coordinate without hierarchy.

### Base Boids rules (organic movement)

1. **Separation** — don't crowd your neighbors (individual herring maintain spacing)
2. **Alignment** — steer toward the average heading of your group (herring in the same school move together)
3. **Cohesion** — steer toward the center of your group (herring stay together)

### Extended rules from commitment dynamics

4. **Complementary attraction** — offers drift toward matching needs. A herring carrying "I can offer watershed monitoring" is pulled toward a herring carrying "we need monitoring data." The pull is stronger when the match is closer (domain overlap, geographic fit, timeframe alignment).

5. **Saturation repulsion** — if many herring already cluster around a well-served need, new herring offering the same thing spread outward. The system visually signals: this is covered, direct your care elsewhere.

6. **Pool formation threshold** — when enough complementary herring cluster, a spawning event occurs. The school tightens. The water brightens. A pool has formed — not imposed, but emerged from local interactions reaching critical mass.

7. **Need gravity** — unmet needs create gravitational wells in the water. Dark spots that pull herring toward them. The more people voice the same need, the stronger the pull. Intent pressure made visible as gravitational force.

8. **Evidence glow** — if the installation tracks fulfillment (a longer-term aspiration), fulfilled commitments brighten. The water around them comes alive. Unfulfilled ones gradually dim — visual demurrage, encouraging movement.

9. **Federation bridges** — some herring stretch between schools, showing connections across clusters. These bridge-herring represent commitments that belong to multiple pools or connect different domains (a food systems commitment that also supports watershed health).

### Each herring carries semantic data

```
herring.voice       = the original spoken words (preserving the person's language)
herring.type        = care | offer | need | conditional
herring.domain      = [restoration, food_systems, monitoring, culture, education, ...]
herring.intensity   = how strongly it was voiced (volume, emphasis)
herring.timestamp   = when in the exhibition it was spoken
herring.connections = [other herring it relates to]
```

The Boids rules give organic movement. The semantic data shapes the forces. The result: herring school based on what they mean, not just where they are.

---

## The Visitor Experience

### Individual moment

You walk up to the microphone. The water is projected around you — Moonfish footage, real herring, kelp, bioluminescence. Dark where the ecosystem is struggling.

An invitation, spoken or displayed: *"What do you want for the Salish Sea? What can you offer? What do you need?"*

You speak. Your words appear briefly as text, then become a herring — your care, given direction, swimming. You watch your intent find others. It drifts toward complementary vectors. Offers toward needs. Care toward care. It joins a school.

### Collective accumulation

- **Day 1**: Mostly dark water. A few scattered herring. The constellation is sparse.
- **Day 8**: Schools forming. Pools emerging. The gap between the frontiers is visible but the herring are moving toward it.
- **Day 16**: Dense schools. Multiple pools. The dark water has bright spots where commitments gathered. A living record of collective care self-organizing through local rules.

### The spawning moment

When a pool forms — enough complementary commitments reaching threshold — it should feel like witnessing a herring spawn. Sudden. Collective. Alive. The water turns milky-bright in that spot. The school pulses. Something has emerged that wasn't there before: a collective commitment that no individual created alone.

This is the most important visual event in the piece. It's the moment coordination becomes visible.

---

## Aesthetic Principles

- **Moonfish footage is the ground layer** — real herring, real kelp, real underwater light. Not abstract particle art.
- **Briony's watercolor aesthetic** through the LoRA — the visual language is painterly, organic, hand-rendered. The herring-commitments should feel like they belong in one of her illustrations.
- **Sound matters** — the visitor's voice becomes part of the soundscape. Herring eggs on kelp. Underwater acoustics. The biosonification layer (Ableton/Max for Live) could respond to pool formation events.
- **Each herring is someone's care, swimming** — they move organically, follow fluid dynamics, school naturally. Not particles on a grid. Each one carries a voice.
- **Stillness and attention are rewarded** — per the project vision. The herring respond to presence, not performance. A visitor who watches quietly may see patterns that a hurried visitor misses.

---

## Technical Path

### What exists now

- **TouchDesigner** — production stack, Pravin's domain. Handles particle systems, real-time rendering, projection mapping natively.
- **Boids in TouchDesigner** — well-documented. CHOP-based or GLSL compute shader implementations available. Scalable to thousands of particles.
- **Real-time transcription** — Whisper.cpp runs locally on CPU/GPU. ~1s latency for short utterances. No cloud dependency.
- **OSC/WebSocket** — standard TouchDesigner input. Transcribed text can enter TD as string data, triggering herring spawn events.
- **Moonfish footage** — 13 videos (4.7 GB), 8 hero segments trimmed. Ready as backdrop layer.
- **Briony LoRA** — trained/training. Can style-transfer the herring-commitments into Briony's visual language.
- **Biosonification** — Ableton + Max for Live infrastructure designed. Pool formation events could trigger sonic events.

### What needs building

- **Boids implementation** with extended semantic forces (the commitment dynamics rules). Pravin would architect this in TD.
- **Transcription → herring spawn pipeline** — Whisper.cpp → parse intent type/domain → OSC message → TD spawns herring with semantic data.
- **Semantic force computation** — simple: domain overlap = attraction weight, type complementarity (offer↔need) = attraction, saturation = repulsion. Computed per-frame as additional steering vectors.
- **Pool formation detection** — density threshold on herring clusters. When N herring within radius R for T frames → trigger spawning event.
- **Persistence** — save all voiced intents + herring state across exhibition days. Load previous state at start of each day.
- **Data layer** — pre-processed ecological data (DFO herring surveys, water quality) as texture/displacement maps driving the water brightness/darkness.

### Scope consideration

This could be:
- **Minimal**: A single mic station with Boids on one wall. Herring accumulate. No ecological data layer. Still powerful.
- **Medium**: Mic + Boids + Moonfish backdrop + ecological data driving water brightness. Pool formation events trigger visual/sonic responses.
- **Full**: All of the above + Briony LoRA styling + biosonification + persistence across 16 days + final-day collective intent field artifact.

Suggest starting with minimal, proving the mic→herring→schooling loop works, then layering.

---

## After the Exhibition

The voiced intents don't disappear. They're transcribed, structured, reviewed — the same pipeline used for mapping workshop outputs. Some are offers. Some are needs. Some are commitments. They can flow into:

- The **Herring Pool** — the stewarded commitment pool for Lekwungen territory regeneration
- The **open infrastructure** — anyone's pool, anyone's commitments
- The **mapping workshop** — the exhibition's intent field as input to the May-June landscape mapping
- The **flow funding decisions** — what the community voiced at the exhibition informs where the $3,000 flows

The art installation becomes a sensing instrument for the community's intent field. The coordination infrastructure makes the voiced care actionable. The herring — vectors of care — swim from the gallery wall into the living map.

---

## Connection to Broader Architecture

This concept sits at the intersection of several projects:

- **Salish Sea Dreaming** — the art installation and immersive experience
- **Spore / Agent Commons** — the coordination grammar (intent pressure, commitment pooling, provisioning/redistribution, the coordination ecology)
- **BKC / KOI** — the knowledge infrastructure (entity resolution, commitment registry, federation, evidence)
- **Herring Pool** — the local commitment pool for Lekwungen territory, anchored to herring restoration
- **LHC mapping workshops** — the community coordination process that the exhibition feeds into
- **Kwaxala model** — "worth more swimming" economics, forage fish valued for ecosystem services

The herring is the bridge. An intent is care as a vector. A herring is a vector of life moving through water. In this installation they are the same thing — and the same dynamics that make herring school make commitments pool. The biology is the coordination grammar. The art makes it visible.

---

## Questions for the Team

**For Pravin:**
- Does this serve the artistic vision or distract from it?
- Can the Boids + semantic forces run alongside the existing exhibition sequences, or does it need its own wall/moment?
- What's the minimal proof-of-concept you'd want to see before committing development time?

**For Carol Anne:**
- Does the voiced-intent framing align with the co-dreaming vision? Is voicing care into the installation consistent with "wisdom internally generated, not externally imposed"?
- How does this relate to the seven domains of Indigenous worldview that structure the experience?

**For Shawn:**
- Could the Living Memory Substrate hold the voiced intents as memories that fade if not attended to? Herring that dim unless renewed?
- Integration surface with the KOI knowledge graph for post-exhibition persistence?

**For Brad:**
- Could the agentic characters respond to the accumulating intent field? The world state shifting as the community's care changes the environment?
