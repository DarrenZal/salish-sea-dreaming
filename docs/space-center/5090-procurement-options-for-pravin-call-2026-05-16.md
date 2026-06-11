# RTX 5090 Procurement Options — for Pravin Call

**Date:** 2026-05-16 (Sat, revised eve after independent audit)
**Context:** Pravin greenlit ordering the 5090 workstation during today's call ("let's reconvene, order the 590... going on my credit card"). Need to pick a procurement path together before Mon, since shipping / build / soak time eats the window before install Mon May 25 / Tue May 26.
**Reference:** Base build spec at `docs/space-center/5090-build-spec-2026-05-13.md` (verified 2026-05-13).

---

## ⚡ TL;DR — Revised recommendation (post-audit)

**Path: MemEx Victoria local pickup Sun/Mon, self-build, with spec cuts.**

| Item | Was (May 13 spec) | Now | $ delta |
|---|---|---|---|
| GPU | **Premium-tier AIB anchor** ($5,499 — May 13 doc mislabeled this as "generic"; it's actually halo-tier pricing) | **Mid-tier AIB: ASUS TUF OC** (or equivalent: MSI Gaming Trio OC / Vanguard SOC / Zotac Solid OC / Gigabyte Gaming OC — whichever has stock first) | ~$3,500–4,200 |
| Mobo | ASUS X870E Hero ($950) | **MSI PRO X870-P** ($250) | **–$700** |
| Storage | 2 TB Samsung 9100 PRO Gen5 ($450) + 4 TB Gen5 secondary ($560) | **2 TB Samsung 990 Pro w/ heatsink** ($250), single drive only | **–$760** |
| RAM | 96 GB DDR5-6000 CL28 | unchanged — show-day paging risk not worth $300 savings | $0 |
| PSU | Seasonic PRIME PX-1300 1300W | unchanged — 1000W is NVIDIA's stated minimum, headroom is right call | $0 |
| Everything else | unchanged | unchanged | $0 |

**New estimated turnkey:** ~**$8,000–8,700 CAD** (was $11,360). Saves ~$3k. Redirect to: spare 12V-2x6 cable, cloned boot NVMe, transit insurance, rehearsed 3090 fallback.

**⚠️ Load-bearing assumption — the GPU price line.** The $8k turnkey depends on landing a mid-tier 5090 in the $3,500–4,200 band. If MemEx Victoria only carries the Astral OC at $5,430 and Best Buy ship-only can't guarantee delivery by Wed May 21, the all-in **jumps back to ~$10,100**. Still under original budget, but the spec cuts only "pay off" if the GPU pricing line holds. Phone-verify before pulling the trigger.

**Prebuilt correction:** Halifax/Astral is **not** the only prebuilt route. There are BC / Vancouver / Best Buy marketplace leads (Uniway BC, MemEx MEPC, Concept, KesTech, TEKX, Computer 101) plus Canadian online builders. Treat these as **Path E: BC / marketplace prebuilt**, not as the primary plan until a seller confirms a built machine, full component disclosure, and delivery / pickup by Wed May 21–Fri May 22.

**❌ Uniway BC lead RETRACTED (2026-05-16 eve, Playwright re-verified):** Earlier in this doc Uniway Burnaby was flagged as the "🎯 strong lead" based on three 5090 prebuilts (Robin / JONSBO / Y70) being listed at $7,999–$8,999 with "Low stock" labels. **All three are actually sold out** — each page shows multiple `label-unavailable: "Variant sold out or unavailable"` markers, "Store Pickup Unavailable at Burnaby", and "Delivery Not Available to Ship". The "Add to cart" button being enabled is a Shopify default, not a purchase signal. Uniway BC is NOT a viable path right now. Worth phoning anyway to ask if any of the three are being rebuilt this week, but treat as a long shot, not a primary plan.

**🎯 Strongest real lead so far (2026-05-16 eve, Playwright-verified on Best Buy CA product page):** **UNIWAY Aurora via Best Buy CA marketplace — $8,999.99 CAD.** Spec: Ryzen 7 9850X3D (likely a 9800X3D typo — verify) + RTX 5090 + 64GB DDR5 + 2TB NVMe + Liquid Cooled + LCD screen + **Win 11 Pro** + 1-year warranty. **Sold and shipped by UNIWAY** (same Burnaby BC company whose direct site is sold out — different sales channel, different inventory). Page shows: "seller's location within 2 business days", "Available online only", "available with delivery", Add-to-Cart enabled, no sold-out markers, 535 seller reviews. URL: https://www.bestbuy.ca/en-ca/product/uniway-gaming-pc-aurora-series-black-ryzen-7-9850x3d-rtx-5090-64gb-ddr5-2tb-nvme-lcd-screen-windows-11-pro-ai-ready-liquid-cooled-1-year-warranty/19735970

**Tradeoff:** CPU is 8-core (below our doc's 16-core 9950X target) — for TD + StreamDiffusion + Resolume concurrent it's tighter than ideal but workable, especially with the 3D V-cache. RAM (64GB) is below 96GB target but adequate. SSD, OS, cooling all match or exceed spec.

**Other Best Buy CA 5090 prebuilts also verified available (no sold-out markers, Add-to-Cart enabled):**
- YEYIAN Mirage X (Ryzen 7 9900X3D + 5090 + 32GB + 1TB + Win 11 Home) — $8,239.99 (more cores than UNIWAY but less RAM/SSD/OS-tier)
- YEYIAN Mirage S (Ryzen 7 7800X3D + 5090 + 32GB) — $9,059.99 (older CPU, similar caveats)
- CLX Horus 9950X3D + 96GB + 5090 + 2TB SSD + 8TB HDD — $14,679.99 (matches spec but ~$5k over budget)
- CLX Horus 9950X variant — $14,509.99 (closest spec match, same budget concern)
- CLX Horus Intel Ultra 9 285K + 96GB — $14,269.99

**Sold out at Best Buy CA:** ASUS ROG G700 (both 5090 variants).

**Critical unverified for ALL Best Buy options:** firm delivery date to Salt Spring V8K — must be ≤ Wed May 21. Action: add to cart and read checkout date estimate before committing.

**⚠️ MemEx Victoria configurator reality check (Playwright 2026-05-16 eve):** Most spec-doc target parts NOT in stock at MemEx (Ryzen 9950X, MSI PRO X870-P, Fractal Meshify 2 XL, Seasonic PRIME PX-1300, G.Skill TZ5 Royal Neo CL28 96GB). Parts that ARE stocked are priced *significantly* higher than spec doc estimates (Samsung 990 Pro 2TB w/ heatsink listed at $914.98 vs $250 spec estimate — possibly configurator markup vs walk-in retail; phone-verify required). If MemEx walk-in pricing matches configurator pricing, Path A self-build all-in is realistically **$11-13k** not $8k. **Uniway BC prebuilt is now likely cheaper than MemEx Victoria self-build.**

**Why this is the right call** — see "Independent audit findings" section below.

### 5090 AIB tier ladder (for context — all use the same Blackwell GB202 + 32 GB GDDR7)

| Tier | Example cards | CAD range | Cooler |
|---|---|---|---|
| Entry | MSI Ventus 3X (base), Gigabyte Windforce OC, Zotac Solid (base) | $3,000–3,500 | 3-fan, basic — risk of throttling under sustained load |
| **Mid (our target)** | **ASUS TUF / TUF OC**, Gigabyte Gaming OC, MSI Gaming Trio OC, MSI Vanguard SOC, Zotac Solid OC | $3,500–4,200 | 3-fan, robust — engineered for sustained load |
| Premium | MSI Suprim SOC / Liquid, Gigabyte Aorus Master, ASUS ROG Strix | $4,500–5,500 | 3-fan, premium VRM |
| Halo | **ASUS ROG Astral / Astral OC**, ASUS ROG Matrix | $5,400–6,500 | Quad-fan vapor chamber, highest factory OC |

The May 13 spec doc's "$5,499 generic" anchor was effectively halo-tier pricing; the actual generic/entry tier is ~$3k. Mid-tier is the right fit for our workload.

---

## Independent audit findings (2026-05-16 eve)

Sent the morning draft of this doc to an independent reviewer agent for spec sanity-check + missed-options research. Key findings:

### Pricing reality check (correcting the morning draft)

- **NowInStock "$4,059 Astral OC" was stale tracker pricing.** Per audit's live check: ASUS Astral OC is **$5,429.99 with 4 in stock at MemEx Victoria today**. Canada Computers reportedly lists the same $5,429.99. Newegg.ca current listings reportedly ~$6,600+. The Newegg "last seen" price was an artifact, not executable. *(All three figures came from the independent reviewer's web check, not directly re-verified by us — phone MemEx to confirm before driving.)*
- **Real online bargain is Best Buy Canada ship-only:** Zotac / TUF / MSI 5090s in the **$3,200–$3,800 range**, shippable. Requires confirmed delivery date guarantee by Wed May 21.
- **NVIDIA FE path is dead.** US marketplace + HotStock Canada both show FE out of stock; not a realistic plan.

### Spec cuts the audit recommended (and we're adopting)

- **Motherboard:** X870E Hero $949.99 → MSI PRO X870-P $249.99. One 5090 + 1–2 NVMe doesn't need Hero. Alternatives in the same tier if PRO X870-P unavailable: MSI MAG X870 Tomahawk ($295) or TUF X870-Plus ($410). **Save ~$700, high confidence.**
- **Storage:** 2 TB Samsung 9100 PRO Gen5 ($450) → 2 TB Samsung 990 Pro w/ heatsink ($250). "Live diffusion/video output is GPU/RAM/VRAM-bound, not Gen5-NVMe-bound." **Save ~$200, medium-high confidence.**
- **PSU:** **Do NOT downsize to 1000W.** NVIDIA spec is 1000W minimum for 5090; ASUS table implies 1200W for 600W 5090 + Ryzen 9. Keep 1200–1300W (PRIME PX-1300 fine). High confidence.
- **RAM:** Keep 96 GB. "64 GB is probably enough until it isn't; the savings are not worth show-day paging risk." Medium confidence — defer to operator preference, but recommended keep.
- **CPU:** 9950X is correct. 9950X3D not worth chasing for this workload.

### GPU tier — what we actually need

For our workload (TD + StreamDiffusion + Resolume + Autolume concurrent, 6h/day sustained, 4-day install+show, multi-venue arc): **mid-tier AIB is sufficient, premium tier is overkill.**

| Tier | Cards | Fit | $ |
|---|---|---|---|
| Premium | ASUS Astral OC, MSI Suprim SOC, Gigabyte Aorus Master | Margin we don't need | ~$5,200–5,500 |
| **Mid (right tier)** | **ASUS TUF OC**, MSI Gaming Trio OC, MSI Vanguard SOC, Gigabyte Gaming OC, Zotac Solid OC | Exactly matches workload | $3,500–4,200 |
| Budget | MSI Ventus 3X, Gigabyte Windforce OC | Will throttle under sustained load in warm gallery | $3,000–3,500 |

**Decision: target ASUS TUF OC**, with the other mid-tier cards (Gaming Trio OC / Vanguard SOC / Zotac Solid OC / Gigabyte Gaming OC) as acceptable substitutes if TUF unavailable. TUF is the ASUS line specifically engineered for sustained / exhibition use.

### Top 3 risks the audit flagged

1. **Shipping fantasy on Path C** (Halifax → Gulf Islands): can arrive after May 25; Purolator time-guarantees have geographic exclusions. → Path C demoted.
2. **Power connector / 12V-2x6 transient risk:** use native ATX 3.1 12V-2x6 cable, no adapters. Log cable temps / power draw during soak.
3. **Insufficient burn-in:** a prebuilt arriving May 23–25 is worse than a slightly-pricier local build on May 18.

### Retailers we missed (per audit)

- **VI PC Builder, Duncan** — Island-local PC builder, worth a phone call as a fallback.
- **Best Buy Canada ship-only** — *was* in our list but we undervalued it; cheap-tier AIBs there are the actual deal IF delivery can be guaranteed by Wed May 21.
- **Uniway BC** — has cheap 9950X3D/5090 prebuilt listing but sold out / custom 2–9 BD with variable component brands. Risky.
- **OrdinaryTech / Infinity** — Canadian prebuilts, not BC-fast for our deadline.
- **PC-Canada / CDW / DirectDial** — quote-and-ship fallbacks, not primary.
- **NCIX is dead** (confirmed).

### What the audit said it would do with its own money

> "Buy locally from MemEx Victoria on May 18: Astral OC only if you accept the $5.43k premium; otherwise take a Best Buy TUF/Zotac only if delivery is guaranteed by May 21. Drop the Hero and Gen5 SSD immediately, keep 96 GB and 1200–1300 W, self-build, then spend the saved money on insurance, spare 12V-2x6 cable, spare boot NVMe clone, and a rehearsed 3090 fallback."

### Follow-up prebuilt audit (2026-05-17 AM)

Question raised after the audit: **"Are there really no BC / Vancouver prebuilt options?"**

Answer: there are several leads. The problem is not absence; it is **verification quality + timeline**. Most listings either hide exact component models, use marketplace sellers, show "ships in 5–7 business days", or require phone confirmation to know whether the machine is physically built.

#### BC / Vancouver / Island-adjacent prebuilt leads

| Lead | What we found | Status / risk | Action |
|---|---|---|---|
| **Uniway Computers Burnaby BC** (7209 Gilley Ave) | **3 RTX 5090 prebuilts listed (Robin $7,999.99 / JONSBO $8,499.99 / Y70 $8,999.99) but ALL VERIFIED SOLD OUT** (Playwright 2026-05-16 eve): each page has 3-4 `label-unavailable: "Variant sold out or unavailable"` markers + "Unavailable at Burnaby" + "Delivery Not Available to Ship". The "Low stock" label and the price visibility were misleading. Earlier in this doc this was flagged as a "strong lead" — that was wrong. | **Not currently purchasable.** Listings remain visible, possibly for future restock. | Optional: phone to ask if a Robin/JONSBO/Y70 build slot is opening this week. Not a primary plan. |
| **Best Buy CA (direct, not marketplace)** | **5 RTX 5090 prebuilts verified in-stock (Playwright 2026-05-16 eve, "Available online only" + Add to Cart enabled, no sold-out markers):** **YEYIAN Mirage X** (Ryzen 7 9900X3D + 5090 + 32GB DDR5 + 1TB NVMe + X870 mobo + Win 11 Home) **$8,239.99**; **YEYIAN Mirage S** (Ryzen 7 7800X3D + 5090 + 32GB) **$9,059.99**; **CLX Horus liquid-cooled** with **96GB RAM + 2TB + 8TB HDD** in three CPU variants (9950X3D $14,679 / 9950X $14,509 / Intel Ultra 9 285K $14,269). **SOLD OUT:** ASUS ROG G700 (both 5090 variants $5,300 + $6,000). | Real, purchasable today. Need delivery-date check to V8K (Salt Spring). YEYIAN units have <our-spec RAM/SSD; CLX Horus matches/exceeds spec but >budget. | **Add-to-cart YEYIAN Mirage X to checkout (don't buy) → read firm delivery date for Salt Spring postal code. If ≤ Wed May 21, this is the realistic primary plan.** |
| ~~Best Buy marketplace~~ (separate from Best Buy direct above) | Older audit said marketplace had RTX 5090 prebuilts $6,599–9,040 CAD (Canada Gaming / Zonic / Uniway / others) | Marketplace seller risk + vague specs; given Uniway-direct sold out, their Best Buy marketplace listings likely same | Skip unless Best Buy direct + MemEx both fail. |
| **Memory Express MEPC EVOLV5090V2** | MemEx prebuilt listing: 9800X3D + RTX 5090 + 64 GB + 2 TB | Need phone verification; could be easiest local single-warranty prebuilt if Victoria can get it | Ask MemEx Victoria whether any MEPC 5090 prebuilt is in-store or transferable same-day. |
| **Concept Computers, North Vancouver** | Local custom performance PC builder | No 5090 SKU online; phone-only quote path | Call if Pravin can receive / pick up in Vancouver before install. |
| **KesTech Systems, Vancouver** | Local custom PC builder | Likely custom quote, not ready-stock | Call only if MemEx / Best Buy fail. |
| **TEKX, Delta** | BC workstation / custom PC builder with Metro Vancouver delivery | Inventory not visible online | Phone as same-week build possibility. |
| **Computer 101, Vancouver** | Assembly / custom build service | Better if parts are already sourced; not necessarily a 5090 inventory source | Fallback assembler, not primary supplier. |

#### Canadian online prebuilt leads (not BC-fast by default)

| Lead | What we found | Timeline risk |
|---|---|---|
| **OrdinaryTech** | Ready-built RTX 5090 systems around **$9,549–9,799 CAD** | Canada-wide ship; must phone for built/ship-now status. |
| **Infinity Computers** | RTX 5090 prebuilts around **$8,999–10,299 CAD**; lists "built & stress tested" | Site says **ships in 5–7 business days** — likely too slow unless expedited. |
| **Qi Tech** | 9950X3D + RTX 5090 + **96 GB** listed at **$9,799 CAD**, "1 left" | Need location + ship-date confirmation; good spec if real and ready. |
| **Dell Alienware Area-51** | 9950X3D + RTX 5090 config listed around **$6,999.99 CAD** | Only 32 GB RAM in observed config; proprietary-ish platform; delivery date is everything. |
| **GamerTech Toronto** | Some same-day ship/pickup language for ready systems; 9950X3D/5090 custom page observed **sold out** | Ontario shipping; use only if confirmed physically built and express-shippable. |

#### Prebuilt go / no-go criteria

A prebuilt is in play only if the seller confirms all of the following:

1. **Physically built or guaranteed ship by Tue May 19**; hardware in hand by **Wed May 21–Fri May 22**.
2. **Full component disclosure:** exact GPU model, PSU brand/model/wattage, motherboard, case, cooler, RAM speed/capacity.
3. **Power:** 1000W is bare minimum; **1200W preferred** for 5090 + Ryzen 9. Native ATX 3.1 / 12V-2x6 cable, no mystery adapter.
4. **RAM:** 64 GB minimum; **96 GB preferred**. Anything 32 GB is a no unless upgraded before shipping.
5. **Warranty / DOA path:** clear same-week replacement or local support route. A delayed RMA after May 23 is not useful.

Verdict on prebuilts: add them as a live phone-call path, especially **Uniway BC / Best Buy marketplace / MemEx MEPC**, but do not let a cheap prebuilt with vague parts outrank a verified MemEx local build.

---

## Timeline reality check

| Date | Event |
|---|---|
| Sat 2026-05-16 | Today. Call complete. Decide path. |
| Sun 2026-05-17 | Phone calls / online order window |
| Mon 2026-05-18 | Last clean order day if shipping from outside BC |
| Wed–Thu 2026-05-20–21 | Build / arrival window |
| Fri–Sat 2026-05-22–23 | Soak / driver-shakeout (TouchDesigner, StreamDiffusion, Resolume) |
| Sun 2026-05-24 | Travel to Vancouver |
| Mon 2026-05-25 | Install day 1 (per Pravin: install Mon/Tue) |
| Tue 2026-05-26 | Install day 2 |
| Wed–Thu 2026-05-27–28 | **IMPACT 2026 — show** |

Net: **9 days from today to install start**. Pravin's call line: "we're not panicking, we're not rushing. Slow is smooth."

---

## Pricing snapshot — REVISED post-audit

**Morning-draft pricing was based on stale NowInStock tracker data. Audit-verified live pricing below.**

### GPU pricing (as of 2026-05-16 eve — per audit; MemEx + Best Buy phone/checkout verification still pending)

| Card | MemEx Victoria | Best Buy CA (ship-only) | Notes |
|---|---|---|---|
| ASUS Astral OC (halo tier) | **$5,429.99, 4 in stock** *(per audit's live check; phone to reconfirm before driving)* | — | Premium tier — not needed for our workload |
| ASUS TUF OC (mid tier) | TBD — phone-verify | within audit's **$3,200–3,800 range** | **Our target.** Sustained-load designed. |
| MSI Gaming Trio OC (mid tier) | TBD | within $3,200–3,800 range | Acceptable substitute |
| MSI Vanguard SOC (mid tier) | TBD | within $3,200–3,800 range | Acceptable substitute |
| Zotac Solid OC (mid tier) | TBD | within $3,200–3,800 range — typically the cheapest mid-tier | Acceptable substitute |
| Gigabyte Gaming OC (mid tier) | TBD | within $3,200–3,800 range | Acceptable substitute |
| NVIDIA FE | — | Out of stock | Dead path |

⚠️ Best Buy CA per-SKU prices are within the audit-reported $3,200–3,800 range; we have not verified individual SKU prices ourselves. Phone-check before committing.

Memory Express Victoria: **250-940-5151** (open Sat 10–6, Sun 11–6). Canada Computers also reportedly lists Astral OC at $5,429.99 (per audit; online, mainland-only pickup).

### What this means

- Target mid-tier AIB (TUF OC preferred, others acceptable substitutes).
- Whichever of MemEx Victoria or Best Buy ship-only has stock + reasonable delivery wins.
- **Astral OC is in-stock locally** at $5,430 — viable last-resort if mid-tier ships fall through, but ~$1,600+ over target.

---

## Updated spec — POST-AUDIT FINAL

| Component | Part | Estimated CAD | Notes |
|---|---|---|---|
| GPU | **ASUS TUF RTX 5090 OC** (or mid-tier substitute: Gaming Trio OC / Vanguard SOC / Zotac Solid OC / Gigabyte Gaming OC) | **$3,500 – $4,200** | Mid-tier sustained-load card; whichever has stock first |
| CPU | AMD Ryzen 9 9950X (16C/32T) | $770 | unchanged |
| Mobo | **MSI PRO X870-P** (or MAG X870 Tomahawk $295 / TUF X870-Plus $410) | **$250** | **–$700 vs spec doc** (Hero was overkill) |
| RAM | 96 GB DDR5-6000 CL28 (G.Skill TZ5 Royal Neo 2×48) | $850 | unchanged — show-day paging risk not worth $300 savings |
| Storage | **2 TB Samsung 990 Pro w/ heatsink (Gen4)** | **$250** | **–$200 vs spec doc** + secondary NVMe dropped (–$560) |
| PSU | Seasonic PRIME PX-1300 1300W Plat | $550 | unchanged — 1000W min for 5090, headroom is right call |
| Cooling | Arctic Liquid Freezer III 360 + 4× 140 mm fans | $200 | unchanged |
| Case | Fractal Design Meshify 2 XL | $310 | unchanged |
| OS | Windows 11 Pro retail | $240 | unchanged |
| **Subtotal hardware (low–high)** | | **$6,920 – $7,620** | |
| BC tax 12% | | $830 – $914 | |
| **Turnkey (low–high)** | | **$7,750 – $8,534** | **~$3k under original spec** |
| + Build labor (MemEx, optional) | | +$200–300 | for Path B |
| Spares to budget for | spare 12V-2x6 cable, 1× extra 990 Pro for boot clone, transit insurance | +$200–400 | |

**Total all-in including spares: ~$8,000 – $9,000 CAD.** Still well under the $11k+ original budget.

---

## Four procurement paths (detailed — morning-draft pricing, superseded by audit matrix above)

> The descriptions below were written before the independent audit. Cost numbers reflect the morning-draft (pre-spec-cut) build. The decision matrix above is the authoritative current view. Kept here for audit trail.

### Path A — MemEx Victoria, self-build  *(Darren's lean)*

**What:** Drive to 2680 Blanshard Street Sun morning. Buy all parts on the floor. Build at home Sun/Mon. Soak Tue–Thu.

**Cost:** ~$9,500 – $11,200 CAD depending on GPU pricing
**Time-to-install:** 7 days (lots of soak buffer)
**Pros:**
- Direct pickup, no shipping risk
- Full control over every component
- MemEx has known stock breadth in Victoria
- Build hardware in-hand by Sunday afternoon

**Cons:**
- 6–8 hour self-build (cable routing, CPU/AIO mount, BIOS flash, Win 11 install, driver install)
- Risk of one DOA part requiring a return trip
- Need bench space + tools

~~Verification needed before this path:~~ *(stale — see "MemEx Victoria phone script" section above for the current verification list)*

### Path B — MemEx Victoria, their build service

**What:** Same parts list as Path A. Pay MemEx ~$200–300 to assemble + bench-test.

**Cost:** ~$9,700 – $11,500 CAD
**Time-to-install:** 5–6 days (depends on their build queue, typically 2–4 days)
**Pros:**
- Pro assembly, basic burn-in done
- No self-build risk
- Single transaction, single warranty point

**Cons:**
- Build queue could push delivery into Wed/Thu → eats soak time
- Premium on labor
- Less hands-on familiarity with the box

~~Verification needed~~ *(stale — current verification list in phone script section above; build queue length still applies)*

### Path C — Astral PCs prebuilt (Halifax → Salt Spring)  *(highest risk on timing)*

**What:** Configure online today/tomorrow at `astralpcs.com`. Ships from Halifax.

**Reference config (per their site):** Ryzen 9 9950X3D + RTX 5090 + 64 GB DDR5 6000 + 4 TB Crucial P310 Gen4 + Gigabyte X870E AORUS PRO + 1200 W Montech PSU + Corsair 3500X case + Win 11 Pro = **$9,579.99 CAD** before tax.

To match our 96 GB target: +$485 RAM upgrade = $10,064.99 → ~$11,272 CAD turnkey with BC tax.

**Cost:** ~$11,270 CAD (with 96 GB upgrade)
**Time-to-install:** Order today/Sun → ships 2–4 BD → 5–7 BD transit Halifax-to-Salt-Spring → arrives ~**Thu May 21 best case / Mon May 25 worst case**

**Pros:**
- Single SKU, pre-assembled, pre-tested
- 1-year warranty single point
- No Darren build labor

**Cons:**
- **Shipping to Salt Spring carries island/ferry risk** — Purolator/UPS can stretch to 5+ business days for the Gulf Islands
- Spec deviations from doc: Ryzen 9950**X3D** (per audit: 3D V-cache "not worth chasing for this workload" — neutral, not a benefit), Gigabyte AORUS PRO mobo (acceptable), 1200 W PSU (sufficient), Corsair 3500X case (smaller than Meshify 2 XL but adequate)
- No second NVMe option in their config (matches our spec delta)
- No bench access if something's wrong on install day

### Path D — Hybrid (lock GPU online, source rest in Victoria)

**What:** Order **just the Astral OC** from Amazon CA or Newegg CA today if in stock at ~$4,000. Pickup the rest at MemEx Victoria Sun/Mon.

**Cost:** GPU $4,100 + MemEx parts ~$4,400 = ~$8,500 before tax → ~$9,500 turnkey
**Time-to-install:** GPU arrives Tue–Thu, parts on hand Sunday, build Tue–Thu
**Pros:**
- Locks the scarce GPU at online pricing (save ~$1,000 vs MemEx markup if that holds)
- Still get to bench-build at home with most parts in-hand Sun
- Hedges against MemEx not having Astral OC in stock

**Cons:**
- Two transactions, two trackings
- Build day blocked until GPU arrives
- Amazon/Newegg returns more painful than MemEx walk-in

~~Verification needed~~ *(this path's premise — Astral OC at ~$4k online — was discredited by the audit. Astral OC online is ~$5.4k+ everywhere. The mid-tier-via-Best-Buy variant of this idea survives as Path A+ in the decision matrix above.)*

---

## Decision matrix — REVISED post-audit

| Path | Cost (mid-tier GPU) | Cost (Astral OC if forced) | Time-to-install | Build risk | Shipping risk | Verdict |
|---|---|---|---|---|---|---|
| **A — MemEx Victoria, self-build (RECOMMENDED)** | **$7.8–8.5k** | $10.1k | 7 days | Medium (self) | None | **Primary plan** |
| **A+ — Hybrid: GPU from Best Buy ship-only, rest from MemEx Victoria** | **$7.5–8.3k** | n/a | 5–7 days IF Best Buy ships by Wed May 21 | Medium (self) | Low (Best Buy ship to Salt Spring) | **Best $ if delivery guaranteed** |
| **A-bench — MemEx self-build + bench-POST sanity check** | A + $50–100 | A + $50–100 | A + 0.5 day | **Low** (catches DOA mobo/RAM before ferry) | None | **Recommended add-on to A** if MemEx offers it |
| B — MemEx Victoria, their full build service | $8.0–8.8k | $10.3k | 5–6 days | Low | None | Fallback if no time for self-build |
| C — Astral PCs prebuilt (Halifax) | ~$10–11k | n/a (uses their AIB) | 5–9 days | Low | **High (Gulf Islands)** | **Demoted — shipping fantasy per audit** |
| **E — BC / Best Buy marketplace prebuilt** | **$7.4–10k** | n/a | 2–7 days only if physically built / firm delivery | Low | Medium | **Phone-call path; not primary until verified** |
| VI PC Builder Duncan (Island-local fallback) | TBD | TBD | TBD | Low | Low | Worth one phone call as fallback |

> Note: the old morning-draft "Path D" (hybrid online GPU + Victoria parts, anchored on a discredited Newegg $4k Astral price) is dead. Its concept survives in **Path A+** above, but using **mid-tier** Best Buy cards instead of the Astral. Labeling deliberately avoided re-using "D" to prevent confusion.

The bench-POST service (CPU + RAM + mobo only, ~30 min) is a cheap insurance policy: it catches a dead-on-arrival board / bent CPU pin / RAM-incompatibility before Darren takes the parts home and burns build day debugging. Per audit: "Paying a small bench fee may be worth it if it catches a board/RAM/CPU issue before the ferry clock starts."

---

## Recommended pre-call actions (Sat eve / Sun AM)

### MemEx Victoria phone script (250-940-5151, Sat until 6pm, Sun 11–6)

**Lead with the GPU question — it's the load-bearing decision.**

1. **GPU — physically in Victoria today, not shipping from another warehouse:**
   - Do you have any of these 5090 SKUs *on the Victoria floor right now*: ASUS TUF OC, MSI Gaming Trio OC, MSI Vanguard SOC, Zotac Solid OC, Gigabyte Gaming OC?
   - For each in-stock card: **exact before-tax price**
   - **Can you hold one until close + take payment over phone?** (Lock the GPU before driving up.)
   - Backup: Astral OC still in stock at $5,429.99? (We may take it if mid-tier unavailable, but want to know before deciding.)

2. **Rest of build — Victoria-shelf stock + before-tax prices:**
   - MSI PRO X870-P motherboard (fallback: MAG X870 Tomahawk $295, TUF X870-Plus $410)
   - AMD Ryzen 9 9950X CPU
   - G.Skill Trident Z5 Royal Neo 96 GB DDR5-6000 CL28 kit (or equivalent CL30 if CL28 unavailable)
   - Samsung 990 Pro 2 TB w/ heatsink
   - Seasonic PRIME PX-1300 (1300W Platinum)
   - Arctic Liquid Freezer III 360
   - Fractal Design Meshify 2 XL Black
   - Windows 11 Pro retail license

3. **PSU cable verification — critical:**
   - Does the PRIME PX-1300 ship with a **native 12V-2x6 GPU power cable** (no adapter required)?
   - If not, do you carry a Seasonic-compatible 12V-2x6 native cable for in-store purchase?

4. **Bench services — half-build option:**
   - Do you offer a **POST / BIOS / RAM-EXPO bench check** (CPU + RAM + mobo only, ~30 min) as a paid service? What's the fee, and can it be same-day?
   - Full build/test service queue length + price (for Path B fallback)

### Other parallel checks

- **Best Buy CA online** — search "RTX 5090" → filter to mid-tier AIBs (TUF / Zotac Solid / Gaming Trio). For each, click through to checkout to see *concrete delivery date* to Salt Spring postal code (V8K). **Do not anchor on the "estimated" date; require the firm date.** If guaranteed by **Wed May 21**, it's in play; otherwise demote.
- **Best Buy CA prebuilts / marketplace** — search "RTX 5090 gaming PC". Shortlist Canada Gaming / Zonic / Uniway / similar listings only if seller can disclose exact GPU, PSU, motherboard, RAM, cooler, and firm delivery date. Reject 32 GB RAM systems unless seller can upgrade before shipping.
- **Uniway Computers BC** — ask whether any 5090 prebuilt is physically built in BC today, including the $7,599 9950X3D / 5090 / 64 GB listing or Best Buy marketplace equivalents.
- **MemEx Victoria MEPC prebuilt check** — ask specifically about MEPC EVOLV5090V2 or any other RTX 5090 desktop physically in Victoria / transferable same-day.
- **Vancouver local builders** — Concept Computers (North Vancouver), KesTech (Vancouver), TEKX (Delta), Computer 101 (Vancouver). Ask only one question first: "Can you deliver or hand off a tested RTX 5090 workstation by Fri May 22?" If no, stop.
- **Phone VI PC Builder (Duncan)** — Island-local fallback. Ask: 5090 build turnaround, mid-tier card availability, base build fee on operator-supplied parts.

### Pre-call decision tree

Bring numbers to Pravin call → pick path:

- **If MemEx has a mid-tier 5090 at ≤ $4,200:** → Path A (full MemEx self-build) at ~$8k all-in. Probably also use their bench-POST service for ~$50–100. **This is the win.**
- **If MemEx only has Astral OC at $5,430, AND Best Buy guarantees TUF/Zotac delivery by Wed May 21:** → Path A+ (Best Buy ship-only GPU + MemEx parts) at ~$8k all-in. Take the small shipping risk for $1,500 savings.
- **If MemEx only has Astral OC AND Best Buy can't guarantee:** → Path A with Astral OC at ~$10.1k all-in. Eat the premium for shipping certainty. Still under original budget.
- **If a BC / Best Buy marketplace prebuilt is physically built, fully disclosed, and deliverable by Fri May 22:** → compare as Path E. Use it only if it does not hide PSU/GPU/cooling details.
- **If MemEx is short on multiple components:** → Path B (their build service) is still better than chasing parts across two retailers.

## Open call questions for Pravin

1. **Machine location:** Hubble Space (primary live workstation, 5090 runs StreamDiffusion + Austin style transfer) vs. downstairs theater? Spec is the same either way, but it shapes how we frame the role on the credit / sponsor side.
2. **Credit card limit / preference:** Is the ~$8–9k all-in (or ~$10k worst-case if Astral OC forced) within one transaction limit on his card? If not, may need to split GPU + rest into two purchases.
3. **Ship-to-Salt-Spring tolerance:** If Path A+ (Best Buy ship-only GPU) is the best price but delivery slips a day past Wed May 21, what's his risk tolerance? Switch to MemEx Astral OC at +$1,500 to lock certainty, or accept the slip?
4. **Build labor preference:** Self-build + MemEx bench-POST add-on ($50–100, recommended), or full MemEx build service ($200–300)?
5. **Margin for one screwup:** Local pickup gives a return-trip safety window; ship-only does not. Worth $1,500 to lock the certainty?

## Notes

- Sponsor-financing framing in the May 13 spec doc still stands (multi-venue arc IMPACT → MOVE37XR → DEVCON → Life at Center 2027). Even if Pravin's card covers this, Natalia's sponsor pitch from the 5090 doc can still recover the cost.
- 3090 stays on as second machine. Per call: "we'd run the 90 and the 3090". 5090 = primary live; 3090 = downstairs theater or secondary surface.
- No Founders Edition path. FE clears in minutes when restocked; not realistic for our timeline.
- No Best Buy in-store pickup for the GPU itself. Their pickup is for accessories only.

---

## Sources

- `docs/space-center/5090-build-spec-2026-05-13.md` — base spec (Darren, verified May 13). Note: that doc's "$5,499 generic AIB" GPU anchor was effectively halo-tier pricing; not actually generic.
- Memory Express Victoria store info: 2680 Blanshard St, V8T 5E1, 250-940-5151. Hours per their site: Mon–Fri 10–8, Sat 10–6, Sun 11–6.
- Independent reviewer audit (anonymous; web-research-capable agent) — sourced live MemEx + Canada Computers Astral OC pricing ($5,429.99), Best Buy CA mid-tier range ($3,200–3,800), FE out-of-stock, alternative mobos (MSI PRO X870-P / Tomahawk / TUF X870-Plus), VI PC Builder Duncan lead. Quote captured in audit-findings section above. **Not re-verified by us.**
- Astral PCs prebuilt landing page: https://astralpcs.com/buy-rtx-5090-32gb-desktop-computers-canada/ (verified by WebFetch this session)
- Astral PCs sample config page: https://astralpcs.com/product/amd-ryzen-9-9950x3d-5090-prebuilt-desktop-pc/ ($9,579.99 verified by WebFetch this session)
- Memory Express Victoria 5090 product pages (Cloudflare-protected — direct fetch returned a JS challenge; phone-verify):
  - ASUS TUF Gaming 5090: `MX00132352` — https://www.memoryexpress.com/Products/MX00132352
  - ASUS Astral OC: `MX00132349`
  - Gigabyte Gaming OC: `MX00132477`
  - MSI Gaming Trio OC: `MX00132645`
- Best Buy direct 5090 GPU product pages verified openable 2026-05-17:
  - MSI Gaming Trio RTX 5090 OC: https://www.bestbuy.ca/en-ca/product/msi-gaming-trio-geforce-rtx-5090-oc-32gb-gddr7-video-card/18938751 — sold/shipped by Best Buy; observed available to ship.
  - Zotac Solid OC RTX 5090: https://www.bestbuy.ca/en-ca/product/zotac-gaming-geforce-rtx-5090-solid-oc-32gb-gddr7-video-card/18931632 — sold/shipped by Best Buy; observed sold out online.
  - ASUS TUF RTX 5090: https://www.bestbuy.ca/en-ca/product/asus-tuf-gaming-geforce-rtx-5090-32gb-gddr7-gaming-graphics-card-pcie-5-0-hdmi-dp-2-1-3-6-slot-military-grade-components-protective-pcb-coating-axial-tech-fans-vapor-cha/19836561 — marketplace seller, not Best Buy direct; observed available online only.
- Best Buy RTX 5090 gaming PC category: https://www.bestbuy.ca/en-ca/shop/computers-tablets/rtx-5090-gaming-pc — verified openable 2026-05-17; marketplace prebuilts observed in the $6,599–9,040 range; verify seller, exact parts, and checkout delivery date.
- Uniway BC RTX 5090 prebuilt: https://www.uniwaybc.ca/products/uniway-legendary-gaming-pc-amd-ryzen-9-9950x3d-rtx-5090-64gb-ddr5-wi-fi — observed $7,599 CAD but sold out during audit; phone for current BC stock.
- Memory Express MEPC EVOLV5090V2: https://www.memoryexpress.com/Products/MX00133823 — 9800X3D / RTX 5090 / 64 GB / 2 TB prebuilt listing; phone Victoria for current availability.
- Concept Computers gaming/custom performance PCs: https://www.conceptcomputers.ca/gaming
- KesTech Systems custom computer builds: https://kestechsystems.ca/
- TEKX / TEK Services Group custom PC solutions: https://tekx.estherbatycki.com/
- Computer 101 Vancouver custom PC / assembly services: https://computer101.ca/pc-repair-vancouver-burnaby-richmond-surrey-langley-west-vancouver-coquitlam
- OrdinaryTech RTX 5090 ready-built listings: https://ordinarytech.ca/
- Infinity RTX 5090 prebuilt example: https://infinitycomputers.ca/product/infinity-obsidian-rtx-5090-gaming-pc/
- Qi Tech 9950X3D / RTX 5090 / 96 GB listing: https://qitech.ca/products/trio-vision-ultra-5090-9950x3d
- Dell Alienware Area-51 Canada: https://www.dell.com/en-ca/shop/dell-desktops-workstations/alienware-area-51-gaming-desktop/spd/alienware-area-51-aat2265-gaming-desktop

### Sources flagged as unreliable (do not anchor decisions on these alone)

- NowInStock CA RTX 5090 tracker (https://www.nowinstock.net/ca/computers/videocards/nvidia/rtx5090/) — useful for SKU/availability discovery; "last seen" prices freeze when a card goes OOS and can drift far from current retail. **Caused this doc's morning-draft Path D error** (anchored on $4,059 Astral OC that wasn't executable anywhere). See `feedback_nowinstock_newegg_last_seen_unreliable.md` memory note.
- BestValueGPU CA price history (https://bestvaluegpu.com/en-ca/history/new-and-used-rtx-5090-price-history-and-specs/) — same caveat; useful as a directional indicator only.
