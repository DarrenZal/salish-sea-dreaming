"""
Repair/configure the TouchDesigner MCP bridge in the current project.

Use when /mcp_webserver_base exists and port 9981 opens, but MCP calls return
404 with Textport errors like "No module named 'mcp'".
"""

import json
import os
import sys


ROOT = "/Users/darrenzal/projects/salish-sea-dreaming"
MCP_BUNDLE_DIR = f"{ROOT}/td/templates/touchdesigner-mcp"
MCP_TOX = f"{MCP_BUNDLE_DIR}/mcp_webserver_base.tox"
MCP_SCRIPT = f"{MCP_BUNDLE_DIR}/modules/mcp_webserver_script.py"


def _add_path(path):
    if path not in sys.path:
        sys.path.append(path)


def repair():
    if not os.path.exists(MCP_TOX):
        raise RuntimeError(f"Missing MCP TOX: {MCP_TOX}")
    if not os.path.exists(MCP_SCRIPT):
        raise RuntimeError(f"Missing MCP script: {MCP_SCRIPT}")

    mcp = op("/mcp_webserver_base")
    if mcp is None:
        raise RuntimeError("/mcp_webserver_base not found")

    # The upstream import_modules.py discovers modules relative to parent().par.externaltox.
    if hasattr(mcp.par, "externaltox"):
        mcp.par.externaltox.val = MCP_TOX

    _add_path(MCP_BUNDLE_DIR)
    _add_path(f"{MCP_BUNDLE_DIR}/modules")
    _add_path(f"{MCP_BUNDLE_DIR}/modules/td_server")

    script_dat = op("/mcp_webserver_base/mcp_webserver_script")
    if script_dat is None:
        raise RuntimeError("/mcp_webserver_base/mcp_webserver_script not found")
    with open(MCP_SCRIPT, "r") as fh:
        script_dat.text = fh.read()

    # Restart the WebServer DAT if it uses the conventional name.
    web = op("/mcp_webserver_base/webserver1") or op("/mcp_webserver_base/webserver")
    if web is not None:
        if hasattr(web.par, "active"):
            web.par.active.val = False
            web.par.active.val = True

    result = {
        "mcp": mcp.path,
        "externaltox": mcp.par.externaltox.eval() if hasattr(mcp.par, "externaltox") else None,
        "script_dat": script_dat.path,
        "webserver": web.path if web is not None else None,
    }
    print(json.dumps(result, indent=2))
    return result


repair_result = repair()
