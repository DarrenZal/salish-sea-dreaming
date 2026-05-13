# Deep Research Prompt #4 — Live OSC Bioregional Feeds

**Best tools:** ChatGPT Deep Research, Claude.ai web-research, Gemini Deep Research.

**Decision unblocked:** Which live feeds we ship in Phase 2 vs defer to MOVE37XR.

**Deadline:** 2026-05-16 (T+5 days).

---

## Prompt (paste verbatim)

```
I'm building an AI art installation about the Salish Sea (BC, Canada) and
want to integrate live bioregional data as OSC streams into TouchDesigner
+ Resolume. The piece runs late May 2026 in Vancouver.

Research and report on real-time data feeds for:

1. Burrard Inlet + Salish Sea tide, wind, surface temp, salinity. Best
   sources: NOAA Tides & Currents (Vancouver Station 9442396), Environment
   Canada Wateroffice, DFO Open Data portal. API stability, refresh rate,
   latency, free-tier limits, JSON/XML format.

2. AIS / ship traffic / anchor density via MarineTraffic, AIS-Hub,
   Spire Maritime. Free-tier limits. Ethical considerations for displaying
   vessel data publicly.

3. Fraser River discharge + freshwater flux into the Salish Sea — USGS Water
   Services equivalents in Canada (Environment Canada). Real-time vs daily.

4. Herring spawn timing — DFO Pacific spawn index, Salish Sea Marine
   Survival Project (UW + PSF). What's available in real-time vs. annual
   archive. Cultural-protocol considerations around displaying spawn data
   publicly given First Nations rights-holders.

5. Orca / cetacean acoustic monitoring — Ocean Networks Canada hydrophone
   feeds, OrcaSound, NEPTUNE observatory. Streaming audio + spectrogram
   APIs.

6. Forage-fish ecosystem monitoring — Kwaxala framework (Heiltsuk and
   Wuikinuxv nations' alternative herring stock assessment). Is any of
   that data public?

7. Open-data ethics — bioregional data that touches Indigenous
   rights-holders' jurisdictions, what protocols apply, who to consult.

Deliverable: A catalog table (source, endpoint, auth, refresh rate, free
tier, format) plus narrative analysis of which 1–3 feeds are worth
shipping for a May install (recommendation), and which to defer to October.
Cultural-protocol notes on each. 6–10 pages.
```
