#!/usr/bin/env python3
"""Small Jupyter Contents API sync helper for TELUS pod file transfer.

Examples:
  python3 scripts/jupyter_contents_sync.py upload austin-v2-ingest/training austin-v2-pilot
  python3 scripts/jupyter_contents_sync.py download austin-v2-eval output/austin-v2-eval

Credentials are read from --url/--token, the environment, or .env:
  TELUS_POD_URL=https://...
  Jupyter_REST_API=...
"""

from __future__ import annotations

import argparse
import base64
import fnmatch
import os
import posixpath
import sys
import urllib.parse
from pathlib import Path
from typing import Any

import requests


TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def clean_remote(path: str) -> str:
    return path.strip("/")


def join_remote(*parts: str) -> str:
    return clean_remote(posixpath.join(*(p.strip("/") for p in parts if p)))


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


class JupyterContents:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"token {token}"})

    def url(self, remote_path: str) -> str:
        quoted = urllib.parse.quote(clean_remote(remote_path), safe="/")
        return f"{self.base_url}/api/contents/{quoted}"

    def exists(self, remote_path: str, expected_type: str | None = None) -> bool:
        response = self.session.get(self.url(remote_path), timeout=30)
        if response.status_code != 200:
            return False
        if expected_type is None:
            return True
        return response.json().get("type") == expected_type

    def put_directory(self, remote_path: str) -> None:
        if not remote_path:
            return
        response = self.session.put(self.url(remote_path), json={"type": "directory"}, timeout=30)
        if response.status_code in (200, 201):
            return
        if response.status_code in (400, 409) and self.exists(remote_path, "directory"):
            return
        if response.status_code not in (200, 201):
            raise RuntimeError(f"mkdir {remote_path}: {response.status_code} {response.text[:300]}")

    def mkdir_parents(self, remote_path: str) -> None:
        parts = [p for p in clean_remote(remote_path).split("/") if p]
        for i in range(1, len(parts) + 1):
            self.put_directory("/".join(parts[:i]))

    def put_file(self, local_path: Path, remote_path: str) -> None:
        data = local_path.read_bytes()
        if is_text_file(local_path):
            payload: dict[str, Any] = {
                "type": "file",
                "format": "text",
                "content": data.decode("utf-8"),
            }
        else:
            payload = {
                "type": "file",
                "format": "base64",
                "content": base64.b64encode(data).decode("ascii"),
            }
        response = self.session.put(self.url(remote_path), json=payload, timeout=60)
        if response.status_code not in (200, 201):
            raise RuntimeError(f"upload {local_path} -> {remote_path}: {response.status_code} {response.text[:300]}")

    def get(self, remote_path: str) -> dict[str, Any]:
        response = self.session.get(self.url(remote_path), timeout=60)
        if response.status_code != 200:
            raise RuntimeError(f"get {remote_path}: {response.status_code} {response.text[:300]}")
        return response.json()


def iter_local_files(root: Path, include: list[str], exclude: list[str]) -> list[Path]:
    if root.is_file():
        return [root]
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        if include and not any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(path.name, pat) for pat in include):
            continue
        if exclude and any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(path.name, pat) for pat in exclude):
            continue
        files.append(path)
    return sorted(files)


def upload(client: JupyterContents, local: Path, remote: str, include: list[str], exclude: list[str]) -> None:
    if not local.exists():
        raise FileNotFoundError(local)
    files = iter_local_files(local, include, exclude)
    if local.is_file():
        client.mkdir_parents(posixpath.dirname(clean_remote(remote)))
        client.put_file(local, remote)
        print(f"uploaded {local} -> {remote}")
        return

    client.mkdir_parents(remote)
    for path in files:
        rel = path.relative_to(local).as_posix()
        remote_path = join_remote(remote, rel)
        client.mkdir_parents(posixpath.dirname(remote_path))
        client.put_file(path, remote_path)
        print(f"uploaded {rel} -> {remote_path}")
    print(f"upload complete: {len(files)} file(s)")


def decode_file(model: dict[str, Any]) -> bytes:
    content = model.get("content")
    if not isinstance(content, str):
        raise RuntimeError("Jupyter file response has no string content")
    fmt = model.get("format")
    if fmt == "base64":
        return base64.b64decode(content)
    if fmt == "text":
        return content.encode("utf-8")
    raise RuntimeError(f"Unsupported Jupyter file format: {fmt}")


def download(client: JupyterContents, remote: str, local: Path) -> int:
    model = client.get(remote)
    model_type = model.get("type")
    if model_type == "file":
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(decode_file(model))
        print(f"downloaded {remote} -> {local}")
        return 1
    if model_type != "directory":
        raise RuntimeError(f"Unsupported Jupyter model type for {remote}: {model_type}")

    count = 0
    for child in model.get("content") or []:
        child_path = join_remote(remote, child["name"])
        count += download(client, child_path, local / child["name"])
    return count


def list_remote(client: JupyterContents, remote: str) -> None:
    model = client.get(remote)
    if model.get("type") == "directory":
        for child in model.get("content") or []:
            print(f"{child.get('type','?'):9s} {child.get('path') or child.get('name')}")
    else:
        print(f"{model.get('type','?'):9s} {model.get('path') or remote}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--url", default=None, help="Jupyter base URL; defaults to TELUS_POD_URL")
    parser.add_argument("--token", default=None, help="Jupyter token; defaults to Jupyter_REST_API/TELUS_TOKEN/JUPYTER_TOKEN")
    sub = parser.add_subparsers(dest="command", required=True)

    upload_p = sub.add_parser("upload")
    upload_p.add_argument("local", type=Path)
    upload_p.add_argument("remote")
    upload_p.add_argument("--include", action="append", default=[])
    upload_p.add_argument("--exclude", action="append", default=[])

    download_p = sub.add_parser("download")
    download_p.add_argument("remote")
    download_p.add_argument("local", type=Path)

    list_p = sub.add_parser("list")
    list_p.add_argument("remote", nargs="?", default="")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    load_env_file(args.env_file)

    url = args.url or os.getenv("TELUS_POD_URL")
    token = args.token or os.getenv("Jupyter_REST_API") or os.getenv("TELUS_TOKEN") or os.getenv("JUPYTER_TOKEN")
    if not url or not token:
        parser.error("missing TELUS_POD_URL/Jupyter_REST_API; pass --url/--token or provide .env")

    client = JupyterContents(url, token)
    try:
        if args.command == "upload":
            upload(client, args.local, args.remote, args.include, args.exclude)
        elif args.command == "download":
            count = download(client, args.remote, args.local)
            print(f"download complete: {count} file(s)")
        elif args.command == "list":
            list_remote(client, args.remote)
    except Exception as exc:
        print(f"jupyter_contents_sync error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
