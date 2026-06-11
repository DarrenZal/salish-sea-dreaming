#!/usr/bin/env python3
"""Build a tiny "stable palette review" folder for Darren's Pravin call.

Per operator brief 2026-05-18 PM: Pravin asked for stable palette + production-
quality coherence. STOP new morph experiments.

Categories per operator:
  1. PRODUCTION FLOOR — the stable palette (Pravin-facing)
  2. INTERNAL AUSTIN REVIEW — needs Austin per-output OK; sketch tray
  3. SALMON + REAL FOOTAGE TESTS — internal compositing proofs

No failed controls, no Bee variants, no Agent 3 LoRA footage in lead section.

Screen-share friendly: one folder, README + HTML index, concise labels.
"""
from pathlib import Path
import os
import shutil

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / "track2-deterministic/morph_outputs_INTERNAL/stable-palette-review-2026-05-18"


PRODUCTION_FLOOR = [
    ("media/hero-subclips/H6_kelp_forest_floor_4k.mp4",
     "01_H6_kelp_4k.mp4",
     "H6 Kelp forest floor — 4K Moonfish hero footage. Ready for Resolume."),
    ("track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_dark.mp4",
     "02_primitive_field_DARK.mp4",
     "60 atoms curl-noise drift on deep blue BG. Underwater ambient layer. ZERO cultural load."),
    ("track2-deterministic/morph_outputs_INTERNAL/primitive_field_v002_flocking_light.mp4",
     "03_primitive_field_LIGHT.mp4",
     "Same atoms on cream BG. Lighter ambient/transition layer. ZERO cultural load."),
    ("track2-deterministic/morph_outputs_INTERNAL/raven_sun_to_cosmic_sun_endpoint_correct_v001.mp4",
     "04_raven_to_cosmic_endpoint_correct.mp4",
     "Preferred deterministic Raven→Cosmic baseline. Exact verified training-JPG endpoints. No SD/LoRA."),
    ("track2-deterministic/morph_outputs_INTERNAL/cosmic_sun_to_salmon_spawn_raw_motion_endpoint_correct_v006_remove_dest_background_rect.mp4",
     "05_cosmic_to_salmon_v006_HERO_CANDIDATE.mp4",
     "Strongest hero transition so far. Start/end match source pieces; primitive motion reads strongly. Internal until Austin OK."),
    ("td/templates/assets/raven_sun_to_cosmic_sun_endpoint_correct_v001_scrub_preview.mp4",
     "06_TD_raven_to_cosmic_scrub_preview.mp4",
     "TouchDesigner scrubber preview — same Raven→Cosmic clip wired to gesture/control input."),
    ("track2-deterministic/morph_outputs_INTERNAL/resolume-wide-wall-plan-2026-05-18/resolume_wide_wall_layout_options_contact_sheet_3840x2160.png",
     "07_wide_wall_layout_contact_sheet.png",
     "Resolume wide-wall layout options contact sheet (3840×2160). Layout reference for Pravin."),
    ("track2-deterministic/morph_outputs_INTERNAL/wide_wall_mvp_loop_v001/wide_wall_mvp_loop_v001_3840x2160_20sec.mp4",
     "08_wide_wall_MVP_loop_v001_3840x2160_20sec.mp4",
     "NEW one-clean-version wide-wall proof: H6 4K background + low-opacity primitive field dark + large centered Cosmic→Salmon v006 insert. Internal until Austin OK."),
]

INTERNAL_AUSTIN_REVIEW = [
    ("track2-deterministic/morph_outputs_INTERNAL/salmon_in_place_v005.mp4",
     "01_salmon_in_place_v005.mp4",
     "Canonical Salmon 'alive within yin-yang' mechanic. Per-output Austin OK required."),
    ("track2-deterministic/morph_outputs_INTERNAL/pearl-bead-prototype-2026-05-17/04_pearl_bead_traversal.mp4",
     "02_pearl_bead_traversal.mp4",
     "Pearl-bead-on-edges concept. Single pearl carrying morph along graph edge."),
]

SALMON_FOOTAGE_TESTS = [
    ("track2-deterministic/morph_outputs_INTERNAL/salmon_spawn_footage_composite_v001/01_salmon_spawn_over_h1_salmon_school_overlay_v001.mp4",
     "01_salmon_spawn_over_h1_salmon_school_overlay_v001.mp4",
     "INTERNAL compositing proof: Austin Salmon Spawn Eggs geometry as a transparent overlay over H1 salmon-school footage. Austin OK required."),
    ("track2-deterministic/morph_outputs_INTERNAL/salmon_spawn_footage_composite_v001/02_salmon_spawn_h6_kelp_inside_forms_mask_window_v001.mp4",
     "02_salmon_spawn_h6_kelp_inside_forms_mask_window_v001.mp4",
     "INTERNAL compositing proof: H6 kelp footage visible inside Austin salmon/roe forms as masks/windows. Austin OK required."),
    ("track2-deterministic/morph_outputs_INTERNAL/salmon_spawn_footage_composite_v001/03_salmon_spawn_footage_overlay_mask_3up_comparison_v001.mp4",
     "03_salmon_spawn_footage_overlay_mask_3up_comparison_v001.mp4",
     "INTERNAL 3-up comparison: source H1 footage / overlay / mask-window result. Austin OK required."),
]


def make_symlink(src_rel: str, dst: Path) -> bool:
    src = ROOT / src_rel
    if not src.exists():
        print(f"  ✗ missing: {src_rel}")
        return False
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    rel = os.path.relpath(src, dst.parent)
    dst.symlink_to(rel)
    return True


def write_subfolder_readme(folder: Path, title: str, entries: list, note: str):
    lines = [f"# {title}", "", note, "", "## Contents", ""]
    for i, (_, dst_name, framing) in enumerate(entries, 1):
        lines.append(f"### {i}. {dst_name}")
        lines.append("")
        lines.append(framing)
        lines.append("")
    (folder / "README.md").write_text("\n".join(lines))


def main():
    if FOLDER.exists():
        shutil.rmtree(FOLDER)
    FOLDER.mkdir(parents=True)

    cats = [
        ("1_production_floor", "1. Production floor — stable palette",
         "**Pravin-facing review set.** Stable composable layers first, plus Austin-derived "
         "hero candidates clearly marked internal until Austin OK. This is for production-floor "
         "composition discussion, not public approval.",
         PRODUCTION_FLOOR),
        ("2_internal_austin_review", "2. Internal Austin review — sketch tray",
         "**Per-output Austin OK required.** Strong artifacts that need Austin's specific approval "
         "before any audience-facing use. Shown to Pravin only for context on what's developing.",
         INTERNAL_AUSTIN_REVIEW),
        ("3_salmon_footage_tests", "3. Salmon + real footage tests — internal compositing proofs",
         "**INTERNAL / Austin OK required.** Deterministic Salmon + real-footage composites. "
         "These are not production-floor items yet; they answer whether Austin geometry can act "
         "as composable material over real footage.",
         SALMON_FOOTAGE_TESTS),
    ]

    summary = []
    for sub, title, note, entries in cats:
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
        summary.append((sub, title, ok, len(entries)))

    # Top-level README
    readme = [
        "# Stable palette review — 2026-05-18",
        "",
        "**For Pravin call (stable-palette + production-quality coherence).**",
        "",
        "Open `index.html` for screen-share. Or browse the 3 subfolders directly.",
        "",
        "## Structure",
        "",
    ]
    for sub, title, ok, total in summary:
        readme.append(f"- [{sub}/]({sub}/) — {title} — {ok}/{total} artifacts")
    readme += [
        "",
        "## What this is / isn't",
        "",
        "- **IS**: stable palette artifacts for Resolume / TD / wide-wall layout decisions, with Austin-derived candidates clearly marked internal until Austin OK.",
        "- **IS NOT**: a full experiment review. No failed controls. No Bee variants. No Lane 2E POCs.",
        "- **IS NOT**: Agent 3 LoRA footage review. Keep LoRA footage tests technical-only, not in the main lead section.",
        "- For a fuller exploration packet see `morning-demo-folder-2026-05-18/`.",
        "",
        "## Cultural floor reminder",
        "",
        "- Low-cultural-load production-floor ingredients: Moonfish footage and abstract primitive fields.",
        "- Austin-derived production-floor candidates (Raven→Cosmic, Cosmic→Salmon, and the wide-wall MVP loop) REQUIRE per-output Austin OK before audience-facing use.",
        "- Internal-Austin-review items REQUIRE per-output Austin OK before audience-facing use.",
        "- Salmon + real footage tests REQUIRE per-output Austin OK and should not be moved into production floor yet.",
        "",
        "## Reference",
        "",
        "- Compact Pravin/Austin review index (full top-6): `docs/space-center/pravin-austin-compact-review-index-2026-05-18.md`",
        "- Morning checklist: `docs/space-center/morning-checklist-2026-05-18.md`",
    ]
    (FOLDER / "README.md").write_text("\n".join(readme))

    # HTML index — screen-share friendly
    html = ['<!DOCTYPE html>', '<html><head><meta charset="utf-8">',
            '<title>Stable palette review — 2026-05-18</title>',
            '<style>',
            'body { font-family: -apple-system, sans-serif; max-width: 1000px; margin: 20px auto; padding: 20px; background: #f5f0e4; }',
            'h1 { color: #2a2a2a; margin-bottom: 4px; } h2 { color: #4a3a20; margin-top: 28px; }',
            '.subtitle { color: #888; font-size: 13px; margin-bottom: 20px; }',
            '.cat { background: white; padding: 18px; margin: 14px 0; border-radius: 6px; border-left: 4px solid #999; }',
            '.cat.c1 { border-left-color: #3c8c3c; }',
            '.cat.c2 { border-left-color: #c88228; }',
            '.cat.c3 { border-left-color: #3c64a0; }',
            '.cat .note { color: #555; font-size: 13px; margin: 4px 0 10px 0; font-style: italic; }',
            'ul { margin: 8px 0 0 0; padding-left: 22px; }',
            'li { margin: 6px 0; }',
            'a { color: #2a5a8a; text-decoration: none; font-weight: 500; }',
            'a:hover { text-decoration: underline; }',
            '.label { color: #555; font-size: 13px; }',
            '.banner { background: #fff8e6; border-left: 4px solid #c8aa50; padding: 10px 14px; margin: 12px 0; font-size: 14px; }',
            '</style></head><body>',
            '<h1>Stable palette review</h1>',
            '<div class="subtitle">2026-05-18 · For Pravin call · Screen-share friendly</div>',
            '<div class="banner"><strong>Pravin asked for stable palette + production-quality coherence.</strong> '
            'These are the production-stable artifacts (cat 1), internal-Austin-review sketch tray (cat 2), '
            'and separate Salmon + real footage compositing proofs (cat 3). '
            'No failed controls. No Bee variants. No Lane 2E POCs. No Agent 3 LoRA footage in the lead section.</div>',
            ]
    for ci, (sub, title, note, entries) in enumerate(cats, 1):
        html.append(f'<div class="cat c{ci}"><h2>{title}</h2>')
        html.append(f'<div class="note">{note}</div>')
        html.append('<ul>')
        for src_rel, dst_name, framing in entries:
            html.append(f'<li><a href="{sub}/{dst_name}">{dst_name}</a> — <span class="label">{framing}</span></li>')
        html.append('</ul></div>')
    html += ['<hr style="margin-top:30px;border:none;border-top:1px solid #ddd;">',
             '<p style="color:#888;font-size:12px;">Built 2026-05-18 PM via <code>scripts/build_stable_palette_review.py</code>. ',
             'For fuller exploration packet see <code>morning-demo-folder-2026-05-18/</code>.</p>',
             '</body></html>']
    (FOLDER / "index.html").write_text("\n".join(html))

    print(f"\n→ {FOLDER}")
    print(f"  Open: {FOLDER}/index.html")


if __name__ == "__main__":
    main()
