#!/usr/bin/env python3
"""
Upload a video to the TELUS H200 Jupyter pod, run Spandrel + Real-ESRGAN
upscale, download the 4K result.

This is the local driver. The pod-side worker is `_pod_upscale_worker.py`.
Communication is via the Jupyter Contents REST API (for file transfer)
and Jupyter kernel WebSocket protocol (for triggering execution).

Usage:
    python3 scripts/telus_upscale.py INPUT.mp4 [-o OUTPUT.mp4]
                                     [--model x2plus|x4plus]
                                     [--canvas 3840x2160]
                                     [--job-name NAME]

For 1080p sources targeting UHD: use --model x2plus (default).
For 1024² Autolume sources targeting UHD: use --model x4plus
(produces 4096², downfit to 2160², letterboxed to 3840×2160).

Requires .env in repo root with TELUS_POD_URL + Jupyter_REST_API.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
import websocket


CHUNK_BYTES = 700 * 1024  # 700 KB pre-base64; nginx limit on pod is ~1 MB
POD_JOBS_ROOT = "upscale-test/jobs"
POD_WEIGHTS = {
    "x2plus": "upscale-test/weights/RealESRGAN_x2plus.pth",
    "x4plus": "upscale-test/weights/RealESRGAN_x4plus.pth",
}
WORKER_LOCAL = Path(__file__).parent / "_pod_upscale_worker.py"


# ---------- env + http helpers ----------

def load_env() -> tuple[str, str]:
    # Env-var override for parallel-pod scenarios (added 2026-05-23 for
    # IMPACT install asset crunch — operator starts 2nd TELUS pod, passes
    # creds via shell env without touching .env).
    env_url = os.environ.get("TELUS_POD_URL")
    env_token = os.environ.get("Jupyter_REST_API")
    if env_url and env_token:
        return env_url, env_token
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        sys.exit(f"missing .env at {env_path}; need TELUS_POD_URL + Jupyter_REST_API")
    url = token = None
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == "TELUS_POD_URL":
            url = v.strip()
        elif k.strip() == "Jupyter_REST_API":
            token = v.strip()
    if not url or not token:
        sys.exit("TELUS_POD_URL or Jupyter_REST_API missing from .env")
    return url, token


def auth_headers(token: str) -> dict:
    return {"Authorization": f"token {token}"}


def http_get(base_url: str, token: str, path: str, **kw) -> requests.Response:
    return requests.get(f"{base_url}{path}", headers=auth_headers(token), timeout=30, **kw)


def http_put(base_url: str, token: str, path: str, json_body: dict) -> requests.Response:
    return requests.put(
        f"{base_url}{path}", headers=auth_headers(token), json=json_body, timeout=60,
    )


def http_post(base_url: str, token: str, path: str, json_body: dict | None = None) -> requests.Response:
    return requests.post(
        f"{base_url}{path}", headers=auth_headers(token), json=json_body or {}, timeout=30,
    )


# ---------- contents API ----------

def pod_mkdir(base_url: str, token: str, pod_path: str) -> None:
    """Create a directory on the pod (no-op if it exists)."""
    r = http_put(base_url, token, f"/api/contents/{pod_path}",
                 {"type": "directory"})
    if r.status_code not in (200, 201):
        # 409 / 400 may mean "already exists"; verify via GET
        check = http_get(base_url, token, f"/api/contents/{pod_path}")
        if check.status_code != 200:
            raise RuntimeError(f"mkdir {pod_path} failed: {r.status_code} {r.text[:300]}")


def pod_put_text(base_url: str, token: str, pod_path: str, text: str) -> None:
    r = http_put(base_url, token, f"/api/contents/{pod_path}",
                 {"type": "file", "format": "text", "content": text})
    if r.status_code not in (200, 201):
        raise RuntimeError(f"put text {pod_path}: {r.status_code} {r.text[:300]}")


def pod_put_b64_chunk(base_url: str, token: str, pod_path: str, b64: str) -> None:
    r = http_put(base_url, token, f"/api/contents/{pod_path}",
                 {"type": "file", "format": "base64", "content": b64})
    if r.status_code not in (200, 201):
        raise RuntimeError(f"put chunk {pod_path}: {r.status_code} {r.text[:300]}")


def pod_get_text(base_url: str, token: str, pod_path: str) -> str | None:
    r = http_get(base_url, token, f"/api/contents/{pod_path}")
    if r.status_code != 200:
        return None
    return r.json().get("content")


def pod_download_file(base_url: str, token: str, pod_path: str, local_path: Path) -> int:
    """Download a binary file from the pod via contents API. Returns bytes written."""
    r = http_get(base_url, token, f"/api/contents/{pod_path}",
                 params={"format": "base64"})
    if r.status_code != 200:
        raise RuntimeError(f"download {pod_path}: {r.status_code} {r.text[:300]}")
    body = r.json()
    if body.get("format") != "base64":
        raise RuntimeError(f"unexpected format {body.get('format')} for {pod_path}")
    data = base64.b64decode(body["content"])
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(data)
    return len(data)


# ---------- chunked upload ----------

def chunked_upload(base_url: str, token: str, local_path: Path, pod_dir: str,
                   pod_filename: str) -> None:
    """
    Upload a binary file to the pod in <=700KB base64 chunks, then reassemble
    via kernel execution. nginx on the pod tops out around 1MB per PUT body.
    """
    chunks_dir = f"{pod_dir}/_chunks_{pod_filename}"
    pod_mkdir(base_url, token, chunks_dir)

    data = local_path.read_bytes()
    n_chunks = (len(data) + CHUNK_BYTES - 1) // CHUNK_BYTES
    print(f"  uploading {local_path.name} ({len(data)/1024:.1f} KB) in {n_chunks} chunk(s)")

    for i in range(n_chunks):
        chunk = data[i * CHUNK_BYTES:(i + 1) * CHUNK_BYTES]
        b64 = base64.b64encode(chunk).decode("ascii")
        pod_put_b64_chunk(base_url, token, f"{chunks_dir}/chunk_{i:05d}.b64", b64)

    # Reassemble on pod. Jupyter Contents API has ALREADY decoded each chunk's
    # base64 to binary on disk, so we just concatenate raw bytes.
    reassemble_code = f"""
import os
chunks_dir = {chunks_dir!r}
out_path = {(pod_dir + '/' + pod_filename)!r}
parts = sorted(p for p in os.listdir(chunks_dir) if p.startswith('chunk_'))
with open(out_path, 'wb') as fout:
    for p in parts:
        with open(os.path.join(chunks_dir, p), 'rb') as fin:
            fout.write(fin.read())
for p in parts:
    os.remove(os.path.join(chunks_dir, p))
os.rmdir(chunks_dir)
print('reassembled', out_path, os.path.getsize(out_path), 'bytes')
"""
    run_on_pod(base_url, token, reassemble_code, timeout=120)


# ---------- kernel ws ----------

def start_kernel(base_url: str, token: str) -> str:
    r = http_post(base_url, token, "/api/kernels", {"name": "python3"})
    if r.status_code not in (200, 201):
        raise RuntimeError(f"start_kernel: {r.status_code} {r.text[:300]}")
    return r.json()["id"]


def shutdown_kernel(base_url: str, token: str, kernel_id: str) -> None:
    requests.delete(f"{base_url}/api/kernels/{kernel_id}",
                    headers=auth_headers(token), timeout=10)


def run_on_pod(base_url: str, token: str, code: str, *,
               kernel_id: str | None = None, timeout: float = 300.0,
               stream_to_stdout: bool = False) -> str:
    """
    Run a code block on the pod via Jupyter kernel WebSocket. Spawns + reaps
    its own kernel unless kernel_id is provided.

    Returns concatenated stdout. Raises on execute_reply.status == 'error'.
    """
    own_kernel = kernel_id is None
    if own_kernel:
        kernel_id = start_kernel(base_url, token)

    parsed = urlparse(base_url)
    ws_scheme = "wss" if parsed.scheme == "https" else "ws"
    ws_url = f"{ws_scheme}://{parsed.netloc}/api/kernels/{kernel_id}/channels?token={token}"

    ws = websocket.create_connection(ws_url, timeout=timeout)
    ws.settimeout(timeout)
    msg_id = uuid.uuid4().hex
    session_id = uuid.uuid4().hex
    request = {
        "header": {
            "msg_id": msg_id, "username": "telus_upscale", "session": session_id,
            "msg_type": "execute_request", "version": "5.3",
        },
        "parent_header": {},
        "metadata": {},
        "content": {
            "code": code, "silent": False, "store_history": False,
            "user_expressions": {}, "allow_stdin": False, "stop_on_error": True,
        },
        "buffers": [], "channel": "shell",
    }
    ws.send(json.dumps(request))

    stdout_buf: list[str] = []
    error_payload: dict | None = None
    deadline = time.time() + timeout

    try:
        while True:
            if time.time() > deadline:
                raise TimeoutError(f"kernel exec timed out after {timeout}s")
            msg = json.loads(ws.recv())
            parent = msg.get("parent_header", {}).get("msg_id")
            if parent != msg_id:
                continue
            mtype = msg.get("header", {}).get("msg_type")
            if mtype == "stream":
                text = msg["content"]["text"]
                stdout_buf.append(text)
                if stream_to_stdout:
                    print(text, end="", flush=True)
            elif mtype == "error":
                error_payload = msg["content"]
            elif mtype == "execute_reply":
                if msg["content"]["status"] == "error":
                    err = error_payload or msg["content"]
                    raise RuntimeError(
                        f"kernel error: {err.get('ename')}: {err.get('evalue')}\n"
                        + "\n".join(err.get("traceback", []))
                    )
                break
    finally:
        ws.close()
        if own_kernel:
            shutdown_kernel(base_url, token, kernel_id)

    return "".join(stdout_buf)


# ---------- main flow ----------

def main() -> int:
    ap = argparse.ArgumentParser(description="Upscale a video on TELUS H200")
    ap.add_argument("input", help="local MP4 to upscale")
    ap.add_argument("-o", "--output", help="local output MP4 path (default: <input>_4k.mp4)")
    ap.add_argument("--model", choices=["x2plus", "x4plus"], default="x2plus",
                    help="ESRGAN model (default: x2plus for 1080p sources)")
    ap.add_argument("--canvas", default="3840x2160",
                    help="output canvas WxH (default 3840x2160)")
    ap.add_argument("--framing", choices=["letterbox", "crop"], default="letterbox",
                    help="letterbox = pad square content to canvas with bars (default); "
                         "crop = take center 16:9 slice from square + scale to canvas")
    ap.add_argument("--job-name", help="job dir name on pod (default: timestamp+uuid)")
    ap.add_argument("--keep-job-dir", action="store_true",
                    help="don't delete the pod job dir after success")
    ap.add_argument("--exec-timeout", type=float, default=1800.0,
                    help="kernel exec timeout in seconds (default 1800 = 30min; "
                         "bump higher for longer/heavier upscales — e.g. 5400 for "
                         "20-min 512² source @ x4plus which takes ~45min)")
    args = ap.parse_args()

    if not re.match(r"^\d+x\d+$", args.canvas):
        sys.exit(f"--canvas must be WIDTHxHEIGHT, got {args.canvas!r}")

    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        sys.exit(f"input not found: {input_path}")

    output_path = (Path(args.output).resolve() if args.output
                   else input_path.with_name(input_path.stem + "_4k.mp4"))

    base_url, token = load_env()
    base_url = base_url.rstrip("/")

    job_name = args.job_name or f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    pod_job_dir = f"{POD_JOBS_ROOT}/{job_name}"
    pod_weights = POD_WEIGHTS[args.model]
    pod_input = f"{pod_job_dir}/{input_path.name}"
    pod_output_name = f"{input_path.stem}_4k.mp4"
    pod_output = f"{pod_job_dir}/{pod_output_name}"
    pod_worker = f"{pod_job_dir}/_pod_upscale_worker.py"

    print(f"== TELUS upscale ==")
    print(f"  input:  {input_path}")
    print(f"  output: {output_path}")
    print(f"  model:  {args.model}")
    print(f"  canvas: {args.canvas}")
    print(f"  pod:    {base_url}")
    print(f"  job:    {pod_job_dir}")

    pod_mkdir(base_url, token, POD_JOBS_ROOT)
    pod_mkdir(base_url, token, pod_job_dir)

    # Upload worker (text, small).
    print("[stage 1/4] uploading worker script")
    pod_put_text(base_url, token, pod_worker, WORKER_LOCAL.read_text())

    # Chunked-upload input video.
    print("[stage 2/4] uploading input video")
    chunked_upload(base_url, token, input_path, pod_job_dir, input_path.name)

    # Verify weights exist on pod (one HEAD via contents check).
    weights_check = http_get(base_url, token, f"/api/contents/{pod_weights}",
                             params={"content": 0})
    if weights_check.status_code != 200:
        sys.exit(f"weights not found on pod: {pod_weights}\n"
                 f"  status={weights_check.status_code}\n"
                 f"  body={weights_check.text[:300]}")

    # Trigger worker via kernel exec.
    print("[stage 3/4] running upscale on H200 (streaming worker stdout)")
    home_path = "/home/jovyan"  # default Jupyter user; worker uses absolute path
    abs_job_dir = f"{home_path}/{pod_job_dir}"
    abs_weights = f"{home_path}/{pod_weights}"
    abs_worker = f"{home_path}/{pod_worker}"

    exec_code = f"""
import os
os.environ['TELUS_UPSCALE_JOB_DIR'] = {abs_job_dir!r}
os.environ['TELUS_UPSCALE_INPUT'] = {input_path.name!r}
os.environ['TELUS_UPSCALE_OUTPUT'] = {pod_output_name!r}
os.environ['TELUS_UPSCALE_WEIGHTS'] = {abs_weights!r}
os.environ['TELUS_UPSCALE_MODEL'] = {args.model!r}
os.environ['TELUS_UPSCALE_CANVAS'] = {args.canvas!r}
os.environ['TELUS_UPSCALE_FRAMING'] = {args.framing!r}
exec(open({abs_worker!r}).read())
"""
    # Long timeout: 1 frame at 0.2s × big sweeps could be many minutes.
    # 2026-05-25: 512² Autolume source needs ~45 min for 20-min content at x4plus;
    # default 1800s (30min) was insufficient. Made configurable via --exec-timeout.
    run_on_pod(base_url, token, exec_code, timeout=args.exec_timeout, stream_to_stdout=True)

    # Check status marker.
    status = pod_get_text(base_url, token, f"{pod_job_dir}/_status.txt") or ""
    if not status.strip().startswith("DONE"):
        sys.exit(f"worker did not complete cleanly. status:\n{status}")

    # Download output.
    print("[stage 4/4] downloading 4K output")
    n = pod_download_file(base_url, token, pod_output, output_path)
    print(f"  wrote {output_path} ({n/1024/1024:.2f} MB)")

    if not args.keep_job_dir:
        # Best-effort cleanup; ignore failures.
        cleanup_code = f"import shutil; shutil.rmtree({abs_job_dir!r}, ignore_errors=True)"
        try:
            run_on_pod(base_url, token, cleanup_code, timeout=30)
        except Exception as e:
            print(f"  cleanup warning: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
