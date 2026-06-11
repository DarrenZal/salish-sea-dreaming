# 5090 Show Machine Order Readiness Decision Sheet

**Date:** Tuesday 2026-05-19  
**Lane:** Agent D  
**Purpose:** decision sheet for ordering / queuing the RTX 5090 show machine with Memory Express Victoria today.  
**Scope:** readiness and procurement only. Do not send messages, place orders, or imply the machine is already queued.

## Decision Summary

Proceed today only if Memory Express Victoria can confirm the hard gates:

1. Premium Plus + Priority Assembly can realistically target **Friday 2026-05-22 pickup**.
2. The GPU is powered by a **native PSU-to-GPU 12V-2x6 cable**, with **no adapter**.
3. The build team verifies **case, GPU, PSU, 360mm AIO, side-panel cable bend, and GPU support fit** before finalizing the order.
4. The order stays at or above the minimum show-machine floor: RTX 5090, 1200W+ PSU, 64GB RAM as 2x32GB, 2TB NVMe, Windows 11 Pro unless deliberately overridden.

If any hard gate is not confirmed, pause for a new decision.

## Exact Purchase / Readiness Checklist For Ordering Today

Use this as the live checklist before authorizing payment or queue placement.

| Check | Required answer | Blocking? | Notes |
|---|---|---:|---|
| Store can reserve / sell the parts today | Yes | Yes | Do not rely on stale web stock. Confirm live by phone. |
| Premium Plus Assembly + Load OS is available | Yes | Yes | SKU in prior call sheet: `MX1704`. |
| Priority Assembly is available | Yes | Yes | SKU in prior call sheet: `MX00121884`. |
| Friday 2026-05-22 pickup target is realistic | Yes | Yes | Ask for the exact confidence level: committed, likely, or best effort. |
| RTX 5090 is held for this build | Yes | Yes | Target: Gigabyte RTX 5090 Gaming OC 32GB, SKU `MX00132477`. |
| PSU is 1200W+ and ATX 3.x / PCIe 5.x appropriate | Yes | Yes | Target: Corsair HX1200i 1200W Platinum, SKU `MX00135884`. |
| GPU power is native 12V-2x6 from PSU to GPU | Yes | Yes | No 3x/4x 8-pin adapter, no bundled adapter, no extension as the primary solution. |
| Side panel closes without stressing GPU power cable | Yes | Yes | Must verify with the actual selected case / GPU / PSU. |
| GPU anti-sag support installed | Yes | Yes | Required for transport and installation reliability. |
| Case fits GPU length / thickness | Yes | Yes | Target case: Corsair 7000D AIRFLOW Full Tower, White, SKU `MX00118101`. |
| Case fits 360mm AIO and PSU together cleanly | Yes | Yes | Target cooler: Corsair iCUE LINK TITAN 360 RX RGB AIO, SKU `MX00131482`. |
| RAM is 64GB as 2x32GB DDR5 EXPO | Yes | Yes | Do not accept 4x16GB as a convenience substitution. |
| Storage is at least 2TB fast NVMe | Yes | Blocking for today's build floor | Target: WD_BLACK SN850X 2TB Gen4 NVMe, SKU `MX00122322`. More storage is useful but not required to queue. |
| Windows 11 Pro is selected | Yes, unless deliberate override | Blocking if changed casually | Target: Windows 11 Pro DPK, SKU `MX00119521`. Do not let this drift to Home for convenience. |
| BIOS update included | Yes | Important | Especially for X870E / 9950X3D stability. |
| EXPO enabled and tested | Yes | Important | Confirm stable memory profile, not just installed RAM. |
| NVIDIA Studio driver installed | Yes | Important | Prefer Studio driver for TD / Blender / Resolume reliability. |
| Basic stress / burn-in test included | Yes | Important | Ask what they run and for how long. |
| Total before tax recorded | Yes | Important | Needed for Pravin / sponsor tracking. |
| Total after BC tax recorded | Yes | Important | Prior estimate with UPS was about $11,250 all-in. |
| Any substitution written down | Yes | Important | Record exact part, SKU, price, and reason. |

## Target Build To Read Back

| Component | Target part | SKU / note |
|---|---|---|
| Case | Corsair 7000D AIRFLOW Full Tower ATX, White | `MX00118101` |
| CPU | AMD Ryzen 9 9950X3D | Confirm live SKU |
| Cooler | Corsair iCUE LINK TITAN 360 RX RGB AIO | `MX00131482` |
| Motherboard | ASUS TUF GAMING X870E-PLUS WIFI7 | `MX00134563` |
| RAM | G.SKILL Flare X5 64GB DDR5-6000 CL36 EXPO, 2x32GB | `MX00132328` |
| Storage | WD_BLACK SN850X 2TB Gen4 NVMe | `MX00122322` |
| GPU | Gigabyte RTX 5090 GAMING OC 32GB | `MX00132477` |
| PSU | Corsair HX1200i 1200W Platinum, native 12V-2x6 | `MX00135884` |
| OS | Windows 11 Pro DPK | `MX00119521` |
| Assembly | Premium Plus Assembly + Load OS | `MX1704` |
| Assembly speed | Priority Assembly | `MX00121884` |
| Optional UPS | CyberPower CP1500 Pure Sine UPS, 1500VA / 900W | `MX32714` |

## Friday May 22 Readiness Questions

Ask these directly and record the answers.

1. Can you realistically have this build ready for pickup on **Friday 2026-05-22** with Premium Plus + Priority Assembly?
2. Is Friday a firm pickup commitment, a likely target, or a best-effort estimate?
3. What must happen today for Friday pickup to remain realistic: full payment, deposit, part holds, build queue approval, or technician review?
4. By what time today does the order need to be finalized to enter the Priority Assembly queue?
5. If a part substitution is needed, who will call Darren, and how quickly?
6. Will the build include BIOS update, Windows install, NVIDIA Studio driver, EXPO enablement, and stress testing before pickup?
7. What specific stress / bench tests will be run before the machine is released?
8. If pickup slips, what is the earliest fallback: Saturday 2026-05-23, Sunday 2026-05-24, or Monday 2026-05-25?
9. Can the assembled machine be held safely until pickup if it is completed earlier?
10. Can they provide a final parts list / invoice showing any substitutions before pickup?

## Windows 11 Home vs Pro Flag

Use **Windows 11 Pro** by default.

Windows 11 Home is not an acceptable convenience substitution without a deliberate decision because the show machine may need:

- Remote Desktop host access for setup / support.
- More predictable production administration.
- Better local account / policy flexibility.
- Fewer surprises if the machine later joins a managed production or studio workflow.

This is not about performance. TouchDesigner, Blender, and Resolume can run on Home, but Pro reduces operational friction. If Memory Express proposes Home only because it is easier or cheaper, pause and decide.

## Native 12V-2x6 / No Adapter Requirement

This is a hard gate.

Required:

- Native 12V-2x6 cable directly from PSU to RTX 5090.
- Cable supplied or approved for the exact PSU model.
- No 3x/4x 8-pin adapter as the primary GPU power path.
- No sharp bend at the GPU connector.
- Side panel must close without pushing on or kinking the cable.
- Cable should be fully seated and visually inspected by the build team.

Reason: this machine will be transported and used in a production setting. GPU power reliability matters more than minor cost or cosmetic choices.

## Case / GPU / PSU Physical Fit Checks

Have Memory Express verify the physical build before finalizing substitutions.

| Fit area | Check |
|---|---|
| GPU length | RTX 5090 must fit without interfering with front fans / radiator / drive cages. |
| GPU thickness | PCIe slots and airflow clearance must be clean; no contact with lower case structures. |
| GPU support | Anti-sag bracket or support installed and travel-safe. |
| GPU power bend | 12V-2x6 cable has adequate straight run before bend; no side-panel pressure. |
| Case width | Side panel closes normally after the GPU power cable is installed. |
| PSU length | HX1200i and modular cables fit without cramping the PSU shroud / cable chamber. |
| AIO placement | 360mm AIO fits with motherboard heatsinks, RAM height, and case airflow. |
| Airflow path | Intake / exhaust layout supports sustained GPU load, not just idle acoustics. |
| Transport | Internal heavy components are supported enough for pickup and installation movement. |

If the Corsair 7000D creates any cable-bend or fit risk, a larger airflow case is an acceptable substitution. Do not solve a fit issue by accepting an adapter or unsafe cable bend.

## Storage Needs For 4K / DXV / HAP Media

Minimum order floor: **2TB fast NVMe**.

Why 2TB is acceptable today:

- The current wide-wall deck is a small 3840x2160 Resolume package.
- H.264 files are usable for assembly and testing.
- HAP transcode is deferred until the deck is stable.
- The urgent task is a stable show machine, not a perfect archival workstation.

Why more storage may be useful soon:

- DXV3 / HAP files are much larger than H.264.
- 4K loops multiply quickly when keeping H.264 originals, HAP/DXV show copies, and fallback versions.
- Blender image sequences, render caches, TouchDesigner captures, and Resolume recordings can consume hundreds of GB quickly.
- A second 4TB NVMe or SSD is helpful for media cache / show assets / render output, but it should not block today's queue.

Decision:

- Blocking: at least 2TB NVMe in the build.
- Recommended if available without schedule risk: add or plan a second 4TB NVMe / SSD for show media and render output.
- Not worth delaying Friday pickup: Gen5 storage upsell, premium heatsink upsell, or perfect two-drive layout.

## What Matters By Application

### TouchDesigner

Most important:

- RTX 5090 32GB VRAM and strong CUDA / GPU headroom.
- NVIDIA Studio driver.
- Stable thermals under sustained GPU load.
- Fast NVMe for caches, clips, and frame sequences.
- 64GB RAM minimum; more is useful later.

TouchDesigner is the likely next live/prototype stack for heightfield / SDF water and future interaction. Do not promise it as the load-bearing show system without a separate stress test.

### Blender

Most important:

- RTX 5090 GPU rendering headroom.
- 32GB VRAM for larger scenes / textures / geometry.
- 16-core CPU for simulation, export, and general throughput.
- Fast storage for image sequences and cache files.
- Adequate cooling for long renders.

Blender is the higher-quality pre-render path for hero clips. It benefits from more storage, but the first procurement priority is the GPU / PSU / thermal foundation.

### Resolume

Most important:

- Stable GPU output and driver.
- Smooth 3840x2160 playback.
- Fast local storage for DXV/HAP media.
- Reliable Windows install and audio/video output configuration.
- Operator-safe fallback deck and kill-switch structure.

The current deck can test with H.264. Production playback should prefer DXV3 or HAP once the deck is settled, but transcoding is a content workflow step, not a PC-order blocker.

## Blocking vs Non-Blocking

### Blocking

- RTX 5090 unavailable or cannot be held.
- Friday 2026-05-22 readiness is not realistic and no acceptable fallback pickup exists.
- PSU below 1200W.
- No native 12V-2x6 PSU-to-GPU cable.
- GPU power requires an adapter.
- Side-panel cable bend / case fit cannot be verified.
- No GPU anti-sag support.
- RAM substitution changes to 4x16GB.
- Windows 11 Home substitution is proposed casually.
- Build team cannot include BIOS / driver / basic stability testing.

### Non-Blocking

- UPS availability, unless the PC order is already secure.
- Price-beat approval.
- Gen5 vs Gen4 storage.
- CPU substitution from 9950X3D to 9950X if it protects timing / budget.
- Exact RAM latency, as long as it is 64GB DDR5 EXPO in 2x32GB.
- Adding a second 4TB media drive, if unavailable today.
- HAP / DXV transcode timing.
- Clean-master media delivery from Moonfish.
- TouchDesigner live system readiness.

### Ask Before Accepting

- Any non-5090 GPU.
- Any PSU under 1200W.
- Any PSU without native 12V-2x6 support.
- Any smaller case where GPU power-cable clearance is uncertain.
- Any move to Windows 11 Home.
- Any RAM layout other than 2x32GB or better.
- Any storage below 2TB NVMe.

## Short Call Script

> Hi, I want to queue a custom RTX 5090 workstation build today with Premium Plus Assembly plus Priority Assembly, targeting pickup on Friday May 22.
>
> This is for an art installation next week, so timing, stability, and build safety matter more than minor substitutions.
>
> The target build is: Ryzen 9 9950X3D, Gigabyte RTX 5090 Gaming OC 32GB, ASUS TUF X870E-PLUS WIFI7, 64GB DDR5-6000 EXPO as 2x32GB, WD_BLACK SN850X 2TB NVMe, Corsair HX1200i 1200W, Corsair iCUE LINK TITAN 360 AIO, Corsair 7000D AIRFLOW case, Windows 11 Pro, Premium Plus Assembly, and Priority Assembly.
>
> Before I authorize the order, can your build team confirm three hard requirements?
>
> First: is Friday May 22 pickup realistic if I place the order today?
>
> Second: will the RTX 5090 be powered by a native 12V-2x6 cable directly from the PSU to the GPU, with no adapter?
>
> Third: can you verify the physical fit: RTX 5090, HX1200i, 360mm AIO, side-panel cable clearance, safe GPU power-cable bend, and GPU anti-sag support?
>
> Please do not substitute below an RTX 5090, 1200W PSU, native 12V-2x6 GPU power, 2x32GB RAM, 2TB NVMe, or Windows 11 Pro without checking with me first.
>
> If any listed part creates schedule or fit risk, I am open to the nearest reliable equivalent that protects Friday readiness and the native GPU power requirement.

## Notes To Record During The Call

- Person spoken to:
- Time of call:
- Friday 2026-05-22 readiness answer:
- Pickup status: committed / likely / best effort:
- Parts held:
- Exact GPU:
- Exact PSU:
- Native 12V-2x6 confirmed by:
- Case / cable bend / side-panel fit confirmed by:
- GPU support included:
- Windows edition:
- Storage included:
- Tests included:
- Total before tax:
- Total after tax:
- Price beats accepted:
- Substitutions:
- Remaining risks:
- Next action and deadline:

## Post-Call Decision Rule

If all hard gates are green, the order can be treated as procurement-ready.

If any hard gate is yellow or red, do not improvise under pressure. Record the issue and decide whether to:

1. approve a safer substitution,
2. accept a later pickup date,
3. continue with the current 3090 for the immediate venue work,
4. or defer the 5090 purchase to the next Phase 2.x window.
