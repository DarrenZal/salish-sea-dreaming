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

### Step 1 — Dongle compatibility check

- [ ] Prav photos the label of each Epson model + BenQ model to Darren on Signal.
- [ ] Darren cross-checks dongle EDID spec vs each model. Any mismatch → don't install that one; UIA rebind script is the fallback for that wall.
- [ ] Only install on compatible projectors.

### Step 2 — EDID install

- [ ] Power off each projector before inline-dongle install (dongle goes between projector HDMI-in and the source cable).
- [ ] Install one projector at a time, power it back on, confirm it shows content at its native resolution.
- [ ] Move to the next projector.

### Step 3 — Reboot test with dongles in place

- [ ] `ssh windows-desktop-remote "shutdown /r /t 0 /f"` (Darren remote) — Prav watches walls.
- [ ] Wait ~4 min for the full auto-start sequence.
- [ ] Expected: every wall comes up at the correct resolution, playing content, no BenQ 4K revert, no manual Advanced Output click required.
- [ ] **Re-run both enumerations from Step 0** (UIA probe + `[System.Windows.Forms.Screen]::AllScreens`). Expected: every `{Arena Display N ↔ \\.\DISPLAY# ↔ wall}` tuple matches pre-reboot. This is what the dongles are supposed to buy us.
- [ ] **Power-cycle one projector** (e.g., BenQ off 30 s → back on). Re-run enumerations. Expected: IDs unchanged. If they shift → dongle didn't seat correctly or isn't compatible with that projector.
- [ ] If a wall is dark post-reboot OR post-power-cycle: `ssh windows-desktop-remote "schtasks /run /tn SSD-Resolume-Rebind-UIA"` — this is the semantic test of last night's UIA work we've never been able to run.
- [ ] Document outcome: which dongles worked, whether UIA rebind was ever needed, what Windows resolution each display reports, whether IDs were stable across the power-cycle test.

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
