#!/usr/bin/env python3
"""Tiny state server for QC review app. Reads/writes JSON files to disk."""

import json
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

STATE_DIR = "/opt/qc-review/state"
os.makedirs(STATE_DIR, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def _safe_name(self, path):
        name = path.strip("/").replace("state/", "", 1)
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return None
        return name

    def do_GET(self):
        name = self._safe_name(self.path)
        if not name:
            self.send_error(400, "Invalid state name")
            return
        fpath = os.path.join(STATE_DIR, name + ".json")
        if os.path.exists(fpath):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with open(fpath, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"{}")

    def do_POST(self):
        name = self._safe_name(self.path)
        if not name:
            self.send_error(400, "Invalid state name")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        # Validate it's JSON
        try:
            json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return
        fpath = os.path.join(STATE_DIR, name + ".json")
        with open(fpath, "wb") as f:
            f.write(body)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "size": len(body)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass  # Suppress logs

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8091), Handler)
    print("QC state server on :8091")
    server.serve_forever()
