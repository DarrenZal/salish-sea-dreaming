"""
wire_ndi_out.py — Paste-into-TD-textport snippet.

Adds an `ndioutTOP` named `salish_dreamworld_mac` inside /project1/salish_dreamworld
sourced from the existing `output` outTOP. Verifies it's active.

USAGE (in TD textport):

    exec(open('/Users/darrenzal/projects/salish-sea-dreaming/scripts/td_setup/wire_ndi_out.py').read())

After running, open NDI Studio Monitor on this Mac (separate macOS app) — you should
see `salish_dreamworld_mac` as an available source.

Result stored at op('/project1').fetch('mcp_probe').
"""

import json
import td

c = op('/project1/salish_dreamworld')
result = {'step': 'wire_ndi_out'}

if c is None:
    result['status'] = 'FAIL'
    result['reason'] = '/project1/salish_dreamworld not found — restore from .tox first'
else:
    # Remove any existing NDI out we previously created (idempotent)
    existing = op('/project1/salish_dreamworld/ndi_out')
    if existing:
        existing.destroy()

    # The output TOP — this is the final-composited HUD; if HUD bypassed, fallback to render1
    src = op('/project1/salish_dreamworld/output')
    if src is None:
        src = op('/project1/salish_dreamworld/render1')
    if src is None:
        result['status'] = 'FAIL'
        result['reason'] = 'Neither output nor render1 TOP found inside salish_dreamworld'
    else:
        ndi = c.create(td.ndioutTOP, 'ndi_out')
        ndi.par.name = 'salish_dreamworld_mac'
        ndi.par.active = True
        ndi.inputConnectors[0].connect(src)
        ndi.nodeX = 900
        ndi.nodeY = 0

        result['status'] = 'PASS'
        result['ndi_path'] = ndi.path
        result['ndi_source_name'] = ndi.par.name.eval()
        result['ndi_active'] = bool(ndi.par.active.eval())
        result['ndi_source_input'] = src.path
        result['next'] = 'Open NDI Studio Monitor on Mac (separate app); confirm "salish_dreamworld_mac" appears in source list. At venue, drop this source onto a Resolume layer.'

op('/project1').store('mcp_probe', json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
