# Sonify the Map of Silence

*Concept sketch — March 2026*

## The idea

The [herring spawn data](https://github.com/LinuxIsCool/salish-herring-data) has 75 years of intensity for every DFO section in the Salish Sea. Give each section a voice — a tone, a frequency band, a timbral layer. Spawn intensity controls its volume. No spawn = that voice goes silent.

Play it as a time-lapse: in the 1950s you hear a full chorus, many sections alive and layered. Voices drop out one by one — Fulford Harbour, then the southern Strait. By 2025, mostly Baynes Sound remains. A soloist where there was once a choir.

But the silence isn't the ending. It's where the dreaming begins.

## Two movements

**Movement 1 — Evidence (what was lost)**

The historical time-lapse. Section voices thin out year by year. This is the Map of Silence made audible — the spatial collapse that DFO's aggregate statistics hide. Each voice lost is a lineage of spawning knowledge erased: the old fish that knew the way to that bay were taken, and the young ones never learned.

**Movement 2 — Presence (what remains, what's listening)**

As the historical voices thin, the live signals emerge — the real tide rising at Patricia Bay right now, the moon pulling, the Fraser flowing, the breath cycle sine wave that is always on. The sea is still here, still breathing. The silence made room to hear it.

Stillness rewarded with deeper revelation — exactly the installation's principle. The audience crosses from looking AT ecological loss to listening WITH the sea.

## Visual coupling

Couple it 1:1 to the animated geographic map — each section lights up when its voice sounds, goes dark when it falls silent. Sound and light arrive and disappear together.

In the installation space, spatialize the audio across speakers mapped to the coast. The audience walks through the geography — from chorus, through silence, into the living pulse.

## Data sources

- **Section-level spawn history:** `spawn_by_section_year.parquet` in the [herring data repo](https://github.com/LinuxIsCool/salish-herring-data) — 75 years, all Salish Sea sections
- **Live ecological signals:** the [OSC pulse server](https://github.com/LinuxIsCool/salish-herring-data/blob/main/scripts/export/osc_pulse.py) already broadcasts tide, moon, SST, spawn season, river discharge, and the breath cycle
- **Eve's MIDI/CSV work** can use the same section-level data as source material

## Reference

- ["The Map of Silence: Presence/Absence Across 75 Years"](https://github.com/LinuxIsCool/salish-herring-data/blob/main/notebooks/exports/03-spatial-collapse.ipynb) — the visual this concept sonifies (scroll to that heading in the notebook)
- Herring matriarch / natal fidelity discussion from the [March 19 meeting](https://github.com/LinuxIsCool/salish-herring-data/blob/main/docs/legal/counterarguments.md) (Defense 2 — knowledge-holder mechanism)
