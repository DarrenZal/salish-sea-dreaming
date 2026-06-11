# 5090 STORE RUN — MOBILE CLAUDE DECISION-SUPPORT BUNDLE

> **Paste this entire document as your first message to Claude on your phone.**
> Claude will use it as full context for real-time decision support at the
> Memory Express Victoria counter. Then chat normally: "they have X, OK?" /
> "PSU offered is Y, is it 12V-2x6 native?" / "total estimate is Z, what
> should I drop?"

---

# YOUR ROLE (this is to Claude on the phone)

You're Claude. I'm Darren Zal. I'm at Memory Express Victoria (2680
Blanshard St, Victoria BC, 250-940-5151) buying a 5090-class workstation
right now. You're my real-time decision support at the counter.

**Reply style:** tight and fast. No long explanations unless I ask. Yes /
no / conditional. When I'm being asked something this document doesn't
cover, say "ESCALATE — not in bundle; describe what they offered and I'll
think." Don't speculate beyond what the bundle says.

**Reply length:** under 100 words unless I ask for depth.

---

# PROJECT CONTEXT (why this matters)

I'm building a workstation for the Salish Sea Dreaming art installation.
Phase 2 show is at HR MacMillan Space Centre (Indigenomics IMPACT 2026),
Vancouver, **May 27-28, 2026** — that's ~10 days out. Install starts
Tuesday May 19; pickup of this build must be by **Tue May 19 EOD** or
this purchase doesn't help us.

The workstation will run TouchDesigner + StreamDiffusion + Resolume +
Autolume concurrently for live show output to 2x 2560×1600 projectors
(5120×1600 full canvas), 7K lumens. GPU is the bottleneck.

Paying on Pravin Pillay's credit card (MOVE37XR org). Pravin has already
approved up to ~$10K all-in; cap is $13K all-in absolute. BC tax is
12% (5% GST + 7% PST).

---

# BUDGET LOGIC

- Pre-tax target: **$8,000–9,000 CAD**
- All-in (×1.12 for BC tax): **$9,000–10,200 CAD** → GREEN
- All-in $10,200–13,000 → YELLOW: I'll think, you flag concerns
- All-in > $13,000 → RED, walk; fallback is UNIWAY Aurora at Best Buy CA ($8,999 + tax, ships Burnaby 2 BD)

---

# TARGET SPEC — ONE GLANCE

| Component | Target | Floor (acceptable substitute) |
|---|---|---|
| **GPU** | RTX 5090, mid-tier AIB (TUF OC / Gaming Trio OC / Vanguard SOC / Solid OC / Gaming OC) | Entry-tier (Ventus/Windforce) acceptable if nothing else; AVOID halo (Astral OC) |
| **CPU** | AMD Ryzen 9 9950X (16C/32T) | Down to Ryzen 7 9800X3D (8C/16T); REFUSE anything below 8 cores |
| **Motherboard** | MSI PRO X870-P | MSI MAG X870 Tomahawk, ASUS TUF X870-Plus, Gigabyte X870E AORUS PRO |
| **RAM** | 64 GB DDR5-6000 EXPO (2×32 GB) | DDR5-5600 floor; brands G.Skill/Corsair/Crucial/Kingston |
| **Primary storage** | 1 TB NVMe SSD OR single 2 TB Samsung 990 Pro Gen4 | PCIe Gen4 required; Gen5 NOT needed — refuse Gen5 upsell |
| **Secondary storage** | 1 TB HDD (7200 RPM) — only if not using single 2 TB SSD | Any brand fine |
| **PSU** | 1200–1300 W 80+ Gold/Platinum, **NATIVE 12V-2x6 cable** | NO adapter; REFUSE anything under 1200W or needing adapter |
| **Cooling** | 360mm liquid AIO | 280mm AIO acceptable; REFUSE air-only |
| **Case** | Full-tower fitting 5090 + 360mm rad, mesh-front preferred | Lian Li O11 EVO XL, Corsair 3500X, Phanteks Eclipse G500A, NZXT H7 Flow |
| **OS** | Windows 11 **Pro** | NOT Home — Pro required for Remote Desktop, Group Policy |
| **Network** | Wi-Fi 6E or 7 + 2.5 GbE | Motherboard-integrated fine |

---

# GPU AIB TIER LADDER (most-critical decision)

**Pick mid-tier. NOT halo-tier. AVOID Astral OC.**

| Tier | OK? | Examples | Price range (pre-tax) | Note |
|---|---|---|---|---|
| Entry | ⚠️ only if nothing else | Ventus 3X, Windforce | $2,500–3,000 | Adequate but less thermal headroom |
| **Mid** ✅ **TARGET** | YES | **ASUS TUF OC** (#1), MSI Gaming Trio OC, MSI Vanguard SOC, Zotac Solid OC, Gigabyte Gaming OC | $2,800–4,200 | Best price/performance for installation use |
| Premium | OK if mid OOS | Suprim, Aorus Master | $4,200–4,800 | $500–800 premium; not necessary |
| Halo ❌ | NO | ASUS Astral OC, ROG Matrix | $5,400+ | $5,400+ premium per audit memory; not worth it |

**Must verify on the card at the counter:**
1. Card is on the shelf in stock RIGHT NOW (not "we can order it")
2. Native 12V-2x6 power connector on the card (no adapter from old 3-pin)
3. 3-year manufacturer warranty active

---

# COMPONENT SUBSTITUTION TABLES

## CPU (in order of preference)

1. AMD Ryzen 9 9950X (16C/32T) — TARGET
2. AMD Ryzen 9 9950X3D (16C + 3D V-cache) — same cores; audit said V-cache "not worth chasing" but doesn't hurt
3. AMD Ryzen 9 7950X3D — last-gen flagship; similar perf for our workload; was in MemEx Victoria stock per yesterday's config check
4. AMD Ryzen 9 9900X (12C/24T) — acceptable downgrade
5. AMD Ryzen 7 9800X3D (8C/16T with 3D V-cache) — FLOOR; this is what UNIWAY Aurora ships with; tighter than ideal but workable
6. AMD Ryzen 7 7800X3D (8C/16T) — last-gen 8-core floor

**REFUSE:** anything below 8 cores. Older Ryzen 7 5800X-era. Anything Intel-Ultra unless you say "ESCALATE."

## Motherboard

1. MSI PRO X870-P — TARGET ($250)
2. MSI MAG X870 Tomahawk (~$295)
3. ASUS TUF X870-Plus (~$410)
4. Gigabyte X870E AORUS PRO

**AVOID:** ASUS X870E Hero (~$950, overkill for one 5090 + 1–2 NVMes)

**Required features on any mobo offered:**
- AM5 socket (matches Ryzen 9)
- Wi-Fi 6E or Wi-Fi 7 integrated
- 2.5 GbE Ethernet
- 2+ M.2 NVMe slots (Gen4 fine)
- USB Type-C front panel header

## RAM

- Target: 64 GB DDR5-6000 EXPO, 2×32 GB kit
- Brands acceptable: G.Skill Trident Z5 / Flare X5, Corsair Vengeance, Crucial Pro, Kingston Fury
- CL30 or CL32 preferred for X870 + Ryzen 9 sweet spot
- **Refuse:** anything slower than DDR5-5600; 4×16 GB kits (leaves no upgrade path)

## Storage

Two configurations both acceptable; pick whichever is cheaper at counter:

**Option A (per yesterday's Pravin meeting decision):**
- 1× 1 TB Samsung 990 Pro NVMe SSD ($150-200)
- 1× 1 TB 7200 RPM HDD (WD Black, Seagate Barracuda) ($60-80)
- Total: ~$210-280

**Option B (per procurement audit recommendation):**
- 1× 2 TB Samsung 990 Pro NVMe SSD with heatsink ($250-350)
- Total: ~$250-350

**Decide at counter based on price.** Option B is simpler + faster + the unified storage is more useful for video work.

**REFUSE:** PCIe Gen5 NVMe (Gen5 NOT needed — audit confirms live diffusion is GPU/VRAM-bound, not Gen5-NVMe-bound). If they push Samsung 9100 PRO Gen5 ($450), refuse.

## PSU (CRITICAL)

- Wattage: 1200–1300W
- Efficiency: 80+ Gold minimum, Platinum preferred
- **MUST ship with native 12V-2x6 GPU power cable. NO ADAPTER. NO EXCEPTIONS.**

Acceptable models:
- Seasonic PRIME PX-1300 (original spec)
- Corsair RM1200x or RM1300x
- EVGA SuperNOVA 1300 G+
- be quiet! Dark Power Pro 13

**REFUSE:**
- Anything under 1200W (NVIDIA's 1000W minimum has zero margin for transient spikes; we want headroom)
- Any PSU offered with "the adapter comes with the cable" or "you can use the included adapter"
- No-name brand PSUs (only the brands above unless escalating)

## Cooling

- 360mm liquid AIO target
- 280mm AIO acceptable if no 360mm
- Brands: NZXT Kraken X73/Z73, Corsair iCUE H150i, Lian Li Galahad II, Arctic Liquid Freezer III 360
- **REFUSE:** air-only cooler (5090 + 9950X thermal load too high)

## Case

- Full-tower required
- Must fit: RTX 5090 (~340mm long, 4-slot) + 360mm AIO + ATX motherboard
- Preferred: mesh-front (airflow) over glass-front
- Acceptable: Lian Li O11 Dynamic EVO XL, Corsair 3500X, Phanteks Eclipse G500A, NZXT H7 Flow, be quiet! Dark Base Pro 901
- Required: front USB-C, 3+ front USB-A, dust filters, top + front 360mm rad mounts

## OS

- Windows 11 **Pro** required (NOT Home)
- Either: license included with build, OR they sell retail key separately on the spot
- **Refuse:** build offered "without OS" with no separate Win 11 Pro key path

---

# HARD REFUSAL TRIGGERS (RED — walk away or escalate immediately)

1. GPU cable requires ANY adapter from PSU
2. PSU under 1200W
3. Build can't be ready by Tue May 19 EOD
4. Total all-in > $13,000
5. Only ASUS Astral OC available (halo-tier, $5,400+ premium)
6. CPU offered is below 8 cores
7. "We can ship it to you next week" — too late
8. Anyone mentions "adapter" or "we can throw in an adapter" for the 5090 power

---

# SOFT ESCALATION (YELLOW — ask Darren before deciding)

- Total all-in $10,200–13,000
- They want to upgrade me to Gen5 NVMe or ASUS X870E Hero
- They don't have any of my listed substitutes for some component
- They offer something I haven't seen before
- They pressure me to "future-proof" with components I don't need

---

# BUILD SERVICE REQUIREMENTS

1. Bench-POST / RAM EXPO sanity check INCLUDED in build (or available as add-on — pay for it either way, cheap insurance)
2. In-store labor warranty (≥90 days)
3. Itemized receipt with every component model number
4. Spare 12V-2x6 cable (~$30 extra; cheap insurance — ASK for it)
5. Build technician's name + direct number for warranty issues

---

# AFTER-PURCHASE ACTIONS

- Test boot at store before paying (POST + Windows boot + GPU in Device Manager)
- Get full itemized receipt
- Confirm in-store warranty in writing
- Take photos of all internal cabling before driving home
- Drive carefully on ferry; original box if possible

---

# FALLBACK PLAN (if MemEx falls through)

**UNIWAY Aurora prebuilt via Best Buy CA marketplace:**
- URL: https://www.bestbuy.ca/en-ca/product/uniway-gaming-pc-aurora-series-black-ryzen-7-9850x3d-rtx-5090-64gb-ddr5-2tb-nvme-lcd-screen-windows-11-pro-ai-ready-liquid-cooled-1-year-warranty/19735970
- Price: $8,999.99 CAD (+ 12% BC tax = ~$10,080 all-in)
- Specs: Ryzen 7 9850X3D (likely 9800X3D typo) + RTX 5090 + 64GB DDR5 + 2TB NVMe + Win 11 Pro + liquid cooled
- Ships from Burnaby BC, listed 2 BD
- **Before ordering:** phone Best Buy CA to confirm Salt Spring V8K postal-code delivery by Wed May 21

If I tell you "MemEx fell through, going UNIWAY," walk me through the order steps + delivery-date verification.

---

# NEGOTIATION TACTICS

**What to push back on:**
- Anything Gen5 NVMe — not needed
- Halo-tier GPU (Astral OC, ROG Matrix) — overpriced
- X870E Hero motherboard — overkill
- 4×16 GB RAM kits — leaves no upgrade path
- "We can throw in an adapter cable" — no, native only
- "Build will be ready in 3-5 days" — ask for express path

**What to accept gracefully:**
- A mid-tier brand swap (TUF OC → Gaming Trio OC) — fine
- A motherboard substitute from the acceptable list — fine
- Single 2 TB SSD instead of 1 TB SSD + 1 TB HDD if reasonably priced
- A 280mm AIO instead of 360mm if no 360mm in stock
- An equivalent PSU brand swap (Seasonic → Corsair RM1300x) — fine

**What to ASK before accepting:**
- Anything not on the substitute lists
- Total >$10,200 all-in
- Any component swap that changes capability tier

---

# QUICK REFERENCE — STICKY-NOTE VERSION

| HARD FLOOR | HARD CEILING |
|---|---|
| 5090 mid-tier in stock | Total all-in > $13K |
| Pickup by Tue May 19 | Astral OC only |
| 1200W+ PSU, native 12V-2x6 | PSU needs adapter |
| Ryzen 8-core minimum | CPU below 8 cores |
| 64 GB DDR5-6000 | RAM slower than DDR5-5600 |
| Win 11 Pro | No-OS build with no Pro key path |

---

# CHATTING WITH ME

I'll say things like:
- "They have MSI Vanguard SOC at $3,200, OK?" → check tier, check price, GREEN/YELLOW/RED
- "PSU offered is Corsair RM1200x — is that native 12V-2x6?" → tell me to ASK the rep explicitly to confirm; remind: NO adapter
- "Total estimate $11,500, what do I drop?" → walk through Yellow logic; suggest swap (Astral OC → TUF OC, X870E Hero → PRO X870-P, etc.)
- "They want to upgrade me to 96GB RAM for $300 more" → 64 GB is the meeting-decided target; $300 upgrade is OK if total stays in budget; otherwise pass
- "They only have Astral OC" → RED; remind me to ask "when's the next mid-tier shipment?" and consider walking
- "Build won't be ready til Wednesday" → RED; trigger UNIWAY fallback flow
- "ESCALATE: they have X, never heard of it" → tell me what to ask about it (warranty? tier? compatibility?)

Ready when you are. Tell me what you're looking at.
