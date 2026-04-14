#!/usr/bin/env python3
"""
Launch Landscape Dissolution on TELUS Node 2.
==============================================
Uploads the script, installs deps, and runs with nohup.

Usage:
  python3 scripts/launch_landscape_dissolution.py          # upload + launch
  python3 scripts/launch_landscape_dissolution.py status    # check progress log
  python3 scripts/launch_landscape_dissolution.py gpu       # check GPU status
"""

import requests
import base64
import json
import time
import uuid
import sys
import os
import threading

NODE2 = {
    "url": "https://ssd-style-transfer-2-0b50s.paas.ai.telus.com",
    "token": "15335440de57b5646cd4c25bdf1957d5",
}

SCRIPT_NAME = "landscape_dissolution_narrative.py"
SCRIPT_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCRIPT_NAME)
REMOTE_DIR = "landscape_dissolution"
REMOTE_SCRIPT = f"{REMOTE_DIR}/{SCRIPT_NAME}"


def api_headers():
    return {
        "Authorization": f"token {NODE2['token']}",
        "Content-Type": "application/json",
    }


def mkdir_remote(path):
    """Create directory on remote Jupyter."""
    r = requests.put(
        f"{NODE2['url']}/api/contents/{path}",
        headers=api_headers(),
        json={"type": "directory"},
        timeout=15,
    )
    return r.status_code


def upload_script():
    """Upload the landscape dissolution script to Node 2."""
    print(f"Reading local script: {SCRIPT_LOCAL}")
    with open(SCRIPT_LOCAL, "r") as f:
        content = f.read()
    print(f"  Size: {len(content)} bytes, {content.count(chr(10))} lines")

    # Create directories
    for d in [REMOTE_DIR, f"{REMOTE_DIR}/depth", f"{REMOTE_DIR}/output"]:
        status = mkdir_remote(d)
        print(f"  mkdir {d}: {status}")

    # Upload script as text
    r = requests.put(
        f"{NODE2['url']}/api/contents/{REMOTE_SCRIPT}",
        headers=api_headers(),
        json={
            "type": "file",
            "format": "text",
            "content": content,
        },
        timeout=30,
    )
    if r.status_code in (200, 201):
        print(f"  Script uploaded: {REMOTE_SCRIPT} ({len(content)} bytes)")
        return True
    else:
        print(f"  Upload FAILED: {r.status_code} {r.text[:300]}")
        return False


def get_or_create_kernel():
    """Get existing kernel or create new one."""
    r = requests.get(
        f"{NODE2['url']}/api/kernels",
        headers=api_headers(),
        timeout=10,
    )
    kernels = r.json()
    if kernels:
        kid = kernels[0]["id"]
        print(f"  Using existing kernel: {kid}")
        return kid

    r = requests.post(
        f"{NODE2['url']}/api/kernels",
        headers=api_headers(),
        json={},
        timeout=30,
    )
    if r.status_code in (200, 201):
        kid = r.json()["id"]
        print(f"  Created new kernel: {kid}")
        return kid
    else:
        print(f"  Kernel creation FAILED: {r.status_code} {r.text[:200]}")
        return None


def execute_code(kernel_id, code, label="exec", timeout_s=60):
    """Execute code on kernel via websocket, capture output."""
    ws_url = NODE2["url"].replace("https://", "wss://")
    ws_full = f"{ws_url}/api/kernels/{kernel_id}/channels?token={NODE2['token']}"

    msg_id = str(uuid.uuid4())
    execute_msg = {
        "header": {
            "msg_id": msg_id,
            "msg_type": "execute_request",
            "username": "",
            "session": str(uuid.uuid4()),
            "date": "",
            "version": "5.3",
        },
        "parent_header": {},
        "metadata": {},
        "content": {
            "code": code,
            "silent": False,
            "store_history": True,
            "user_expressions": {},
            "allow_stdin": False,
            "stop_on_error": True,
        },
        "buffers": [],
        "channel": "shell",
    }

    result_text = []
    got_reply = threading.Event()

    import websocket

    def on_message(ws, message):
        try:
            msg = json.loads(message)
            msg_type = msg.get("msg_type", "")
            parent_id = msg.get("parent_header", {}).get("msg_id", "")
            if parent_id == msg_id:
                if msg_type == "stream":
                    text = msg["content"].get("text", "")
                    result_text.append(text)
                    for line in text.strip().split("\n"):
                        print(f"  [{label}] {line}")
                elif msg_type == "execute_result":
                    text = msg["content"]["data"].get("text/plain", "")
                    result_text.append(text)
                    print(f"  [{label}] {text.strip()}")
                elif msg_type == "error":
                    tb = msg["content"].get("traceback", [])
                    err = "\n".join(tb)
                    print(f"  [{label}] ERROR:\n{err}")
                    result_text.append(f"ERROR: {err}")
                elif msg_type == "execute_reply":
                    got_reply.set()
        except Exception as e:
            print(f"  [{label}] WS parse error: {e}")

    def on_error(ws, error):
        print(f"  [{label}] WS error: {error}")

    def on_open(ws):
        ws.send(json.dumps(execute_msg))

    ws = websocket.WebSocketApp(
        ws_full,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
    )

    ws_thread = threading.Thread(
        target=ws.run_forever,
        kwargs={"sslopt": {"check_hostname": False}},
    )
    ws_thread.daemon = True
    ws_thread.start()

    got_reply.wait(timeout=timeout_s)
    time.sleep(2)
    ws.close()
    return "".join(result_text)


def launch():
    """Upload script, install deps, and launch with nohup."""
    print("=" * 60)
    print("LANDSCAPE DISSOLUTION — LAUNCH ON NODE 2")
    print("=" * 60)

    # Step 1: Upload
    print("\n--- Step 1: Upload script ---")
    if not upload_script():
        sys.exit(1)

    # Step 2: Get kernel
    print("\n--- Step 2: Get kernel ---")
    kernel_id = get_or_create_kernel()
    if not kernel_id:
        sys.exit(1)
    time.sleep(2)

    # Step 3: Install dependencies
    print("\n--- Step 3: Install dependencies ---")
    deps_code = """
import subprocess, sys
deps = [
    "pip install -q diffusers transformers accelerate safetensors",
    "pip install -q controlnet_aux",
    "pip install -q imageio imageio-ffmpeg",
    "pip install -q scipy",
    "pip install -q xformers 2>/dev/null || true",
    "pip install -q websocket-client",
]
for cmd in deps:
    print(f"  {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0 and "xformers" not in cmd:
        print(f"    WARN: {r.stderr[:200]}")
print("Dependencies installed.")

# GPU check
import torch
if torch.cuda.is_available():
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU: {gpu} ({vram:.1f} GB)")
else:
    print("WARNING: No CUDA GPU!")
"""
    execute_code(kernel_id, deps_code, label="deps", timeout_s=120)

    # Step 4: Launch with nohup
    print("\n--- Step 4: Launch with nohup ---")
    launch_code = f"""
import subprocess, sys, os

log_path = "/home/jovyan/{REMOTE_DIR}/progress.log"
script_path = "/home/jovyan/{REMOTE_SCRIPT}"

# Ensure log file exists
os.makedirs(os.path.dirname(log_path), exist_ok=True)

proc = subprocess.Popen(
    [sys.executable, script_path],
    stdout=open(log_path, "w"),
    stderr=subprocess.STDOUT,
    start_new_session=True,
)
print(f"Launched PID {{proc.pid}}")
print(f"Script: {REMOTE_SCRIPT}")
print(f"Log: {REMOTE_DIR}/progress.log")
print(f"Output: {REMOTE_DIR}/output/")
"""
    execute_code(kernel_id, launch_code, label="launch", timeout_s=30)

    print("\n" + "=" * 60)
    print("LAUNCHED!")
    print("=" * 60)
    print(f"\nMonitor progress:")
    print(f"  python3 scripts/launch_landscape_dissolution.py status")
    print(f"\nOr manually:")
    url = NODE2["url"]
    token = NODE2["token"]
    print(f"  curl -s -H 'Authorization: token {token}' \\")
    print(f"    '{url}/api/contents/{REMOTE_DIR}/progress.log' \\")
    print(f"    | python3 -c \"import sys,json; print(json.load(sys.stdin)['content'][-3000:])\"")
    print()


def check_status():
    """Read progress log from Node 2."""
    print("Fetching progress log from Node 2...")
    r = requests.get(
        f"{NODE2['url']}/api/contents/{REMOTE_DIR}/progress.log",
        headers=api_headers(),
        timeout=15,
    )
    if r.status_code != 200:
        print(f"  Cannot read log: {r.status_code}")
        # Try checking if the completion marker exists
        r2 = requests.get(
            f"{NODE2['url']}/api/contents/{REMOTE_DIR}/output/COMPLETE",
            headers=api_headers(),
            timeout=10,
        )
        if r2.status_code == 200:
            print("  COMPLETE marker found!")
            print(r2.json().get("content", "")[-500:])
        return

    content = r.json().get("content", "")
    # Show last 3000 chars
    if len(content) > 3000:
        print(f"... (showing last 3000 of {len(content)} chars)\n")
        print(content[-3000:])
    else:
        print(content)

    # Check for completion
    if "LANDSCAPE DISSOLUTION COMPLETE" in content:
        print("\n>>> RENDERING COMPLETE! <<<")
    elif "FATAL" in content:
        print("\n>>> FATAL ERROR detected — check log <<<")


def check_gpu():
    """Check GPU status on Node 2."""
    print("Checking GPU on Node 2...")
    kernel_id = get_or_create_kernel()
    if not kernel_id:
        return
    time.sleep(1)
    execute_code(
        kernel_id,
        "import subprocess; r = subprocess.run(['nvidia-smi'], capture_output=True, text=True); print(r.stdout[:600])",
        label="gpu",
        timeout_s=15,
    )


def list_outputs():
    """List output files on Node 2."""
    print("Listing outputs on Node 2...")
    r = requests.get(
        f"{NODE2['url']}/api/contents/{REMOTE_DIR}/output",
        headers=api_headers(),
        timeout=15,
    )
    if r.status_code != 200:
        print(f"  Cannot list: {r.status_code}")
        return

    items = r.json().get("content", [])
    for item in sorted(items, key=lambda x: x["name"]):
        name = item["name"]
        size = item.get("size", 0)
        if item["type"] == "directory":
            print(f"  [DIR] {name}/")
        elif name.endswith(".mp4") or name.endswith(".png"):
            size_mb = (size or 0) / 1e6
            print(f"  {name} ({size_mb:.1f} MB)")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "launch"

    if mode == "launch":
        launch()
    elif mode == "status":
        check_status()
    elif mode == "gpu":
        check_gpu()
    elif mode == "outputs" or mode == "ls":
        list_outputs()
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: launch | status | gpu | outputs")


if __name__ == "__main__":
    main()
