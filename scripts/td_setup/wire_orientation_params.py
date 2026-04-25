"""
wire_orientation_params.py — Paste-into-TD-textport snippet.

Wires per-instance rotation parameters on /project1/salish_dreamworld/dream_cloud
to the rx/ry/rz channels emitted by the morning callback (when orient_fish toggle is on).

PRE-REQ: Must be run AFTER pasting `dream_positions_cb_morning.py` into the callback DAT,
because the callback only emits rx/ry/rz channels when orient_fish toggle is on. Wiring
the params is harmless when the channels don't exist (TD just won't apply rotation).

USAGE (in TD textport):

    exec(open('/Users/darrenzal/projects/salish-sea-dreaming/scripts/td_setup/wire_orientation_params.py').read())

Result stored at op('/project1').fetch('mcp_probe').
"""

import json

geo = op('/project1/salish_dreamworld/dream_cloud')
result = {'step': 'wire_orientation_params'}

if geo is None:
    result['status'] = 'FAIL'
    result['reason'] = '/project1/salish_dreamworld/dream_cloud not found'
else:
    try:
        geo.par.instancerx = 'rx'
        geo.par.instancery = 'ry'
        geo.par.instancerz = 'rz'
        result['status'] = 'PASS'
        result['instancerx'] = geo.par.instancerx.eval()
        result['instancery'] = geo.par.instancery.eval()
        result['instancerz'] = geo.par.instancerz.eval()
        result['next'] = 'In textport, run: op("/project1/salish_dreamworld").store("orient_fish", 1) to enable. Toggle off with .store("orient_fish", 0).'
    except Exception as e:
        result['status'] = 'FAIL'
        result['reason'] = str(e)

op('/project1').store('mcp_probe', json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
