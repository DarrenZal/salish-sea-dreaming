#!/usr/bin/env python3
"""Smoke test td_bioregional_osc_callbacks.py without TouchDesigner."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import td_bioregional_osc_callbacks as callbacks


class FakeCell:
    def __init__(self, value: Any):
        self.val = value

    def __str__(self) -> str:
        return str(self.val)


class FakeTable:
    def __init__(self) -> None:
        self.rows: list[list[str]] = []

    @property
    def numRows(self) -> int:
        return len(self.rows)

    def appendRow(self, row: list[Any]) -> None:
        self.rows.append([str(value) for value in row])

    def replaceRow(self, row_index: int, row: list[Any]) -> None:
        self.rows[row_index] = [str(value) for value in row]

    def __getitem__(self, index: tuple[int, int]) -> FakeCell:
        row, col = index
        return FakeCell(self.rows[row][col])

    def __setitem__(self, index: tuple[int, int], value: Any) -> None:
        row, col = index
        self.rows[row][col] = str(value)


class FakeComp:
    def __init__(self) -> None:
        self.storage: dict[str, Any] = {}

    def fetch(self, key: str, default: Any = None) -> Any:
        return self.storage.get(key, default)

    def store(self, key: str, value: Any) -> None:
        self.storage[key] = value


class FakeTD:
    def __init__(self) -> None:
        self.project = FakeComp()
        self.table = FakeTable()
        self.ops = {
            "/project1": self.project,
            "/project1/bioregional_values": self.table,
        }

    def op(self, path: str) -> Any:
        return self.ops.get(path)


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> None:
    fake_td = FakeTD()
    messages = [
        ("/sea/tide/level_m", [2.968]),
        ("/sea/tide/rate_mph", [-0.1]),
        ("/sea/tide/predicted_next_hilo_m", [2.534]),
        ("/sea/tide/predicted_next_hilo_seconds", [6847.0]),
        ("/river/fraser/discharge_cms", [6050.0]),
        ("/river/fraser/level_m", [7.105]),
        ("/system/heartbeat", [1, 1778731200.0]),
        ("/system/cache_used", [0]),
    ]

    for address, args in messages:
        update = callbacks.handle_message(
            address,
            args,
            time_stamp=123.5,
            op_func=fake_td.op,
        )
        if update is None:
            raise AssertionError(f"{address} did not produce an update")

    state = fake_td.project.fetch("bioregional_values", {})
    assert_equal(state["bio_tide_level_m"], 2.968, "tide level")
    assert_equal(state["bio_tide_rate_mph"], -0.1, "tide rate")
    assert_equal(state["bio_fraser_discharge_cms"], 6050.0, "fraser discharge")
    assert_equal(state["bio_heartbeat_status"], 1, "heartbeat status")
    assert_equal(state["bio_cache_used"], 0, "cache flag")
    assert_equal(fake_td.table.numRows, len(messages) + 1, "table rows")

    callbacks.handle_message(
        "/sea/tide/level_m",
        [3.125],
        time_stamp=124.0,
        op_func=fake_td.op,
    )
    state = fake_td.project.fetch("bioregional_values", {})
    assert_equal(state["bio_tide_level_m"], 3.125, "updated tide level")
    assert_equal(fake_td.table.numRows, len(messages) + 1, "table upsert rows")
    assert_equal(fake_td.table.rows[1][2], "3.125", "table value updated")

    unknown = callbacks.handle_message(
        "/not/in/contract",
        [1.0],
        time_stamp=125.0,
        op_func=fake_td.op,
    )
    assert_equal(unknown, None, "unknown address")

    bad = callbacks.handle_message(
        "/sea/tide/level_m",
        ["not-a-number"],
        time_stamp=125.0,
        op_func=fake_td.op,
    )
    assert_equal(bad, None, "bad payload")

    print("td_bioregional_osc_callbacks smoke: PASS")
    print(f"stored_keys={len(state)} table_rows={fake_td.table.numRows}")


if __name__ == "__main__":
    main()
