"""Probe the TD remote-exec endpoint at localhost:9981 to see what it actually does."""
import json
import urllib.request
import urllib.error

URL = "http://127.0.0.1:9981/api/td/server/exec"

def post(payload, label):
    print(f"--- {label} ---")
    try:
        req = urllib.request.Request(
            URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"status: {r.status}")
            print(f"body:   {r.read().decode('utf-8', 'replace')[:500]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500] if e.fp else ""
        print(f"HTTPError {e.code}: {body}")
    except Exception as e:
        print(f"err: {type(e).__name__}: {e}")
    print()


post({"script": "print('hello from remote')"},
     "Simple print")

post({"script": "import json; print(json.dumps([n.name for n in root.findChildren(type=topCOMP, depth=1)]))"},
     "List top-level OPs")

post({"script": "print([op.name for op in op('/').findChildren(type=COMP) if 'ndi' in op.name.lower()])"},
     "Search for NDI-related ops")

post({"script": "print('discoverable nodes:'); print([op.name for op in op('/').findChildren(maxDepth=4) if op.OPType.lower().startswith('ndi')])"},
     "Find NDI TOPs anywhere in project")
