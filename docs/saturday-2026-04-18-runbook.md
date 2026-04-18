# Saturday 2026-04-18 Runbook

> Time-sequenced action list for Prav on-site + Darren remote. Start-of-day working document; annotate as we go, commit at end of day.
>
> **Reference plan:** `~/.claude/plans/auto-reboot-recovery.md` has the full rationale, ACs, risks, rollback for every item below.

---

## Before Prav arrives (remote, Darren)

- [ ] Confirm all overnight Telegram alerts reviewed (`ssh windows-desktop-remote "Get-Content C:\Users\user\ssd_notify.log -Tail 30"`). Any new FAIL since last night's relay + SD fix?
- [ ] Check `health_probe.log` tail — 5-min probes all green?
- [ ] Check `td_relay.log` — snapshots still uploading, varying sizes?
- [ ] Peek at `visitor.html` in a browser — image still changing?
- [ ] Signal Prav the questions he needs to answer on arrival (see below).

## Questions for Prav on arrival (via Signal, phone, or at the gallery)

1. **Epson model(s)** — photo the rear label on each Epson. Needed to verify EDID dongle compatibility.
2. **Which Resolume layer does the TD feed occupy?** Default code assumption is layer 4; need to confirm before deploying v2 relay (Phase 0.5).
3. **Autolume preset** — still preset 0 / `network-snapshot-000120.pkl`? (For Phase 2 on Sunday, but get the answer today.)
4. **`.toe` SD resolution** — quick look: is it saved at 768 or 1024? (Phase 3B branch selector.)
5. **Screensaver/lock** — is it disabled? Confirm no auto-lock on the 3090.

---

## Morning block — EDID install + display mapping (Phase 1)

Target: gallery looks ready before 11 AM opening. All work finishes before Blair arrives.

> **Scope note 2026-04-18:** Prav has **one** EDID dongle today (~$50 CAD). It goes on the **BenQ** — the known-problematic projector (resolution reverts to 4K, EDID drift, crashed Arena in prior weeks). The three Epsons stay un-dongled today; we'll evaluate whether to order three more based on how today's BenQ install performs. Epson-side display-ID shuffle is therefore still a risk this week; UIA rebind (`SSD-Resolume-Rebind-UIA`) remains the fallback for any Epson-side dark wall.

### Step 0 — Establish real display mapping (BEFORE any EDID install)

Critical: last night's UIA probe only saw 4 displays because BenQ was off. With everything on there should be 5 (BenQ + 3 Epsons + terminal).

**Important caveat — Windows is NOT deterministic about display IDs across projector power-cycles.** Each off/on can renumber the Arena "Display N" assignments. Post-EDID-install, IDs should stabilise because the dongles keep Windows seeing the EDID even when projector is off (no re-handshake, no re-enumeration). We verify that in Step 3. For now, this step captures *the mapping at this moment*.

- [ ] Prav powers on **all** displays — BenQ + 3 Epsons + terminal monitor. Let them settle 2 min.
- [ ] **Darren remote — capture Arena's Display N view:**
  ```bash
  ssh windows-desktop-remote "schtasks /run /tn SSD-Resolume-UIA-Probe"
  sleep 6
  ssh windows-desktop-remote "type C:\Users\user\resolume_uia_probe.log"
  ```
- [ ] **Also capture Windows' DeviceName view (so we can verify stability separately from Arena's numbering):**
  ```bash
  ssh windows-desktop-remote "powershell -Command \"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::AllScreens | Select DeviceName, Bounds, Primary | Format-List\""
  ```
- [ ] Record every tuple `{Arena Display N ↔ Windows \\.\DISPLAY# ↔ resolution ↔ physical wall name}`. Expect 5 rows.
- [ ] Prav: use Arena's **Output → Identify Displays** menu to visually confirm which Display N lights up on which physical wall + the terminal monitor.
- [ ] Lock the mapping in `docs/resolume-display-rebind-research.md` — replace the night-of-4/17 "4 displays, BenQ off" observation with the real mapping.
- [ ] **Stability pre-test (optional, if time):** power-cycle BenQ off → on, re-run both enumerations, see if the IDs shifted. Gives us a before/after baseline for what the dongles are supposed to fix.

### Step 1 — Dongle compatibility check (BenQ only today)

- [ ] Prav photos the BenQ model label to Darren on Signal.
- [ ] Prav photos the dongle itself (model + any spec sticker) to Darren.
- [ ] Darren confirms dongle is HDMI 1.4+ EDID copy-from-source type compatible with BenQ. If mismatch → don't install; note for refund/exchange.
- [ ] Also photo each **Epson model label** — not blocking today, but we'll use it to order the right dongles if BenQ install goes well.

### Step 2 — EDID install (BenQ)

- [ ] Power off the BenQ projector.
- [ ] Install the dongle inline between projector HDMI-in and the source cable. Follow any "capture" procedure the dongle needs (some EDID copiers require a learn-mode button press while the native signal is active).
- [ ] Power the BenQ back on, confirm it shows content at 1920×1080, no 4K revert.
- [ ] Reboot the 3090 (`ssh windows-desktop-remote "shutdown /r /t 0 /f"`) to test that BenQ stays at 1080p across reboots (this is the historical failure — Windows reverts the res to 4K on every boot without a dongle).

### Step 3 — Verification with the BenQ dongle

Two tests. One for BenQ stability (the thing we just fixed), one for Epson-side instability (the thing we haven't fixed — to confirm UIA rebind still recovers it).

**Test A — BenQ deterministic under power-cycle:**
- [ ] Re-run both enumerations from Step 0 (UIA probe + `[System.Windows.Forms.Screen]::AllScreens`).
- [ ] Power-cycle BenQ: off 30 s → on. Re-run enumerations.
- [ ] Expected: BenQ's `{Arena Display N ↔ \\.\DISPLAY# ↔ 1920×1080}` tuple unchanged. If it shifts → dongle didn't seat correctly or isn't compatible.
- [ ] Reboot 3090. Re-run enumerations. Expected: BenQ still at 1080p, still same Display #.

**Test B — Epson still shifts (no dongle), UIA rebind recovers it:**

**Important**: Prav's normal overnight procedure on the Epsons is **A/V Mute** (blanks the image but keeps the projector powered on — HDMI handshake stays alive, so Display IDs don't shift). That's why the Epsons have been relatively stable despite no dongles. To simulate the dark-wall failure mode, we need a **full** power cycle — the A/V Mute button won't trigger it.

- [ ] Pick one Epson (e.g., Right wall). Use the **Power** button on the remote (not A/V Mute / Blank) to fully power it off. Wait 30 s.
- [ ] Power back on with Power button. Wait for warm-up to complete.
- [ ] Re-run enumerations. Expected: some Display # shift across the three Epsons (Windows renumbered after re-handshake).
- [ ] If the Epson wall goes dark: `ssh windows-desktop-remote "schtasks /run /tn SSD-Resolume-Rebind-UIA"` — this is the semantic test of last night's UIA work we've never been able to run against real-world failure. Expected: wall recovers within 10 s.
- [ ] If the Epson wall stays lit on its own (Windows re-handshakes cleanly): still a win, note for the week.

**Documentation:**
- [ ] Record per-projector outcome: Prav's real wall mapping, BenQ stability post-dongle, which Epson (if any) had to be rebind'd, timing of each.
- [ ] If BenQ dongle works cleanly: order three more for the Epsons. Decision to be logged in `docs/tour-readiness-plan.md` (the touring BOM already assumed 4 dongles).

---

## Mid-day block — deploy the TD-layer fade-in relay (Phase 0.5)

Independent of EDID. Can run in parallel with EDID work if Prav has a quiet moment at the Arena UI.

- [ ] Prav confirms Resolume layer number for TD NDI feed in the current `.avc` composition. Default is 4; if different, note the number.
- [ ] Prav (in Arena): set that layer's opacity to 0 in the composition. Save the `.avc`. (If this conflicts with his live-performance flow, skip this step — the relay will still fade, but starting from non-zero looks less dramatic.)
- [ ] **Darren remote:**
  ```bash
  # confirm python-osc is installed on 3090
  ssh windows-desktop-remote "C:\Users\user\streamdiffusion-env\Scripts\pip.exe show python-osc"
  # if missing:
  ssh windows-desktop-remote "C:\Users\user\streamdiffusion-env\Scripts\pip.exe install python-osc"

  # deploy both files
  scp scripts/resolume_fade.py windows-desktop-remote:C:/Users/user/resolume_fade.py
  scp scripts/td_relay_v2.py   windows-desktop-remote:C:/Users/user/td_relay_v2.py

  # stop current v1 relay cleanly
  ssh windows-desktop-remote "powershell -Command \"Get-Process python | Where-Object { $_.Id -eq (Get-Content C:\\Users\\user\\td_relay.pid) } | Stop-Process -Force; Remove-Item C:\\Users\\user\\td_relay.pid -ErrorAction SilentlyContinue\""

  # update SSD-Relay task to launch v2 (layer=4 or whatever Prav confirmed)
  ssh windows-desktop-remote 'schtasks /change /tn "SSD-Relay" /tr "C:\Users\user\streamdiffusion-env\Scripts\python.exe C:\Users\user\td_relay_v2.py"'

  # fire the task
  ssh windows-desktop-remote "schtasks /run /tn SSD-Relay"
  sleep 4
  ssh windows-desktop-remote "Get-Content C:\Users\user\td_relay.log -Tail 10"
  ```
- [ ] Expected log line: `ResolumeFader: layer=4 target=127.0.0.1:7001 fade=2.0s`

### Test single prompt

- [ ] Prav (or Darren) submits via visitor web app.
- [ ] Watch Arena's layer — opacity should climb 0 → 1 over 2 s, hold, fall 1 → 0 over 2 s after ~30 s total.
- [ ] Wall shows the TD/SD output during the hold.

### Test rapid-fire

- [ ] Submit 3 prompts within 5 s. Each new prompt should cancel any in-progress fade and reset the 30 s dwell timer. No stuck opacities.

### Test mode toggle

- [ ] `ssh windows-desktop-remote "curl http://127.0.0.1:7002/mode/live"` — auto-fade suppressed.
- [ ] Submit test prompt → no fade happens.
- [ ] `ssh windows-desktop-remote "curl http://127.0.0.1:7002/mode/auto"` — back to auto.

### Rollback if broken

- [ ] `ssh windows-desktop-remote 'schtasks /change /tn "SSD-Relay" /tr "C:\Users\user\streamdiffusion-env\Scripts\python.exe C:\Users\user\td_relay.py"'`
- [ ] Fire task → back to v1 baseline.

---

## Side quests (if time permits)

- [ ] **Investigate why `td_relay.py` died on 2026-04-16 16:34:38.** Look at Windows Event Viewer → Application log for 3090 around that timestamp. Likely irrelevant after v2 deploy, but worth capturing root cause for the postmortem.
- [ ] **Check for unread Telegram alerts from the overnight run.**
- [ ] **Verify `.toe` SD resolution** — if we're in the TD UI anyway, check the StreamDiffusion res parameter. If 1024, change to 768 and Save Project. This is Phase 3B Option A — may persist, may not.
- [ ] **Open Arena Preferences → Webserver and enable it.** Will be needed for future Arena REST API monitoring (Phase 6 extra). No downside to enabling now.

---

## Before gallery opens (10:45 AM)

- [ ] Walk the gallery: both walls moving, audio playing.
- [ ] Visitor QR loads on a phone.
- [ ] Submit one test prompt end-to-end.
- [ ] Blair arrives → Prav briefs him on any changes from yesterday's one-pager (none if we stayed additive).

---

## During gallery hours — passive monitoring

- `SSD-Health-Probe` runs every 5 min, fires Telegram on any FAIL with de-dupe.
- `td_relay.log` tails for snapshot upload pattern (should see ~35 s cadence with varying sizes).
- If visitor pipeline fails (prompts not landing), first check is `Streamactive` on SD — last night's failure mode. Heal with `pulse(Startstream)` via TD MCP.

### Emergency remote-repair shortcut

If something silent breaks during the day (SD frozen, Arena stuck, etc):

```bash
# open TD MCP tunnel
ssh -fN -L 9981:127.0.0.1:9981 windows-desktop-remote
# then from Claude Code: execute_python_script with op() calls
```

See `docs/playbook.md` Known Gaps → "StreamDiffusion can silently stop" for the exact heal recipe.

---

## End of day — cleanup + prep for Sunday

- [ ] Close out any open Telegram alerts (review + clear if stale).
- [ ] If Phase 0.5 landed cleanly: update `docs/playbook.md` to reflect v2 is the deployed relay.
- [ ] Annotate this runbook with `[ok]` / `[deferred]` / `[blocked]` per item and commit.
- [ ] Sunday preview: Phase 2 (Autolume auto-start validation) with Prav on RDP/console. See plan.

---

*Template for future runbooks — copy, change date, re-sequence per phase priorities.*
