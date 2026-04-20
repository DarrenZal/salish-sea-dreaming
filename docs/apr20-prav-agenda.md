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

4. **Hardware walk-around** — answer 4 questions while looking at the
   tower:
   - Any USB mic or 3.5mm mic connected?
   - Where does audio-out go? (single cable? splitter?)
   - Camera connected?
   - Wireless headphones — Bluetooth or analog?

5. **Smoke test before you leave:** Darren sends a visitor prompt from
   his phone. You confirm: (a) wall shows a new image, (b) audio is
   audible in the gallery.

6. **Leave for ferry.** Darren continues remaining work remotely.

---

**Before bed tonight** — on admin.tailscale.com, generate a **reusable
auth key** (24h expiry) and Signal it to Darren. That lets him install
and authenticate Tailscale on the 3090 entirely over SSH tomorrow
without you touching the keyboard.

If anything is weird or Darren can't reach you, call him: 518-210-2828.

Full detail (for Darren's reference): `docs/apr20-morning-checklist.md`.
Remote plan Darren runs in parallel: `docs/apr20-darren-remote-plan.md`.
