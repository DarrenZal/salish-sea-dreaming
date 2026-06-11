# 5090 Build — Memory Express Victoria Shopping List

**Date:** Sunday 2026-05-17
**Store:** Memory Express Victoria — 2680 Blanshard St, Victoria BC, 250-940-5151
**Listed Sunday/holiday hours:** 11 AM – 6 PM (phone-confirm before driving)
**Purpose:** Complete custom 5090-class build for SSD IMPACT show (May 27-28)
**Payment:** Pravin's credit card (MOVE37XR asset)
**Budget target:** ~$8,000–9,000 CAD before tax. BC tax = 12% (5% GST + 7% PST) → $9,000–10,200 all-in.
**Hard walk-away cap:** $13,000 all-in. Above that, switch to Best Buy CA UNIWAY Aurora fallback ($8,999 + tax, ships from Burnaby in 2 BD).

---

## The headline spec (one-glance)

| Component | Spec |
|---|---|
| **GPU** | NVIDIA RTX 5090 — mid-tier AIB preferred (see GPU section below) |
| **CPU** | AMD Ryzen 9 9950X (16C/32T) target |
| **Motherboard** | MSI PRO X870-P (or similar X870 mid-tier) |
| **RAM** | 64 GB DDR5-6000 EXPO (2x32 GB kit) |
| **Primary storage** | 1 TB NVMe SSD (Samsung 990 Pro Gen4 or equivalent) |
| **Secondary storage** | 1 TB HDD (bulk / backups) |
| **PSU** | 1200–1300 W 80+ Gold/Platinum, native 12V-2x6 cable |
| **Cooling** | 360mm liquid AIO |
| **Case** | Full-tower with 5090 clearance + 360mm rad mount |
| **OS** | Windows 11 Pro |
| **Network** | Wi-Fi 6E or Wi-Fi 7, 2.5 GbE Ethernet (motherboard-integrated is fine) |

---

## Component-by-component decisions

### GPU — RTX 5090 (THE critical decision)

**AIB tier matters; pick mid-tier, NOT halo-tier.**

| Tier | Acceptable? | Examples | Notes |
|---|---|---|---|
| Entry | ⚠️ only if nothing else available | Ventus 3X, Windforce | Cheapest 5090s; usually adequate but less robust thermals |
| **Mid (TARGET)** | ✅ **PREFERRED** | **ASUS TUF OC** (#1 pick), MSI Gaming Trio OC, MSI Vanguard SOC, Zotac Solid OC, Gigabyte Gaming OC | Best price/performance balance; robust enough for installation use |
| Premium | ✅ acceptable if mid-tier OOS | Suprim, Aorus Master | $500–800 premium; not necessary for our workload |
| Halo | ❌ **AVOID** | ASUS Astral OC, ROG Matrix | $5,400+ premium per memory `feedback_nowinstock_newegg_last_seen_unreliable`; not worth the cost |

**Must confirm at store:**
- ☐ Card is genuinely in stock (not "we can order it")
- ☐ Native 12V-2x6 power connector on the card (no adapter from old 3-pin)
- ☐ Card has 3-year manufacturer warranty active

### CPU — AMD Ryzen 9 9950X (target)

**Acceptable substitutes if 9950X out of stock:**
1. **Ryzen 9 9950X3D** — 3D V-cache version; same 16C; per audit "not worth chasing" for our workload but doesn't hurt
2. **Ryzen 9 7950X3D** — last-gen flagship; similar performance for our use; this was confirmed in MemEx Victoria configurator stock yesterday
3. **Ryzen 9 9900X** — 12C/24T; acceptable downgrade if RAM-heavy workloads dominate
4. **Ryzen 7 9800X3D** — 8C/16T with 3D V-cache; FLOOR; tighter than ideal for TD + StreamDiffusion + Resolume concurrent, but workable (this is what UNIWAY Aurora ships with)

**Walk-away:** anything below 8 cores. Do NOT accept Ryzen 5 or older Ryzen 7 (5800X-era).

### Motherboard — MSI PRO X870-P (target)

**Acceptable substitutes:**
- MSI MAG X870 Tomahawk (~$295)
- ASUS TUF X870-Plus (~$410)
- Gigabyte X870E AORUS PRO (Astral PCs uses this)
- **Avoid:** ASUS X870E Hero ($950) — overkill for one 5090 + 1–2 NVMes

**Required features:**
- ☐ AM5 socket (matches Ryzen 9 9950X)
- ☐ Wi-Fi 6E or Wi-Fi 7 integrated
- ☐ 2.5 GbE Ethernet
- ☐ At least 2x M.2 NVMe slots (PCIe Gen4 fine)
- ☐ USB Type-C front panel header (for case)

### RAM — 64 GB DDR5-6000 EXPO

- 2× 32 GB kit (NOT 4× 16 GB — leaves no upgrade path)
- DDR5-6000 EXPO is the X870 + Ryzen 9 sweet spot
- CL30 or CL32 preferred
- Brands: G.Skill Trident Z5 / Flare X5, Corsair Vengeance, Crucial Pro, Kingston Fury — all acceptable
- **Walk-away:** anything slower than DDR5-5600

### Primary storage — 1 TB NVMe SSD

- Samsung 990 Pro 2 TB w/ heatsink is audit's recommendation (single drive, simpler) — could substitute for 1 TB SSD + 1 TB HDD split per meeting decision
- **Decision at store:** if 2 TB Samsung 990 Pro is reasonably priced (~$250-350), take it instead of 1 TB SSD + 1 TB HDD. Faster, simpler, more useful storage.
- If meeting-spec (1 TB SSD + 1 TB HDD): Samsung 990 Pro 1 TB + any 7200 RPM 1 TB HDD (WD Black, Seagate Barracuda)
- **Required:** PCIe Gen4 NVMe (Gen5 not needed — audit confirms live diffusion is GPU/VRAM-bound, not Gen5-NVMe-bound)
- **Avoid:** Gen5 Samsung 9100 PRO ($450 vs $250 for Gen4 990 Pro = no benefit for this workload)

### Secondary storage — 1 TB HDD (only if not using 2 TB SSD)

- 7200 RPM, 64 MB+ cache
- For show videos, backups, training corpora archive
- Any brand fine (WD, Seagate, Toshiba)

### PSU — 1200–1300 W

- Seasonic PRIME PX-1300 was original spec
- Acceptable alternatives at 1200–1300W: Corsair RM1200x/1300x, EVGA SuperNOVA 1300 G+, be quiet! Dark Power Pro 13
- **Required:** 80+ Gold (Platinum preferred), native 12V-2x6 GPU cable (NO adapter)
- **Walk-away:** under 1200W; ANY mention of "adapter required" for the 5090 cable
- NVIDIA's stated minimum is 1000W; we want headroom for 5090's transient spikes

### Cooling — 360mm liquid AIO

- 360mm radiator (mounts to top or front of case)
- Acceptable: NZXT Kraken X73/Z73, Corsair iCUE H150i, Lian Li Galahad II, Arctic Liquid Freezer III 360
- 280mm AIO acceptable if no 360mm available
- **Walk-away:** air cooler only (5090 + 9950X is too much thermal load for air)

### Case — Full-tower

- Must fit: RTX 5090 (~340mm long, 4-slot) + 360mm AIO + ATX motherboard
- Per audit: Fractal Meshify 2 XL was spec target but NOT in MemEx stock; Corsair 3500X was Astral PCs alternative (acceptable)
- Other acceptable: Lian Li O11 Dynamic EVO XL, Phanteks Eclipse G500A, NZXT H7 Flow, be quiet! Dark Base Pro 901
- **Required:** front USB-C, 3+ front USB-A, dust filters, top + front 360mm rad mounts
- Mesh-front (good airflow) preferred over glass-front

### OS — Windows 11 Pro

- ✅ Pro, not Home (Pro needed for Remote Desktop, Group Policy, BitLocker)
- License included with build or buy retail key separately

---

## What to ask the rep (confirm before they ring it up)

1. ☐ **"Is everything in this build on the floor right now, not on order?"**
   - If anything is "we'll order it" → confirm ship-by date is BEFORE Tue May 19
2. ☐ **"Build service: how long? When can I pick up?"**
   - Walk-away if not "today" or "tomorrow latest"
3. ☐ **"Does the build come with a bench-POST/EXPO sanity check?"**
   - 30-min CPU+RAM+mobo only test catches DOA parts before you take it home
   - Pay for this if it's optional — cheap insurance per the audit
4. ☐ **"Native 12V-2x6 GPU cable from the PSU?"**
   - NO adapter. NO "we'll throw in an adapter cable." Native only.
5. ☐ **"Warranty terms?"**
   - In-store labor warranty (90 days minimum) + individual component manufacturer warranties (1–3 years typical)
6. ☐ **"Final out-the-door price WITH tax, all included?"**
   - Should be in $9,000–10,200 range. Anything above $11,000 → recalculate or downgrade GPU tier.

---

## Hard walk-away conditions

❌ All-in price >$13,000 → leave; UNIWAY Aurora at Best Buy CA ($8,999 + tax, Burnaby ship in 2 BD) is the fallback
❌ GPU cable requires ANY adapter → leave (12V-2x6 native or no deal)
❌ Build won't be ready by Tue May 19 EOD → leave (we ship to Salt Spring Wed at latest)
❌ PSU under 1200W → leave (no exceptions)
❌ Only ASUS Astral OC available (halo-tier $5.4k premium) → leave
❌ CPU offered is below Ryzen 7 9800X3D / 7700X tier → leave

---

## Red flags to refuse

- "We can ship it to you next week" — too late
- "The adapter comes with the cable" — no, native 12V-2x6 only
- "This is the only 5090 we have" + it's Astral OC at premium → check Best Buy CA on phone first
- "We don't include Windows" — confirm OS is included OR buy retail Win 11 Pro key separately on the spot
- "Build will be ready in 3-5 days" — not for show timeline; ask if there's a faster path
- Any pressure to "upgrade to Gen5 NVMe" or "ROG/Suprim/Aorus Master" beyond the mid-tier list above

---

## After-purchase actions

1. ☐ Test boot at the store before paying (POST + Windows boot + GPU recognized in Device Manager)
2. ☐ Get full itemized receipt (every component listed by exact model #)
3. ☐ Confirm in-store warranty in writing
4. ☐ Ask for spare 12V-2x6 cable (per audit) — even $30 is cheap insurance
5. ☐ Get build technician's name + direct number for warranty issues
6. ☐ Take photos of all internal cabling before driving home (for future reference)
7. ☐ Drive carefully on the ferry; bubble-wrap or original box if possible

---

## Fallback if MemEx walks-away

**Best Buy CA UNIWAY Aurora prebuilt** — $8,999.99 + 12% BC tax = ~$10,080
- URL: https://www.bestbuy.ca/en-ca/product/uniway-gaming-pc-aurora-series-black-ryzen-7-9850x3d-rtx-5090-64gb-ddr5-2tb-nvme-lcd-screen-windows-11-pro-ai-ready-liquid-cooled-1-year-warranty/19735970
- Specs: Ryzen 7 9850X3D (likely 9800X3D typo) + RTX 5090 + 64GB DDR5 + 2TB NVMe + Win 11 Pro + liquid cooled + 1-year warranty
- Ships from Burnaby BC, listed 2 BD
- **Before ordering: phone Best Buy CA to confirm delivery date to Salt Spring V8K postal code is ≤ Wed May 21**

---

## References

- Full procurement options: `docs/space-center/5090-procurement-options-for-pravin-call-2026-05-16.md`
- Pravin one-pager (Signal-ready, gated on this call): `docs/space-center/drafts/5090-onepager-for-pravin-signal-2026-05-16.md`
- Original spec doc: `docs/space-center/5090-build-spec-2026-05-13.md`
- Audit memory: `~/.claude/projects/-Users-darrenzal-projects-salish-sea-dreaming/memory/feedback_nowinstock_newegg_last_seen_unreliable.md` + `feedback_verify_pricing_before_sponsor_facing.md`
- Meeting decisions: `~/Documents/Notes/Meetings/The Salish Sea Dreaming/2026-05-16 The Salish Sea Dreaming Meeting.md` frontmatter
