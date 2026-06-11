# SSD Test Framework

Probe-based testing for the Salish Sea Dreaming web app. Built after the
2026-05-25 IMPACT cutover. Stable enough to run multiple times a day against
the live production URL.

## Usage

```bash
# Run all suites
python3 scripts/test/run_tests.py

# Run a specific suite by name
python3 scripts/test/run_tests.py chat_indigenomics_depth

# Run all chat suites (substring match)
python3 scripts/test/run_tests.py chat

# List available suites
python3 scripts/test/run_tests.py --list

# Verbose (prints replies as they come)
python3 scripts/test/run_tests.py --verbose chat_multi_turn

# Stop at first suite with failures
python3 scripts/test/run_tests.py --stop-on-fail
```

## Env knobs

| Var | Default | Notes |
|-----|---------|-------|
| `PRIMARY_URL` | `https://salishseadreaming.art` | Target host (override for staging) |
| `WAIT_SECONDS` | `7` | Cooldown between probes (respects chat rate-limit + Gemma load cliff) |
| `RETRIES` | `3` | Retry on transient empty replies |

## Suite layout

Each suite is a YAML file in `probes/`. Schema:

```yaml
category: chat_identity
description: "Single-line description of what this suite tests"
type: chat | chat_multi_turn | kg | live_show
event: impact-2026         # default event for all probes (chat suites only)
wait_seconds: 7            # cooldown between probes
probes:
  - name: A1-installation-name
    query: "what is the name of this installation?"
    must_contain: "salish sea dreaming"        # case-insensitive regex
    must_not_contain: "mahon hall|salt spring" # case-insensitive regex
```

### Probe types

**`chat`** (single-turn):
- `query`, `must_contain`, `must_not_contain`, optional per-probe `event` override

**`chat_multi_turn`** (conversation flows):
- `turns: [{query, must_contain?, must_not_contain?}, ...]`
- History carries across turns; tests context retention + drift defense

**`kg`** (KG HTTP endpoints):
- `method` (GET/HEAD/POST), `path`, `expect_status`, `expect_keys`,
  `expect_min_count: {nodes: N, links: M}`, `must_contain_node`,
  `must_not_contain_node`

**`live_show`** (end-to-end flows):
- `flow: <name>`, plus flow-specific parameters
- Flow registry in `framework.py`:
  - `submit_prompt_check_kg` — submit → wait → verify appears in `/graph/event/<id>`
  - `submit_prompt_check_snapshot` — submit → wait → verify `/td/snapshot/visitor/<id>.jpg` returns 200
  - `consent_off_does_not_appear` — submit with consent off → verify hidden
  - `head_supported_on_snapshot` — verify the HEAD-405 bug stays fixed
  - `graph_redirect_preserves_query` — verify `/graph?event=...` doesn't strip query string

## Adding probes

To add a new probe to an existing suite, edit the YAML. To add a new suite,
drop a new YAML file in `probes/` — the runner discovers it automatically.

To add a new `live_show` flow:
1. Add a `_flow_<name>` function in `framework.py`
2. Register it in `run_live_show_probe`'s dispatch table
3. Reference it from a YAML probe via `flow: <name>`

## Pre-show smoke

Before doors on May 27, run this end-to-end smoke:

```bash
python3 scripts/test/run_tests.py live_show
python3 scripts/test/run_tests.py kg
python3 scripts/test/run_tests.py chat_identity
python3 scripts/test/run_tests.py chat_consent_refusals
```

Exit code 0 = ship. Anything else = investigate before doors.

## Adding event-scoped tests

When the chat or KG gains a new event (e.g., MOVE37XR Oct 2026):

1. Add an event block in `gallery_server.py:CHAT_SYSTEM_PROMPT_EVENT_BLOCKS`
2. Add an entry in `ssd-events.json`
3. Add cards tagged `event:<new>` in `ssd-cards.json`
4. Copy the `06_chat_cross_event.yaml` pattern with the new event slug
5. Add probes verifying isolation in both directions

## Known transients

- Gemma can return empty replies under load (3+ concurrent /chat in flight).
  The framework retries 3× with 2s backoff; if all retries fail the probe is
  marked failed with `<RETRY_EXHAUSTED: ...>` in the reason.
- POST /prompt has a 3s rate limit per IP. Set `WAIT_SECONDS >= 5` for the
  `live_show` suite which submits multiple prompts.

## Where to add what

| New thing | File |
|-----------|------|
| New chat probe | One of `probes/0X_chat_*.yaml` |
| New multi-turn flow | `probes/11_chat_multi_turn.yaml` |
| New KG endpoint check | `probes/12_kg_endpoints.yaml` |
| New live-show flow | Both `framework.py` (handler) and `probes/14_live_show_integration.yaml` (probe entry) |
| New probe TYPE entirely | Add a runner to `framework.py:RUNNERS`, document here |
