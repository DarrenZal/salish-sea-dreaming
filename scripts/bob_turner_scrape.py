#!/usr/bin/env python3
"""Bob Turner YouTube scrape — fires once Pravin answers the gap questions.

Pulls all 18 URLs from his annotated film list, sorts into theme folders,
preserves max-quality source (4K native if available else 1080p).

Run: python3 scripts/bob_turner_scrape.py
"""
import subprocess, os, sys
from pathlib import Path

OUT = Path("/Users/darrenzal/projects/salish-sea-dreaming/bob-turner-corpus")
OUT.mkdir(exist_ok=True)

# Theme → [(video_id, short_label)]
CATALOG = {
    "01_humpback": [
        ("AmIpFWfjS2I", "howe_sound_humpbacks"),
        ("XvCuL-coVOM", "humpback_hero_4k"),
    ],
    "02_orca": [
        ("3NCuLawvQaE", "orca_sea_lion_howe_sound"),
    ],
    "03_human_impact": [
        ("6EzO5wugg4Y", "herring_roe_gill_net_fishery"),
    ],
    "04_intertidal": [
        ("F2LRC7mMres", "tide_pool_atlkatsem"),
    ],
    "05_birds": [
        ("XJ4WyRy0oQg", "snow_geese_fraser_skagit"),
        ("oneCVfKdI9I", "extraordinary_salish_sea_full"),  # extract dunlin 6:02-6:16
    ],
    "06_herring_anchovy": [
        ("V4dMyHzz_80", "herring_spawn_serengeti"),
        ("0aclqNlNWt4", "dance_of_herring"),
        ("Ycx1hvrPAqc", "howe_sound_ballet_seals_sealions"),
        ("pg3SPTI0A28", "why_kill_foundation"),
    ],
    "07_salmon": [
        ("st2EFuA0wh8", "sockeye_adams_river"),
        ("ZLUyHagHNMw", "salmon_stronghold_harrison"),
        ("DjOWJd3Y554", "you_could_be_a_salmon"),
        ("lQO9KdG-3K0", "chum_salmon_spawn"),
        ("FsiIxZNtECg", "pink_salmon_stawamus_sawa7e"),
    ],
    "08_ecosystem": [
        ("PYlSyQ0T1V0", "single_body_of_life"),
        ("XT2htr1-MXY", "why_salish_sea_rich"),
    ],
}

# yt-dlp options: best mp4 video + best m4a audio merged, max quality
YDL_FMT = "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/best"

for theme, videos in CATALOG.items():
    theme_dir = OUT / theme
    theme_dir.mkdir(exist_ok=True)
    for vid, label in videos:
        url = f"https://youtu.be/{vid}"
        outfile = theme_dir / f"{label}__{vid}.%(ext)s"
        # Skip if exists
        existing = list(theme_dir.glob(f"{label}__{vid}.*"))
        existing_video = [p for p in existing if p.suffix in (".mp4", ".mkv", ".webm")]
        if existing_video:
            print(f"  [skip] {theme}/{label} — already on disk: {existing_video[0].name}")
            continue
        print(f"  [pull] {theme}/{label} ({vid})")
        cmd = [
            "yt-dlp",
            "--extractor-args", "youtube:player_client=android",
            "--sleep-interval", "3",
            "--max-sleep-interval", "8",
            "-f", YDL_FMT,
            "--merge-output-format", "mp4",
            "--no-warnings",
            "-o", str(outfile),
            url,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"    ERROR: {r.stderr[:200]}")
        else:
            # Print final filename + size
            final = list(theme_dir.glob(f"{label}__{vid}.*"))
            if final:
                fp = final[0]
                size_mb = fp.stat().st_size / (1024*1024)
                print(f"    OK: {fp.name} ({size_mb:.1f} MB)")

print("\n=== Scrape complete ===")
print(f"Output root: {OUT}")
subprocess.run(["du", "-sh", str(OUT)])
