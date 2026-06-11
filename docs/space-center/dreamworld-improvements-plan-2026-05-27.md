# Dreamworld Show-Day P0+P1 Plan

Prepared for agent review on 2026-05-27.

## Summary

- Treat this as live-show work for Wednesday, May 27, 2026: build in v6 first, verify on phone and desktop, then apply the same changes to v5.
- Ship P0 plus all P1: IMPACT-only default, sphere reskin, anjali reveal of DE fish, semantic kNN edges, Coast Salish ripple interactions, deep-link focus, cluster collapse, temporal spiral, and existing two-hand fish-constellation gesture repurposed to field-wide ripple.
- Do not edit chat prompt/cards/UI files; leave a handoff note for the other session to add the `meta:remember-mudra` card and entity links.

## Server, API, And Data

- Before changes, create timestamped backups for both `~/ssd-v5` and `~/ssd-v6`: `static/dreamworld.html`, `scripts/gallery_server.py`, `static/js/*.js`, and the active prompts DB.
- Add DB columns through existing startup migration:
  - `neighbors TEXT`: JSON object `{ "global": [id,id,id], "same_event": [id,id,id] }`
  - `neighbors_updated_at TEXT`
- Adapt `~/ssd-v6/reembed.py` into a reusable TELUS re-embed script for both v5/v6:
  - Use `json.loads(embedding)` length checks in Python, not SQLite JSON functions.
  - Re-embed rows where `embedding IS NULL` or dimension is not `2048`.
  - Set touched rows to `x=0,y=0,z=0`, then run the existing full `recompute_umap()` once.
- Add semantic neighbor computation:
  - Exclude seeds, archived rows, non-visible rows, and rows without 2048-dim embeddings.
  - Compute cosine top-3 globally and top-3 within each `event_id`.
  - After new prompt embedding, refresh neighbor cache server-side; full refresh is acceptable at current scale.
  - Note post-show optimization: at about 2000 dreams, replace full refresh with O(N) incremental kNN insert/update.
- Change `/dreams/3d` contract:
  - Default `event` is `impact-2026`.
  - `?event=impact-2026` returns only IMPACT visible dreams.
  - `?event=digital-ecologies-2026` returns only DE visible dreams.
  - Nodes include `event_id`, `neighbors`, `eventNeighbors`, `shape`, and existing cluster fields.
  - `links` are semantic same-event links for the returned event; `timelineLinks` are faint submission-order links.
- Preserve v6's optional `?theme=on` behavior if present; do not make it part of the default dreamworld.

## Dreamworld Client

- Load IMPACT data first from `/dreams/3d?event=impact-2026`; load DE once into a hidden client buffer from `/dreams/3d?event=digital-ecologies-2026`.
- If the DE buffer fetch fails or is still pending during anjali, retry silently and surface a brief "The past is loading..." status rather than making the gesture look broken.
- Render IMPACT nodes as glowing cluster-colored spheres; render DE nodes as existing fish meshes with opacity `0` by default and target opacity about `0.4` during remembrance.
  - Spheres should be roughly current-fish visual size, with a simple fresnel-edge/emissive rim atmosphere; avoid additive blending because it will white out on low-end phones.
- Add a subtle starfield using one low-cost `THREE.Points` buffer behind the graph.
- Add anjali detection in `mudra-detector.js`:
  - Two hands, palms/wrists close, fingers roughly vertical, near body midline.
  - Hold above threshold for about `1.7s` to activate remembrance; tune down toward `1.2s` if venue tests feel sluggish.
  - Release below threshold to fade DE fish out over about `3s`.
- Replace temporal-chain primary edges with kNN semantic edges; keep timeline edges as a faint secondary layer.
- During anjali, smoothly interpolate edge visibility from same-event IMPACT edges to global resonance edges, including cross-event DE-to-IMPACT connections; reverse on release.
- On node focus or click, emit a pooled instanced ripple:
  - Inner circle/ring at the focused node.
  - Mid crescents around the ripple perimeter, cupping the origin/edge path.
  - Outer trigons radiating along semantic edges.
  - Ripple lasts about `2s`, with widening gaps and fading alpha.
  - Cap at 3 concurrent ripples, newest preempts oldest, target 30fps on iPhone 12 and mid-tier Android.
  - Pull palette, easing, and shape-proportion cues from the wall-show pond-ripple layer before final shader tuning so the dreamworld and projection wall read as one system.
  - When a visible DE fish is tapped during anjali, it can emit a ripple too, but the ripple should stay muted in proportion to the fish's remembered alpha.
- Improve `/cloud?event=impact-2026&dream=<id>`:
  - Focus camera on the target plus roughly 10-20 semantic neighbors.
  - Show a soft "your dream gathered with ..." cluster annotation.
  - Fire one ripple cascade after focus lands.
- P1 gesture/layout changes:
  - Index pinch toggles semantic field to cluster-sphere view and back.
  - Middle pinch toggles cluster-sphere view to single dream-field sphere and back.
  - Open-palm lateral sweep toggles temporal spiral; repeat sweep restores the prior view.
  - Confirm the current fish-constellation gesture name in code before wiring: if it is two-hand Hakini/fingertip-to-fingertip, reuse that detector; if it is another two-hand open gesture, name it explicitly. That existing gesture triggers a field-wide Coast Salish ripple wave; old herring behavior stays disabled unless behind a debug URL flag.

## Test Plan

- API checks: confirm v5/v6 `/dreams/3d`, `?event=impact-2026`, and `?event=digital-ecologies-2026` return correct counts, `event_id`, 2048-dim-only neighbor caches, semantic links, and timeline links.
- DB checks: verify no visible non-seed row has missing/non-2048 embedding after re-embed; verify `neighbors` JSON is populated.
- UMAP smoke-test: after re-embed and full UMAP recompute, compare existing IMPACT coordinates before/after; if current IMPACT dreams move more than about 25% of the field span, pause for operator review before rollout.
- Browser checks with Playwright: desktop and mobile screenshots for default IMPACT-only view, anjali reveal, node focus ripple, deep-link focus, cluster collapse, field sphere, temporal spiral, and `?gestures=off`.
- Phone checks at venue: camera permission flow, anjali hold/release, pinch toggles, open-palm sweep, Hakini ripple, frame rate, and tap/hover info panels.
- Rollout checks: v6 health and visuals first; after operator acceptance, apply same changes to v5, restart, then verify `https://salishseadreaming.art/cloud?event=impact-2026`.

## Assumptions

- Full UMAP recompute is approved even though it moves old DE positions; semantic coherence for TELUS embeddings is the priority.
- Incremental UMAP transform/model persistence is post-show P1 and not part of this build.
- The current v6 DB has IMPACT rows marked invisible; the code should respect consent/visibility rather than force-display them.
- Coast Salish primitives are approved for this functional ripple use, not for static branding or decorative chrome.

## Implementation Handoff

Updated 2026-05-27 after rollout.

- Shipped to both v6 and v5: event-scoped `/dreams/3d`, TELUS 2048-dim re-embed helper, same-event/global kNN neighbors, IMPACT spheres, hidden DE fish buffer, anjali remembrance reveal/release, semantic/resonance/timeline links, Coast Salish ripple on focus/field gesture, deep-link focus, cluster/field/spiral toggles.
- v6 backups: `dreamworld-p0p1-20260527-050349`, plus ripple fallback backup `dreamworld-ripple-mesh-20260527-051506`.
- v5 backups: `dreamworld-p0p1-20260527-051928`.
- Server label fallback backups: `dreamworld-label-fallback-20260527-052839` on both v5 and v6.
- v5 data refresh: 264 rows re-embedded via TELUS, UMAP recomputed for 253 prompts, kNN refreshed for 209 visible dreams.
- v6 data refresh: 0 rows needed re-embed, UMAP recomputed for 247 prompts, kNN refreshed for 201 visible dreams.
- Smoke-test note: v5 had 8 visible IMPACT rows, but their pre-refresh coordinates were all `(0,0,0)`, so the "movement <25%" test was not meaningful; the recompute fans them into actual semantic positions.
- Browser smoke: production mobile and desktop load with 8 IMPACT spheres + 201 hidden DE fish in buffer; anjali reveal shows 201 fish at ~0.4 opacity and release hides them; field ripple produces no WebGL warnings after switching ripple marks to a pooled mesh fallback; deep-link focus opens the panel and shows the cluster annotation fallback.
- Chat handoff: anjali now ships in dreamworld. Other session should add `meta:remember-mudra` plus entity links for `anjali` and `remember mudra`.
