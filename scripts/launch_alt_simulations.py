#!/usr/bin/env python3
"""
Upload alt_simulations.py to TELUS Node 3 and launch with nohup.

Node 3: https://ssd-style-transfer-3-0b50s.paas.ai.telus.com
Token: ada49fecb49f8b4a4d53a5fb44f91af0

Usage:
  python3 scripts/launch_alt_simulations.py
"""

import json
import base64
import urllib.request
import urllib.error
import time
from pathlib import Path

NODE3_URL = "https://ssd-style-transfer-3-0b50s.paas.ai.telus.com"
TOKEN = "ada49fecb49f8b4a4d53a5fb44f91af0"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Content-Type": "application/json",
}

SCRIPT_PATH = Path(__file__).parent / "alt_simulations.py"
REMOTE_DIR = "alt_simulations"
REMOTE_SCRIPT = f"{REMOTE_DIR}/alt_simulations.py"


def api_request(method, path, data=None, timeout=30):
    """Make an API request to the Jupyter server."""
    url = f"{NODE3_URL}/api/{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()[:200]}")
        return None


def ensure_directory(path):
    """Create directory on remote if it doesn't exist."""
    result = api_request("GET", f"contents/{path}")
    if result and result.get("type") == "directory":
        print(f"  Directory exists: {path}")
        return True

    data = {"type": "directory"}
    result = api_request("PUT", f"contents/{path}", data)
    if result:
        print(f"  Created directory: {path}")
        return True
    return False


def upload_file(local_path, remote_path):
    """Upload a file to the Jupyter server."""
    content = local_path.read_text()
    data = {
        "type": "file",
        "format": "text",
        "content": content,
    }
    result = api_request("PUT", f"contents/{remote_path}", data)
    if result:
        print(f"  Uploaded: {remote_path} ({len(content)} bytes)")
        return True
    return False


def get_or_create_terminal():
    """Get existing terminal or create a new one."""
    terminals = api_request("GET", "terminals")
    if terminals:
        for t in terminals:
            print(f"  Found terminal: {t['name']}")
            return t["name"]

    result = api_request("POST", "terminals")
    if result:
        name = result["name"]
        print(f"  Created terminal: {name}")
        return name
    return None


def send_terminal_command(term_name, command):
    """Send a command to a terminal via WebSocket-like API."""
    # Use the REST API to send input to terminal
    import websocket
    ws_url = f"wss://ssd-style-transfer-3-0b50s.paas.ai.telus.com/terminals/websocket/{term_name}?token={TOKEN}"
    try:
        ws = websocket.create_connection(ws_url, timeout=10)
        ws.send(json.dumps(["stdin", command + "\n"]))
        time.sleep(2)
        # Read any output
        ws.settimeout(3)
        try:
            while True:
                msg = ws.recv()
                data = json.loads(msg)
                if data[0] == "stdout":
                    print(f"  [terminal] {data[1]}", end="")
        except Exception:
            pass
        ws.close()
        return True
    except ImportError:
        print("  websocket-client not available, using notebook kernel instead")
        return False
    except Exception as e:
        print(f"  WebSocket error: {e}")
        return False


def execute_via_kernel(code, timeout=30):
    """Execute code via a Jupyter kernel."""
    # Create a new kernel
    result = api_request("POST", "kernels", {"name": "python3"})
    if not result:
        print("  ERROR: Could not create kernel")
        return None

    kernel_id = result["id"]
    print(f"  Kernel created: {kernel_id}")

    # Execute code via kernel
    try:
        import websocket
        ws_url = f"wss://ssd-style-transfer-3-0b50s.paas.ai.telus.com/api/kernels/{kernel_id}/channels?token={TOKEN}"
        ws = websocket.create_connection(ws_url, timeout=timeout)

        msg_id = f"exec_{int(time.time())}"
        execute_request = {
            "header": {
                "msg_id": msg_id,
                "msg_type": "execute_request",
                "username": "",
                "session": "",
                "version": "5.3",
            },
            "parent_header": {},
            "metadata": {},
            "content": {
                "code": code,
                "silent": False,
                "store_history": False,
                "user_expressions": {},
                "allow_stdin": False,
                "stop_on_error": True,
            },
        }
        ws.send(json.dumps(execute_request))

        # Wait for results
        outputs = []
        ws.settimeout(timeout)
        start = time.time()

        while time.time() - start < timeout:
            try:
                msg = json.loads(ws.recv())
                msg_type = msg.get("msg_type", "")

                if msg_type == "stream":
                    text = msg["content"]["text"]
                    outputs.append(text)
                    print(f"  [kernel] {text}", end="")

                elif msg_type == "execute_result":
                    text = msg["content"]["data"].get("text/plain", "")
                    outputs.append(text)
                    print(f"  [kernel] {text}")

                elif msg_type == "error":
                    ename = msg["content"]["ename"]
                    evalue = msg["content"]["evalue"]
                    outputs.append(f"ERROR: {ename}: {evalue}")
                    print(f"  [kernel] ERROR: {ename}: {evalue}")
                    break

                elif msg_type == "execute_reply":
                    status = msg["content"]["status"]
                    if status == "ok":
                        break
                    elif status == "error":
                        break

            except Exception:
                break

        ws.close()
        return "\n".join(outputs)

    except ImportError:
        print("  websocket-client not available")
        return None
    except Exception as e:
        print(f"  Kernel execution error: {e}")
        return None


def launch_via_notebook(script_remote_path):
    """Create a notebook that launches the script with nohup and run it."""
    notebook_content = {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import subprocess, os\n",
                    f"script = '/home/jovyan/{script_remote_path}'\n",
                    f"log = '/home/jovyan/{REMOTE_DIR}/progress.log'\n",
                    "os.makedirs(os.path.dirname(log), exist_ok=True)\n",
                    "# Kill any existing alt_simulations process\n",
                    "subprocess.run(['pkill', '-f', 'alt_simulations.py'], capture_output=True)\n",
                    "import time; time.sleep(2)\n",
                    "# Launch with nohup\n",
                    "proc = subprocess.Popen(\n",
                    "    f'nohup python3 {script} >> {log} 2>&1 &',\n",
                    "    shell=True,\n",
                    "    stdout=subprocess.DEVNULL,\n",
                    "    stderr=subprocess.DEVNULL,\n",
                    ")\n",
                    "import time; time.sleep(3)\n",
                    "# Verify it's running\n",
                    "result = subprocess.run(['pgrep', '-f', 'alt_simulations.py'],\n",
                    "                       capture_output=True, text=True)\n",
                    "pids = result.stdout.strip()\n",
                    "if pids:\n",
                    "    print(f'alt_simulations.py launched! PIDs: {pids}')\n",
                    "    # Show first lines of log\n",
                    "    import time; time.sleep(5)\n",
                    "    if os.path.exists(log):\n",
                    "        with open(log) as f:\n",
                    "            lines = f.readlines()\n",
                    "            print(f'Log ({len(lines)} lines):')\n",
                    "            for line in lines[-20:]:\n",
                    "                print(line, end='')\n",
                    "else:\n",
                    "    print('ERROR: Process not found!')\n",
                    "    if os.path.exists(log):\n",
                    "        with open(log) as f:\n",
                    "            print(f.read()[-2000:])\n",
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.10.0"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    nb_path = f"{REMOTE_DIR}/launch.ipynb"
    data = {
        "type": "notebook",
        "format": "json",
        "content": notebook_content,
    }
    result = api_request("PUT", f"contents/{nb_path}", data)
    if result:
        print(f"  Uploaded launch notebook: {nb_path}")
    else:
        print("  ERROR: Could not upload launch notebook")
        return False

    return nb_path


def main():
    print("=" * 60)
    print("Launching Alternative Simulations on TELUS Node 3")
    print("=" * 60)

    # 1. Create remote directory
    print("\n1. Creating remote directories...")
    for d in [REMOTE_DIR, f"{REMOTE_DIR}/output", f"{REMOTE_DIR}/depth",
              f"{REMOTE_DIR}/frames"]:
        ensure_directory(d)

    # 2. Upload script
    print("\n2. Uploading alt_simulations.py...")
    if not SCRIPT_PATH.exists():
        print(f"  ERROR: {SCRIPT_PATH} not found")
        return

    ok = upload_file(SCRIPT_PATH, REMOTE_SCRIPT)
    if not ok:
        print("  ERROR: Upload failed")
        return

    # 3. Launch via notebook
    print("\n3. Creating launch notebook...")
    nb_path = launch_via_notebook(REMOTE_SCRIPT)
    if not nb_path:
        return

    # 4. Try to execute the notebook
    print("\n4. Executing launch notebook...")
    try:
        import websocket
        has_ws = True
    except ImportError:
        has_ws = False
        print("  NOTE: Install websocket-client for auto-execution:")
        print("    pip install websocket-client")

    if has_ws:
        code = (
            "import subprocess, os, time\n"
            f"script = '/home/jovyan/{REMOTE_SCRIPT}'\n"
            f"log = '/home/jovyan/{REMOTE_DIR}/progress.log'\n"
            "os.makedirs(os.path.dirname(log), exist_ok=True)\n"
            "subprocess.run(['pkill', '-f', 'alt_simulations.py'], capture_output=True)\n"
            "time.sleep(2)\n"
            "proc = subprocess.Popen(\n"
            "    f'nohup python3 {script} >> {log} 2>&1 &',\n"
            "    shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
            "time.sleep(5)\n"
            "result = subprocess.run(['pgrep', '-f', 'alt_simulations.py'],\n"
            "                       capture_output=True, text=True)\n"
            "pids = result.stdout.strip()\n"
            "if pids:\n"
            "    print(f'LAUNCHED! PIDs: {pids}')\n"
            "    if os.path.exists(log):\n"
            "        with open(log) as f:\n"
            "            lines = f.readlines()\n"
            "            for line in lines[-15:]:\n"
            "                print(line, end='')\n"
            "else:\n"
            "    print('ERROR: not running')\n"
            "    if os.path.exists(log):\n"
            "        with open(log) as f:\n"
            "            print(f.read()[-2000:])\n"
        )
        execute_via_kernel(code, timeout=60)
    else:
        print("\n  Manual steps:")
        print(f"  1. Open {NODE3_URL}/notebooks/{nb_path}?token={TOKEN}")
        print("  2. Run the cell to launch the script")
        print(f"\n  Or open a terminal at {NODE3_URL}/terminals/1?token={TOKEN}")
        print(f"  and run:")
        print(f"    nohup python3 /home/jovyan/{REMOTE_SCRIPT} >> /home/jovyan/{REMOTE_DIR}/progress.log 2>&1 &")

    print("\n" + "=" * 60)
    print("Monitor progress:")
    print(f"  curl -s -H 'Authorization: token {TOKEN}' \\")
    print(f"    '{NODE3_URL}/api/contents/{REMOTE_DIR}/progress.log' | python3 -c \"import json,sys; print(json.load(sys.stdin)['content'][-3000:])\"")
    print("")
    print("Check output files:")
    print(f"  curl -s -H 'Authorization: token {TOKEN}' \\")
    print(f"    '{NODE3_URL}/api/contents/{REMOTE_DIR}/output' | python3 -m json.tool")
    print("=" * 60)


if __name__ == "__main__":
    main()
