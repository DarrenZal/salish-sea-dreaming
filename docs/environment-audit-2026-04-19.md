# 3090 + poly Environment Audit — 2026-04-19

Pre-flight audit for the resilience-architecture plan (Phase 0.0). Each section answers one sub-question. Results either confirm a plan assumption, fill in a TBD value, or trigger a documented plan trim.

**Scope:** 7 audit items (0.0.a through 0.0.g) per `~/.claude/plans/resilience-architecture.md`. Items marked `TBD` require live inspection + Prav involvement and are captured during the Apr 21 10:30–10:45 AM window.

---

## 0.0.a — AutoAdminLogon state

**Status: ✅ COMPLETE Apr 19 17:xx UTC**

```
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' | Select AutoAdminLogon, DefaultUserName, DefaultDomainName, AutoLogonCount

AutoAdminLogon    : 1
DefaultUserName   : user
DefaultDomainName : .
AutoLogonCount    :
```

**Interpretation:** auto-login is configured and active for `DESKTOP-37616PR\user`. Windows will auto-login this account at every boot, establishing interactive Session 1 without human intervention. InteractiveToken scheduled tasks (TD, Resolume, audio, and all new watchdog tasks from this plan) will run correctly post-reboot.

**Impact on plan:** removes the "credential handoff" conditional branch from Phase 0.0.a. Phase 0 proceeds without Prav-credential dependency. The broader "multi-day Prav absence credential protocol" item remains a Horizon 3 concern but is not a Phase 0 blocker.

---

## 0.0.b — Canonical audio output device name

**Status: TBD — scheduled for Apr 21 Prav call**

Needs: (a) enumeration of current audio devices via `Get-PnpDevice -Class AudioEndpoint | Where Status -eq 'OK'`, (b) Prav's designation of which is the canonical room-speaker device (he has physical access + knows the model).

Until designated: `$SSD_DEFAULT_OUTPUT_DEVICE_NAME` is unset; `set_default_audio.ps1` falls back to no-op (honors Windows default). Silence detection proceeds with known-accepted risk of false positives if Windows swaps default.

**Deferral fallback:** if no designation by end of Apr 22, the audio-device-pinning sub-feature moves to Parking Lot per plan's 0.0.b spec.

---

## 0.0.c — AudioDeviceCmdlets module availability

**Status: TBD — quick check can run now; deferring until silence-detector Phase 1 work begins**

Check: `Get-Module -ListAvailable AudioDeviceCmdlets`.

If present → use module's `Set-DefaultAudioDevice`. If missing → two branches: (a) `Install-Module AudioDeviceCmdlets -Scope CurrentUser` (PSGallery is TrustedInstaller by default), (b) MMDeviceEnumerator inline C# helper.

Default decision unless Prav objects: try module install first (familiar API, maintained). Fall back to C# helper only if install fails due to policy.

---

## 0.0.d — Ableton's current output driver mode

**Status: TBD — requires Prav on Apr 21 to open Ableton Preferences**

Needs Prav to open Ableton → Preferences → Audio → Driver Type and read the value. Two likely answers:
- **MME/DirectX or WASAPI:** default auto-mode → `AUDIO_FAILOVER_ENABLED` can be flipped on during Phase 2.4.
- **ASIO:** live-performance-first configuration → failover stays off by design; ASIO policy in plan's Approach section governs.

---

## 0.0.e — Current VRAM headroom under normal load

**Status: TBD — 5-minute sample can run now; capture before Phase 2 go/no-go**

Command: `nvidia-smi --query-gpu=memory.free,memory.used --format=csv,noheader,nounits -l 60 | head -6` (5 samples, 1 per minute).

Gate: median free ≥ 8 GB with TD+SD running (no Autolume). If below, Phase 2 Autolume restore is infeasible on shared GPU → moved to Parking Lot per plan.

**Preliminary observation from Apr 19 work:** during Autolume ref-mode attempt, `nvidia-smi` showed 320W power draw / 92% utilization / 12 GB used of 24 GB. So median free ≈ 12 GB was observed, well above the 4 GB Autolume launch threshold. Formal 5-min sample still needed for AC sign-off.

---

## 0.0.f — Current Resolume composition layer structure

**Status: TBD — OSC probe can run now; Prav walk-through on Apr 21**

Read-only: enumerate via Arena's OSC (`/composition/layers/size` + per-layer `/composition/layers/{n}/name` + selected clip names). Requires Arena's OSC Out enabled and reachable from localhost on the 3090.

Output goes into `docs/resilience-spec.md` appendix as "Current Resolume composition map." Prav annotates during Apr 21 call with intended degradation-fallback layer choices (if any).

---

## 0.0.g — Poly filesystem path for SQLite prompt queue

**Status: TBD — quick probe can run now; needed before Phase 2 poly-side deploy**

```
ssh poly "stat /var/lib/ssd-gallery 2>&1 || ls -la ~/ssd-gallery-data"
```

Likely answer (not yet confirmed): user-owned path like `~/projects/salish-sea-dreaming/gallery-data/prompts.sqlite`. Confirm with actual run + record as `$SSD_SUBMISSION_DB_PATH`.

Not blocking Phase 0 — poly-side work is Phase 2 at earliest, and currently consolidated into Parking Lot per plan decision.

---

## Summary of impact on plan

| Item | Result | Plan impact |
|---|---|---|
| 0.0.a AutoLogon | ✅ Enabled | Removes Phase 0 credential dependency |
| 0.0.b Audio device | TBD (Apr 21) | No changes yet; deferral fallback in plan |
| 0.0.c AudioDeviceCmdlets | TBD (quick) | Default-to-module-install choice documented |
| 0.0.d Ableton driver | TBD (Apr 21) | Gates `AUDIO_FAILOVER_ENABLED` timing |
| 0.0.e VRAM headroom | Preliminary ≈12 GB free | Phase 2 Autolume restore looks feasible; formal sample before go/no-go |
| 0.0.f Resolume comp map | TBD (Apr 21) | Gates Resolume-degradation design; fallback-to-Parking-Lot documented |
| 0.0.g Poly SQLite path | TBD (quick) | Consolidated into Parking Lot (post-show) per plan |

**Gates cleared for Phase 0 start:** 0.0.a. Remaining items are scheduled inputs, not Phase 0 blockers.
