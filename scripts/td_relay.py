"""
td_relay.py — runs on TD machine (Windows 3090).
Pulls enriched prompts from poly via SSE, sends each as OSC to TouchDesigner.
Auto-reconnects on disconnect. Run: python td_relay.py
"""
import os
import time

import requests
from pythonosc import udp_client

POLY_URL = os.getenv("POLY_URL", "https://ssd-gallery.cfargotunnel.com")
TD_HOST = os.getenv("TD_HOST", "127.0.0.1")
TD_PORT = int(os.getenv("TD_PORT", "7000"))

osc = udp_client.SimpleUDPClient(TD_HOST, TD_PORT)
print(f"OSC target: {TD_HOST}:{TD_PORT}")

while True:
    try:
        print(f"Connecting to {POLY_URL}/td/stream ...")
        with requests.get(f"{POLY_URL}/td/stream", stream=True, timeout=60) as r:
            r.raise_for_status()
            print("Connected. Waiting for prompts...")
            for raw in r.iter_lines():
                if raw and raw.startswith(b"data:"):
                    prompt = raw[5:].strip().decode("utf-8")
                    if prompt and prompt != "ping":
                        osc.send_message("/salish/prompt/visitor", prompt)
                        print(f"  \u2192 OSC: {prompt[:80]}...")
    except KeyboardInterrupt:
        print("Stopped.")
        break
    except Exception as e:
        print(f"Disconnected ({e}). Reconnecting in 5s...")
        time.sleep(5)
