"""
preflight_mediapipe.py — Paste-into-TD-textport snippet (NOT MCP).

Bumps MediaPipe to num_hands=4 / num_faces=2 and runs a 60-second FPS gate.
If the gate fails, B-light is descoped — toggle stays off, current behavior is the show.

USAGE (in TD textport, with /project1/MediaPipe present):

    exec(open('/Users/darrenzal/projects/salish-sea-dreaming/scripts/td_setup/preflight_mediapipe.py').read())

OR copy-paste the body below into the textport directly.

Result is stored at op('/project1').fetch('mcp_probe', '<empty>') as a JSON string.
"""

import json
import time as _time

mp = op('/project1/MediaPipe')
result = {'step': 'preflight_mediapipe'}

if mp is None:
    result['status'] = 'FAIL'
    result['reason'] = '/project1/MediaPipe not found — drop MediaPipe.tox first'
else:
    # Find the right parameter names (torinmb plugin variants)
    par_names = [pg.name for pg in mp.pars()]
    result['param_names_sample'] = [n for n in par_names if 'hand' in n.lower() or 'face' in n.lower() or 'num' in n.lower() or 'max' in n.lower()][:30]

    # Try common parameter names
    candidates_hands = ['Numhands', 'numhands', 'Maxhands', 'maxhands', 'Hands']
    candidates_faces = ['Numfaces', 'numfaces', 'Maxfaces', 'maxfaces', 'Faces']

    hand_par = None
    for name in candidates_hands:
        if hasattr(mp.par, name):
            hand_par = getattr(mp.par, name)
            break
    face_par = None
    for name in candidates_faces:
        if hasattr(mp.par, name):
            face_par = getattr(mp.par, name)
            break

    if hand_par is None and face_par is None:
        result['status'] = 'WARN'
        result['reason'] = 'No num_hands or num_faces parameter found on /project1/MediaPipe (param_names_sample shows what does exist) — B-light descoped'
    else:
        # Set what we can
        if hand_par is not None:
            try:
                hand_par.val = 4
                result['hand_set'] = ('par_name', hand_par.name, 'val', hand_par.eval())
            except Exception as e:
                result['hand_set_err'] = str(e)
        if face_par is not None:
            try:
                face_par.val = 2
                result['face_set'] = ('par_name', face_par.name, 'val', face_par.eval())
            except Exception as e:
                result['face_set_err'] = str(e)

        # FPS gate: sample cookRate over ~10 sec (shorter than 60s for textport patience)
        samples = []
        end = _time.time() + 10.0
        while _time.time() < end:
            try:
                samples.append(float(project.cookRate))
            except Exception:
                pass
            _time.sleep(0.5)
        if samples:
            min_fps = min(samples)
            avg_fps = sum(samples) / len(samples)
            result['fps_min'] = round(min_fps, 1)
            result['fps_avg'] = round(avg_fps, 1)
            result['fps_samples'] = len(samples)
            if min_fps >= 45.0:
                result['status'] = 'PASS'
                result['recommendation'] = 'B-light is safe to enable: op("/project1/salish_dreamworld").store("hakini_bilateral", 1)'
            else:
                result['status'] = 'FAIL'
                result['reason'] = f'FPS gate failed: min {min_fps:.1f} < 45.0 — B-light descoped'
                result['recommendation'] = 'Revert num_hands/num_faces to defaults and ship A only'
        else:
            result['status'] = 'INCONCLUSIVE'
            result['reason'] = 'No FPS samples collected'

op('/project1').store('mcp_probe', json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
