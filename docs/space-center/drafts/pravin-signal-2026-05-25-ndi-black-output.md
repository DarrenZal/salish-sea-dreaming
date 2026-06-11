OBS on the 3090 is recording cleanly (HEVC, 3840×2160 — matched to your NDI), but the frames coming through are all black. I extracted a frame from a test record — mean brightness 0/255. Receiver side is fine; the NDI source is sending black.

Quick checks on your end in Resolume:

1. Is a clip actually triggered + playing on master? (preview screen showing content)
2. Master blackout button engaged? (or master fader pulled to zero)
3. The layer with content — is its visibility eye on?
4. Output → NDI Output — still toggled on? (worth checking, you may have flipped it when changing resolution)
5. If all four look right — toggle NDI Output off then on to force a re-broadcast

Let me know what you see — I can fire a fresh 30-sec test record the moment you're sending non-black.

— sent by Claude
