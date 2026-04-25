# Salish Dreamworld — Restart / Recovery Procedure

Use this if TouchDesigner crashes mid-show, or you reopen TD fresh and the
`/project1/salish_dreamworld` scene is missing.

**Target: ≤60 seconds from "TD is open" to "gestures live."**

## Pre-requisites

- TouchDesigner is open with the patreon project (`~/Downloads/patreon-001-hand-tracking-instancing-v0.toe`)
- `MediaPipe.tox` and `hand_tracking.tox` are present in
  `~/projects/salish-sea-dreaming/tools/mediapipe/`
- The latest checkpoint exists at
  `~/projects/salish-sea-dreaming/td/checkpoints/salish_dreamworld_*.tox`

## Restore sequence

### Step 1 — Open TD textport (Alt-T)

### Step 2 — Drop MediaPipe + hand_tracking and wire `cam` and `instance_data`

Paste this block:

```python
import td
project = op('/project1')

# Load MediaPipe (if not already present)
if not op('/project1/MediaPipe'):
    mp = project.loadTox('/Users/darrenzal/projects/salish-sea-dreaming/tools/mediapipe/MediaPipe.tox')
    mp.nodeX = -800; mp.nodeY = 400

# Load hand_tracking (if not already present)
if not op('/project1/hand_tracking3'):
    ht = project.loadTox('/Users/darrenzal/projects/salish-sea-dreaming/tools/mediapipe/hand_tracking.tox')
    ht.nodeX = -800; ht.nodeY = 200

mp = op('/project1/MediaPipe')
ht = op('/project1/hand_tracking3')
cam = op('/project1/cam')
inst = op('/project1/instance_data')

# Wire MediaPipe.video (outputConnectors[8]) -> cam
if cam:
    mp.outputConnectors[8].connect(cam.inputConnectors[0])
# Wire hand_tracking3.instance_data (outputConnectors[2]) -> instance_data
if inst:
    ht.outputConnectors[2].connect(inst.inputConnectors[0])

print('MediaPipe + hand_tracking restored.')
```

### Step 3 — Restore the dreamworld scene from latest checkpoint

```python
import os, glob
ck_dir = '/Users/darrenzal/projects/salish-sea-dreaming/td/checkpoints'
toxes = sorted(glob.glob(ck_dir + '/salish_dreamworld_*.tox'), key=os.path.getmtime, reverse=True)
if not toxes:
    print('NO CHECKPOINTS FOUND — manual rebuild required')
else:
    latest = toxes[0]
    print(f'Loading latest checkpoint: {latest}')
    existing = op('/project1/salish_dreamworld')
    if existing: existing.destroy()
    sd = op('/project1').loadTox(latest)
    sd.nodeX = 800; sd.nodeY = -1200
    print(f'Restored: {sd.path}')
```

### Step 4 — Force callback re-import (clears any stale module state)

```python
sc = op('/project1/salish_dreamworld/dream_positions')
cb = op('/project1/salish_dreamworld/dream_positions_cb')
old = cb.text
cb.text = old + '\n'  # force-modify
cb.text = old          # restore
sc.par.callbacks = ''
sc.par.callbacks = cb.path
# Reset spring states
m = cb.module
if hasattr(m, '_phase'): m._phase[0] = 0.5
if hasattr(m, '_herring_phase'): m._herring_phase[0] = 0.0
if hasattr(m, '_hakini_smoothed'): m._hakini_smoothed[0] = 0.0
print('Callback re-imported, springs reset')
```

### Step 5 — Grant camera permission (if first run on this machine since reboot)

If you see no webcam preview in `/project1/MediaPipe/webBrowser1`, macOS may have
revoked camera permission. Open **System Settings → Privacy & Security → Camera**
and ensure **TouchDesigner** is enabled, then restart TD.

### Step 6 — Verify

```python
import json, math
sc = op('/project1/salish_dreamworld/dream_positions')
hands = op('/project1/MediaPipe/hands')
out = {
    'samples': sc.numSamples,
    'fps': float(project.cookRate),
    'hands_text_len': len(hands.text or ''),
}
if sc.numSamples > 0:
    tx = sc.chan('tx'); ty = sc.chan('ty'); tz = sc.chan('tz')
    max_r = 0
    for i in range(sc.numSamples):
        r = math.sqrt(tx[i]**2 + ty[i]**2 + tz[i]**2)
        if r > max_r: max_r = r
    out['cloud_max_radius'] = round(max_r, 3)
op('/project1').store('mcp_probe', json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
```

**Pass criteria:**
- `samples` ≥ 1 (ideally 195 — varies with current dream count)
- `fps` ≥ 30 (ideally 60)
- `hands_text_len` > 100 (MediaPipe alive)
- `cloud_max_radius` between 1.5 and 4.0 (cloud expanded, not collapsed)

### Step 7 — View output

In Network Editor: navigate to `/project1/salish_dreamworld`, right-click on `output`
TOP → **View...**

You should see colored fish-shaped silhouettes drifting in 3D, breathing.

## Toggle states (after restore)

All toggles default OFF on restore (current-known-good behavior):

| Toggle | Default | What it does when 1 |
|---|---|---|
| `hakini_bilateral` | 0 | Adds asymmetric break/fray detection (B-light) |
| `orient_fish` | 0 | Per-fish rx/ry/rz from `node.dir` |
| `swim_wiggle` | 0 | Subtle per-fish swim wiggle |

To enable a toggle:
```python
op('/project1/salish_dreamworld').store('hakini_bilateral', 1)
```

To disable instantly:
```python
op('/project1/salish_dreamworld').store('hakini_bilateral', 0)
```

## If gestures don't fire after restore

1. Verify hand is visible in `/project1/MediaPipe/webBrowser1` panel.
2. Read live mudra value:
   ```python
   c = op('/project1/salish_dreamworld')
   print('mudra:', c.fetch('mudra_now', 0))
   print('hakini:', c.fetch('hakini_now', 0))
   ```
3. If both are 0 with hand visible → MediaPipe is detecting but `_read_*` isn't firing.
   Check the cb.module: `print(dir(cb.module))` should show `_read_mudra`, `_read_hakini`.
4. If module attrs are missing → re-paste the morning callback file:
   ```python
   path = '/Users/darrenzal/projects/salish-sea-dreaming/scripts/dreamworld_callback/dream_positions_cb_morning.py'
   with open(path) as f: cb.text = f.read()
   sc.par.callbacks = ''; sc.par.callbacks = cb.path
   ```

## Total restore time target

- Open TD: 5 sec
- Step 2 (paste): 5 sec
- Step 3 (paste): 5 sec
- Step 4 (paste): 3 sec
- Step 6 (verify): 5 sec
- Step 7 (view): 5 sec

**Total: ~30 sec.** Add 10 sec for camera-permission edge case.
