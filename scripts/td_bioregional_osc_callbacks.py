"""
TouchDesigner OSC In DAT callbacks for May-scope bioregional feeds.

Paste this into a TD callback DAT such as:

    /project1/bioregional_osc_callbacks

Recommended OSC In DAT setup:

    /project1/bioregional_osc_in
      port: 7001
      callbacks DAT: /project1/bioregional_osc_callbacks

The bridge can then run with:

    python3 scripts/bioregional_osc_bridge.py --osc-port 7001

This file is intentionally independent from ssd_osc_in_callbacks.py so the
visitor prompt path can keep using its existing callback and port.
"""

from typing import Any, Callable, Dict, Iterable, List, Optional


ADDRESS_SPECS: Dict[str, Dict[str, Any]] = {
    "/sea/tide/level_m": {
        "key": "bio_tide_level_m",
        "unit": "m",
        "kind": "float",
    },
    "/sea/tide/rate_mph": {
        "key": "bio_tide_rate_mph",
        "unit": "m/h",
        "kind": "float",
    },
    "/sea/tide/predicted_next_hilo_m": {
        "key": "bio_tide_next_hilo_m",
        "unit": "m",
        "kind": "float",
    },
    "/sea/tide/predicted_next_hilo_seconds": {
        "key": "bio_tide_next_hilo_seconds",
        "unit": "s",
        "kind": "float",
    },
    "/river/fraser/discharge_cms": {
        "key": "bio_fraser_discharge_cms",
        "unit": "cms",
        "kind": "float",
    },
    "/river/fraser/level_m": {
        "key": "bio_fraser_level_m",
        "unit": "m",
        "kind": "float",
    },
    "/system/cache_used": {
        "key": "bio_cache_used",
        "unit": "bool",
        "kind": "int",
    },
    "/system/heartbeat": {
        "key": "bio_heartbeat",
        "unit": "status,unix_ts",
        "kind": "heartbeat",
    },
}

STORE_OP_PATHS = (
    "/project1/salish_dreamworld",
    "/project1",
)

TABLE_OP_PATHS = (
    "/project1/bioregional_values",
    "/project1/salish_dreamworld/bioregional_values",
)

TABLE_HEADER = [
    "address",
    "store_key",
    "value0",
    "value1",
    "updated_at_td_seconds",
    "unit",
]


def coerce_update(
    address: str,
    args: Iterable[Any],
    updated_at_td_seconds: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Map one OSC packet into a TD-friendly update dict.

    Unknown addresses return None. Bad payloads are ignored rather than raising
    inside TD's callback thread.
    """

    spec = ADDRESS_SPECS.get(address)
    if spec is None:
        return None

    values = list(args or [])
    if not values:
        return None

    kind = spec["kind"]
    try:
        if kind == "heartbeat":
            if len(values) < 2:
                return None
            value0 = int(values[0])
            value1 = float(values[1])
            store_values = {
                "bio_heartbeat_status": value0,
                "bio_heartbeat_unix_ts": value1,
            }
        elif kind == "int":
            value0 = int(values[0])
            value1 = ""
            store_values = {spec["key"]: value0}
        else:
            value0 = float(values[0])
            value1 = ""
            store_values = {spec["key"]: value0}
    except (TypeError, ValueError):
        return None

    update = {
        "address": address,
        "store_key": spec["key"],
        "value0": value0,
        "value1": value1,
        "updated_at_td_seconds": updated_at_td_seconds,
        "unit": spec["unit"],
        "store_values": store_values,
    }
    return update


def handle_message(
    address: str,
    args: Iterable[Any],
    time_stamp: Optional[float] = None,
    op_func: Optional[Callable[[str], Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Pure-ish handler used by both TD and local smoke tests."""

    update = coerce_update(address, args, time_stamp)
    if update is None:
        return None

    if op_func is not None:
        _write_to_td(update, op_func)

    return update


def _write_to_td(update: Dict[str, Any], op_func: Callable[[str], Any]) -> None:
    store_target = _first_existing_op(op_func, STORE_OP_PATHS)
    if store_target is not None:
        _store_update(store_target, update)

    table = _first_existing_op(op_func, TABLE_OP_PATHS)
    if table is not None:
        _upsert_table_row(table, update)


def _first_existing_op(op_func: Callable[[str], Any], paths: Iterable[str]) -> Any:
    for path in paths:
        try:
            candidate = op_func(path)
        except Exception:
            candidate = None
        if candidate is not None:
            return candidate
    return None


def _store_update(target: Any, update: Dict[str, Any]) -> None:
    state = _fetch(target, "bioregional_values", {})
    if not isinstance(state, dict):
        state = {}

    for key, value in update["store_values"].items():
        state[key] = value
        _safe_store(target, key, value)

    state[update["store_key"] + "_updated_at_td_seconds"] = update[
        "updated_at_td_seconds"
    ]
    _safe_store(target, "bioregional_values", state)


def _fetch(target: Any, key: str, default: Any) -> Any:
    fetch = getattr(target, "fetch", None)
    if fetch is None:
        return default
    try:
        return fetch(key, default)
    except TypeError:
        try:
            value = fetch(key)
        except Exception:
            return default
        return default if value is None else value
    except Exception:
        return default


def _safe_store(target: Any, key: str, value: Any) -> None:
    store = getattr(target, "store", None)
    if store is None:
        return
    try:
        store(key, value)
    except Exception:
        return


def _upsert_table_row(table: Any, update: Dict[str, Any]) -> None:
    _ensure_table_header(table)
    row = [
        update["address"],
        update["store_key"],
        _format_cell(update["value0"]),
        _format_cell(update["value1"]),
        _format_cell(update["updated_at_td_seconds"]),
        update["unit"],
    ]

    existing_row = _find_table_row(table, update["address"])
    if existing_row is None:
        table.appendRow(row)
        return

    replace_row = getattr(table, "replaceRow", None)
    if replace_row is not None:
        replace_row(existing_row, row)
        return

    for col, value in enumerate(row):
        try:
            table[existing_row, col] = value
        except Exception:
            pass


def _ensure_table_header(table: Any) -> None:
    if _num_rows(table) == 0:
        table.appendRow(TABLE_HEADER)
        return
    if _cell_text(table, 0, 0) != TABLE_HEADER[0]:
        # Avoid clearing operator-created data. Add a header only when the DAT is empty.
        return


def _find_table_row(table: Any, address: str) -> Optional[int]:
    for row_index in range(1, _num_rows(table)):
        if _cell_text(table, row_index, 0) == address:
            return row_index
    return None


def _num_rows(table: Any) -> int:
    value = getattr(table, "numRows", 0)
    try:
        return int(value() if callable(value) else value)
    except Exception:
        return 0


def _cell_text(table: Any, row: int, col: int) -> str:
    try:
        cell = table[row, col]
    except Exception:
        return ""
    return str(getattr(cell, "val", cell))


def _format_cell(value: Any) -> str:
    if value is None:
        return ""
    if value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def _td_seconds(time_stamp: Optional[float]) -> Optional[float]:
    try:
        return float(absTime.seconds)  # type: ignore[name-defined]
    except Exception:
        if time_stamp is None:
            return None
        try:
            return float(time_stamp)
        except (TypeError, ValueError):
            return None


def onReceiveOSC(
    dat,
    rowIndex: int,
    message: str,
    byteData: bytes,
    timeStamp: float,
    address: str,
    args: List[Any],
    peer,
):
    update = handle_message(
        address,
        args,
        time_stamp=_td_seconds(timeStamp),
        op_func=op,  # type: ignore[name-defined]
    )
    if update is not None:
        print(
            "[SSD bio] "
            + update["address"]
            + " -> "
            + update["store_key"]
            + "="
            + _format_cell(update["value0"])
        )
