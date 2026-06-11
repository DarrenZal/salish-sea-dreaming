#!/usr/bin/env python3
"""SSD test runner — orchestrates probe suites against the live web app.

Usage:
  python scripts/test/run_tests.py                  # run all suites
  python scripts/test/run_tests.py chat             # all chat-* suites
  python scripts/test/run_tests.py chat_indigenomics_depth  # one suite by name
  python scripts/test/run_tests.py --list           # list available suites
  python scripts/test/run_tests.py --verbose chat   # verbose output

Env:
  PRIMARY_URL=https://salishseadreaming.art  # target host
  WAIT_SECONDS=7                              # default cooldown between probes
  RETRIES=3                                   # retry on empty/error replies
"""
import argparse
import sys
import time
from pathlib import Path

THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))

from framework import run_suite, SuiteResult  # noqa: E402

PROBES_DIR = THIS_DIR / "probes"


def discover_suites() -> list[Path]:
    """Return all YAML probe files in deterministic order."""
    return sorted(PROBES_DIR.glob("*.yaml"))


def filter_suites(all_suites: list[Path], pattern: str) -> list[Path]:
    """Filter by name match. Pattern can be a prefix ('chat') or full stem ('chat_identity')."""
    if not pattern or pattern == "all":
        return all_suites
    return [s for s in all_suites if pattern in s.stem]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("filter", nargs="?", default="", help="filter suites by name (substring match)")
    p.add_argument("--list", action="store_true", help="list available suites and exit")
    p.add_argument("--verbose", "-v", action="store_true", help="print full replies")
    p.add_argument("--stop-on-fail", action="store_true", help="stop at first suite with failures")
    args = p.parse_args()

    all_suites = discover_suites()
    if args.list:
        print("Available test suites:")
        for s in all_suites:
            print(f"  - {s.stem}")
        return 0

    suites_to_run = filter_suites(all_suites, args.filter)
    if not suites_to_run:
        print(f"No suites match: {args.filter!r}")
        print("Available:")
        for s in all_suites:
            print(f"  - {s.stem}")
        return 2

    print(f"=== SSD test framework ===")
    print(f"Running {len(suites_to_run)} suite(s): {[s.stem for s in suites_to_run]}")
    t0 = time.time()

    all_results: list[SuiteResult] = []
    for s in suites_to_run:
        result = run_suite(s, verbose=args.verbose)
        all_results.append(result)
        if args.stop_on_fail and result.failed > 0:
            print(f"\nStop-on-fail: {result.category} had {result.failed} failure(s)")
            break

    elapsed = time.time() - t0
    print(f"\n=== Summary ({elapsed:.1f}s) ===")
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    for r in all_results:
        line = f"  {r.category}: {r.passed} passed"
        if r.failed:
            line += f", {r.failed} FAILED"
        print(line)
        if r.failed:
            for pr in r.probe_results:
                if not pr.ok:
                    print(f"     ! {pr.name} — {pr.reason}")
    print(f"\n  TOTAL: {total_passed} passed, {total_failed} FAILED")
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
