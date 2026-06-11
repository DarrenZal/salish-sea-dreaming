Heads up — 3090 ssh died ~10:45am (had a clean ping at 10:43, gone since). Tunnel client isn't reconnecting; poly's listening but no one's home.

I checked the H200 fallback — preset 0 and the autolume source tree live only on the 3090 (not on Drive), so even H200 needs 3090 ssh first to grab them. We're firmly 3090-dependent for the render.

When you have 1 min at the studio:
1. cmd → schtasks /run /tn "SSD-SSH-Tunnel"
2. If no joy, reboot the 3090

No rush — if you're heads-down on Natalia or composite work, just ping when you can poke it. Render is ~40 min wall-clock once tunnel is back, upscale ~5h, still well within tonight.
