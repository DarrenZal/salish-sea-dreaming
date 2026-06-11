# TouchDesigner Live-Feed Receiver - 2026-05-13

Purpose: receive the May-scope bioregional OSC contract in TouchDesigner and expose stable values for CHOP/TOP logic without changing the visitor prompt callback.

## Files

| File | Role |
|---|---|
| `scripts/td_bioregional_osc_callbacks.py` | Paste/import into a TD callback DAT |
| `scripts/test_td_bioregional_callbacks.py` | Local fake-TD smoke test for callback mapping and table upsert behavior |
| `scripts/bioregional_osc_bridge.py` | Polls IWLS Vancouver + Fraser Hope and emits OSC |
| `docs/next-iteration/_research/live-feed-osc-contract.md` | Source contract for addresses, types, endpoints, and cache behavior |

## Recommended TD Setup

Use a separate OSC port for bioregional data so the existing visitor/audio OSC path on `7000` is not disturbed.

1. Create a callback DAT:
   - Path: `/project1/bioregional_osc_callbacks`
   - Contents: paste `scripts/td_bioregional_osc_callbacks.py`
2. Create an OSC In DAT:
   - Path: `/project1/bioregional_osc_in`
   - Port: `7001`
   - Active: on
   - Callbacks DAT: `/project1/bioregional_osc_callbacks`
3. Optional but useful: create a Table DAT:
   - Path: `/project1/bioregional_values`
   - The callback will upsert one row per OSC address.
4. Run the bridge:

```bash
python3 scripts/bioregional_osc_bridge.py --osc-host 127.0.0.1 --osc-port 7001
```

## Values Written

The callback stores values on the first available component from this list:

1. `/project1/salish_dreamworld`
2. `/project1`

It also updates `/project1/bioregional_values` if that Table DAT exists.

| OSC address | Stored key |
|---|---|
| `/sea/tide/level_m` | `bio_tide_level_m` |
| `/sea/tide/rate_mph` | `bio_tide_rate_mph` |
| `/sea/tide/predicted_next_hilo_m` | `bio_tide_next_hilo_m` |
| `/sea/tide/predicted_next_hilo_seconds` | `bio_tide_next_hilo_seconds` |
| `/river/fraser/discharge_cms` | `bio_fraser_discharge_cms` |
| `/river/fraser/level_m` | `bio_fraser_level_m` |
| `/system/cache_used` | `bio_cache_used` |
| `/system/heartbeat` | `bio_heartbeat_status`, `bio_heartbeat_unix_ts` |

The aggregate TD storage key `bioregional_values` holds a dict of the latest values plus `*_updated_at_td_seconds` timestamps.

## Local Verification

The callback was smoke-tested without TouchDesigner using a fake `op()` network:

```bash
python3 scripts/test_td_bioregional_callbacks.py
```

Verified behavior:

- All eight contract addresses produce updates.
- Unknown addresses are ignored.
- Bad payloads are ignored instead of raising inside the callback thread.
- The table DAT behavior is upsert, not append-only growth.
- The callback compiles outside TD.

## Live-TD Verification Still Needed

When the TD machine or MCP is reachable:

1. Add the DATs above.
2. Run `python3 scripts/bioregional_osc_bridge.py --once --osc-port 7001`.
3. Confirm `/project1/bioregional_values` has nine rows: header plus eight addresses.
4. Confirm `/project1` storage contains `bioregional_values`.
5. Wire values through Lag/Filter CHOPs before driving visual parameters.

Public framing remains unchanged: these are present-tense physical-system signals, not Nation-held knowledge or ecological interpretation.
