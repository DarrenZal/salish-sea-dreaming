# Prav Catch-Up Call Prep — 2026-05-14

Purpose: prepare Darren for a focused catch-up with Pravin Pillay on SSD Phase 2 / IMPACT, using the latest Proton mail and project-state checks.

Status: current as of 2026-05-14 local afternoon/evening check. Proton Bridge was searched read-only. 3090 SSH is reachable; the five-minute reconnect cause was found and disabled on poly.

## Call Goal

Leave the call with explicit calls on:

1. Austin asset path: how/when the curated Drive lands, and whether Prav should nudge.
2. Hubble Space production path: what we can keep building today without Austin's files.
3. Dome path: how Prav wants SSD/MOVE37XR to relate to Carol Anne/Shawn/Dan's Living Intelligence visuals.
4. Hardware path: 5090 go/no-go timing and whether the 3090 remains the May primary.
5. Venue/test logistics: John contact, projector pack send, 3090/TD access, and Autolume output path.

Keep the call to decisions and unblockers. Avoid reopening yesterday's settled experiments unless Prav has new information.

## Latest Facts To Surface

### Proton / Austin

- Proton Bridge search found **no incoming Austin / INDIGITAL reply** since Darren's May 13 email.
- Sent email exists: `SSD files access + a quick hello`, sent to `austin@indigitaldesign.ca` on 2026-05-13 17:41 UTC.
- `austin-v2-ingest/inbox/`, `approved/`, and `training/` are still pristine; orchestrator has no state yet and waits at preflight.

Ask Prav:

- Should Prav nudge Austin today, or should we leave Austin until he is ready?
- If Austin sends files to Prav first, should Prav forward the Drive to Darren immediately without waiting for a sync?
- Does Austin prefer first-look outputs today/tomorrow, or should we only show process scaffolding until he can review?

### Hubble Space / SSD

Ready:

- v2 ingest/training/eval orchestrator: `scripts/austin_v2_pipeline.py`
- Track 2 deterministic morph engine: `track2-deterministic/`
- Austin consent/review packet: `docs/space-center/austin-review-packet-2026-05-14.md`
- public-language drafts with `[PENDING AUSTIN REVIEW]`
- John projector diagnostic pack: `austin-reference/john-projector-test-pack-v1_2026-05-13.zip`
- Resolume show package checklist + validator

Still blocked / needs confirmation:

- Austin Drive
- TD live verification / Autolume runtime check
- whether to keep Autolume NDI for May or budget a Spout patch
- John contact channel
- Moonfish / Denning written reuse confirmation

Latest local check:

- 3090 SSH responds: `DESKTOP-37616PR`.
- Poly reverse socket `127.0.0.1:2222` is open and fresh SSH commands succeed through `windows-desktop-remote`.
- `SSD-SSH-Tunnel` and `SSD-Tunnel-Watchdog` tasks are both running.
- Root cause of five-minute flapping found: poly crontab ran `/home/poly/clean_tunnel.sh` every five minutes; that script killed a healthy idle reverse-forward listener because it only looked for an active `ESTABLISHED` client connection on `:2222`.
- Fix applied: disabled only that cron line on poly. Backup: `/home/poly/crontab.backup.20260515-032306`. Post-fix watch through the next former kill window showed no new `Tunnel exited` line; `windows-desktop-remote` still worked.
- Backup access is confirmed: `windows-desktop-wg` over WireGuard works and reaches the same 3090. `WireGuardTunnel$wg-koi` is running and automatic.
- Tailscale is not a verified fallback from Darren's Mac today: Windows Tailscale service is running and has `100.91.172.10`, but `ssh windows-desktop-tailscale` timed out from here.
- Live Autolume file found: `C:\Users\user\autolume\modules\visualizer.py`, last modified 2026-04-19 13:16.
- That file imports `NDIlib`, creates sender name `Autolume Live`, and sends frames via `ndi.send_send_video_v2(...)`.
- No Spout evidence found in the live `visualizer.py` search.
- GPU is idle enough for checks: RTX 3090, about 243 MiB VRAM used, about 24,080 MiB free, 39 C in the last check.

Ask Prav:

- Keep the 3090 tunnel/watchdog running; five-minute reconnect cause appears fixed, but avoid declaring it show-hardened until it survives a longer window.
- Can he confirm whether opening TD/Autolume remotely will disrupt any active VVVV work?
- Does he want us to keep the known-good NDI path for May, or deliberately pursue a Spout patch after we inspect runtime behavior?
- Who is the right John contact route for the projector diagnostic pack?
- Should we send Moonfish / Denning reuse confirmation asks now, or should Prav own those relationships?

### Dome / Living Intelligence

Dan Tell responded with concrete specs:

- Planetarium software: OpenSpace `0.21.3`
- Dome: 180-degree horizontal/vertical FOV, 10 m radius
- Playback target: single video file
- Preferred video: equirectangular H.265 MP4 at `6144x3072`, 30 fps, 8-bit
- Dome content should use the center 180 degrees of the equirectangular canvas
- Audio: up to 5.1 supported, SMPTE order `(L, R, C, LFE, Ls, Rs)`
- Projectors: mix of Christie D4K 2560 and Christie Roadster HD20K-Js; effective meridian resolution about 3K
- Dan sent OpenSpace converter/encoder tool + instructions links
- Dan emphasized that May 14 was the OpenSpace prep deadline, not a soft creative deadline; final rendered video next week may be acceptable but testing/rework time will be limited.

Kurt clarified:

- Whova owns IMPACT survey / polling / word cloud.
- Whova projects to a normal screen, **not** Dome projection.
- SSD should not build custom survey intake / live survey analytics unless reopened next week.

Ask Prav:

- Does he want the Dome visuals to stay separate from SSD, or should the Hubble visitor app deliberately bridge to the Dome "living graph" surface?
- Should the current concept package be sent to Carol Anne/Shawn as concept material, or held until re-rendered in Dan's native format?
- Does Prav want MOVE37XR visual language in the Dome package, or keep it neutral constellation/graph until Carol Anne directs?
- Can Prav join/shape the 4 PM Dan call, or should Darren handle specs and report back?

### 5090 / Hardware

Sent to Prav + Natalia:

- `SSD Phase 2 — RTX 5090 build spec + sponsor framing`
- current recommendation is a full RTX 5090 workstation around `$11.7K CAD turnkey`, with trim/premium variants.

Decision needed:

- If 5090 is for May primary, procurement needs to move immediately because build + driver + migration soak needs days.
- If no 5090 this week, May Hubble ships on 3090 with strict constraints: more pre-rendered material, lower live-AI ambition, Track 2/footage as production-safe core.

Ask Prav:

- Is Natalia pursuing this today?
- Should Darren keep shaping sponsor framing, or leave it alone until Natalia has a target?
- Are we treating 5090 as May primary, Phase 2.1 primary, or sponsor-R&D narrative only?

## Recommended Call Flow

1. **Start with Austin.** "No reply yet; pipeline is ready; do we nudge or wait?"
2. **Lock the next 24h Hubble path.** If no Drive, work on package/footage/TD; if Drive lands, ingest immediately.
3. **Use 3090 access carefully.** SSH is up; next question is whether TD/Autolume can be opened without disrupting Prav's active work.
4. **Handle Dome briefly.** Dan specs are now concrete; Whova shrinks survey scope; ask how much Prav wants SSD involved.
5. **Hardware.** Decide whether 5090 is urgent procurement or longer arc.
6. **End with who sends what.** Austin nudge, John pack, Moonfish/Denning asks, Carol Anne/Shawn Dome package.

## Recommended Calls

| Topic | Recommended call | Alternative | Cost of waiting |
|---|---|---|---|
| Austin Drive | Prav nudges lightly today; Darren waits for files | wait silently | v2 LoRA / Track 2 can't advance |
| 3090 access | primary reverse SSH is fixed enough for commands; WireGuard backup works; ask before opening TD/Autolume | local-only until stable window | no live TD/Autolume verification |
| Autolume output | treat live file as NDI-only until proven otherwise; decide whether Spout patch is worth May risk | assume Spout exists | may chase wrong output path |
| John pack | send once contact exists | hold | projector test loses useful calibration material |
| Dome package | hold final delivery until Dan format, but keep concept package available | send immediately | risk wrong-format material circulating |
| 5090 | decide whether it is May-critical today | defer to next week | May build window likely closes |
| Whova survey | treat as out of scope for SSD | build custom survey path | wasted effort and duplicated event tooling |

## Things Not To Reopen Unless Prav Has New Data

- AnimateDiff + v1 LoRA. It failed; do not retry without v2.
- More scraped Austin-reference training. v1.5 proved the recipe; wait for curated assets.
- Custom survey intake. Whova owns it.
- Public language. Keep pending Austin/Carol Anne review.
- Any claim that Dome assets are native-ready until Dan's encoder path is tested.

## Fast Talking Points

- "Austin path is ready but blocked on his Drive. No incoming Austin email yet."
- "Dan gave real Dome specs: OpenSpace, 6144x3072 equirectangular H.265 MP4, 30 fps, 8-bit."
- "Whova shrinks our survey scope. We should not build survey intake."
- "For Hubble, the safe production center is Track 2 deterministic primitives once Austin approves source/morphs."
- "For style transfer, v2 LoRA is the next real test. v1.5 taught us the recipe; no more stale-data model work."
- "3090 SSH is alive. The five-minute flap was poly's stale-tunnel cleanup; I disabled that cron line and WireGuard is verified as backup."
