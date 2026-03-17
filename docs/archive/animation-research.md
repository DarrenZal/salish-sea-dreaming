# Animation Research - Bringing Dream Images to Life

> From the dissolving watercolors to breathing, moving video

**Date:** February 9, 2026
**Context:** The dissolving kelp and salmon-stream images have a cosmic, ethereal quality. How do we animate them - make the particles breathe, scatter, and reform?

---

## Three Paths

### Path 1: AI Image-to-Video APIs (Fastest - hours)

Use cloud APIs that take a still image + text prompt and generate 5-10 second video clips. Best for quick Instagram content.

#### Top Options (ranked)

| Tool | Access | Cost/10s clip | Quality | Notes |
|------|--------|---------------|---------|-------|
| **Runway Gen-4 Turbo** | Python SDK (`pip install runwayml`) | ~$0.50 | Best overall | Best style preservation, mature SDK |
| **Wan 2.5** | Replicate / fal.ai / self-host | ~$1.00 (720p) | Excellent | Open source, can run on TELUS H200s for free |
| **Kling 2.5** | Replicate / fal.ai / direct API | ~$0.70 | Excellent | **Motion Brush** - paint dissolution direction onto image |
| **Google Veo 3.1** | Gemini API | ~$0.80 | Excellent | Best physics simulation for particles |
| **MiniMax Hailuo 2.3** | fal.ai / Replicate / direct | ~$0.25 | Very good | Best value for batch processing |
| **Luma Ray3.14** | Luma API | ~credit-based | Very good | Hi-Fi Diffusion, 4K HDR output |
| **OpenAI Sora 2** | `/v1/videos` endpoint | ~$1.00 | Excellent | Access may be limited/invite-only |
| **SVD (Stable Video Diffusion)** | fal.ai / self-host | ~$0.075 | Good | Only 2-4 sec clips but great for particle effects |

#### Aggregator Platforms (multiple models, one API)
- **[fal.ai](https://fal.ai)** - Hosts SVD, Wan, MiniMax, Kling, Veo, Grok. Pay-per-use. Python SDK.
- **[Replicate](https://replicate.com/collections/image-to-video)** - 38+ image-to-video models. Python SDK.

#### Recommended Approach
```python
# Runway Gen-4 Turbo example
from runwayml import RunwayML
client = RunwayML()
response = client.image_to_video.create(
    model="gen4_turbo",
    prompt_image="path/to/dissolving-salmon.png",
    prompt_text="The watercolor dissolves into particles of bioluminescent light, drifting like plankton in dark ocean currents, slow breathing motion",
    ratio="1280:720",
)
```

**Cost to animate all 19 dream images:** ~$10 (Runway) or ~$5 (MiniMax)

#### Looping Strategy
Most models generate 5-10 second clips. For seamless loops:
- Generate multiple clips, crossfade between them
- Sora 2 Pro can do up to 25 seconds
- Luma Ray3 supports keyframe mode (set start/end frame identical)

---

### Path 2: TouchDesigner Point Cloud (Deepest Control - days)

Convert dream images to 3D point clouds where each pixel becomes a particle. Animate with noise displacement for breathing, dissolving, reforming.

#### Core Pipeline

```
MovieFileIn TOP (load dream image)
       |
Grid SOP (pixel grid, quarter-res ~98K points)
       |
Noise SOP (simplex noise displacement - breathing)
       |
Convert SOP (point sprites)
       |
Geometry COMP + Point Sprite MAT (color from image texture)
       |
Camera + Light + Render TOP
       |
MovieFileOut TOP (export video)
```

#### Key Techniques

**Breathing:** Animate Noise SOP offset through time. Modulate amplitude with sine wave:
```python
# Noise SOP amplitude expression
0.02 + 0.015 * sin(absTime.seconds * 0.5)  # slow inhale/exhale
```

**Dissolving:** Ramp noise amplitude from 0.02 (coherent) to 2.0 (scattered). Points drift apart. Reform by ramping back.

**Underwater Current:** Layer 2-3 noise scales (period 1.0, 3.0, 8.0) + slow directional drift.

**Feedback Loop (Living Painting - simplest TD approach):**
```
MovieFileIn TOP → Composite TOP → Displace TOP → Feedback TOP → back to Composite
                                       ↑
                                  Noise TOP (animated)
```
Subtle displacement (0.005-0.02) + slight fading = dreamlike, slowly evolving painting.

#### Resolution/Performance

| Resolution | Points | Performance | Visual |
|-----------|--------|-------------|--------|
| Full (1536x1024) | ~1.57M | Heavy | Pixel-perfect |
| Half (768x512) | ~393K | Moderate | Very good |
| **Quarter (384x256)** | **~98K** | **Light** | **Good - gaps enhance ethereal quality** |
| Eighth (192x128) | ~24K | Very light | Abstract/pointillist |

#### Advanced: AI Depth Estimation + Parallax
Use TD Depth Anything to estimate depth from Briony's watercolors, then:
- True parallax camera movement (closer elements move more)
- Point cloud with real depth (Z from depth map)
- Especially powerful for kelp forest, herring panorama, salmon stream cross-section

#### Phased Implementation

| Phase | What | Time | Result |
|-------|------|------|--------|
| **Phase 1** | Feedback + Displace (2D living painting) | 1-2 hours | Instagram-quality breathing loops |
| **Phase 2** | Full 3D point cloud with dissolve/reform | 3-4 hours | True particle dissolution |
| **Phase 3** | Kinect presence detection | 4-6 hours | Interactive: stillness = coherent, movement = dissolution |

All scriptable via Python over MCP (existing pattern in `scripts/psychedelic_video.py`).

#### Export
- MovieFileOut TOP: Apple ProRes 422 HQ or H.264
- Non-realtime rendering (every frame computed)
- 30fps for Instagram, 60fps for exhibition

---

### Path 3: Three.js + Custom Shaders (Web + Exhibition)

Extends the existing web prototype. Load image pixels as BufferGeometry point cloud, animate with GLSL curl noise shaders.

#### Architecture
1. Load image → offscreen canvas → `getImageData()`
2. Sample every 2nd pixel → ~393K points
3. `BufferGeometry` with position (x, y, 0) + color (r, g, b)
4. Custom `ShaderMaterial`:
   - **Vertex shader:** 3D curl noise displacement, breathing amplitude, z-depth variation
   - **Fragment shader:** Soft radial falloff (bioluminescent glow), alpha modulation
5. `UnrealBloomPass` for particle glow
6. Export with CCapture.js → WebM → FFmpeg → MP4

#### GLSL Shader Sketch (dissolution)
```glsl
// Vertex shader
void main() {
    vec3 pos = position;
    // Curl noise for organic underwater motion
    pos.xy += curlNoise(pos.xy * 0.5, uTime * 0.1) * breathAmplitude;
    pos.z += snoise(pos.xy * 2.0 + uTime * 0.05) * 0.1;
    // Dissolution: particles drift from origin
    float dissolve = snoise(pos.xy * 5.0 + uTime * 0.05);
    pos += normalize(pos) * dissolve * uDissolveAmount;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    gl_PointSize = 2.0 + sin(uTime + pos.x) * 0.5;
}
```

#### Strengths
- Code transfers directly to interactive exhibition
- Runs in browser for sharing
- Rich ecosystem (Three.js, GLSL, post-processing)
- Builds on existing prototype at https://darrenzal.github.io/salish-sea-dreaming/

---

## Recommendation for Feb 13 Deadline

| Priority | Action | Tool | Time | Output |
|----------|--------|------|------|--------|
| **1 (tonight)** | Write script to animate 4-6 strongest images | Runway Gen-4 API | 2 hours | 10-second video clips |
| **2 (Feb 10-11)** | TD feedback+displace breathing loops | TouchDesigner MCP | 2-3 hours | Living painting loops |
| **3 (Feb 11-12)** | TD point cloud dissolve/reform | TouchDesigner MCP | 3-4 hours | True particle dissolution |
| **4 (ongoing)** | Three.js shader point cloud | Web prototype | days | Interactive exhibition prototype |

**Suggested images to animate first:**
- `dissolving/kelp-underwater` - golden particles through blue water
- `dissolving/salmon-stream` - bears and salmon becoming starlight
- `night-ocean/octopus` - T'lep revealed through bioluminescent outlines
- `nested-reality/eelgrass` - oystercatcher/basking shark metaphor

---

## Cost Estimates

| Approach | Cost for 20 animations |
|----------|----------------------|
| Runway Gen-4 Turbo (10s each) | ~$10 |
| MiniMax Hailuo 2.3 (6s each) | ~$5 |
| Wan 2.5 on TELUS H200 | $0 (GPU time only) |
| SVD on fal.ai (4s each) | ~$1.50 |
| TouchDesigner | $0 (local) |
| Three.js | $0 (local) |

---

## References

### AI Video APIs
- Runway: https://docs.dev.runwayml.com/ | SDK: https://github.com/runwayml/sdk-python
- Replicate collection: https://replicate.com/collections/image-to-video
- fal.ai: https://fal.ai/models
- Kling: https://klingai.com/global/dev/pricing
- Luma: https://docs.lumalabs.ai/docs/api
- Google Veo: https://ai.google.dev/gemini-api/docs/video
- MiniMax: https://platform.minimax.io/docs/guides/video-generation
- OpenAI Sora: https://platform.openai.com/docs/guides/video-generation

### TouchDesigner
- Point Clouds: https://derivative.ca/UserGuide/Point_Clouds
- GPU Particles: https://github.com/interactiveimmersivehq/Introduction-to-touchdesigner/blob/master/GLSL/12-7-GPU-Particle-Systems.md
- Noise Displacement: https://www.simonaa.media/tutorials/noisedisplacement
- Feedback Loops: https://www.superhi.com/catalog/generative-art-with-touchdesigner/chapter-01-alla-prima/creating-a-feedback-loop
- TD Depth Anything: https://github.com/olegchomp/TDDepthAnything
- Generative Point Clouds: https://derivative.ca/community-post/tutorial/generative-point-clouds-tops-sops-touchdesigner/71564

### Three.js / Shaders
- GLSL curl noise: https://github.com/cabbibo/glsl-curl-noise
- Book of Shaders: https://thebookofshaders.com/
- CCapture.js: https://github.com/spite/ccapture.js
- Nature of Code: https://natureofcode.com/

---

*Research compiled Feb 9, 2026. Ready to implement.*
