#!/usr/bin/env python3
"""Remote-control NDI In TOPs in the SSD-exhibition TouchDesigner project.

Talks to the Web Server DAT exposed by the project at TD_EXEC_URL
(`http://127.0.0.1:9981/api/td/server/exec` by default — the 3090's localhost).

Remote use (Mac → 3090) via SSH tunnel:

    ssh -fNL 19981:127.0.0.1:9981 windows-desktop
    TD_EXEC_URL=http://127.0.0.1:19981/api/td/server/exec ./scripts/td_ndi.py inspect

Use `127.0.0.1:9981` (not `localhost:9981`) on the remote side — on Windows,
`localhost` may resolve to IPv6 `::1` while TD's Web Server DAT binds IPv4-only
(`0.0.0.0`), causing the tunneled connection to hang on Empty Reply.

Subcommands:
  inspect            List NDI In TOPs, current Source Name, menu options, frame size.
  sources            Print unique NDI broadcasts visible to TD (from menu options).
  set OP SOURCE      Set a specific NDI In TOP's Source Name.
  auto-autolume      Find the Autolume Live broadcast and wire /project1/ndiin2 to it.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_URL = os.environ.get("TD_EXEC_URL", "http://127.0.0.1:9981/api/td/server/exec")
MAIN_NDI_IN = "/project1/ndiin2"


def td_exec(script: str, url: str, timeout: float = 10.0) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps({"script": script}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        sys.exit(f"ERROR: cannot reach {url}: {e}")


def td_eval(script: str, url: str) -> str:
    payload = td_exec(script, url)
    if not payload.get("success"):
        sys.exit(f"ERROR: TD rejected script: {payload.get('error')}")
    return payload["data"]["stdout"]


def parse_json_from_stdout(stdout: str):
    """TD's exec endpoint appends a `[DEBUG] Script evaluated...` line; pick the JSON line."""
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith(("[", "{")):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    sys.exit(f"ERROR: no JSON line found in TD output:\n{stdout}")


INSPECT_SCRIPT = r"""
import json
results = []
for n in op('/').findChildren(maxDepth=10):
    t = getattr(n, 'OPType', '') or ''
    if t.lower().startswith('ndiin'):
        info = {'path': n.path, 'name': n.name, 'optype': n.OPType}
        if hasattr(n.par, 'name'):
            p = n.par.name
            try:
                info['source'] = p.eval()
            except Exception:
                info['source'] = str(p)
            info['menu'] = list(p.menuNames) if getattr(p, 'menuNames', None) else []
        info['active'] = bool(n.par.active.eval()) if hasattr(n.par, 'active') else None
        try:
            info['resolution'] = [n.width, n.height]
        except Exception:
            info['resolution'] = None
        results.append(info)
print(json.dumps(results))
"""


def cmd_inspect(args):
    raw = td_eval(INSPECT_SCRIPT, args.host)
    items = parse_json_from_stdout(raw)
    for it in items:
        print(f"{it['path']}")
        print(f"  source     = {it.get('source')!r}")
        print(f"  active     = {it.get('active')}")
        print(f"  resolution = {it.get('resolution')}")
        menu = it.get("menu") or []
        if menu:
            print(f"  menu       = {menu}")
        else:
            print(f"  menu       = (empty — no broadcasts visible to this TOP)")
        print()


def cmd_sources(args):
    raw = td_eval(INSPECT_SCRIPT, args.host)
    items = parse_json_from_stdout(raw)
    seen = set()
    for it in items:
        for src in it.get("menu") or []:
            seen.add(src)
    if not seen:
        print("(no NDI broadcasts visible to TD)")
        return
    for src in sorted(seen):
        print(src)


def cmd_set(args):
    op_path = args.op_path
    source = args.source
    script = (
        f"o = op({op_path!r})\n"
        f"if o is None:\n"
        f"    print('NOT_FOUND')\n"
        f"else:\n"
        f"    o.par.name = {source!r}\n"
        f"    print('OK ' + repr(o.par.name.eval()))\n"
    )
    out = td_eval(script, args.host).strip()
    if out.startswith("NOT_FOUND"):
        sys.exit(f"ERROR: op not found: {op_path}")
    print(out)


def cmd_auto_autolume(args):
    raw = td_eval(INSPECT_SCRIPT, args.host)
    items = parse_json_from_stdout(raw)
    candidates = set()
    for it in items:
        for src in it.get("menu") or []:
            if "autolume" in src.lower():
                candidates.add(src)
    if not candidates:
        sys.exit("ERROR: no Autolume broadcast visible to TD. Is Autolume running with NDI on?")
    if len(candidates) > 1:
        sys.exit(f"ERROR: multiple Autolume broadcasts found: {sorted(candidates)} — pick one with `set`.")
    chosen = next(iter(candidates))
    args.op_path = args.op_path or MAIN_NDI_IN
    args.source = chosen
    print(f"Wiring {args.op_path} -> {chosen!r}")
    cmd_set(args)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--host", default=DEFAULT_URL,
                   help=f"TD exec URL (default: {DEFAULT_URL})")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("inspect", help="List NDI In TOPs and current state").set_defaults(func=cmd_inspect)
    sub.add_parser("sources", help="List NDI broadcasts visible to TD").set_defaults(func=cmd_sources)

    s_set = sub.add_parser("set", help="Set NDI Source Name on a specific NDI In TOP")
    s_set.add_argument("op_path", help="TD op path, e.g. /project1/ndiin2")
    s_set.add_argument("source", help='NDI source name, e.g. "DESKTOP-37616PR (Autolume Live)"')
    s_set.set_defaults(func=cmd_set)

    s_auto = sub.add_parser("auto-autolume",
                            help=f"Find the Autolume Live broadcast and wire it to {MAIN_NDI_IN}")
    s_auto.add_argument("--op-path", default=MAIN_NDI_IN,
                        help=f"Target NDI In TOP (default: {MAIN_NDI_IN})")
    s_auto.set_defaults(func=cmd_auto_autolume)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
