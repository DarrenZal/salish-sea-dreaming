#!/usr/bin/env python3
"""Browser-level verifier for the Salish Sea Dreaming knowledge-graph panel.

Runs Playwright against the live KG page (default:
https://salishseadreaming.art/graph-assets/ssd-data-map.html) to assert
the ontology + directed-panel + predicate-coloured-edges behaviour
specified in `~/.claude/plans/edge-semantics-ontology.md`.

Exits non-zero if any requested check fails. Each assertion prints a
PASS: or FAIL: line so CI/dev logs stay readable.

Prerequisites (developer machine only — NOT required on poly):
    pip install playwright
    playwright install chromium

Usage:
    python scripts/verify_kg_panel.py --check all
    python scripts/verify_kg_panel.py --check typed-sections --base-url http://localhost:9000
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
ZOOM_PATH = REPO_ROOT / "static" / "ssd-data-map-zoom.json"
VOCAB_PATH = REPO_ROOT / "static" / "ssd-edge-vocab.json"

DEFAULT_BASE_URL = "https://salishseadreaming.art/"
GRAPH_PATH = "/graph-assets/ssd-data-map.html"
GRAPH_READY_MAX_WAIT_MS = 20_000
VISITOR_NODE_RUNTIME_WAIT_MS = 8_000

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _graph_url(base: str) -> str:
    parsed = urlparse(base)
    if not parsed.scheme:
        base = "http://" + base
    if not base.endswith("/"):
        base += "/"
    return urljoin(base, GRAPH_PATH.lstrip("/"))


def _wait_for_graph_ready(page):
    # The graph payload is large (1351 nodes on the live site); wait for
    # window.__ssd_kg to be populated and at least one hub label to exist.
    page.wait_for_function(
        "() => window.__ssd_kg && window.__ssd_kg.data"
        " && Array.isArray(window.__ssd_kg.data.links)"
        " && window.__ssd_kg.data.links.length > 0",
        timeout=GRAPH_READY_MAX_WAIT_MS,
    )


def _click_node_by_id(page, node_id: str) -> None:
    # The d3 drag system binds its click via mouseup/mousedown inside a
    # `.call(d3.drag()...)` chain; a synthetic `MouseEvent('click')` dispatched
    # onto the circle element doesn't trigger the drag's end handler. Instead
    # call the exposed handleNodeClick + showDetail directly — same code path
    # the drag handler invokes on line 955 / 979.
    ok = page.evaluate(
        """
        (id) => {
          const kg = window.__ssd_kg;
          if (!kg) return false;
          const node = kg.nodeById[id];
          if (!node) return false;
          kg.handleNodeClick(node);
          return true;
        }
        """,
        node_id,
    )
    if not ok:
        raise AssertionError(f"could not find node id={node_id!r} in window.__ssd_kg.nodeById")


def _expand_hub_for_node(page, target_id: str) -> None:
    # Make the target node visible by walking its cluster-hub / parent chain
    # and invoking handleNodeClick on the hub (which toggles expansion).
    page.evaluate(
        """
        (id) => {
          const kg = window.__ssd_kg;
          if (!kg) return;
          const node = kg.nodeById[id];
          if (!node) return;
          if (node.clusterHub && kg.nodeById[node.clusterHub]) {
            kg.handleNodeClick(kg.nodeById[node.clusterHub]);
          }
        }
        """,
        target_id,
    )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_untyped_fallback(page, base_url: str) -> list[str]:
    """AC4b — untyped edges render under data-section="related-to"."""
    errors: list[str] = []
    page.goto(_graph_url(base_url), wait_until="domcontentloaded")
    _wait_for_graph_ready(page)

    target = page.evaluate(
        """
        () => {
          const links = window.__ssd_kg.data.links;
          const u = links.find(l => !l.linkType);
          if (!u) return null;
          const sid = (l => (l.source && typeof l.source === 'object') ? l.source.id : l.source)(u);
          return sid;
        }
        """,
    )
    if target is None:
        print("SKIP: no untyped edges in current data — untyped-fallback check is a no-op")
        return errors

    # Surface any console errors during the interaction.
    console_errors: list[str] = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    _expand_hub_for_node(page, target)
    # Wait for the node to become visible (fill-opacity > 0.5).
    page.wait_for_function(
        """
        (id) => {
          const el = [...document.querySelectorAll('circle')]
            .find(c => c.__data__ && c.__data__.id === id);
          if (!el) return false;
          const fo = parseFloat(el.getAttribute('fill-opacity') || '0');
          return fo > 0.5;
        }
        """,
        arg=target,
        timeout=10_000,
    )
    _click_node_by_id(page, target)

    # Assert the related-to section exists with at least one child item.
    result = page.evaluate(
        """
        () => {
          const list = document.getElementById('detail-conn-list');
          if (!list) return {ok: false, reason: 'no #detail-conn-list'};
          const section = list.querySelector('[data-section="related-to"]');
          if (!section) return {ok: false, reason: 'no [data-section="related-to"]'};
          const items = section.querySelectorAll('.detail-conn-item');
          return {ok: items.length > 0, reason: `items=${items.length}`};
        }
        """,
    )
    if not result.get("ok"):
        errors.append(
            f"AC4b: untyped-fallback missing or empty for target={target!r} — {result.get('reason')}"
        )
    else:
        print(f"PASS: AC4b — untyped-fallback section rendered for {target!r} ({result['reason']})")

    if console_errors:
        errors.append("AC4b: console errors during untyped interaction: " + "; ".join(console_errors))
    return errors


def check_typed_sections(page, base_url: str) -> list[str]:
    """AC6 — panel shows ≥2 typed directed sections on hub:exhibition."""
    errors: list[str] = []
    page.goto(_graph_url(base_url), wait_until="domcontentloaded")
    _wait_for_graph_ready(page)

    _click_node_by_id(page, "hub:exhibition")

    result = page.evaluate(
        """
        () => {
          const list = document.getElementById('detail-conn-list');
          if (!list) return {ok: false, reason: 'no #detail-conn-list'};
          const sections = [...list.querySelectorAll('[data-section]')];
          const legacy = [...list.querySelectorAll('[data-section="connected-to"]')];
          const pattern = /^[a-z0-9-]+-(out|in)$|^related-to$/;
          const matched = sections
            .map(s => ({key: s.getAttribute('data-section'),
                        heading: (s.querySelector('.detail-connections-label')||{}).textContent || ''}))
            .filter(o => pattern.test(o.key));
          return {
            ok: true,
            sectionCount: sections.length,
            typed: matched,
            legacy: legacy.length,
          };
        }
        """,
    )
    if not result.get("ok"):
        errors.append(f"AC6: {result.get('reason')}")
        return errors

    if result["legacy"] > 0:
        errors.append(
            f"AC6: legacy [data-section=\"connected-to\"] still present ({result['legacy']} element(s))"
        )

    typed = result["typed"]
    if len([t for t in typed if t["key"].endswith("-out") or t["key"].endswith("-in")]) < 2:
        errors.append(
            f"AC6: expected ≥2 typed sections on hub:exhibition, found {len(typed)}: "
            + json.dumps(typed)
        )
    else:
        print(f"PASS: AC6 — hub:exhibition shows {len(typed)} typed section(s): "
              + ", ".join(t["key"] for t in typed))

    # Heading text must match vocab labels.
    vocab = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))
    for t in typed:
        key = t["key"]
        heading = (t["heading"] or "").strip()
        if key == "related-to":
            if heading.lower() != "related to":
                errors.append(f"AC6: related-to heading text={heading!r}, expected 'related to'")
            continue
        if "-" not in key:
            continue
        # Split on the LAST '-' so predicates containing '-' (e.g. "in-cluster")
        # survive: "in-cluster-out" → ("in-cluster", "out")
        idx = key.rfind("-")
        predicate = key[:idx]
        direction = key[idx + 1 :]
        vocab_entry = vocab.get(predicate)
        if not vocab_entry:
            errors.append(
                f"AC6: section data-section={key!r} has no matching predicate in vocab"
            )
            continue
        expected = vocab_entry["forward_label"] if direction == "out" else vocab_entry["inverse_label"]
        if heading != expected:
            errors.append(
                f"AC6: section {key!r} heading={heading!r}, expected {expected!r}"
            )
    return errors


def check_predicate_colors(page, base_url: str) -> list[str]:
    """AC7 — per-predicate edge-stroke uniformity + cross-hub consistency."""
    errors: list[str] = []
    page.goto(_graph_url(base_url), wait_until="domcontentloaded")
    _wait_for_graph_ready(page)

    vocab = json.loads(VOCAB_PATH.read_text(encoding="utf-8"))

    result = page.evaluate(
        """
        () => {
          const out = {};
          for (const line of document.querySelectorAll('line[data-link-type]')) {
            const lt = line.getAttribute('data-link-type') || '';
            const stroke = line.getAttribute('stroke') || line.style.stroke || '';
            if (!out[lt]) out[lt] = new Set();
            out[lt].add(stroke);
          }
          const serialisable = {};
          for (const [k, v] of Object.entries(out)) serialisable[k] = [...v];
          return serialisable;
        }
        """,
    )

    # Per-predicate uniformity (assertion #1 from AC7).
    for lt, expected in (
        (k, vocab[k]["color"]) for k in vocab
    ):
        colors = result.get(lt, [])
        if not colors:
            # Some vocab predicates may have zero edges in the current data
            # (e.g. in-cluster with zero visitor dreams). That's OK — we only
            # assert uniformity for predicates that have ≥1 edge rendered.
            continue
        if len(colors) != 1:
            errors.append(
                f"AC7.1: linkType={lt!r} has multiple stroke colours: {colors!r}"
            )
            continue
        if colors[0] != expected:
            errors.append(
                f"AC7.1: linkType={lt!r} stroke={colors[0]!r}, expected {expected!r}"
            )

    # Untyped-edge uniqueness (assertion from AC7: "Untyped edges may retain
    # source-hub color — they are tested only for 'not matching any predicate
    # color.'")
    untyped_colors = set(result.get("", []))
    predicate_colors = {v["color"] for v in vocab.values()}
    overlapping = untyped_colors & predicate_colors
    if overlapping:
        errors.append(
            f"AC7: untyped edges using predicate colours: {sorted(overlapping)!r}"
        )

    # Cross-hub consistency (assertion #2 from AC7). Pick a predicate with
    # edges originating from ≥ 2 different source hubs — `contains` is the
    # most populous predicate and covers ≥ 2 hubs in the live data.
    zoom = json.loads(ZOOM_PATH.read_text(encoding="utf-8"))
    hub_ids = {n["id"] for n in zoom["nodes"] if n.get("type") == "hub"}
    source_hubs_by_lt: dict[str, set[str]] = {}
    for l in zoom["links"]:
        lt = l.get("linkType") or ""
        if not lt:
            continue
        s = l["source"] if isinstance(l["source"], str) else l["source"].get("id")
        if s in hub_ids:
            source_hubs_by_lt.setdefault(lt, set()).add(s)

    chosen = next(
        (lt for lt, hubs in source_hubs_by_lt.items() if len(hubs) >= 2),
        None,
    )
    if chosen is None:
        print(
            "SKIP: AC7.2 — no predicate with ≥2 source hubs in zoom data; "
            "cross-hub consistency check is a no-op."
        )
    else:
        page_result = page.evaluate(
            """
            (args) => {
              const {lt, hubs} = args;
              const perHub = {};
              for (const line of document.querySelectorAll(`line[data-link-type="${lt}"]`)) {
                const d = line.__data__;
                if (!d) continue;
                const sid = (d.source && typeof d.source === 'object') ? d.source.id : d.source;
                if (!hubs.includes(sid)) continue;
                const stroke = line.getAttribute('stroke') || line.style.stroke || '';
                if (!perHub[sid]) perHub[sid] = new Set();
                perHub[sid].add(stroke);
              }
              const out = {};
              for (const [k, v] of Object.entries(perHub)) out[k] = [...v];
              return out;
            }
            """,
            {"lt": chosen, "hubs": sorted(source_hubs_by_lt[chosen])},
        )
        hub_colors = {c for colors in page_result.values() for c in colors}
        if len(hub_colors) > 1:
            errors.append(
                f"AC7.2: predicate {chosen!r} renders different colours across source hubs: "
                f"{page_result!r}"
            )
        else:
            print(f"PASS: AC7.2 — predicate {chosen!r} uses one colour across "
                  f"{len(page_result)} source hub(s)")

    if not errors:
        print("PASS: AC7 — predicate colours uniform + cross-hub consistent")
    return errors


def check_regressions(page, base_url: str) -> list[str]:
    """AC8 — invariants on hub labels, expand/collapse, deep-link round-trip."""
    errors: list[str] = []
    page.goto(_graph_url(base_url), wait_until="domcontentloaded")
    _wait_for_graph_ready(page)

    # Hub-label count invariant.
    r = page.evaluate(
        """
        () => {
          const labels = [...document.querySelectorAll('text')]
            .filter(t => {
              const d = t.__data__;
              return d && d.type === 'hub';
            });
          const hubNodes = window.__ssd_kg.data.nodes.filter(n => n.type === 'hub');
          return {labels: labels.length, hubs: hubNodes.length};
        }
        """,
    )
    if r["labels"] != r["hubs"]:
        errors.append(
            f"AC8.1: hub labels={r['labels']} but data.nodes hub count={r['hubs']}"
        )
    else:
        print(f"PASS: AC8.1 — hub labels ({r['labels']}) match hub node count")

    # Expand/collapse Visitor Dreams.
    before = page.evaluate(
        """
        () => {
          const rows = [];
          for (const c of document.querySelectorAll('circle')) {
            const d = c.__data__;
            if (!d || d.type !== 'cluster-summary') continue;
            rows.push({id: d.id, fo: parseFloat(c.getAttribute('fill-opacity') || '0')});
          }
          return rows;
        }
        """,
    )
    _click_node_by_id(page, "hub:visitor-dreams")
    time.sleep(1.5)
    after = page.evaluate(
        """
        () => {
          const rows = [];
          for (const c of document.querySelectorAll('circle')) {
            const d = c.__data__;
            if (!d || d.type !== 'cluster-summary') continue;
            rows.push({id: d.id, fo: parseFloat(c.getAttribute('fill-opacity') || '0')});
          }
          return rows;
        }
        """,
    )
    by_id_before = {r["id"]: r["fo"] for r in before}
    revealed = [r for r in after if by_id_before.get(r["id"], 0) < 0.1 and r["fo"] > 0.5]
    if len(revealed) < 1 and after:
        errors.append(
            f"AC8.2: expand — no cluster-summary transitioned fill-opacity <0.1 → >0.5 "
            f"(before={before!r} after={after!r})"
        )
    elif after:
        print(f"PASS: AC8.2 — {len(revealed)} cluster-summary node(s) revealed")

        # Click a revealed cluster → some visitor child should appear.
        cluster_id = revealed[0]["id"]
        _click_node_by_id(page, cluster_id)
        time.sleep(1.5)
        visitor_vis = page.evaluate(
            """
            () => {
              let count = 0;
              for (const c of document.querySelectorAll('circle')) {
                const d = c.__data__;
                if (!d || d.type !== 'visitor') continue;
                const fo = parseFloat(c.getAttribute('fill-opacity') || '0');
                if (fo > 0.5) count += 1;
              }
              return count;
            }
            """,
        )
        if visitor_vis < 1:
            errors.append(
                f"AC8.2: expand cluster {cluster_id!r} — zero visitor children visible"
            )
        else:
            print(f"PASS: AC8.2 — cluster {cluster_id!r} reveals {visitor_vis} visitor child(ren)")

        # Collapse the hub again by clicking it.
        _click_node_by_id(page, "hub:visitor-dreams")
        time.sleep(1.5)
        collapsed = page.evaluate(
            """
            () => {
              let visible = 0;
              for (const c of document.querySelectorAll('circle')) {
                const d = c.__data__;
                if (!d || d.type !== 'cluster-summary') continue;
                const fo = parseFloat(c.getAttribute('fill-opacity') || '0');
                if (fo > 0.5) visible += 1;
              }
              return visible;
            }
            """,
        )
        if collapsed > 0:
            errors.append(
                f"AC8.2: after re-click hub — {collapsed} cluster-summary still visible (expected 0)"
            )
        else:
            print("PASS: AC8.2 — hub re-click collapses cluster-summary nodes back")
    else:
        print(
            "SKIP: AC8.2 — no cluster-summary nodes present in live data; "
            "expand/collapse check is a no-op."
        )

    # Deep-link round-trip via dreamworld.html — use /dreams/3d to pick a node id.
    dreamworld_url = urljoin(
        _graph_url(base_url).replace(GRAPH_PATH, "/graph-assets/dreamworld.html"),
        "",
    )
    dreams_url = urljoin(_graph_url(base_url).replace(GRAPH_PATH, "/dreams/3d"), "")
    try:
        dreams_resp = page.request.get(dreams_url)
        if dreams_resp.ok:
            dreams = dreams_resp.json()
            first = (dreams.get("nodes") or [None])[0]
            if first is not None:
                deep = f"{dreamworld_url}?dream={first['id']}"
                page.goto(deep, wait_until="domcontentloaded")
                # Poll for #info-text content matching the node's text.
                for _ in range(10):
                    txt = page.evaluate(
                        "() => (document.getElementById('info-text') || {}).innerText || ''",
                    )
                    if first.get("text") and first["text"][:40] in (txt or ""):
                        print("PASS: AC8.3 — dreamworld deep-link populates #info-text")
                        break
                    time.sleep(0.5)
                else:
                    errors.append(
                        f"AC8.3: dreamworld deep-link did not populate #info-text for id={first.get('id')}"
                    )
            else:
                print("SKIP: AC8.3 — /dreams/3d returned no nodes")
        else:
            print(f"SKIP: AC8.3 — /dreams/3d returned HTTP {dreams_resp.status}")
    except Exception as e:  # pragma: no cover - defensive network
        print(f"SKIP: AC8.3 — /dreams/3d or dreamworld unreachable ({e})")

    return errors


def check_runtime_linktypes(page, base_url: str) -> list[str]:
    """AC4c — every runtime visitor link has linkType='in-cluster'."""
    errors: list[str] = []
    page.goto(_graph_url(base_url), wait_until="domcontentloaded")
    _wait_for_graph_ready(page)

    ok = page.evaluate(
        """
        () => {
          // Runtime visitor links always have at least one *visitor-side* end —
          // either a visitor-* dream id or a visitor-cluster-* cluster-summary id.
          // Static hub-to-hub signals (e.g. hub:machine → hub:visitor-dreams)
          // touch the hub but never carry a visitor-namespace id on either end,
          // so they're excluded by this rule. Per AC4c: those static edges
          // preserve their original linkType.
          const isRuntimeVisitorEnd = id => typeof id === 'string'
            && (id.startsWith('visitor-') || id.startsWith('visitor-cluster-'));
          const offending = window.__ssd_kg.data.links
            .filter(l => {
              const s = (l.source && typeof l.source === 'object') ? l.source.id : l.source;
              const t = (l.target && typeof l.target === 'object') ? l.target.id : l.target;
              if (!isRuntimeVisitorEnd(s) && !isRuntimeVisitorEnd(t)) return false;
              return l.linkType !== 'in-cluster';
            })
            .map(l => {
              const s = (l.source && typeof l.source === 'object') ? l.source.id : l.source;
              const t = (l.target && typeof l.target === 'object') ? l.target.id : l.target;
              return {s, t, lt: l.linkType || ''};
            });
          return offending;
        }
        """,
    )
    if ok:
        errors.append(f"AC4c (pre-event): {len(ok)} offending visitor link(s): {ok[:5]!r}")
    else:
        print("PASS: AC4c (pre-event) — all visitor-related links carry linkType='in-cluster'")

    # Inject a synthetic visitor event and re-check. Use a large id to avoid
    # clashing with any real prompts that might stream in during the check.
    page.evaluate(
        """
        () => {
          const fake = {
            id: 999999,
            text: 'verify_kg_panel synthetic visitor',
            source: 'verifier',
            color: '#7fffb2',
          };
          window.__ssd_kg.addVisitorNode(fake);
        }
        """,
    )
    time.sleep(0.5)
    ok2 = page.evaluate(
        """
        () => {
          const isRuntimeVisitorEnd = id => typeof id === 'string'
            && (id.startsWith('visitor-') || id.startsWith('visitor-cluster-'));
          return window.__ssd_kg.data.links
            .filter(l => {
              const s = (l.source && typeof l.source === 'object') ? l.source.id : l.source;
              const t = (l.target && typeof l.target === 'object') ? l.target.id : l.target;
              if (!isRuntimeVisitorEnd(s) && !isRuntimeVisitorEnd(t)) return false;
              return l.linkType !== 'in-cluster';
            })
            .map(l => {
              const s = (l.source && typeof l.source === 'object') ? l.source.id : l.source;
              const t = (l.target && typeof l.target === 'object') ? l.target.id : l.target;
              return {s, t, lt: l.linkType || ''};
            });
        }
        """,
    )
    if ok2:
        errors.append(f"AC4c (post-event): {len(ok2)} offending links after synthetic visitor: {ok2[:5]!r}")
    else:
        print("PASS: AC4c (post-event) — synthetic visitor link carries linkType='in-cluster'")
    return errors


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


CHECKS = {
    "untyped-fallback": check_untyped_fallback,
    "typed-sections": check_typed_sections,
    "predicate-colors": check_predicate_colors,
    "regressions": check_regressions,
    "runtime-linktypes": check_runtime_linktypes,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        default="all",
        help="check name (untyped-fallback, typed-sections, predicate-colors, "
        "regressions, runtime-linktypes, or 'all')",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="origin hosting /graph-assets/ssd-data-map.html (default: live site)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="run Chromium with a visible window (for debugging)",
    )
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        print(
            "ERROR: playwright is not installed. Install with:\n"
            "  pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return 2

    if not VOCAB_PATH.exists():
        print(f"ERROR: edge vocab not found at {VOCAB_PATH}. Run scripts/emit_edge_vocab.py first.",
              file=sys.stderr)
        return 2

    if args.check == "all":
        ordered = list(CHECKS.keys())
    elif args.check in CHECKS:
        ordered = [args.check]
    else:
        print(f"ERROR: unknown --check {args.check!r}. Known: {sorted(CHECKS)}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        try:
            context = browser.new_context(viewport={"width": 1400, "height": 900})
            page = context.new_page()
            for name in ordered:
                print(f"\n=== {name} ===")
                try:
                    errs = CHECKS[name](page, args.base_url)
                except AssertionError as e:
                    errs = [f"{name}: assertion failed — {e}"]
                except Exception as e:  # noqa: BLE001
                    errs = [f"{name}: unexpected error — {type(e).__name__}: {e}"]
                if errs:
                    for msg in errs:
                        print(f"FAIL: {msg}")
                    all_errors.extend(errs)
        finally:
            browser.close()

    print()
    if all_errors:
        print(f"TOTAL FAILURES: {len(all_errors)}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
