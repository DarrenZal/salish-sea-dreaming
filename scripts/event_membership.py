#!/usr/bin/env python3
"""event_membership.py — Map a prompt submission timestamp to an event slug.

Phase 8 of the IMPACT KG event-scoped views plan
(~/.claude/plans/impact-kg-event-scoped-views.md).

The SSD prompts databases store `submitted_at` as a UTC TIMESTAMP (SQLite
CURRENT_TIMESTAMP default). This module provides a single function that maps
that timestamp to the canonical event slug used by the event-scoped graph
endpoints (`/graph?event=<id>`).

Strategy:
    Strategy (b) per the P8 plan: do NOT add `event_id` columns to the DBs.
    Instead the gallery_server's `/graph/event/<id>` and `/dreams/3d?event=<id>`
    endpoints compute event membership at query time by calling
    `event_for(submitted_at)` on each row. Reasons:

      - zero migration risk on two live DBs (v1 + v5)
      - the date ranges are simple + stable (locked in plan §5)
      - single source of truth for the date math (this module)
      - identical helper applies across both DB schemas (v1 lacks consent
        columns, v5 has them — backfilling event_id into both would diverge)
      - trivial to add MOVE37XR Oct / future events: extend EVENT_WINDOWS

Date windows (Pacific time, locked 2026-05-25):
    digital-ecologies-2026: 2026-04-10 00:00 PDT → 2026-04-26 23:59:59 PDT
    impact-2026:            2026-05-25 00:00 PDT → 2026-05-29 23:59:59 PDT

PDT is UTC-7 (no DST flip in this window). Boundaries are stored internally
as timezone-aware UTC datetimes for unambiguous comparison.

Stdlib-only.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional, Union


# Pacific Daylight Time = UTC-7 (in effect across both windows in 2026)
PDT = timezone(timedelta(hours=-7), name="PDT")


# Event windows, half-open at the end: [start_pdt, end_exclusive_pdt)
# Storing as PDT-aware datetimes makes the human-readable intent obvious.
EVENT_WINDOWS = [
    {
        "slug": "digital-ecologies-2026",
        # 2026-04-10 00:00 PDT inclusive through 2026-04-26 23:59:59.999 PDT
        # (i.e., < 2026-04-27 00:00 PDT)
        "start": datetime(2026, 4, 10, 0, 0, 0, tzinfo=PDT),
        "end_exclusive": datetime(2026, 4, 27, 0, 0, 0, tzinfo=PDT),
    },
    {
        "slug": "impact-2026",
        # 2026-05-25 00:00 PDT inclusive through 2026-05-29 23:59:59.999 PDT
        # Covers May 27-28 doors + May 25-26 install/jam adjacent days.
        "start": datetime(2026, 5, 25, 0, 0, 0, tzinfo=PDT),
        "end_exclusive": datetime(2026, 5, 30, 0, 0, 0, tzinfo=PDT),
    },
]


def _coerce_utc(ts: Union[str, datetime]) -> datetime:
    """Coerce a SQLite-style UTC timestamp (str or naive datetime) → aware UTC.

    Accepts:
      - "2026-04-10 18:13:09" (SQLite CURRENT_TIMESTAMP default format)
      - "2026-04-10T18:13:09" (ISO 8601 variant)
      - "2026-04-10 18:13:09.123" (fractional seconds)
      - naive datetime (interpreted as UTC, matching SQLite convention)
      - aware datetime (used as-is, converted to UTC)
    """
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    if not isinstance(ts, str):
        raise TypeError(f"event_for: expected str or datetime, got {type(ts).__name__}")

    # Normalize "YYYY-MM-DD HH:MM:SS" → ISO 8601
    s = ts.strip().replace(" ", "T")
    # Strip trailing 'Z' if present
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(s)
    except ValueError as e:
        raise ValueError(f"event_for: cannot parse timestamp {ts!r}: {e}") from e

    if dt.tzinfo is None:
        # SQLite stores CURRENT_TIMESTAMP in UTC by default
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def event_for(submitted_at: Union[str, datetime, None]) -> Optional[str]:
    """Return the event slug for a given submission timestamp, or None.

    None signals "between shows / outside any event window" — the prompt lives
    in the DB but is not surfaced in any event-scoped graph view.

    Args:
        submitted_at: UTC timestamp (str from SQLite, datetime, or None).

    Returns:
        Event slug ("digital-ecologies-2026" or "impact-2026") or None.

    Examples:
        >>> event_for("2026-04-10 18:13:09")   # 11:13 PDT on opening day
        'digital-ecologies-2026'
        >>> event_for("2026-04-27 06:59:59")   # 23:59:59 PDT on closing day
        'digital-ecologies-2026'
        >>> event_for("2026-04-27 07:00:00")   # 00:00 PDT next day, after close
        >>> event_for("2026-05-25 07:00:00")   # 00:00 PDT May 25 — IMPACT opens
        'impact-2026'
        >>> event_for("2026-05-15 12:00:00")   # between shows
        >>> event_for(None)
    """
    if submitted_at is None:
        return None

    dt_utc = _coerce_utc(submitted_at)

    for window in EVENT_WINDOWS:
        start_utc = window["start"].astimezone(timezone.utc)
        end_utc = window["end_exclusive"].astimezone(timezone.utc)
        if start_utc <= dt_utc < end_utc:
            return window["slug"]

    return None


def bucket_counts(rows) -> dict:
    """Bucket an iterable of submitted_at values into {slug: count, None: count}.

    Convenience for the sanity-check sweep run by the gallery_server at
    startup, or by any CLI tool inspecting an SSD prompts DB.

    Args:
        rows: iterable of submitted_at values (str | datetime | None).

    Returns:
        dict mapping event slug (or the string '__between__' for None) → count.
    """
    counts = {"digital-ecologies-2026": 0, "impact-2026": 0, "__between__": 0}
    for ts in rows:
        slug = event_for(ts)
        key = slug if slug is not None else "__between__"
        counts[key] = counts.get(key, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# CLI: sanity-check a SQLite prompts DB
# ---------------------------------------------------------------------------

def _cli(argv=None) -> int:
    import argparse
    import sqlite3
    import sys

    parser = argparse.ArgumentParser(
        description="Bucket SSD prompts.db rows by event membership."
    )
    parser.add_argument(
        "db",
        help="Path to prompts.db (v1 or v5)",
    )
    parser.add_argument(
        "--show-between",
        action="store_true",
        help="Also list each row that falls outside both event windows",
    )
    args = parser.parse_args(argv)

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    cur.execute("SELECT submitted_at FROM prompts")
    timestamps = [row[0] for row in cur.fetchall()]
    counts = bucket_counts(timestamps)
    total = sum(counts.values())

    print(f"DB: {args.db}")
    print(f"Total rows: {total}")
    for k, v in counts.items():
        label = k if k != "__between__" else "(between / outside any event)"
        print(f"  {label}: {v}")

    if args.show_between:
        cur.execute(
            "SELECT id, submitted_at, source, substr(raw_text, 1, 60) "
            "FROM prompts ORDER BY submitted_at"
        )
        print("\nBetween-window rows:")
        for row in cur.fetchall():
            row_id, ts, source, raw = row
            if event_for(ts) is None:
                print(f"  [{row_id}] {ts} ({source}) {raw!r}")

    conn.close()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())
