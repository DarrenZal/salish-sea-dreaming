# Apr 20 — Prav's morning at gallery

Darren on Signal + phone the whole time. This is just the things **you**
(Prav) have to do physically. Almost everything else Darren runs remotely
over SSH.

Ferry at 11:50 — leave gallery by 10:30 latest.

---

1. **Open PowerShell on the 3090, run:**
   ```
   schtasks /run /tn "SSD-SSH-Tunnel"
   ```
   Message Darren: "tunnel restarted." He's in within 30s.

2. **Hand-off** — Darren does the bulk of the deploy over SSH in the
   background (watchdog, Tailscale, Windows Update block, etc.). You do
   the physical items below in parallel.

3. **Install the new dongle.**

4. **Smoke test before you leave:** Darren sends a visitor prompt from
   his phone. You confirm: (a) wall shows a new image, (b) audio is
   audible in the gallery.

5. **Leave for ferry.** Darren continues remaining work remotely.

---

Darren is handling Tailscale entirely over SSH tomorrow (creating the
tailnet on his own account, installing + auth'ing the 3090 remotely).
No action from you needed on the Tailscale side.

If anything is weird or Darren can't reach you, call him: 518-210-2828.

Full detail (for Darren's reference): `docs/apr20-morning-checklist.md`.
Remote plan Darren runs in parallel: `docs/apr20-darren-remote-plan.md`.
