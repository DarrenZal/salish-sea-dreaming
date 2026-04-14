# Salish Sea Dreaming — Tour Readiness Plan

**Origin:** April 13 call with Prav (post-BenQ-fix, post-transitions-locked, post-"all good now").
**Horizon:** April exhibition (running) → Impact (May) → Polygon Vancouver / Salish Sea tour / schools (post).
**Framing (Prav):** "We can't send an installation off and then have it die. We need it install-ready, trainable, shippable."

---

## Horizon 0 — Today (resolved/rolled forward)

| # | Item | Status | Notes |
|---|------|--------|-------|
| 0.1 | **School marketing images** | ✅ delivered | 16 images (photo + Briony watercolor + multiply/gradient blends) in Drive folder; Prav selected + forwarded. |
| 0.2 | **NDI flicker investigation** | 🟡 root cause identified, partial fix | Evening diagnostic via TD MCP uncovered that `ndiin2` was hardcoded to `MSI (Autolume Live)` — stream doesn't exist since hostname changed to `DESKTOP-37616PR`. Fixed at runtime — pipeline now producing real frames end-to-end. **Persistence + Arena-side check rolled to Horizon 1.** |
| 0.3 | **Ableton ambient audio swap** | ⏭️ deferred to April 14 | `.als` path received. Auto-boot requires AutoHotkey (Ableton doesn't auto-play without spacebar). Can't do reliably in a 10-min reboot window; proper setup tomorrow. |
| 0.4 | **Reboot test** | ✅ done | Full cold-boot validated. TD/SD/Resolume/Relay/SSH/watchdogs/ambient-audio all auto-started. `SSD-Autolume` wrapper failed (`PickleWidget.load()` TypeError) — reverted to disabled + old launcher. |

---

## Horizon 1 — This week (gallery running, 3090 on-site, collaborative hardening)

### April 14 morning — priority sequence with Prav

Run in order. Each step independently valuable so we can stop at any point.

1. **Verify overnight state.** Check `https://salishseadreaming.art/static/visitor.html` — is it showing real content (eagles/water/GAN imagery) or black? The runtime NDI fix from April 13 evening should still be active *as long as TD hasn't been restarted*. TD watchdog log will tell us if it restarted overnight.
2. **Persist the NDI source name in `SSD-exhibition.toe`.** With TD running and `ndiin2` showing real frames: Prav opens TD → confirms `ndiin2.name = "DESKTOP-37616PR (Autolume Live)"` → Ctrl+S. Now the fix survives reboots.
3. **Grep the .toe for other `MSI` hardcodings.** `findstr /C:"MSI " SSD-exhibition.toe` — surface any other ops (NDI, DAT config, etc.) still pointing at the old hostname. Each one is a latent bug waiting for the next reboot.
4. **Arena composition: re-pick all NDI sources from dropdown + save.** Walks through the same stale-hostname problem for Resolume. Open every NDI source in the Sources panel, re-select from the dropdown (should now show `DESKTOP-37616PR (…)`), save the .avc composition. This likely also eliminates the "click Advanced Output to start playback" symptom.
5. **Cold-boot test round 2 — validate persistence.** Trigger another remote reboot. Expected: TD + Arena come back with correct NDI bindings, walls + web app show real content without manual intervention. This is the Impact-tour-readiness baseline.
6. **StreamDiffusion default resolution.** Verify it comes up at 768×768 (Prav's save held) rather than reverting to 1024. If it reverts, find where the default is stored.
7. **BenQ Windows resolution automation.** Write a small PowerShell script that enforces 1920×1080 @ 60Hz on the BenQ display at boot (since Windows reverts). Register as an SSD-* task that fires on logon, early in the sequence (before Display-Watchdog).
8. **Ambient audio output device check.** Verify PowerShell SoundPlayer is reaching the gallery USB speakers, not NVIDIA HDMI or NDI Webcam Audio. If wrong, pin the default audio endpoint via a boot script.
9. **Arena "click to play" automation.** Small PowerShell that focuses the Arena composition window after launch. Script triggered ~30s after Arena task fires.
10. **Ableton auto-start proper setup.** Create AutoHotkey script: launch Ableton with `.als`, wait for main window + ~45s plugin load, send spacebar. Register as `SSD-Ableton` task. Disable or remove the WMP-style `SSD-Ambient-Audio` once Ableton is validated.

### Horizon 1 — other items (backlog, not tied to tomorrow's morning window)

| # | Item | Why | Notes |
|---|------|-----|-------|
| 1.A | **Fix the Autolume wrapper's `PickleWidget.load()` bug** | Re-enable SSD-Autolume auto-start | Wrapper currently disabled due to TypeError on `ignore_errors` kwarg. Fix: monkey-patch `PickleWidget.load` in the wrapper to swallow extra kwargs, without modifying Autolume source. Test locally on a non-gallery copy before re-enabling. |
| 1.B | **NDI flicker — separate from hostname issue.** | Still a real concern if drops recur | After hostname fix is persisted, observe whether flicker still happens. If yes: NDI Tools Studio Monitor, NIC power-mgmt settings, GPU encode capacity. If no: root cause was hostname all along, close issue. |
| 1.C | **MIDI Mini key illumination** (Akai MPK Mini or similar) | Prav wants visual feedback on clip selection during live performance | Prav: "had to do a hack" — involves SysEx messages via Akai MIDI Mix Editor. Research + port his notes into a runbook. |
| 1.D | **Dual-SD-instance audit.** | Post-reboot spawned two Python processes running `td_main.py` (one venv, one system Python) | Confirm design intent with Prav: is the composition supposed to have both `StreamDiffusionTD` and `StreamDiffusionTD1`? If yes, hardcode venv Python path in the spawning DAT so PATH resolution doesn't pick up system Python. If no, delete the duplicate. |
| 1.E | **Visitor app UX first pass** — "come co-dream with the SSD" framing | Prav: "we really need to blow people's minds with this by Vancouver" | Work remotely. Phone overlay of visitor's dream into the stream preview. Requires the web app + server work, not on-site. |
| 1.F | **Decide Briony styling path for Impact.** | Current SD is effectively pass-through — a significant gap from the original vision | Three options already in `CLAUDE.md`: SD-Turbo LoRA, IP-Adapter, SD 1.5 + LCM + LoRA. Pick one and prove-out in a sandbox before Impact. |

---

## Horizon 2 — Before Impact (May 2026)

| # | Item | Why | Notes |
|---|------|-----|-------|
| 2.1 | **Equipment list** — drafted with Prav + Shawn (Carol Anne requested) | Need shippable install bill-of-materials | See "Equipment list" section below — seed structure for the doc. |
| 2.2 | **Epson projector sourcing** — replace BenQ | Prav: "BenQs aren't a VJ-grade brand; Epsons are what you want." BenQ was root cause of Resolume crashes this week. | Spec options: lumens, throw ratio, native res (1080p sufficient, 4K if budget), NDI-friendly (HDMI passthrough quality). |
| 2.3 | **EDID copy-from-source dongles** (2 staging — 1 per projector + spare) | Handshake drift mitigation; the proper install-world fix | Previously discussed; Prav said "for Impact let's get those." Order by end of day April 13. |
| 2.4 | **GPU/compute for shipping — dual GPU is now a confirmed requirement, not nice-to-have** | Today's fps data: single 3090 hits 94% util with TD/SD + Autolume co-running, ~6-11 fps. Sustained 30 fps requires either dropping quality or splitting workload across two GPUs. | Options: (a) second 3090-class tower (one per wall — Autolume on one, TD/SD on other), (b) single workstation with 2× 4090/5090, (c) accept ~10fps on single-GPU — might read fine artistically, costs less but doesn't meet "30fps promise." Prav + Carol Anne decide on budget envelope. |
| 2.5 | **Transport case design** — flight-case / pelican | Must survive shipping | After equipment spec locks. |

---

## Horizon 3 — Tour-ready (post-April, pre-Polygon / Impact-circuit)

| # | Item | Why | Notes |
|---|------|-----|-------|
| 3.1 | **Install-ready package** — a single kit (hardware + software image + cables + documentation) | Ship + forget model | After Horizon 2 equipment lands. |
| 3.2 | **Gallery tech manual for non-technical staff** — extends current docent playbook into a trainable-person runbook | "How do we train a person so that there's just a manual and they can troubleshoot" — Prav | Current `docs/playbook.md` covers docents. This is one level deeper: "what a trained tech at a receiving gallery does." |
| 3.3 | **Remote support protocol** — SSH tunnel baseline works, but what's the SLA / escalation for a receiving gallery? | Can't let installations die in the field | Define: who's on call, response time commitment, remote reboot URL (still in the backlog from earlier playbook), etc. |
| 3.4 | **Touring grant research** | Funding the tour | Canada Council, BC Arts Council, etc. |
| 3.5 | **Venue targets** | Strategic direction | Polygon Vancouver (Prav: "the height of the height"), Salish Sea tour (if Raf goes that route), schools (Prav hypothesized), church-scale spaces (Claire's suggestion — but requires high-lumen projectors). |
| 3.6 | **Cultural / authorship frame** — "The Salish Sea has dreamed us into existence." | Frame for grants, press, program notes | Prav's phrasing. Capture as canonical language. |

---

## Equipment list — seed structure (for Horizon 2.1)

To be filled in collaboratively w/ Prav + Shawn. Rough categories:

### Compute + graphics
- [ ] Primary render machine (GPU, CPU, RAM, storage, OS spec)
- [ ] Backup/failover machine
- [ ] Peripherals (keyboard, mouse, monitor for setup)

### Projection
- [ ] Projectors (lumens, native res, throw ratio, N units)
- [ ] Mounting (ceiling / floor-stand / rigging)
- [ ] Projector cables (HDMI 2.1 high-bandwidth, lengths)
- [ ] **EDID copy-from-source dongles** (N + 1 spare)
- [ ] HDMI splitter / scaler (if signal chain requires)

### Audio
- [ ] Stereo speakers + stands / wall mounts
- [ ] Audio interface (if Ableton live mix)
- [ ] XLR / TRS cables

### Network
- [ ] Router (gallery-local)
- [ ] Cellular backup (for tunnel resilience)
- [ ] Ethernet runs + switch (NDI capacity depends on LAN quality)

### Control surfaces
- [ ] Akai Mini (MIDI) — Prav's current live-control device
- [ ] Backup MIDI controller

### Visitor interaction
- [ ] Printed QR codes + signage
- [ ] Optional: installed tablet(s) for visitor app (vs phone-only)

### Transport / storage
- [ ] Flight case(s)
- [ ] Foam inserts
- [ ] Spare cables bag

### Consumables / spares
- [ ] Spare lamps (if lamp projectors — laser is preferred for tour)
- [ ] Spare cables (all types)
- [ ] Cleaning supplies (projector lenses)

---

## Open coordination items

- [ ] **Raf**: Is the show touring through the Salish Sea? (Prav pinged April 13, awaiting)
- [ ] **Shawn**: Equipment list contribution; when is he next in the loop?
- [ ] **Carol Anne**: Reviews equipment list, funds Horizon 2 purchases? (Impact budget / Indigenomics funding)
- [ ] **Polygon Vancouver**: Prav planning to bring Vancouver Gallery folks to Impact — "next proof of experience."

---

## Change log

| Date | Change |
|------|--------|
| 2026-04-13 | Initial plan. Post-BenQ-fix call. Horizons 0–3 drafted. Equipment list seeded (empty rows — fills in collaboratively). |
| 2026-04-13 | **Evening reboot test + deep NDI diagnostics.** Horizon 0 items mostly resolved. Root cause of "black web app" identified: TD `ndiin2` hardcoded to stale hostname `MSI (Autolume Live)`; actual hostname is `DESKTOP-37616PR`. Runtime fix applied. Horizon 1 reshaped around a concrete April 14 morning sequence (persist NDI fix, grep for other MSI refs, Arena-side fix, BenQ resolution automation, ambient audio device, Arena click-to-play, Ableton auto-start with AHK). Horizon 2.4 strengthened: dual-GPU confirmed as requirement based on today's single-3090 saturation data. New Horizon 1.F: decide Briony-styling path for Impact — SD is currently pass-through. |
