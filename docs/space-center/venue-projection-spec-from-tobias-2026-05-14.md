# Space Centre Hubble Space — Projection Hardware Spec

**Source:** Email from Tobias Chen (Technology Consultant, T: 647.225.4462, tobiaschen.com) to John Desnoyers-Stewart, dated 2026-05-14 15:54 PT. Forwarded by Pravin to Darren via Signal on 2026-05-25.

## The numbers

- **2 projectors**, mapped side-by-side
- **Each projector: 2560 × 1600 px** (WQXGA, 8:5 aspect)
- **7000 lumens each**
- **Combined native canvas: 5120 × 1600 px** (3.2:1)
- **The wall is "around 4k"** (per Tobias)
- **Recommended deliverable: 2:1 aspect 4K video** (per Tobias)

## What 2:1 4K means in practice

Standard interpretations:
- **3840 × 1920** (16:9 4K trimmed to 2:1)
- **4096 × 2048** (DCI 4K cropped to 2:1)
- **4000 × 2000** (cleanest math, no standard codec preset)

Pravin's Resolume composition + NDI output should be set to one of these. The compositor downstream presumably handles the blend/crop to land cleanly within the 5120 × 1600 projector envelope (with letterboxing top + bottom).

## Implication for 3090 NDI record

- Set Resolume → NDI Output → 2:1 4K (Pravin's choice of exact res)
- Match OBS canvas on 3090 to the same value
- Record native 2:1 4K — what you record = what the venue gets

## John's earlier question (context)

John asked Tobias whether the "1280×720 limit" they'd been seeing was an NDI stream cap or a per-projector cap. Tobias answered without addressing the cap directly — instead just stated the projector specs + recommended 2:1 4K. So the 1280×720 thing was likely from an earlier test setup, not the actual install spec.

This may explain why our OBS on the 3090 is seeing the NDI source at 1920×1080: Pravin's NDI Output is probably still at a test/dev resolution, not the production 2:1 4K target.
