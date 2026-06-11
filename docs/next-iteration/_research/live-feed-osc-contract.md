# Live Feed OSC Contract — Phase 2 May Scope

Date: 2026-05-13  
Scope: HR MacMillan Space Centre Phase 2, three-projector triptych, May sprint.

## Decision

Ship only two live physical-system feeds for May:

| Feed | Source | Station | Role |
|---|---|---|---|
| Vancouver tide | DFO CHS IWLS | Station code `07735`, internal station id `5cebf1de3d0f4a073c4bb943` | present-tense breath of the inlet |
| Fraser discharge | ECCC MSC GeoMet hydrometric realtime | `08MF005`, Fraser River at Hope | slow seasonal freshet memory |

Deferred for October: AIS, hydrophones, Orcasound, herring spawn index, forage-fish governance data, and Nation-held monitoring frameworks.

This follows the Prompt 04 report recommendation that tide and discharge are low-risk, agency-stewarded physical measurements, while species, vessel, audio, and governance feeds carry licensing, privacy, or cultural-protocol risk.

## Tested Endpoints

### IWLS Vancouver Tide

Station lookup:

```text
https://api-iwls.dfo-mpo.gc.ca/api/v1/stations?code=07735
```

Observed water level:

```text
https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/5cebf1de3d0f4a073c4bb943/data?time-series-code=wlo&from=<UTC>&to=<UTC>&resolution=THREE_MINUTES
```

Next predicted high/low values:

```text
https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/5cebf1de3d0f4a073c4bb943/data?time-series-code=wlp-hilo&from=<UTC>&to=<UTC>
```

Important implementation detail: IWLS `stations/{stationId}/data` requires the internal station id, not the public station code. Passing `07735` as the path id returns `400 BAD_REQUEST`.

### Fraser River at Hope

Latest real-time hydrometric readings:

```text
https://api.weather.gc.ca/collections/hydrometric-realtime/items?STATION_NUMBER=08MF005&sortby=-DATETIME&f=json&limit=3
```

## OSC Addresses

All values are raw live targets. TouchDesigner should smooth locally.

| OSC address | Type | Meaning | Update |
|---|---:|---|---|
| `/sea/tide/level_m` | float | latest observed tide height in metres | poll 60 s |
| `/sea/tide/rate_mph` | float | derived tide rate in metres per hour, positive=flood, negative=ebb | poll 60 s |
| `/sea/tide/predicted_next_hilo_m` | float | next predicted high/low value in metres | poll 5 min |
| `/sea/tide/predicted_next_hilo_seconds` | float | seconds until next predicted high/low | poll 5 min |
| `/river/fraser/discharge_cms` | float | latest discharge in cubic metres per second | poll 5 min |
| `/river/fraser/level_m` | float | latest river level in metres at Hope | poll 5 min |
| `/system/heartbeat` | int, float | status flag `1` plus Unix timestamp | every poll |
| `/system/cache_used` | int | `1` if any value came from cache fallback, else `0` | every poll |

`/river/fraser/anomaly_vs_30yr` is intentionally omitted for May. It needs a HYDAT baseline decision and could imply interpretive certainty the current sprint does not need.

## Cache Behavior

The bridge writes a last-good JSON cache after each successful poll. On endpoint failure:

1. Reuse the most recent cached values.
2. Emit `/system/cache_used 1`.
3. Keep emitting heartbeat so TD/Resolume does not drop to black during short agency API outages.

If no cache exists on cold start and any feed fails, the bridge exits non-zero in `--once` mode. In loop mode, it logs the failure and retries on the next interval.

## TD Mapping

Recommended mappings for May:

| Signal | TD use |
|---|---|
| tide level | horizon height, pearl interior waterline, low-frequency brightness |
| tide rate | breath direction, subtle inhale/exhale timing bias |
| next high/low seconds | set whether the 7-minute cycle leans toward gathering or release |
| Fraser discharge | particle density, slow background tone, river-to-sea mixing amount |

Public copy should frame these as ways of listening to present-tense waters, not as a claim to measure or represent Nation-held knowledge.

## Implementation

Bridge script:

```bash
python3 scripts/bioregional_osc_bridge.py --once --dry-run
python3 scripts/bioregional_osc_bridge.py --osc-host 127.0.0.1 --osc-port 7000
```

TD receiver callback:

```bash
python3 scripts/test_td_bioregional_callbacks.py
```

TouchDesigner setup note: if the existing visitor/audio OSC path is already using port `7000`, run the bioregional bridge on `7001` and use the standalone callback in `scripts/td_bioregional_osc_callbacks.py`. Setup details are in `docs/space-center/td-live-feed-receiver-2026-05-13.md`.

End-to-end local receiver test:

```bash
python3 scripts/test_bioregional_osc_bridge.py
```

Verified 2026-05-13 PM: the test spun up a local UDP OSC receiver, ran the bridge against live IWLS/Fraser endpoints, received all eight contract addresses, and validated the packet shape. Sample received values included Vancouver tide level `2.968 m`, tide rate `-0.100 m/h`, next high/low `2.534 m` in `6847 s`, Fraser discharge `6050 cms`, Fraser level `7.105 m`, heartbeat, and `cache_used=0`.

Default cache path:

```text
output/live-feeds/bioregional_cache.json
```

The script sends OSC only when `--dry-run` is absent.
