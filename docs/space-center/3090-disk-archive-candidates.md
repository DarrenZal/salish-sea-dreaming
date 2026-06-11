# 3090 Disk — Archive / Free-Up Candidates

**Captured:** 2026-06-10 (post-IMPACT 2026, entering R&D mode)
**Machine:** `windows-desktop` / `DESKTOP-37616PR`, C: drive ~953 GB total, **~308 GB free**

Disk is **not** being freed this round (308 GB free is comfortable for R&D). This is the shortlist for a future free-up pass once an external destination (NAS / external SSD / Google Drive) is chosen. Per project memory `project_large_file_transfer_3090_to_drive`, upload large files directly to Drive rather than scp-through-WireGuard.

## Candidates (largest first)

| Path | Size | Type | Notes |
|---|---|---|---|
| `C:\Users\user\.cache\huggingface` | ~94 GB | Model cache | **Regenerable** — re-downloads on demand. Safe to clear; highest single win. |
| `C:\Users\user\Videos\` | ~68 GB | Show recordings (NDI/screen, May 25–26) | IMPACT footage. **Archive off-box before clearing** — not regenerable. Includes 8.5–9 GB single captures. |
| `C:\Users\user\Desktop\` render exports | ~28 GB | `TDMovieOut*.mov`, `SSD_*.avi/.mp4` | Production render exports (1–11 GB each). Archive selectively; some may be in Drive already. |
| `C:\Users\user\Downloads\` | ~31 GB | Mixed media + installers | Partial: keep source footage, drop re-downloadable installers. |

**Potential reclaim:** ~190–220 GB.

## Keep (R&D essentials — do not clear)

- `C:\Users\user\TouchDesigner\` (~57 GB) — app + StreamDiffusionTD workspace
- `miniconda3` (~19 GB), `streamdiffusion-env` (~5 GB), `kohya-env` (~5.5 GB) — active Python environments
- `models\` (~4.8 GB) — briony-sdturbo-merged + sd-turbo-briony-v5 checkpoints
- `Documents\models\network-snapshot-000120.pkl` — the production Autolume PKL

## Procedure (when run)

1. Pick destination (NAS / external SSD / Drive folder).
2. Archive `Videos/` + selected Desktop renders first (not regenerable) → verify checksums off-box.
3. Then clear `.cache/huggingface` (regenerable, no archival needed).
4. Re-confirm free space + that R&D environments still launch.
