#!/usr/bin/env python3
"""Poll May-scope bioregional feeds and emit TouchDesigner-friendly OSC.

Feeds intentionally limited to low-risk physical measurements:
- DFO CHS IWLS Vancouver tide station 07735
- ECCC MSC GeoMet Fraser River at Hope station 08MF005
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from pythonosc.udp_client import SimpleUDPClient
except Exception:  # pragma: no cover - dependency is present in the SSD env, optional elsewhere.
    SimpleUDPClient = None


IWLS_STATION_CODE = "07735"
IWLS_STATION_ID = "5cebf1de3d0f4a073c4bb943"
FRASER_STATION = "08MF005"

DEFAULT_CACHE = Path("output/live-feeds/bioregional_cache.json")


class FeedError(RuntimeError):
    pass


@dataclass
class Sample:
    timestamp: str
    value: float


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_z(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def fetch_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "salish-sea-dreaming/phase2-live-feed"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FeedError(f"Fetch failed: {url}: {exc}") from exc


def iwls_data_url(time_series_code: str, start: datetime, end: datetime, resolution: str | None = None) -> str:
    params = {
        "time-series-code": time_series_code,
        "from": iso_z(start),
        "to": iso_z(end),
    }
    if resolution:
        params["resolution"] = resolution
    query = urllib.parse.urlencode(params)
    return f"https://api-iwls.dfo-mpo.gc.ca/api/v1/stations/{IWLS_STATION_ID}/data?{query}"


def fetch_tide(now: datetime) -> dict[str, Any]:
    raw = fetch_json(iwls_data_url("wlo", now - timedelta(hours=2), now, "THREE_MINUTES"))
    points = [
        Sample(timestamp=item["eventDate"], value=float(item["value"]))
        for item in raw
        if item.get("value") is not None and item.get("eventDate")
    ]
    points.sort(key=lambda p: p.timestamp)
    if len(points) < 2:
        raise FeedError("IWLS returned fewer than 2 tide points")

    previous, latest = points[-2], points[-1]
    dt_hours = (parse_iso_z(latest.timestamp) - parse_iso_z(previous.timestamp)).total_seconds() / 3600.0
    if dt_hours <= 0:
        raise FeedError("IWLS tide points are not time-ordered")
    rate_mph = (latest.value - previous.value) / dt_hours

    return {
        "level_m": latest.value,
        "level_timestamp": latest.timestamp,
        "rate_mph": rate_mph,
        "rate_window_start": previous.timestamp,
        "rate_window_end": latest.timestamp,
    }


def fetch_next_hilo(now: datetime) -> dict[str, Any]:
    raw = fetch_json(iwls_data_url("wlp-hilo", now, now + timedelta(days=2)))
    points = [
        Sample(timestamp=item["eventDate"], value=float(item["value"]))
        for item in raw
        if item.get("value") is not None and item.get("eventDate")
    ]
    points.sort(key=lambda p: p.timestamp)
    if not points:
        raise FeedError("IWLS returned no upcoming high/low predictions")

    next_point = points[0]
    seconds = (parse_iso_z(next_point.timestamp) - now).total_seconds()
    return {
        "predicted_next_hilo_m": next_point.value,
        "predicted_next_hilo_timestamp": next_point.timestamp,
        "predicted_next_hilo_seconds": max(0.0, seconds),
    }


def fetch_fraser() -> dict[str, Any]:
    params = urllib.parse.urlencode(
        {
            "STATION_NUMBER": FRASER_STATION,
            "sortby": "-DATETIME",
            "f": "json",
            "limit": "3",
        }
    )
    url = f"https://api.weather.gc.ca/collections/hydrometric-realtime/items?{params}"
    raw = fetch_json(url)
    features = raw.get("features") or []
    if not features:
        raise FeedError("MSC GeoMet returned no Fraser hydrometric features")

    props = features[0].get("properties") or {}
    if props.get("DISCHARGE") is None:
        raise FeedError("Latest Fraser hydrometric feature has no DISCHARGE")

    return {
        "discharge_cms": float(props["DISCHARGE"]),
        "level_m": float(props["LEVEL"]) if props.get("LEVEL") is not None else None,
        "timestamp": props.get("DATETIME"),
        "station_name": props.get("STATION_NAME"),
    }


def load_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def write_cache(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def collect_values(cache_path: Path, allow_cache: bool = True) -> tuple[dict[str, Any], bool]:
    now = utc_now()
    cache_used = False
    cached = load_cache(cache_path) if allow_cache else None
    payload: dict[str, Any] = {
        "collected_at": iso_z(now),
        "sources": {
            "tide": "DFO CHS IWLS Vancouver 07735",
            "fraser": "ECCC MSC GeoMet hydrometric-realtime 08MF005",
        },
        "tide": {},
        "fraser": {},
    }

    for key, fetcher in (
        ("tide", lambda: {**fetch_tide(now), **fetch_next_hilo(now)}),
        ("fraser", fetch_fraser),
    ):
        try:
            payload[key] = fetcher()
        except FeedError:
            if not cached or not cached.get(key):
                raise
            payload[key] = cached[key]
            payload.setdefault("warnings", []).append(f"{key} feed using cache fallback")
            cache_used = True

    write_cache(cache_path, payload)
    return payload, cache_used


def osc_messages(payload: dict[str, Any], cache_used: bool) -> list[tuple[str, Any]]:
    tide = payload["tide"]
    fraser = payload["fraser"]
    messages: list[tuple[str, Any]] = [
        ("/sea/tide/level_m", float(tide["level_m"])),
        ("/sea/tide/rate_mph", float(tide["rate_mph"])),
        ("/sea/tide/predicted_next_hilo_m", float(tide["predicted_next_hilo_m"])),
        ("/sea/tide/predicted_next_hilo_seconds", float(tide["predicted_next_hilo_seconds"])),
        ("/river/fraser/discharge_cms", float(fraser["discharge_cms"])),
        ("/system/heartbeat", [1, time.time()]),
        ("/system/cache_used", 1 if cache_used else 0),
    ]
    if fraser.get("level_m") is not None:
        messages.append(("/river/fraser/level_m", float(fraser["level_m"])))
    return messages


def emit_osc(messages: list[tuple[str, Any]], host: str, port: int) -> None:
    if SimpleUDPClient is None:
        raise RuntimeError("python-osc is not installed; rerun with --dry-run or install python-osc")
    client = SimpleUDPClient(host, port)
    for address, value in messages:
        client.send_message(address, value)


def print_messages(messages: list[tuple[str, Any]], payload: dict[str, Any], cache_used: bool) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("\nOSC preview:")
    for address, value in messages:
        print(f"  {address} {value}")
    print(f"\ncache_used={int(cache_used)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--osc-host", default="127.0.0.1")
    parser.add_argument("--osc-port", type=int, default=7000)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--interval-sec", type=float, default=60.0)
    parser.add_argument("--once", action="store_true", help="Poll once and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print values instead of sending OSC")
    parser.add_argument("--no-cache-fallback", action="store_true")
    args = parser.parse_args()

    while True:
        try:
            payload, cache_used = collect_values(args.cache, allow_cache=not args.no_cache_fallback)
            messages = osc_messages(payload, cache_used)
            if args.dry_run:
                print_messages(messages, payload, cache_used)
            else:
                emit_osc(messages, args.osc_host, args.osc_port)
                print(f"{payload['collected_at']} emitted {len(messages)} OSC messages cache_used={int(cache_used)}")
        except Exception as exc:
            print(f"bioregional_osc_bridge error: {exc}", file=sys.stderr)
            if args.once:
                return 1

        if args.once:
            return 0
        time.sleep(args.interval_sec)


if __name__ == "__main__":
    raise SystemExit(main())
