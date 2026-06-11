# v6 Promotion Procedure

**v6 sandbox URL:** https://v6.salishseadreaming.art (port 9005, code at `~/ssd-v6/` on poly, branch `v6-prompt-dreamworld-themes`, commit `0c4c1eb`)

## What v6 adds vs v5

1. **Reciprocal prompt question** — "What are you dreaming as the Salish Sea? / What is the Salish Sea dreaming as you?"
2. **Hybrid dreamworld** — IMPACT dreams full opacity, Digital Ecologies dimmed as ambient corpus (`window._scopeEvent` from `?event=` URL param)
3. **Indigenomics theme overlay** — `?theme=on` recolors fish by hash-based theme attribution

## How to test before promoting

```bash
# Spot-check from phone / desktop browser
open https://v6.salishseadreaming.art/visitor.html
open https://v6.salishseadreaming.art/graph-assets/dreamworld.html
open https://v6.salishseadreaming.art/graph-assets/dreamworld.html?theme=on
open https://v6.salishseadreaming.art/graph-assets/dreamworld.html?event=digital-ecologies-2026

# Full test sweep against v6 URL
PRIMARY_URL=https://v6.salishseadreaming.art python3 scripts/test/run_tests.py
```

## How to promote v6 → primary

When v6 has been approved:

```bash
# 1. Edit Caddyfile: swap primary block to point at port 9005
TS=$(date +%Y%m%d-%H%M%S)
ssh poly@37.27.48.12 "sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak-pre-v6.${TS}"
ssh poly@37.27.48.12 'sudo sed -i "0,/reverse_proxy localhost:9004/{s/reverse_proxy localhost:9004/reverse_proxy localhost:9005/}" /etc/caddy/Caddyfile'
ssh poly@37.27.48.12 'sudo systemctl reload caddy'

# 2. Add a v5 rollback subdomain (v5.salishseadreaming.art → :9004)
# Already exists in current Caddyfile — confirm with:
ssh poly@37.27.48.12 'grep -A2 v5.salishseadreaming /etc/caddy/Caddyfile'

# 3. Re-point the 3090 relay at port 9005
ssh windows-desktop 'powershell -Command "[System.Environment]::SetEnvironmentVariable(\"GALLERY_URL\", \"http://37.27.48.12:9005\", \"User\")"'
# Then restart the SSD-Relay scheduled task on the 3090 to pick up new env

# 4. Smoke test
curl -sL https://salishseadreaming.art/visitor.html | grep -c "dreaming as the Salish Sea"  # should be ≥1
PRIMARY_URL=https://salishseadreaming.art python3 scripts/test/run_tests.py live_show

# 5. v6 DB note
# v6's prompts-v6.db was seeded from v5 at v6-deploy time (2026-05-25 ~21:00 PDT).
# Any visitor submissions between then and promotion will be in v5's DB
# (the previous primary). To merge, copy missing rows from prompts-v5.db
# to prompts-v6.db. For a CLEAN cutover with no traffic in between, this
# isn't needed — but if v5 collected dreams during the v6 test window,
# they'll need to be merged. Check with:
ssh poly@37.27.48.12 "~/ssd-v5/venv/bin/python3 -c 'import sqlite3; c=sqlite3.connect(\"/home/poly/ssd-v5/prompts-v5.db\"); print(c.execute(\"SELECT count(*) FROM prompts WHERE submitted_at > 1779762400\").fetchone())'"
```

## How to rollback v6 → v5

If something breaks after promotion:

```bash
TS=$(date +%Y%m%d-%H%M%S)
ssh poly@37.27.48.12 "sudo cp /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak-rollback.${TS}"
ssh poly@37.27.48.12 'sudo sed -i "0,/reverse_proxy localhost:9005/{s/reverse_proxy localhost:9005/reverse_proxy localhost:9004/}" /etc/caddy/Caddyfile'
ssh poly@37.27.48.12 'sudo systemctl reload caddy'
# Re-point relay back to 9004:
ssh windows-desktop 'schtasks /change /tn SSD-Relay /enable && schtasks /run /tn SSD-Relay'
# Verify:
curl -sL https://salishseadreaming.art/visitor.html | grep -c "What would you co-dream"  # should be ≥1 (v5 label)
```

## Pre-show parallel testing — what to look at

Open both URLs side by side:
- v5: https://salishseadreaming.art (current primary)
- v6: https://v6.salishseadreaming.art (sandbox)

Walk through the visitor flow on each. v6 should feel like the prompt question is more contemplative + the dreamworld reads as "this event's field" rather than "everyone's history".

If v6 feels right, promote.

## Backup snapshots in place on poly

| File | Backup |
|------|--------|
| `/etc/caddy/Caddyfile` | `.bak.20260526-043141` (pre-v6-add) |
| `~/ssd-v5/static/dreamworld.html` | (v5 unchanged — v6 changes are isolated to ~/ssd-v6/) |
| `~/ssd-v5/web/visitor.html` | (v5 unchanged) |
| v5 prompts DB | Lives separately at `~/ssd-v5/prompts-v5.db` |

v5 is untouched. v6 is fully separable. The promotion is purely a Caddy port-swap + relay-repoint.
