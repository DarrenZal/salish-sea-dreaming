# Software & License Audit — Phase 2 Production Stack

**Day 1 audit target.** Confirms every license seat / activation needed for both the primary 3090 production stack AND the cold-spare laptop before transport (Day 11).

---

## Primary 3090 (Salt Spring, transported to Vancouver)

| Software | Required seat | Current status | Notes |
|---|---|---|---|
| Resolume Arena | 1 commercial seat | ☐ Verify | Per `installation-archive/` — was running at Mahon. Confirm seat carries to new install. |
| TouchDesigner | Commercial or Educational | ☐ Verify | Confirm active license, not trial expiring. |
| StreamDiffusion + SDTD | Open-source | ☐ Verify TRT engine compiled for sd-turbo | Re-test post-archive-restoration |
| Autolume | Research stack | ☐ Verify | StyleGAN2 PKL still loads cleanly |
| MediaPipe Python env | Open-source | ☐ Verify | `hand_pos` CHOP bridge from April 25 |
| MultiMonitorTool | Free | ☐ Verify | Reconfigure for 3 displays (was 4 at Mahon) |
| DisplayFusion | Paid | ☐ Verify license | Used for virtual displays / multi-monitor management |
| Spout for TD | Open-source | ☐ Verify | Latest version compatible with TD + Resolume |
| NDI Tools | Free | ☐ Verify | For Autolume → Resolume bridge |
| Win 11 + drivers (NVIDIA, audio, Kinect if used) | OS + driver licenses | ☐ Verify | EDID dongle drivers also |

## Cold-spare laptop (Prav's gaming laptop, Vancouver-prepped Day 8)

| Software | Required seat | Current status | Notes |
|---|---|---|---|
| Resolume Arena | 1 commercial seat (NEW or transferred) | ☐ **Critical** — confirm distinct seat OR transfer policy with Resolume | Without this, cold-spare fallback is unusable |
| 3-output capability | GPU model + ports | ☐ Verify GPU model (likely RTX 3060/3070); confirm 3× HDMI outputs OR HDMI splitter present | |
| Pre-rendered clips library | Copy of final composition | ☐ Sync Day 8 | |
| Spout (if any live elements) | Open-source | ☐ Verify | |
| Power + cabling | Charger + 3× HDMI cables | ☐ Inventory | |

## Cloud / external

| Service | Account | Status |
|---|---|---|
| TELUS H200 cluster | Via Carol Anne | ☐ Confirm Jupyter + Docker access by Day 3 |
| poly gallery server | SSD-owned VPS | ☐ Confirm running; visitor app accessible |
| Reverse SSH tunnel (poly:2222) | poly + 3090 keys | ☐ Verify Day 1 |
| Tailscale | SSD account | ☐ Verify 3090 + laptop joined |
| WireGuard | SSD account | ☐ Verify 3090 + laptop joined |
| Signal (alerts + comms) | Darren + Prav + Austin + Carol Anne + Natalia | ☐ Group thread established |
| Telegram (health beacon) | Darren bot | ☐ Verify alerts firing |

---

**Updated by:** Darren Zal
**Last updated:** 2026-05-11 (audit seeded Day 1 of Phase 0 sprint)
