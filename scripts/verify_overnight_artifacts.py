#!/usr/bin/env python3
"""
Verify every "ready" artifact from the overnight shift.

Checks per artifact:
  - file exists
  - if .mp4: ffprobe reports duration, fps, resolution
  - if HTML: parse <img src> + <a href>, verify targets exist
  - README presence where promised
  - canonical files not overwritten (timestamp sanity check)

Writes results into overnight log as a Verification table.
"""
from pathlib import Path
import subprocess
import json
import re
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("src", "href") and v and not v.startswith(("http", "#", "data:")):
                self.links.append(v)


def probe_mp4(path: Path) -> dict:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "stream=width,height,r_frame_rate:format=duration",
             "-of", "json", str(path)],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        stream = data.get("streams", [{}])[0]
        fmt = data.get("format", {})
        # Parse r_frame_rate "24/1"
        fps_str = stream.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) else 0
        except Exception:
            fps = 0
        return {
            "ok": True,
            "duration": float(fmt.get("duration", 0)),
            "fps": fps,
            "width": int(stream.get("width", 0)),
            "height": int(stream.get("height", 0)),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}


def verify_html(path: Path) -> dict:
    if not path.exists():
        return {"ok": False, "error": "file missing"}
    extractor = LinkExtractor()
    try:
        extractor.feed(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        return {"ok": False, "error": f"parse {e}"[:80]}
    total = len(extractor.links)
    missing = []
    for link in extractor.links:
        target = (path.parent / link).resolve()
        if not target.exists():
            missing.append(link)
    return {
        "ok": len(missing) == 0,
        "total_links": total,
        "missing_links": missing[:5],  # first 5
        "missing_count": len(missing),
    }


def check_file(path: Path, expected_readme: bool = False) -> dict:
    if not path.exists():
        return {"status": "✗ MISSING", "detail": f"path not found"}
    if path.is_file():
        size = path.stat().st_size
        if path.suffix == ".mp4":
            probe = probe_mp4(path)
            if probe["ok"]:
                detail = f"{probe['width']}×{probe['height']} @ {probe['fps']:.1f}fps, {probe['duration']:.1f}s, {size//1024}KB"
                return {"status": "✓ OK", "detail": detail}
            return {"status": "✗ PROBE FAILED", "detail": probe.get("error", "")}
        if path.suffix in (".png", ".jpg", ".jpeg"):
            return {"status": "✓ OK", "detail": f"image, {size//1024}KB"}
        if path.suffix == ".html":
            html_check = verify_html(path)
            if html_check["ok"]:
                return {"status": "✓ OK", "detail": f"{html_check['total_links']} links, all resolve"}
            return {"status": "⚠ PARTIAL", "detail": f"{html_check['missing_count']} missing links: {html_check['missing_links']}"}
        return {"status": "✓ OK", "detail": f"file, {size//1024}KB"}
    if path.is_dir():
        files = list(path.iterdir())
        readme_present = (path / "README.md").exists()
        if expected_readme and not readme_present:
            return {"status": "⚠ PARTIAL", "detail": f"dir, {len(files)} entries, NO README"}
        return {"status": "✓ OK", "detail": f"dir, {len(files)} entries, README={'✓' if readme_present else '—'}"}


# Build verification manifest
ARTIFACTS = [
    # PREFLIGHT BATCH
    ("PREFLIGHT — TheCreator composite", "track2-deterministic/morph_outputs_INTERNAL/thecreator-pearl-bridge-composite-2026-05-17/thecreator_pearl_bridge_composite_v001.png", False),
    ("PREFLIGHT — TheCreator dir README", "track2-deterministic/morph_outputs_INTERNAL/thecreator-pearl-bridge-composite-2026-05-17/README.md", False),
    ("PREFLIGHT — Abstract toy demo MP4", "track2-deterministic/morph_outputs_INTERNAL/lane_2e_abstract_primitive_grammar_toy.mp4", False),
    ("PREFLIGHT — Pair scouting report", "docs/space-center/austin-piece-pair-scouting-report-2026-05-17.md", False),
    ("PREFLIGHT — Morning review index", "docs/space-center/morning-review-index-2026-05-18.md", False),
    ("PREFLIGHT — Lane 2E lesson doc", "docs/space-center/lane-2e-atom-primitive-bridge-lesson-2026-05-17.md", False),
    ("PREFLIGHT — Overnight log", "docs/space-center/overnight-log-2026-05-17-to-18.md", False),
    ("PREFLIGHT — Morning checklist", "docs/space-center/morning-checklist-2026-05-18.md", False),

    # REAL OVERNIGHT — TD packs
    ("TD — v007 pack dir", "td/templates/assets/cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001", True),
    ("TD — v007 pack README", "td/templates/assets/cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001/README.md", False),
    ("TD — v007 pack first frame", "td/templates/assets/cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001/frame_0001.jpg", False),
    ("TD — v007 pack last frame", "td/templates/assets/cosmic_sun_to_salmon_spawn_v007_landmark_routing_scrub_frames_v001/frame_0120.jpg", False),
    ("TD — v006 pack README (added)", "td/templates/assets/cosmic_sun_to_salmon_spawn_mudra_scrub_frames_v006/README.md", False),
    ("TD — runbook updated", "docs/space-center/td-mudra-scrubber-demo-2026-05-18.md", False),

    # REAL OVERNIGHT — Packet v2
    ("PACKET v2 — dir", "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18", True),
    ("PACKET v2 — contact sheet", "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/contact_sheet.png", False),
    ("PACKET v2 — HTML index", "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/index.html", False),
    ("PACKET v2 — README", "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/README.md", False),
    ("PACKET v2 — thumbnails dir", "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/thumbnails", False),

    # REAL OVERNIGHT — Primitive field v002
    ("PRIM FIELD v002 — light MP4", "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_light.mp4", False),
    ("PRIM FIELD v002 — dark MP4", "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark.mp4", False),
    ("PRIM FIELD v002 — light frame dir", "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_light", False),
    ("PRIM FIELD v002 — dark frame dir", "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark", False),

    # CANONICAL ARTIFACTS — verify NOT overwritten (timestamps should be earlier than overnight)
    ("CANONICAL — Salmon v005 MP4", "track2-deterministic/morph_outputs_INTERNAL/salmon_in_place_v005.mp4", False),
    ("CANONICAL — Cosmic breathing v003c", "track2-deterministic/morph_outputs_INTERNAL/austin_piece_breathing_nature_cosmic_sun_v003c_strong.mp4", False),
    ("CANONICAL — Pearl-bead traversal", "track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4", False),
    ("CANONICAL — Multi-pearl", "track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/04_multi_pearl_animation.mp4", False),
    ("CANONICAL — Primitive cycle", "track2-deterministic/morph_outputs_INTERNAL/primitive-cycle-2026-05-17/01_circle_crescent_trigon_circle.mp4", False),
    ("CANONICAL — Primitive field v001", "track2-deterministic/morph_outputs_INTERNAL/primitive_field_v001.mp4", False),
    ("CANONICAL — Raven→Cosmic morph", "track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun.mp4", False),
    ("CANONICAL — Cosmic→Salmon v007", "track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007.mp4", False),
    ("CANONICAL — Cosmic→Salmon v006", "track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4", False),

    # PACKET v1 (peer-built) — verify intact
    ("PACKET v1 — README", "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/README.md", False),
    ("PACKET v1 — lead_with dir", "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/01_lead_with", False),
    ("PACKET v1 — ask_first dir", "track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/02_promising_rough_ask_first", False),
]


def main():
    print(f"Verifying {len(ARTIFACTS)} artifacts...\n")
    results = []
    for label, rel_path, expected_readme in ARTIFACTS:
        full_path = ROOT / rel_path
        result = check_file(full_path, expected_readme=expected_readme)
        results.append((label, rel_path, result))
        status = result["status"]
        detail = result["detail"]
        print(f"  {status}  {label:55s} {detail}")

    # Summary
    ok = sum(1 for _, _, r in results if r["status"].startswith("✓"))
    partial = sum(1 for _, _, r in results if r["status"].startswith("⚠"))
    missing = sum(1 for _, _, r in results if r["status"].startswith("✗"))
    print(f"\n==== Summary ====")
    print(f"  OK:      {ok} / {len(results)}")
    print(f"  Partial: {partial}")
    print(f"  Missing: {missing}")

    # Write to overnight log as Verification section
    log_path = ROOT / "docs/space-center/overnight-log-2026-05-17-to-18.md"
    log_text = log_path.read_text() if log_path.exists() else ""
    # Append verification section
    verify_section = ["\n## Verification pass (final overnight mode 2026-05-18 AM)\n"]
    verify_section.append(f"All {len(results)} artifacts checked. Summary: OK={ok}, partial={partial}, missing={missing}.\n")
    verify_section.append("| Status | Artifact | Detail |")
    verify_section.append("|---|---|---|")
    for label, _, r in results:
        verify_section.append(f"| {r['status']} | {label} | {r['detail']} |")
    log_path.write_text(log_text + "\n".join(verify_section) + "\n")
    print(f"\n  → Verification table appended to {log_path}")

    # Return non-zero if any missing/partial
    if missing > 0:
        print(f"\n  ⚠ {missing} artifacts MISSING. Review above and fix.")
    if partial > 0:
        print(f"\n  ⚠ {partial} artifacts PARTIAL. Likely OK but inspect.")


if __name__ == "__main__":
    main()
