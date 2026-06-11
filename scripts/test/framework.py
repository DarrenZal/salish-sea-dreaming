"""Test framework for the Salish Sea Dreaming web app.

Probe-based, YAML-driven, with retry on transient LLM-load cliffs. Supports
single-turn chat probes, multi-turn conversations, KG endpoint probes, and
live-show integration flows (visitor → relay → TD → snapshot → KG).

Usage from CLI: see `run_tests.py` in this directory.

Design choices:
- One YAML file per test category in ./probes/
- Each probe has property-based assertions (must_contain, must_not_contain
  case-insensitive regex) — never check exact match
- Built-in retry for transient empty replies (Gemma load cliffs)
- Pace probes via per-suite `wait_seconds` to respect server rate limits
"""
from __future__ import annotations

import dataclasses
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import yaml  # PyYAML (pip install pyyaml — available on most systems; if missing, fall back to JSON probe files)

PRIMARY = os.environ.get("PRIMARY_URL", "https://salishseadreaming.art")
LOCAL_HEALTH = "http://37.27.48.12:9004/health"
DEFAULT_WAIT = float(os.environ.get("WAIT_SECONDS", "7"))
DEFAULT_RETRIES = int(os.environ.get("RETRIES", "3"))
HTTP_TIMEOUT = 30.0


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class ProbeResult:
    name: str
    ok: bool
    reason: str = ""
    reply: str = ""
    category: str = ""

    def summary(self) -> str:
        mark = "✓" if self.ok else "✗"
        line = f"  {mark} {self.name}"
        if not self.ok:
            line += f" — {self.reason}"
        return line


@dataclass
class SuiteResult:
    category: str
    description: str
    probe_results: list[ProbeResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for p in self.probe_results if p.ok)

    @property
    def failed(self) -> int:
        return sum(1 for p in self.probe_results if not p.ok)


# ---------------------------------------------------------------------------
# HTTP client with retry
# ---------------------------------------------------------------------------

def http_request(
    url: str,
    method: str = "GET",
    body: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: float = HTTP_TIMEOUT,
) -> tuple[int, str]:
    """Return (status, body_text). Network errors return (-1, error_message)."""
    data: Optional[bytes] = None
    h: dict[str, str] = headers.copy() if headers else {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        h.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception:
            return e.code, str(e)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return -1, f"network error: {e}"


def chat_request(message: str, event: str = "impact-2026", history: Optional[list] = None,
                 retries: int = DEFAULT_RETRIES, wait_between: float = 2.0) -> str:
    """POST /chat; return the reply text. Retries on transient empty replies."""
    payload = {"message": message, "history": history or [], "event": event}
    last_err = ""
    for attempt in range(retries):
        status, text = http_request(f"{PRIMARY}/chat", "POST", body=payload)
        if status == 200:
            try:
                d = json.loads(text)
                reply = d.get("reply", "")
                if reply:
                    return reply
                last_err = f"empty reply (status 200) attempt {attempt+1}"
            except json.JSONDecodeError:
                last_err = f"non-JSON response attempt {attempt+1}"
        elif status == 429:
            last_err = f"rate-limited attempt {attempt+1}"
            time.sleep(wait_between * 2)
            continue
        else:
            last_err = f"status={status} attempt {attempt+1}: {text[:120]}"
        time.sleep(wait_between)
    return f"<RETRY_EXHAUSTED: {last_err}>"


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

def assert_text(text: str, must_contain: str = "", must_not_contain: str = "") -> tuple[bool, str]:
    """Return (ok, reason). Both patterns are case-insensitive regex."""
    if must_contain:
        if not re.search(must_contain, text, re.IGNORECASE):
            return False, f"missing required: /{must_contain}/"
    if must_not_contain:
        m = re.search(must_not_contain, text, re.IGNORECASE)
        if m:
            return False, f"forbidden match: /{must_not_contain}/ → '{m.group(0)}'"
    return True, ""


# ---------------------------------------------------------------------------
# Single-turn chat probes
# ---------------------------------------------------------------------------

def run_chat_probe(probe: dict, suite_default_event: str = "impact-2026",
                   wait: float = DEFAULT_WAIT, verbose: bool = False) -> ProbeResult:
    name = probe["name"]
    query = probe["query"]
    event = probe.get("event", suite_default_event)
    must_contain = probe.get("must_contain", "")
    must_not_contain = probe.get("must_not_contain", "")
    reply = chat_request(query, event=event)
    if reply.startswith("<RETRY_EXHAUSTED:"):
        result = ProbeResult(name=name, ok=False, reason=reply, reply="")
    else:
        ok, reason = assert_text(reply, must_contain, must_not_contain)
        result = ProbeResult(name=name, ok=ok, reason=reason, reply=reply[:600])
    if verbose:
        print(f"    Q: {query}")
        print(f"    A: {reply[:300]}")
    time.sleep(wait)
    return result


# ---------------------------------------------------------------------------
# Multi-turn conversation probes
# ---------------------------------------------------------------------------

def run_multi_turn_probe(probe: dict, suite_default_event: str = "impact-2026",
                         wait: float = DEFAULT_WAIT, verbose: bool = False) -> ProbeResult:
    """Walk a list of turns, building up history, asserting per-turn."""
    name = probe["name"]
    event = probe.get("event", suite_default_event)
    turns = probe.get("turns", [])
    history: list[dict] = []
    transcript: list[str] = []

    for i, turn in enumerate(turns, 1):
        query = turn["query"]
        reply = chat_request(query, event=event, history=history)
        if reply.startswith("<RETRY_EXHAUSTED:"):
            return ProbeResult(
                name=name, ok=False,
                reason=f"turn {i}: {reply}",
                reply="\n---\n".join(transcript + [f"USER: {query}", "ASSISTANT: (retry exhausted)"]),
            )
        transcript.append(f"T{i} USER: {query}")
        transcript.append(f"T{i} ASSISTANT: {reply[:300]}")
        ok, reason = assert_text(reply, turn.get("must_contain", ""), turn.get("must_not_contain", ""))
        if not ok:
            return ProbeResult(
                name=name, ok=False,
                reason=f"turn {i} failed: {reason}",
                reply="\n".join(transcript),
            )
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": reply})
        if verbose:
            print(f"    T{i}: {query}")
            print(f"    →  {reply[:200]}")
        time.sleep(wait)

    return ProbeResult(name=name, ok=True, reply="\n".join(transcript))


# ---------------------------------------------------------------------------
# KG endpoint probes
# ---------------------------------------------------------------------------

def run_kg_probe(probe: dict, wait: float = 1.5, verbose: bool = False) -> ProbeResult:
    """Test KG endpoints with HTTP-level + JSON-shape assertions."""
    name = probe["name"]
    method = probe.get("method", "GET")
    path = probe["path"]
    expect_status = probe.get("expect_status", 200)
    expect_keys = probe.get("expect_keys", [])
    expect_min_count = probe.get("expect_min_count", {})  # {"nodes": 10, "links": 5}
    must_contain_node = probe.get("must_contain_node", "")
    must_not_contain_node = probe.get("must_not_contain_node", "")

    url = f"{PRIMARY}{path}"
    status, body_text = http_request(url, method=method)
    if status != expect_status:
        return ProbeResult(name=name, ok=False,
                           reason=f"expected status {expect_status}, got {status}: {body_text[:120]}")
    if expect_status != 200:
        # success means we got the expected error code
        time.sleep(wait)
        return ProbeResult(name=name, ok=True)

    try:
        d = json.loads(body_text)
    except json.JSONDecodeError as e:
        return ProbeResult(name=name, ok=False, reason=f"non-JSON response: {e}")

    for k in expect_keys:
        if k not in d:
            return ProbeResult(name=name, ok=False, reason=f"missing key in response: {k}")

    for k, minimum in expect_min_count.items():
        actual = len(d.get(k, []))
        if actual < minimum:
            return ProbeResult(name=name, ok=False,
                               reason=f"key {k} count {actual} < {minimum}")

    if must_contain_node:
        node_ids = [n.get("id", "") for n in d.get("nodes", [])]
        if not any(re.search(must_contain_node, nid, re.IGNORECASE) for nid in node_ids):
            return ProbeResult(name=name, ok=False,
                               reason=f"no node matching /{must_contain_node}/ found")
    if must_not_contain_node:
        node_ids = [n.get("id", "") for n in d.get("nodes", [])]
        if any(re.search(must_not_contain_node, nid, re.IGNORECASE) for nid in node_ids):
            return ProbeResult(name=name, ok=False,
                               reason=f"forbidden node /{must_not_contain_node}/ present")

    if verbose:
        print(f"    {method} {path} → {status}, keys: {list(d.keys())[:6]}")
    time.sleep(wait)
    return ProbeResult(name=name, ok=True, reply=str(d)[:300])


# ---------------------------------------------------------------------------
# Live-show integration probes
# ---------------------------------------------------------------------------

def run_live_show_probe(probe: dict, wait: float = 1.5, verbose: bool = False) -> ProbeResult:
    """Live-show flow tests. Each `flow` is a named integration sequence."""
    name = probe["name"]
    flow = probe.get("flow", "")
    if flow == "submit_prompt_check_kg":
        return _flow_submit_prompt_check_kg(probe, wait, verbose)
    if flow == "submit_prompt_check_snapshot":
        return _flow_submit_prompt_check_snapshot(probe, wait, verbose)
    if flow == "consent_off_does_not_appear":
        return _flow_consent_off_does_not_appear(probe, wait, verbose)
    if flow == "head_supported_on_snapshot":
        return _flow_head_supported_on_snapshot(probe, wait, verbose)
    if flow == "graph_redirect_preserves_query":
        return _flow_graph_redirect_preserves_query(probe, wait, verbose)
    return ProbeResult(name=name, ok=False, reason=f"unknown flow: {flow}")


_last_submit_time = 0.0
PROMPT_RATE_LIMIT_SECONDS = 4.0  # server enforces 3s; +1s buffer


_last_submit_status: tuple[int, str] = (0, "")  # for last-error introspection


def _submit_prompt(text: str, consent: dict) -> Optional[int]:
    """Rate-limit-aware POST /prompt. Retries once on 429. Sets _last_submit_status."""
    global _last_submit_time, _last_submit_status
    for attempt in range(2):
        elapsed = time.time() - _last_submit_time
        if elapsed < PROMPT_RATE_LIMIT_SECONDS:
            time.sleep(PROMPT_RATE_LIMIT_SECONDS - elapsed + 0.5)
        status, body = http_request(f"{PRIMARY}/prompt", "POST",
                                    body={"source": "typed", "text": text, "consent": consent})
        _last_submit_time = time.time()
        _last_submit_status = (status, body[:120])
        if status == 200:
            try:
                return json.loads(body).get("prompt_id")
            except json.JSONDecodeError:
                return None
        if status == 429:
            time.sleep(5)  # wait extra and retry once
            continue
        return None  # non-200, non-429: bail
    return None


def _flow_submit_prompt_check_kg(probe, wait, verbose) -> ProbeResult:
    name = probe["name"]
    text = probe.get("prompt_text", f"live-show test probe {int(time.time())}")
    consent_on = probe.get("consent_on", True)
    consent = {
        "visible_in_installation": consent_on,
        "included_in_clustering": consent_on,
        "quotable_by_agent": False,
        "available_post_show": False,
    }
    event = probe.get("event", "impact-2026")
    timeout = probe.get("must_appear_within_seconds", 30)

    pid = _submit_prompt(text, consent)
    if pid is None:
        return ProbeResult(name=name, ok=False,
                           reason=f"prompt submit failed (last_status={_last_submit_status[0]}, body={_last_submit_status[1]!r})")
    if verbose:
        print(f"    submitted prompt_id={pid}")

    deadline = time.time() + timeout
    while time.time() < deadline:
        status, body = http_request(f"{PRIMARY}/graph/event/{event}")
        if status == 200:
            try:
                d = json.loads(body)
                if any(n.get("id") == f"offering:{pid}" for n in d.get("nodes", [])):
                    return ProbeResult(name=name, ok=True,
                                       reply=f"offering:{pid} appeared in {event}")
            except json.JSONDecodeError:
                pass
        time.sleep(2)
    return ProbeResult(name=name, ok=False,
                       reason=f"offering:{pid} did not appear in /graph/event/{event} within {timeout}s")


def _flow_submit_prompt_check_snapshot(probe, wait, verbose) -> ProbeResult:
    name = probe["name"]
    text = probe.get("prompt_text", f"live-show snap test {int(time.time())}")
    consent = {"visible_in_installation": True, "included_in_clustering": True,
               "quotable_by_agent": False, "available_post_show": False}
    timeout = probe.get("must_appear_within_seconds", 60)

    pid = _submit_prompt(text, consent)
    if pid is None:
        return ProbeResult(name=name, ok=False,
                           reason=f"prompt submit failed (last_status={_last_submit_status[0]}, body={_last_submit_status[1]!r})")
    if verbose:
        print(f"    submitted prompt_id={pid}")

    deadline = time.time() + timeout
    while time.time() < deadline:
        status, _ = http_request(f"{PRIMARY}/td/snapshot/visitor/{pid}.jpg", method="HEAD")
        if status == 200:
            return ProbeResult(name=name, ok=True, reply=f"snapshot for {pid} HEAD=200")
        time.sleep(3)
    return ProbeResult(name=name, ok=False,
                       reason=f"snapshot for {pid} not ready within {timeout}s (last status={status})")


def _flow_consent_off_does_not_appear(probe, wait, verbose) -> ProbeResult:
    name = probe["name"]
    text = probe.get("prompt_text", f"consent-off test {int(time.time())}")
    consent = {"visible_in_installation": False, "included_in_clustering": True,
               "quotable_by_agent": False, "available_post_show": False}
    event = probe.get("event", "impact-2026")
    timeout = probe.get("check_after_seconds", 10)

    pid = _submit_prompt(text, consent)
    if pid is None:
        return ProbeResult(name=name, ok=False,
                           reason=f"prompt submit failed (last_status={_last_submit_status[0]}, body={_last_submit_status[1]!r})")

    time.sleep(timeout)
    status, body = http_request(f"{PRIMARY}/graph/event/{event}")
    if status != 200:
        return ProbeResult(name=name, ok=False, reason=f"/graph/event/ status {status}")
    try:
        d = json.loads(body)
        if any(n.get("id") == f"offering:{pid}" for n in d.get("nodes", [])):
            return ProbeResult(name=name, ok=False,
                               reason=f"offering:{pid} appeared despite visible_in_installation=false")
    except json.JSONDecodeError:
        pass
    return ProbeResult(name=name, ok=True,
                       reply=f"offering:{pid} correctly hidden")


def _flow_head_supported_on_snapshot(probe, wait, verbose) -> ProbeResult:
    """Submit + wait + verify HEAD returns 200 (the audit-found bug fix)."""
    name = probe["name"]
    text = f"head-support test {int(time.time())}"
    consent = {"visible_in_installation": True, "included_in_clustering": True,
               "quotable_by_agent": False, "available_post_show": False}
    pid = _submit_prompt(text, consent)
    if pid is None:
        return ProbeResult(name=name, ok=False,
                           reason=f"prompt submit failed (last_status={_last_submit_status[0]}, body={_last_submit_status[1]!r})")
    time.sleep(probe.get("wait_seconds", 12))
    status, _ = http_request(f"{PRIMARY}/td/snapshot/visitor/{pid}.jpg", method="HEAD")
    if status == 200:
        return ProbeResult(name=name, ok=True, reply=f"HEAD={status}")
    return ProbeResult(name=name, ok=False,
                       reason=f"expected HEAD 200, got {status} (visitor.html polling would 405-loop)")


def _flow_graph_redirect_preserves_query(probe, wait, verbose) -> ProbeResult:
    """Verify /graph?event=... 307s to /graph-assets/...?event=... (query preserved)."""
    name = probe["name"]
    qs = probe.get("query_string", "event=digital-ecologies-2026&focus=offering:1")
    req = urllib.request.Request(f"{PRIMARY}/graph?{qs}", method="GET")
    try:
        # Don't follow redirects — inspect Location header
        opener = urllib.request.build_opener(NoRedirectHandler())
        with opener.open(req, timeout=HTTP_TIMEOUT) as resp:
            location = resp.headers.get("Location", "")
            status = resp.status
    except urllib.error.HTTPError as e:
        location = e.headers.get("Location", "") if e.headers else ""
        status = e.code

    if status not in (301, 302, 307, 308):
        return ProbeResult(name=name, ok=False, reason=f"expected redirect, got {status}")
    if "?" not in location or qs.split("&")[0] not in location:
        return ProbeResult(name=name, ok=False,
                           reason=f"location missing query: {location}")
    return ProbeResult(name=name, ok=True, reply=f"{status} → {location}")


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_307(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)
    http_error_308 = http_error_307
    http_error_301 = http_error_307
    http_error_302 = http_error_307


# ---------------------------------------------------------------------------
# Suite runner — loads YAML, dispatches by category
# ---------------------------------------------------------------------------

# Map (suite type) → (runner function). Each runner takes (probe, suite_default_event, wait, verbose)
# returning ProbeResult.
RUNNERS: dict[str, Callable] = {
    "chat": run_chat_probe,
    "chat_multi_turn": run_multi_turn_probe,
    "kg": run_kg_probe,
    "live_show": run_live_show_probe,
}


def run_suite(yaml_path: Path, verbose: bool = False) -> SuiteResult:
    with open(yaml_path) as f:
        suite_data = yaml.safe_load(f)

    category = suite_data.get("category", yaml_path.stem)
    description = suite_data.get("description", "")
    suite_type = suite_data.get("type", "chat")
    default_event = suite_data.get("event", "impact-2026")
    wait = float(suite_data.get("wait_seconds", DEFAULT_WAIT))
    probes = suite_data.get("probes", [])

    result = SuiteResult(category=category, description=description)
    runner = RUNNERS.get(suite_type)
    if not runner:
        print(f"  ! unknown suite type: {suite_type}")
        return result

    print(f"\n=== {category} — {description} ===")
    for probe in probes:
        if suite_type in ("chat", "chat_multi_turn"):
            pr = runner(probe, default_event, wait, verbose)
        else:
            pr = runner(probe, wait, verbose)
        pr.category = category
        result.probe_results.append(pr)
        print(pr.summary())

    return result
