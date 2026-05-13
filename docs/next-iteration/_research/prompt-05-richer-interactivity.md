# Deep Research Prompt #5 — Richer Interactivity (Kinect / Mudras / Co-Dreaming / Voice)

**Best tools:** ChatGPT Deep Research, Claude.ai web-research, Gemini Deep Research.

**Decision unblocked:** Kinect/mudra/field-of-dreams spike decisions during May sprint; gesture-vocabulary design with Austin sign-off.

**Deadline:** 2026-05-14 (T+3 days).

---

## Prompt (paste verbatim)

```
I'm designing the interactive layer of a 3-projector AI art installation at
HR MacMillan Space Centre, Vancouver, late May 2026. Audience is in transit
(museum anteroom). Phase 1 used MediaPipe hand tracking + a mudra gesture
vocabulary (Hakini → herring cloud, Chin mudra → unity-point) that audiences
responded to strongly. We want to extend interactivity for Phase 2.

Research and report on:

1. Body-tracking hardware for gallery installations in 2026 — Azure Kinect
   (status / availability post-Microsoft's deprecation), Orbbec Femto Bolt
   (Kinect successor), Intel RealSense, Stereolabs ZED 2i, LeapMotion Ultraleap.
   Compare on: skeleton tracking accuracy, sensor footprint, Win 11 driver
   stability, integration paths to TouchDesigner via OSC.

2. Webcam-based full-body MediaPipe Pose / BlazePose / MoveNet for the same
   purpose at no hardware cost. Quality vs. dedicated depth sensors. fps on
   RTX 3090.

3. Gesture-vocabulary design for participatory art installations. References:
   The Cooper Hewitt Pen, teamLab installations, Refik Anadol's body-tracking
   work, Random International. What gesture vocabularies stick with transit
   audiences (no explanation needed) vs. require a docent?

4. Multi-visitor concurrent interaction — co-dreaming patterns. How do
   installations let 2+ people drive a single shared visual space without
   one dominating? Token-based turn-taking? Spatial zoning?
   Vector-field blending of inputs?

5. Voice / ambient ASR for noisy public spaces. State of the art in 2026
   for keyword spotting in a museum anteroom with 50+ dB ambient noise.
   Whisper local? Phone-as-mic strategies?

6. Cultural-protocol considerations when designing gesture vocabularies
   that invoke Indigenous iconography (e.g., a Thunderbird-wingspan gesture
   that triggers a Thunderbird crest). What's appropriative, what's
   participatory, what frameworks do Indigenous artists working with
   interactive media use?

Deliverable: comparison matrix of body-tracking hardware + recommendation
for 2-week sprint integration; design notes on multi-visitor co-dreaming
patterns with 3 candidate implementations; gesture-vocabulary design
principles; 8–10 pages.
```
