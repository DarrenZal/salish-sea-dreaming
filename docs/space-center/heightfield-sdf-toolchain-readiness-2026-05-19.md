# Heightfield / SDF Toolchain Readiness — 2026-05-19

Date: 2026-05-19
Lane: Agent A (toolchain audit — no creative rendering, no contact, no media output)
Scope: local laptop only (MacBook Air M2, 24 GB, Metal 3). The 3090 / 5090 show machine has its own toolchain (Resolume + TD + NDI) and is NOT covered here.

Purpose: answer "can today's heightfield/SDF water glyph experiment start on this machine, and which substrate is the right first move?" — per the pivot in `deep-research-fluid-grammar-synthesis-2026-05-19.md`.

## TL;DR

- **TouchDesigner 2025.32050 is installed and launches** — viable substrate today, matches the research recommendation.
- **Blender is NOT installed locally** — hero-clip path is blocked until install (~250 MB + first-launch licensing).
- **Resolume is NOT installed on this laptop** — that's expected; Resolume work lives on the 3090 / 5090 show machine. No local Alley transcode possible here.
- **ffmpeg 7.1.1 covers H.264, ProRes (incl. videotoolbox-accelerated), and HAP encode** — verified via 64×64 1 s smoke encode.
- **Python 3.14.2 has `numpy`, `Pillow`, `scipy` but is missing `moderngl`, `opencv`, `imageio`, `PyOpenGL`, `glfw`** — a script-only headless heightfield/SDF prototype needs ~5 min of pip installs first.
- **Recommendation for today: TD-first.** Python+moderngl fallback is the second choice and requires installing 3–4 packages. Blender is a separate install task; defer.

## Audit Results

### TouchDesigner — ✅ ready

| Field | Value |
|---|---|
| App path | `/Applications/TouchDesigner.app` |
| Version | 2025.32050 |
| Launch test | Process started cleanly; closed via `pkill -x TouchDesigner`. macOS "Secure coding not enabled" warning is harmless. |
| Licensing state | **Not determinable from on-disk artifacts** (TD 2025 uses an account-tied entitlement fetched on launch; `pref.txt` is empty, cfprefs holds only GUI window state, no TD-shaped keychain entries). See Appendix A for the exact manual check Darren should run before any deliverable export. |
| Python bridge | Bundled Python not exposed at the standard path; scripting happens through TD's internal interpreter or the TD MCP if connected. |
| Sufficient for heightfield/SDF? | Yes — GLSL TOP, Feedback TOP, Noise TOP, Slope/Normal generation, Movie File Out, NDI Out all native. Matches the research's "build-today architecture." |

### Blender — ❌ not installed

| Field | Value |
|---|---|
| App path | Not present in `/Applications` |
| CLI `blender` | Not on PATH |
| Sufficient for hero clips? | Path is blocked until install. The Ocean Modifier + Geometry Nodes hero-render path from the synthesis cannot start on this laptop today. |
| Install action (if chosen later) | Download from blender.org (~250 MB DMG); Apple Silicon native build; no license cost; check Cycles Metal backend on M2. |

### Resolume — ❌ not installed locally (expected)

| Field | Value |
|---|---|
| Local install | None — confirmed via `/Applications` scan + `mdfind` (Homebrew cask metadata found but no actual app). |
| Alley transcode here | Not possible locally. |
| Show-machine state | 3090 has Resolume Arena (per `installation-archive/tasks/SSD-Resolume-*.xml` + ops playbook). 5090 will mirror this. |
| Local impact | This laptop is fine for producing source clips (mp4/mov/HAP via ffmpeg). Alley transcode + deck assembly happens on the show machine; see `hubble-wide-wall-resolume-assembly-2026-05-19.md`. |

### ffmpeg — ✅ ready (H.264 + ProRes + HAP)

| Field | Value |
|---|---|
| Version | 7.1.1 (Homebrew, `/opt/homebrew/bin/ffmpeg`) |
| H.264 | `libx264`, `libx264rgb`, `h264_videotoolbox` (hardware) — all available |
| HEVC | `libx265`, `hevc_videotoolbox` |
| ProRes | `prores`, `prores_aw`, `prores_ks`, `prores_videotoolbox` (hardware-accelerated on M2) |
| HAP | `hap` encoder/decoder present (`DEVIL.` flags in `-codecs`) — verified by 64×64 × 1 s smoke encode at `/tmp/hap_smoke.mov` (4,191 bytes; ffprobe confirms `codec_name=hap`). Note: ffmpeg's HAP encoder produces plain HAP only — for HAP Q or HAP Alpha use Resolume Alley on the show machine. For the current black-background Add/Screen workflow, plain HAP is correct (no alpha needed). |
| Net | H.264 for daily review/transport, ProRes for hero-quality masters, HAP for the show-machine deck — all expressible from this machine. |

### Python 3.14 — ⚠️ partial

| Module | Status |
|---|---|
| `numpy` 2.4.2 | ✅ |
| `Pillow` 12.1.1 | ✅ |
| `scipy` 1.17.1 | ✅ |
| `cv2` (opencv-python) | ❌ |
| `imageio` | ❌ |
| `moderngl` | ❌ |
| `PyOpenGL` | ❌ |
| `glfw` | ❌ |
| `pyglet` | ❌ |
| `skimage` | ❌ |

Interpreter: `/opt/homebrew/opt/python@3.14/bin/python3.14`.

If a Python heightfield/SDF prototype becomes the chosen path, the minimum install is:

```
python3 -m pip install moderngl moderngl-window imageio[ffmpeg] opencv-python
```

`moderngl` runs on Apple Silicon via Metal (through OpenGL→Metal translation); expect modest FPS but acceptable for offline frame-by-frame rendering to mp4/mov. Headless framebuffer rendering avoids any window-server dependency.

### System Basics

| Field | Value |
|---|---|
| Model | MacBook Air M2 (Mac14,15) |
| CPU | Apple M2, 8 cores (4P + 4E) |
| Unified memory | 24 GB |
| GPU | Apple M2 integrated, Metal 3 |
| External display capability | Verified 3840×2160 in display profile (matches Hubble wide-wall target). |
| Internet | Assumed available (not probed). |

This is sufficient for heightfield prototyping at 1080p–4K offline. Real-time 4K live diffusion-style workloads are **not** in scope here — that's the 3090's lane.

## Practical Recommendation For Today

**TD-first.** TouchDesigner 2025.32050 is installed and matches the research-recommended substrate exactly. The build-today architecture in `deep-research-fluid-grammar-synthesis-2026-05-19.md` lines 24, 38–68 maps directly onto installed TD nodes (GLSL TOP, Feedback TOP, Noise TOP, Slope/Normal, Movie File Out). No new installs required.

**Python+moderngl is the strong second choice** — about 5 minutes of pip installs, then a script-only headless heightfield/SDF prototype that outputs ProRes or H.264 via ffmpeg. Preferred if Agent B wants a deterministic, version-controlled, scriptable proof rather than a TD `.toe` file. Trade-off: more lines of code, slower iteration than TD's GUI feedback loop.

**Blender-first should be deferred.** It's the right hero-clip path long-term, but the install + first-launch cycle is not justified for today's substrate proof. Park it as a separate task; revisit when the hero-clip lane becomes the active priority.

| Path | Setup cost today | Iteration speed | Fits research recommendation? |
|---|---|---|---|
| TouchDesigner | 0 min | Fast (GUI feedback) | Yes — primary |
| Python + moderngl | ~5 min pip | Medium (script + re-run) | Yes — explicit fallback |
| Blender | ~30 min install + first-launch | Slow today, fast later | Hero path, not today |

## Smoke Tests Performed

Two tiny, documented probes — no creative output, no committed media.

1. **TD launch probe.** Invoked `/Applications/TouchDesigner.app/Contents/MacOS/TouchDesigner --help`. Process spawned, printed `MasterPortDestroyer is armed` + macOS secure-coding warning. Confirmed launchable. Closed cleanly with `pkill -x TouchDesigner`. No `.toe` opened, no project edited.
2. **HAP encode probe.** `ffmpeg -f lavfi -i "color=c=0x102030:s=64x64:d=1:r=30" -c:v hap /tmp/hap_smoke.mov`. Output: 4,191 bytes; ffprobe reports `codec_name=hap`, `width=64`, `height=64`, `duration=1.0`. File deleted post-verification. Confirms HAP encode path is live without depending on Resolume Alley.

Nothing else was rendered. No project files modified. No network calls.

## Caveats And What This Audit Does NOT Cover

- **TD licensing state.** Not determinable from on-disk artifacts on this machine — see Appendix A for the manual check. The Non-Commercial tier caps output resolution (per derivative.ca pricing — verify there, do not trust this doc's recall of the exact pixel cap); if that's the tier active here, 3840×2160 IMPACT deliverables cannot be exported from this laptop and Pravin's commercial-licensed show machine must do the final encode.
- **3090 / 5090 show-machine readiness.** This audit is laptop-only. Show-machine toolchain is tracked in `hubble-wide-wall-resolume-assembly-2026-05-19.md` and the ops playbook.
- **Cross-machine clip transport.** Producing a `.mov` on this laptop is straightforward; getting it onto the show machine still requires the SSH/scp path documented in the project CLAUDE.md (use `scp -O` for `.toe` files per logged macOS-scp truncation memory).
- **Pravin's Resolume codec preference.** Open question from synthesis line 161 — DXV3 vs HAP vs H.264 default. Not resolved by this audit. Producing HAP here is possible; producing DXV3 requires Resolume Alley on the show machine.
- **Shared `grammar.json` contract.** Agent C's deliverable; not in this lane.

## Appendix A — Manual TouchDesigner License Check (~2 min)

Run this before any deliverable export from this laptop. No project files need to be opened.

**What we tried automatically (and why it didn't work):**

- `~/Library/Application Support/Derivative/TouchDesigner099/pref.txt` — empty (0 bytes).
- `~/Library/Preferences/ca.derivative.TouchDesigner.plist` — holds only `NSNavLast…` GUI window state.
- `~/Library/Application Support/Derivative/TouchDesigner099/` — only `FontCache/`, `Palette/`, `ShaderCache/`, `TDLogs/`, `TipsConfig.txt`. No `*license*` / `*.dat` / `*.cfg`.
- `security find-generic-password -s TouchDesigner` and `-s Derivative` — no matches.
- Bundled `Contents/Resources/tfs/Config/license.rtf` — EULA boilerplate, not user tier.

TD 2025 fetches entitlement from a Derivative account at launch and does not write a human-readable tier marker to disk. The check must therefore happen in the running app.

**Manual procedure:**

1. Launch TouchDesigner (it will open a fresh untitled project — do **not** open any SSD `.toe` file).
2. From the top menu bar: **Dialogs → About TouchDesigner**.
   - This panel reports: TD version (already known: 2025.32050), the **License Type** (Non-Commercial / Educational / Commercial / Pro), and the signed-in Derivative account.
3. Also check the title bar of the main TD window:
   - Non-Commercial mode appears as `TouchDesigner Non-Commercial` and projects save with a `.toe` watermark constraint.
   - Commercial/Pro show plain `TouchDesigner` with no suffix.
4. To see the active **output resolution cap**, open the realtime perform-mode preview by pressing `F1` on a default scene. Non-Commercial mode visibly enforces the cap on any Render TOP and the perform window.
5. Close the About dialog. Quit TD (`Cmd-Q`). Do not save anything.

**Reporting back:**

Copy the License Type string from the About dialog into this doc (or paste into Signal). That single line is what Pravin and Darren need to decide whether 4K masters can be exported from this laptop or must be encoded on the show machine.

**Tier reference — VERIFY against derivative.ca/pricing before relying on numbers:**

The publicly advertised TD tiers are roughly: Non-Commercial (free, capped output + commercial-use restriction), Educational (subsidized, reduced caps), Commercial (paid, full output), Pro (paid, full output + Multi-GPU/cluster). The exact pixel cap on Non-Commercial has shifted across TD releases (1280×1280 is the figure most commonly cited for the 2023+ line, but this doc is **not** an authoritative source — confirm on derivative.ca before quoting it to Pravin or anyone external). Per `feedback_verify_pricing_before_sponsor_facing.md`, treat tier numbers as estimated until checked against the live page.

**If TD turns out to be Non-Commercial here:** Hubble's 3840×2160 master cannot be exported from this laptop. Workflow options: (a) produce the heightfield/SDF GLSL pass on this laptop at the capped resolution as a proof-of-concept; (b) port the TOX/GLSL TOP to Pravin's commercial-licensed show machine for the final 4K render; (c) escalate to a Commercial license on this laptop if the workflow rate justifies it.

## Cross-References

- `docs/space-center/deep-research-fluid-grammar-synthesis-2026-05-19.md` — the pivot this audit supports.
- `docs/space-center/hubble-wide-wall-resolume-assembly-2026-05-19.md` — show-machine assembly state (companion doc, different lane).
- `CLAUDE.md` (project) — show machine SSH path, `scp -O` toe-file caveat, ops playbook references.
