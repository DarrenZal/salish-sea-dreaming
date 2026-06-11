#!/usr/bin/env python3
"""
Build a single morning demo folder with 4 categories.

Per overnight final mode #2: one folder operator opens first.
Subfolders + symlinks (preserves single source of truth):
  1_watch_first/       canonical results to view first
  2_supporting/        low-cultural-load supporting artifacts
  3_internal_ask_first/ Austin-derived rough or ask-first
  4_failed_controls/    preserved labeled — DO NOT promote

Each subfolder has README.md with one-line framing per artifact.
Top-level README + HTML index for full navigation.
"""
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "track2-deterministic/morph_outputs_INTERNAL/morning-demo-folder-2026-05-18"


# Each entry: (src_relative_to_ROOT, dst_name, one_line_framing)
WATCH_FIRST = [
    ("track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/contact_sheet.png",
     "01_packet_v2_CONTACT_SHEET.png",
     "Open first. 15 artifacts at a glance, category-colored borders."),
    ("track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/index.html",
     "02_packet_v2_INDEX.html",
     "Same info as contact sheet but clickable. Per-artifact framing + cultural guardrails."),
    ("track2-deterministic/morph_outputs_INTERNAL/salmon_in_place_v005.mp4",
     "03_salmon_v005_CANONICAL.mp4",
     "Canonical Salmon 'alive within yin-yang' mechanic. Per-output Austin OK required."),
    ("track2-deterministic/morph_outputs_INTERNAL/austin_piece_breathing_nature_cosmic_sun_v003c_strong.mp4",
     "04_cosmic_breathing_v003c_CANONICAL.mp4",
     "Canonical Cosmic_Sun breathing. Rays + eyes only, shimmer reads as spirit/energy."),
    ("track2-deterministic/morph_outputs_INTERNAL/thecreator-pearl-bridge-composite-2026-05-17/thecreator_pearl_bridge_composite_v001.png",
     "05_thecreator_pearl_bridge_NEW_OBSERVATION.png",
     "NEW overnight. Visual resonance observation — NOT cosmological claim. Needs Austin interpretation."),
    ("track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4",
     "06_pearl_bead_single_traversal.mp4",
     "Pearl-bead-on-edges core concept. Single pearl carrying morph."),
]

SUPPORTING = [
    ("track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_light.mp4",
     "01_primitive_field_v002_LIGHT_NEW.mp4",
     "NEW overnight. 60 atoms curl-noise drift, cream BG. Zero cultural risk."),
    ("track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark.mp4",
     "02_primitive_field_v002_DARK_NEW.mp4",
     "NEW overnight. Same atoms on deep blue BG. Underwater feel."),
    ("track2-deterministic/morph_outputs_INTERNAL/primitive_field_v001.mp4",
     "03_primitive_field_v001.mp4",
     "Original primitive field — 40-atom grid sweep. Already packet-locked."),
    ("track2-deterministic/morph_outputs_INTERNAL/primitive-cycle-2026-05-17/01_circle_crescent_trigon_circle.mp4",
     "04_primitive_cycle_18s.mp4",
     "18-sec continuous Circle→Crescent→Trigon→Circle cycle. Foundational grammar."),
    ("track2-deterministic/morph_outputs_INTERNAL/multi-pearl-prototype-2026-05-17/04_multi_pearl_animation.mp4",
     "05_multi_pearl_3node_2pearl.mp4",
     "Polyphonic pearl-bead-on-edges. 3-node triangle, 2 simultaneous pearls."),
    ("track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4",
     "06_raven_to_cosmic_clean_morph.mp4",
     "Preferred deterministic Raven→Cosmic baseline. Same 108×108 viewBox; exact verified training-JPG endpoints; no SD/LoRA."),
    ("track2-deterministic/morph_outputs_INTERNAL/lane_2e_abstract_primitive_grammar_toy.mp4",
     "07_abstract_primitive_bridge_TOY.mp4",
     "NEW overnight. 12 primitives demonstrating Lane 2E grammar without Austin assets."),
    ("track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/01_progression_3stage.png",
     "08_pearl_bead_3stage_diagram.png",
     "Static diagram: source → mid-morph → destination."),
    ("track2-deterministic/morph_outputs/raven_sun_to_cosmic_sun.mp4",
     "09_raven_to_cosmic_OLD_SHAPE_MORPH_SUPERSEDED_CONTROL.mp4",
     "Superseded/control Raven→Cosmic shape morph. Preserved for comparison; do not lead with this over endpoint_correct_v001."),
]

INTERNAL_ASK_FIRST = [
    ("track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_landmark_atom_routing_v007.mp4",
     "01_cosmic_to_salmon_v007_landmark_routing.mp4",
     "Cross-piece morph via Lane 2E routing. Smoother than v006. Per-output Austin OK."),
    ("track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4",
     "02_cosmic_to_salmon_v006_endpoint_correct.mp4",
     "Cross-piece morph older sibling of v007. Retained as control."),
    ("track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/02_promising_rough_ask_first/02_raven_sun_to_salmon_raw_shape_morph_rough.mp4",
     "03_raven_to_salmon_RAW_ROUGH.mp4",
     "Rough raw morph; known start z-order, endpoint drift, seam artifacts."),
    ("track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/02_promising_rough_ask_first/03_cosmic_sun_to_salmon_raw_shape_morph_rough.mp4",
     "04_cosmic_to_salmon_RAW_ROUGH.mp4",
     "Earlier rough Cosmic→Salmon. Superseded by v006/v007."),
    ("track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/02_promising_rough_ask_first/04_wolf_whorl_to_salmon_high_load_do_not_lead.mp4",
     "05_wolf_to_salmon_HIGH_LOAD.mp4",
     "HIGH cultural load. Austin discussion BEFORE any external use. Do not lead."),
    ("track2-deterministic/morph_outputs_INTERNAL/lane_2e_atom_primitive_bridge_poc_v002_spatial_pairs.mp4",
     "06_lane_2e_poc_v002_spatial.mp4",
     "Lane 2E POC with spatial pairs. Mechanism shown but too sparse to communicate. Concept locked as rule not visual."),
]

FAILED_CONTROLS = [
    ("track2-deterministic/morph_outputs_INTERNAL/salmon_line_swim_v003_tps_straightened.mp4",
     "01_salmon_line_swim_v003_TPS_THIN_SNAKE.mp4",
     "TPS body straighten over-warped → thin snake. Architecture failed."),
    ("track2-deterministic/morph_outputs_INTERNAL/salmon_line_swim_v004_width_anchored_tps.mp4",
     "02_salmon_line_swim_v004_TPS_WIDTH_DEFORMED.mp4",
     "TPS with width anchors → still globally deformed. Mechanism wrong."),
    ("track2-deterministic/morph_outputs_INTERNAL/salmon_circle_chase_v001.mp4",
     "03_salmon_circle_chase_v001_GEOMETRY_FAIL.mp4",
     "Geometry mismatch: body length vs orbit radius. Can't fit canvas."),
    ("track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_endpoint_emerge_v001.mp4",
     "04_endpoint_emerge_v001_LUMA_BLEND.mp4",
     "Image-level luma blend didn't solve atom-level z-order issues. Preserved as control."),
    ("track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_roe_particle_field_v002.mp4",
     "05_roe_particle_v002_FULL_PIECE_CROSSFADE.mp4",
     "Wrong architecture (whole-piece crossfade). Codex worker owns v003 per spec."),
    ("track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_CURRENT_2026-05-17-1259_crossdissolve-regressed.mp4",
     "06_crossdissolve_regression_DONT_DO_THIS.mp4",
     "Cross-dissolve regression. Killed primitive-motion. Preserved as anti-pattern."),
    ("track2-deterministic/morph_outputs_INTERNAL/austin_006_salmon_body_articulation_v002.mp4",
     "07_salmon_big_shapes_v002_SPRITE_TRANSLATION.mp4",
     "Sprite-based body articulation. Operator: 'disconnected tails, sliding chunks.' Architecture failed."),
]


def make_symlink(src_rel: str, dst: Path) -> bool:
    src = ROOT / src_rel
    if not src.exists():
        print(f"  ✗ source missing: {src_rel}")
        return False
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    # Use relative symlink so the demo folder is portable
    rel_target = os.path.relpath(src, dst.parent)
    dst.symlink_to(rel_target)
    return True


def write_subfolder_readme(folder: Path, title: str, entries: list, category_note: str):
    lines = [f"# {title}", "", category_note, ""]
    lines.append("## Contents (one-line framing per artifact)")
    lines.append("")
    for i, (_, dst_name, framing) in enumerate(entries, 1):
        lines.append(f"### {i}. {dst_name}")
        lines.append(f"")
        lines.append(f"{framing}")
        lines.append("")
    (folder / "README.md").write_text("\n".join(lines))


def main():
    if FOLDER.exists():
        # Clean previous (only symlinks/READMEs — no canonical files)
        import shutil
        shutil.rmtree(FOLDER)
    FOLDER.mkdir(parents=True)

    categories = [
        ("1_watch_first", "1. Watch first",
         "**Canonical results from today/overnight. Open in order.** "
         "Includes the packet v2 contact sheet (single-glance overview) "
         "and the two locked canonical animations (Salmon v005, Cosmic breathing v003c).",
         WATCH_FIRST),
        ("2_supporting", "2. Supporting artifacts",
         "**Low-cultural-load supporting visuals.** Primitive grammar work "
         "(cycle, fields, abstract bridge toy), pearl-bead concept clips. "
         "Safe to show in any context.",
         SUPPORTING),
        ("3_internal_ask_first", "3. Internal — ask first",
         "**Austin-derived rough or culturally-loaded.** Cross-piece morphs "
         "needing per-output Austin OK. Wolf↔Salmon needs Austin discussion "
         "BEFORE any external use.",
         INTERNAL_ASK_FIRST),
        ("4_failed_controls", "4. Failed controls (DO NOT promote)",
         "**Labeled failures preserved for context.** Salmon line-swim "
         "(TPS, rectification, geometry) failed because formline salmon "
         "isn't a continuous tube. Cross-dissolve regression preserved as "
         "anti-pattern. Sprite-translation big-shapes preserved as 'why "
         "swim rig was needed.'",
         FAILED_CONTROLS),
    ]

    summary_lines = []
    for sub, title, note, entries in categories:
        sub_folder = FOLDER / sub
        sub_folder.mkdir(parents=True, exist_ok=True)
        print(f"\n{title}:")
        ok = 0
        for src_rel, dst_name, _ in entries:
            dst = sub_folder / dst_name
            if make_symlink(src_rel, dst):
                ok += 1
                print(f"  ✓ {dst_name}")
        write_subfolder_readme(sub_folder, title, entries, note)
        summary_lines.append((sub, title, ok, len(entries)))

    # Top-level README
    top_readme = ["# Morning demo folder — 2026-05-18", "",
                  "**Single entry point for morning review.** Open this folder's index.html "
                  "or browse the 4 subfolders in order.", "",
                  "## Structure", ""]
    for sub, title, ok, total in summary_lines:
        top_readme.append(f"- [{sub}/]({sub}/) — {title} — {ok}/{total} artifacts symlinked")
    top_readme += ["",
                   "## How to use",
                   "",
                   "1. **First 30 seconds**: open `1_watch_first/01_packet_v2_CONTACT_SHEET.png` for one-glance review.",
                   "2. **Next 2 minutes**: watch the 4 numbered MP4s/PNGs in `1_watch_first/` in order.",
                   "3. **Show to Pravin**: items 1-4 of `1_watch_first/` + items 1-3 of `2_supporting/`.",
                   "4. **Show to Austin (exploratory)**: items 3-5 of `1_watch_first/` + items 1, 2, 6 of `3_internal_ask_first/`.",
                   "5. **DO NOT show anyone**: `4_failed_controls/` — preserved for internal reference only.",
                   "",
                   "## Cultural guardrails",
                   "",
                   "- All Austin-derived outputs require per-output Austin OK before audience-facing use.",
                   "- Wolf↔Salmon (`3_internal_ask_first/05_*`) requires Austin discussion BEFORE any external use, even internal-team.",
                   "- TheCreator pearl-bridge composite (`1_watch_first/05_*`) is visual resonance OBSERVATION, NOT cosmological claim.",
                   "",
                   "## Reference",
                   "",
                   "- Full overnight log: `docs/space-center/overnight-log-2026-05-17-to-18.md`",
                   "- Morning checklist: `docs/space-center/morning-checklist-2026-05-18.md`",
                   "- Packet v1 (source of truth): `track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-2026-05-17/`",
                   "- Packet v2 (with thumbnails): `track2-deterministic/morph_outputs_INTERNAL/austin-team-exploration-review-v2-2026-05-18/`",
                   ""]
    (FOLDER / "README.md").write_text("\n".join(top_readme))

    # Top-level HTML index
    html = ['<!DOCTYPE html>', '<html><head><meta charset="utf-8">',
            '<title>Morning Demo Folder — 2026-05-18</title>',
            '<style>',
            'body { font-family: -apple-system, sans-serif; max-width: 1100px; margin: 20px auto; padding: 24px; background: #f5f0e4; }',
            'h1 { color: #2a2a2a; } h2 { margin-top: 30px; color: #4a3a20; }',
            '.cat { background: white; padding: 16px; margin: 12px 0; border-radius: 6px; border-left: 4px solid #999; }',
            '.cat.c1 { border-left-color: #3c8c3c; }',
            '.cat.c2 { border-left-color: #3c64a0; }',
            '.cat.c3 { border-left-color: #c88228; }',
            '.cat.c4 { border-left-color: #b43c3c; }',
            'ul { margin: 8px 0 0 0; padding-left: 22px; }',
            'li { margin: 4px 0; }',
            '.note { font-size: 13px; color: #666; font-style: italic; margin: 4px 0; }',
            '</style></head><body>',
            '<h1>Morning Demo Folder — 2026-05-18</h1>',
            '<p>Single entry point. 4 categories, each subfolder has README + symlinked artifacts.</p>',
            '<p><strong>First 30 sec</strong>: open <a href="1_watch_first/01_packet_v2_CONTACT_SHEET.png">1_watch_first/01_packet_v2_CONTACT_SHEET.png</a> for one-glance review.</p>',
            ]
    for ci, (sub, title, note, entries) in enumerate(categories, 1):
        html.append(f'<div class="cat c{ci}"><h2>{title}</h2>')
        html.append(f'<p class="note">{note}</p>')
        html.append('<ul>')
        for src_rel, dst_name, framing in entries:
            html.append(f'<li><a href="{sub}/{dst_name}">{dst_name}</a> — {framing}</li>')
        html.append('</ul></div>')
    html += ['<hr><p style="color:#666;font-size:12px;">Built overnight 2026-05-18 AM via <code>scripts/build_morning_demo_folder.py</code>.</p>',
             '</body></html>']
    (FOLDER / "index.html").write_text("\n".join(html))

    print(f"\n→ {FOLDER}")
    print(f"  Open first: {FOLDER}/README.md or {FOLDER}/index.html")


if __name__ == "__main__":
    main()
