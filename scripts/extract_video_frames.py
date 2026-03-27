#!/usr/bin/env python3
"""
Extract frames from video files at configurable intervals.

Writes frames to output directory and an extraction manifest CSV.
Does NOT write to provenance.csv — that is materialize_corpus.py's job.

Usage:
    # Extract underwater clips at 2s intervals
    python scripts/extract_video_frames.py \
        --input media/collaborators/moonfish-video/underwater/ \
        --output images/moonfish-frames/underwater/ \
        --interval 2 --species herring_school --source "Moonfish Media"

    # Extract a single video
    python scripts/extract_video_frames.py \
        --input media/collaborators/moonfish-video/underwater/P1077716.mp4 \
        --output images/moonfish-frames/underwater/ \
        --interval 2 --species herring_kelp

    # Dry run
    python scripts/extract_video_frames.py --input path --output path --dry-run
"""

import argparse
import csv
import os
import subprocess
import sys


def get_video_duration(path):
    """Get video duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def extract_frames(video_path, output_dir, interval, species, source,
                   photographer, dry_run=False):
    """Extract frames from a single video file."""
    basename = os.path.splitext(os.path.basename(video_path))[0]
    duration = get_video_duration(video_path)

    if duration <= 0:
        print(f"  SKIP: {basename} (cannot read duration)")
        return []

    expected_frames = int(duration / interval) + 1
    print(f"  {basename}: {duration:.1f}s, interval={interval}s, "
          f"~{expected_frames} frames")

    if dry_run:
        return [{"filename": f"{species}_{basename}_f{i:04d}.jpg",
                 "source_video": video_path,
                 "timecode": f"{i * interval:.1f}s",
                 "species": species}
                for i in range(expected_frames)]

    os.makedirs(output_dir, exist_ok=True)

    # Use species + video name prefix for unique filenames
    output_pattern = os.path.join(output_dir,
                                  f"{species}_{basename}_f%04d.jpg")

    result = subprocess.run(
        ["ffmpeg", "-v", "quiet", "-i", video_path,
         "-vf", f"fps=1/{interval}",
         "-q:v", "2", output_pattern],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"  ERROR: ffmpeg failed for {basename}")
        if result.stderr:
            print(f"    {result.stderr[:200]}")
        return []

    # Collect extracted frames
    manifest = []
    for f in sorted(os.listdir(output_dir)):
        if f.startswith(f"{species}_{basename}_f") and f.endswith(".jpg"):
            # Parse frame number to compute timecode
            try:
                frame_num = int(f.split("_f")[-1].replace(".jpg", ""))
                timecode = (frame_num - 1) * interval  # ffmpeg starts at 1
            except (ValueError, IndexError):
                timecode = 0

            manifest.append({
                "filename": f,
                "source_video": video_path,
                "timecode": f"{timecode:.1f}s",
                "species": species,
                "source": source,
                "photographer": photographer,
            })

    print(f"    Extracted {len(manifest)} frames")
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Extract video frames at configurable intervals")
    parser.add_argument("--input", required=True,
                        help="Video file or directory of videos")
    parser.add_argument("--output", required=True,
                        help="Output directory for frames")
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Seconds between frames (default: 2.0)")
    parser.add_argument("--species", default="unknown",
                        help="Species tag for filenames")
    parser.add_argument("--source", default="Moonfish Media",
                        help="Source attribution")
    parser.add_argument("--photographer", default="Moonfish Media",
                        help="Photographer/cinematographer")
    parser.add_argument("--manifest", default=None,
                        help="Output manifest CSV path (default: output_dir/manifest.csv)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be extracted without writing")
    args = parser.parse_args()

    # Collect video files
    video_exts = {".mp4", ".mov", ".avi", ".mkv"}
    if os.path.isfile(args.input):
        videos = [args.input]
    elif os.path.isdir(args.input):
        videos = sorted(
            os.path.join(args.input, f)
            for f in os.listdir(args.input)
            if os.path.splitext(f)[1].lower() in video_exts
        )
    else:
        print(f"Error: {args.input} not found")
        sys.exit(1)

    if not videos:
        print(f"No video files found in {args.input}")
        sys.exit(1)

    print(f"{'DRY RUN — ' if args.dry_run else ''}Extracting from "
          f"{len(videos)} videos at {args.interval}s intervals")

    all_manifest = []
    for video in videos:
        entries = extract_frames(
            video, args.output, args.interval, args.species,
            args.source, args.photographer, args.dry_run
        )
        all_manifest.extend(entries)

    # Write manifest
    manifest_path = args.manifest or os.path.join(args.output, "manifest.csv")
    if not args.dry_run and all_manifest:
        os.makedirs(os.path.dirname(manifest_path) or ".", exist_ok=True)
        with open(manifest_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "filename", "source_video", "timecode", "species",
                "source", "photographer"
            ])
            writer.writeheader()
            writer.writerows(all_manifest)

    print(f"\n{'Would extract' if args.dry_run else 'Extracted'} "
          f"{len(all_manifest)} total frames")
    if not args.dry_run and all_manifest:
        print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
