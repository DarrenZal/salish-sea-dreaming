# SALISH SEA DREAMING — On-Site Support Manual

**⚠️ DRAFT v0.1 · 2026-04-19 · Prepared for review by Pravin before distribution**

> This document is written for a non-technical on-site gallery attendant (currently Zoe). Assumes no Windows / networking knowledge. If anything here feels unclear, that's a bug in the manual — tell us.

---

## THE ONE RULE

**Call Prav first.** (Phone: [TK-insert]) He'll loop in Darren if needed. Do not power-cycle the computer tower, unplug cables, or accept Windows prompts without being told to.

**Phone standby: 9:30–10:00 AM daily.** If anything looks off at opening, call the moment you notice — don't wait and hope it resolves.

---

## PART 1 — What working looks like

Every morning at opening, confirm three things:

| # | Check | Pass looks like |
|---|-------|-----------------|
| 1 | **Projection wall** | Moving, dreamy marine imagery (not a frozen image, not black) |
| 2 | **Sound** | Ambient soundscape audible (from speakers OR wireless headphones — whichever mode is active) |
| 3 | **QR code / visitor station** | Reachable on your phone, accepts a test prompt |

If all three pass → walk past, don't touch. If any fails → follow the relevant section below.

---

## PART 2 — Operating modes

We run in one of two configurations on any given day:

### 🟢 MINIMUM (baseline — always acceptable)

- **One projector** (the main wall) showing moving imagery
- **Sound from room speakers** playing Matt's 3-sound ambient loop (via Windows Media Player)
- Visitors experience: visual + audio, no headphones

Use this mode when anything in the optimal setup fails. It still delivers the core experience.

### 🟣 OPTIMAL (preferred when all is well)

- **All projectors** active (main + side walls)
- **Wireless headphones** delivering the full soundscape (Ableton-mixed)
- Visitors experience: immersive spatial projection + intimate headphone audio

---

## PART 3 — Symptom → action cheat sheet

Try the action listed. If it doesn't resolve within 30 seconds, **call Prav**. Do not escalate further on your own.

| You see | Most likely cause | Action |
|---|---|---|
| **Both walls dark at open** | Projectors lost handshake overnight | Open Resolume → top menu → **Output → Advanced Output**. Panel opens. Walls come back in 5–10s. Close panel. |
| **One wall dark, others fine** | Single projector off, or cable jostled | Turn projector off and on with its remote. Wait 30s. Still dark → call Prav. |
| **Frozen image (not moving)** | Render pipeline stalled | Wait 2 minutes (may recover on its own). Still frozen → call Prav. |
| **No sound from speakers** | Audio output routing dropped | See **Audio recovery** below (Part 4). Still silent → call Prav. |
| **No sound from headphones** | Bluetooth / battery / pairing | Check headphone battery + re-pair. Still silent → fall back to speakers (open WMP, play Matt's loop). |
| **Visitor submits prompt, doesn't appear on wall** | Normal — 30 second queue | Tell them "30-second queue." Only call if 2+ minutes with no change. |
| **"No sound" reported by visitor wearing headphones but speakers are on** | Headphones not paired — visitor moved out of range | Guide them back to the listening area, re-pair if needed. |
| **Anything else weird** | — | Call Prav. |

---

## PART 4 — Audio recovery (the most common issue)

Audio output has been the #1 recurring problem. The recovery in order of what to try:

### Step A. Check the physical obvious (10 seconds)

- Is the speaker system powered on? (Indicator light)
- Is the volume knob up? (Should be ~60% for gallery ambient)
- Are headphones paired to the machine? (Bluetooth icon in Windows taskbar)

If any of these are off → fix and listen again. Sound usually returns in 5s.

### Step B. Windows Media Player fallback (1 minute — this is the safest reset)

If speakers should be playing Matt's loop but are silent:

1. On the computer monitor, find **Windows Media Player** in the taskbar (the red/orange music note icon).
2. If not running: Start menu → type "Windows Media Player" → Enter.
3. Click **Music** in the left sidebar → find the playlist called "Salish Dreaming Ambient" (or the single file "Salish Dreaming 21 min.wav").
4. Double-click to play. Enable loop: right-click the track → **Repeat** → **Repeat all**.
5. Confirm sound is audible from speakers.

**This is the minimum config — if WMP is playing, you're good enough. Don't touch anything else.**

### Step C. Ableton recovery (advanced — only if Prav asks)

Ableton is used in performance mode. It needs manual routing after a restart:

1. Find **Ableton Live 12 Suite** in the taskbar (blue icon).
2. Click to bring the window forward.
3. Go to **Options → Preferences → Audio**.
4. Under **Audio Output Device**, select the correct device (Prav will tell you which on the call).
5. Click **OK**.
6. Press **spacebar** in Ableton to start playback.

---

## PART 5 — The cold-start sequence

**Only do this if Prav asks you to.** In order:

1. **Power on all projectors first** (Epson remotes — press power, green light blinks then solid). Wait 90 seconds for warmup.
2. **Power on speaker system** (switch on the speaker controller).
3. **Wake the computer** if sleeping (move mouse or press space on the keyboard at the tower).
4. **Wait 2 minutes.** Most apps auto-start on boot (TouchDesigner, Resolume, audio). Let them settle.
5. **Check the symptom table** (Part 3). If walls are dark → Advanced Output click (top of table). If sound silent → WMP fallback (Part 4, Step B).
6. **Confirm with Prav** that all is well before the gallery opens.

---

## PART 6 — What NOT to do

- ❌ Do **not** press the power button on the computer tower.
- ❌ Do **not** unplug HDMI, USB, or audio cables.
- ❌ Do **not** restart Windows or accept a Windows Update prompt. If a "Restart now" dialog appears, click **Remind me later** or **Snooze**.
- ❌ Do **not** install or uninstall any software.
- ❌ Do **not** close TouchDesigner, Resolume, or Autolume manually, even if they look frozen. Call Prav first.
- ❌ At closing: **just turn the projectors off with their remotes**. Leave the computer running. Leave the speakers on. Only the projectors need shutting down.

**Projector power-cycling is OK.** Turning a projector off and on with its remote is safe. It's only when the image comes back dark that you'd do the Advanced Output click.

---

## PART 7 — Who to call

| Who | When | How |
|-----|------|-----|
| **Pravin** | **First call, always.** Anything unexpected. | Phone: [TK-insert] |
| **Darren** | If Prav is unreachable (remote troubleshooting) | Via Prav / WhatsApp [TK-insert] |
| **Raf** | Gallery/show operational issues only (not tech) | [TK-insert] |

**If you are on the phone with Prav or Darren during a fix — stay on the line. Don't click anything until we confirm.**

---

## PART 8 — Daily routine (for gallery opening)

**30 minutes before opening (9:30 AM):**
- [ ] Phone standby — we will have already received an automated diagnostic email and will message you if anything needs attention.
- [ ] Power on projectors (remotes).
- [ ] Wake computer, confirm taskbar shows TouchDesigner + Resolume + Ableton running.
- [ ] Check walls are moving.
- [ ] Listen for audio from speakers.
- [ ] Submit a test prompt from your phone via the QR code → wait ~30s → confirm it appears on the wall.

**At closing (5:15 PM):**
- [ ] Power off projectors only (remotes). Leave everything else alone.

---

## Changelog

- v0.1 — 2026-04-19 — Initial draft, synthesized from Blair card + Prav's Apr 19 call. Pending Prav review.

---

*This manual is a living document. When something isn't in here that should be, or a step didn't work as described, tell Prav or Darren so we can update it.*
