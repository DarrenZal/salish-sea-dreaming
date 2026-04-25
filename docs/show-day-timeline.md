# Show Day — Saturday 2026-04-26

Hour-by-hour with owners, toggles, kill switches, contingencies. Print or
screenshot before leaving for the venue.

---

## 08:00 — Wake + brief

Read `docs/_meta/2026-04-25-nightshift-readout.md` (≤30 sec). It tells you what
got built overnight, where everything lives, what's queued for AM execution.

## 08:15 — Read the new mudra writing

Read with morning eyes:
- `docs/digital-ecologies/mudra-as-sympoiesis.md`
- `docs/digital-ecologies/mudra-relational-map.md`
- `docs/digital-ecologies/mudra-and-joint-commitment.md`

Edit anything that doesn't fit your voice. Carol Anne / Indigenous-knowledge
flags: re-read the Kwaxala / Heiltsuk / Wuikinuxv passages to ensure they
align with the existing project canon (no new claims, only references to the
Salish Sea Herring + Living Salish Sea reports already in the project).

## 08:30 — Open TouchDesigner + restore scene

1. Launch `~/Downloads/patreon-001-hand-tracking-instancing-v0.toe`
2. **Don't save** when prompted.
3. Open the textport (Alt-T).
4. Paste **`scripts/dreamworld_callback/RESTART.md`** Step 2 (load MediaPipe + hand_tracking)
5. Paste Step 3 (load latest checkpoint .tox)
6. Paste Step 4 (force callback re-import)
7. Paste Step 6 (verify) — confirm samples ≥ 1, fps ≥ 30, cloud_max_radius > 1.5.
8. Right-click `/project1/salish_dreamworld/output` → View. Confirm fish visible, breathing.

## 08:45 — Run preflight gate for B-light

Paste `scripts/td_setup/preflight_mediapipe.py` into textport.

- **PASS** (FPS min ≥ 45 with num_hands=4): proceed to wire B-light.
- **FAIL**: B-light is descoped. Skip step 11; ship A only.
- **WARN** (no hands/faces param found): same — descope.

## 09:00 — Wire NDI Out

Paste `scripts/td_setup/wire_ndi_out.py`. Confirm `salish_dreamworld_mac`
appears as a source in NDI Studio Monitor (separate macOS app — install if
not present).

## 09:15 — Paste morning callback

```python
path = '/Users/darrenzal/projects/salish-sea-dreaming/scripts/dreamworld_callback/dream_positions_cb_morning.py'
cb = op('/project1/salish_dreamworld/dream_positions_cb')
with open(path) as f: cb.text = f.read()
sc = op('/project1/salish_dreamworld/dream_positions')
sc.par.callbacks = ''; sc.par.callbacks = cb.path
```

Verify scene still works (toggles all default 0 = current behavior).

## 09:30 — Wire orientation params

Paste `scripts/td_setup/wire_orientation_params.py`. Sets `instancerx/y/z = 'rx'/'ry'/'rz'`.

## 09:45 — Toggle each behavior on, test, leave on if good

```python
op('/project1/salish_dreamworld').store('orient_fish', 1)
# fish should now point along their dir vectors — visually inspect; herring should still form
op('/project1/salish_dreamworld').store('swim_wiggle', 1)
# subtle wiggle on each fish
op('/project1/salish_dreamworld').store('hakini_bilateral', 1)
# requires preflight PASS — test with both your hands across body
```

If anything looks broken: store back to 0.

## 10:00 — Generate ingestion content

Both branches happen now:

### Branch A — content authoring
- Have Claude generate ~10 entity cards + chunk the 3 mudra essays into doc-chunks
- Output to `static/_proposed/ssd-cards-proposed.json` and `ssd-context-docs-proposed.json`
- Read the proposals; edit if anything reads as overclaim or misframing

### Branch B — patch the 2-token gate
The chat backend has a hard-coded `if len(tokens) < 2: return [], []` at
`gallery_server.py:400`. This means single-token queries ("What is Kwaxala?")
NEVER trigger RAG. **Patch this** to allow 1-token matches when the token
is non-stopword and ≥4 chars:

```python
# Replace line 400-401:
if len(tokens) < 1: return [], []
# (or if you want to be conservative: allow single-token only if score ≥ 5
#  by raising the per-card threshold for single-token queries)
```

## 10:30 — Local preview + smoke test

```bash
bash /Users/darrenzal/projects/salish-sea-dreaming/scripts/local_preview.sh
```

In another terminal:
```bash
python3 /Users/darrenzal/projects/salish-sea-dreaming/scripts/ingest_check.py \
  --cards /tmp/ssd-sandbox-*/static/ssd-cards.json \
  --docs /tmp/ssd-sandbox-*/static/ssd-context-docs.json \
  --queries /Users/darrenzal/projects/salish-sea-dreaming/scripts/sample_queries.txt
```

Coverage should now show ≥7 of 10 queries with matches. Manually hit
`http://localhost:9001/chat` with each query and read the answers.

## 11:00 — Deploy to prod

```bash
# Snapshot prod first
ssh poly@37.27.48.12 "TS=\$(date +%Y%m%d-%H%M); mkdir -p /home/poly/salish-sea-dreaming/static/.bak.\$TS && cp /home/poly/salish-sea-dreaming/static/ssd-cards.json /home/poly/salish-sea-dreaming/static/ssd-context-docs.json /home/poly/salish-sea-dreaming/static/.bak.\$TS/ && echo 'snapshot at .bak.\$TS'"

# Deploy
scp /Users/darrenzal/projects/salish-sea-dreaming/static/ssd-cards.json poly@37.27.48.12:/home/poly/salish-sea-dreaming/static/
scp /Users/darrenzal/projects/salish-sea-dreaming/static/ssd-context-docs.json poly@37.27.48.12:/home/poly/salish-sea-dreaming/static/
scp /Users/darrenzal/projects/salish-sea-dreaming/scripts/gallery_server.py poly@37.27.48.12:/home/poly/salish-sea-dreaming/scripts/
ssh poly@37.27.48.12 "sudo systemctl restart ssd-gallery"
```

Smoke test 3 queries on prod:
```bash
curl -s https://salishseadreaming.art/chat -X POST -H 'content-type: application/json' -d '{"message":"What is Hakini?"}' | python3 -m json.tool
curl -s https://salishseadreaming.art/chat -X POST -H 'content-type: application/json' -d '{"message":"What is sympoiesis?"}' | python3 -m json.tool
curl -s https://salishseadreaming.art/chat -X POST -H 'content-type: application/json' -d '{"message":"Why a herring?"}' | python3 -m json.tool
```

If anything is broken: restore from snapshot:
```bash
ssh poly@37.27.48.12 "cp /home/poly/salish-sea-dreaming/static/.bak.<timestamp>/* /home/poly/salish-sea-dreaming/static/ && sudo systemctl restart ssd-gallery"
```

## 11:30 — Pre-fetch dream snapshot for offline fallback

```bash
curl -s https://salishseadreaming.art/dreams/3d > /Users/darrenzal/projects/salish-sea-dreaming/static/dreams_snapshot_2026-04-26.json
python3 -c "import json; d=json.load(open('/Users/darrenzal/projects/salish-sea-dreaming/static/dreams_snapshot_2026-04-26.json')); print('nodes:', len(d.get('nodes',[])))"
```

## 11:45 — Re-checkpoint + commit

```python
# In TD textport
import time
ts = time.strftime('%Y-%m-%d_%H%M')
op('/project1/salish_dreamworld').save(f'/Users/darrenzal/projects/salish-sea-dreaming/td/checkpoints/salish_dreamworld_showday_{ts}.tox')
```

Commit + push:
```bash
cd /Users/darrenzal/projects/salish-sea-dreaming
git add docs/ scripts/ static/ td/checkpoints/
git status
# review, then:
git commit -m "Show day prep: B-light, NDI, fish orientation, mudra docs, ingestion patch"
git push
```

## 12:00 — Cold-start full cycle test

Quit TD entirely. Reopen patreon .toe. Run RESTART.md from scratch with
stopwatch. Target: ≤60 sec to verified gestures + fish + herring.

## 12:30 — Pack

- MacBook + charger
- USB-C → ethernet adapter
- 25-ft Cat6 cable
- USB hub
- HDMI cable (backup if NDI fails entirely)
- Task light (clip-on, USB-powered)
- Cooling pad if available
- Print or screenshot of: this timeline, prav-play-guide.md, RESTART.md

## 13:00 → 16:00 — Travel + venue setup

Get to Mahon Hall. Same procedure as 08:30 but on-site. Have Prav present.

Specifically:
1. Confirm internet → /dreams/3d works
2. Ping Prav's Resolume machine
3. Bring up TD, MediaPipe, dreamworld
4. Test Hakini under venue lighting (task light if dim)
5. Tune threshold if needed:
   - Too sensitive: lower divisor, e.g.,
     ```
     # in textport, find _read_hakini_bilateral, change tot/1.0 to tot/0.7
     ```
   - Too loose: raise to tot/1.4
6. Drop NDI source into Resolume layer with Prav. Tune blend, FX, scale.
7. Walk Prav through `prav-play-guide.md`.
8. Toggle B-light on; test 2-person Hakini with Prav.

## 17:00 — Dress rehearsal

Run the full set once with Prav. Watch for:
- FPS dropouts under camera+MediaPipe+render load
- False-trigger Hakini from background activity
- NDI stream stability
- Chat answers (have someone with a phone test salishseadreaming.art live during rehearsal)

## 19:00+ — Show

Live. Honor the gesture. Honor the room. The dreams are already there; the
visitors come to recognize them.

## Late — Pack out + migrate to Prav's

Same MacBook. Bring everything. At Prav's:
- Same TD project (already open or reopen via RESTART.md)
- New LAN — re-discover NDI source on Prav's network
- Lighting at his place is probably better than gallery
- Run looser at the party — multi-person Hakini, friends discovering the
  herring, etc.

## Sunday morning — Capture

Before tearing anything down, screen-record:
- The cloud breathing
- Hakini → herring transition (1-2 visitors)
- Asymmetric break / fray (if B-light worked)
- Chat agent answering "What is the mudra?"

Save to `~/projects/salish-sea-dreaming/docs/show-2026-04-26-captures/`.
