"""Inspect NDI In TOPs in the running TD: paths, current source, all source options."""
import json
import urllib.request

URL = "http://127.0.0.1:9981/api/td/server/exec"

SCRIPT = r"""
import json
results = []
for n in op('/').findChildren(maxDepth=10):
    t = n.OPType.lower() if hasattr(n, 'OPType') else ''
    if t.startswith('ndiin'):
        info = {
            'path': n.path,
            'name': n.name,
            'optype': n.OPType,
        }
        # Try common parameter names for NDI In source
        for parname in ('name', 'source', 'sourcename'):
            if hasattr(n.par, parname):
                p = getattr(n.par, parname)
                try:
                    info['par_' + parname + '_value'] = p.eval()
                except Exception:
                    info['par_' + parname + '_value'] = str(p)
                # Menu options if it's a string menu
                if hasattr(p, 'menuNames'):
                    info['par_' + parname + '_menu'] = list(p.menuNames) if p.menuNames else []
        # active flag if present
        if hasattr(n.par, 'active'):
            info['active'] = bool(n.par.active.eval())
        # resolution to check if frames flowing
        try:
            info['resolution'] = [n.width, n.height]
        except Exception:
            pass
        results.append(info)

print(json.dumps(results, indent=2, default=str))
"""

req = urllib.request.Request(
    URL,
    data=json.dumps({"script": SCRIPT}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=10) as r:
    payload = json.loads(r.read().decode())

if payload.get("success"):
    print(payload["data"]["stdout"])
    if payload["data"]["stderr"]:
        print("STDERR:", payload["data"]["stderr"])
else:
    print("ERROR:", payload.get("error"))
