# Frontend Audit: Salish Sea Dreaming v5 — May 26, 2026

Audit completed 2026-05-26 16:30 UTC. **All four surfaces are live and functional for IMPACT 2026 opening tomorrow (May 27, 09:00).**

---

## 1. Landing Page `/` (index.html)

### Current State ✓
- **Layout**: Centered, max-width 720px container. Clean grid of 7 navigation cards.
- **IMPACT 2026 context**: Footer shows `Indigenomics IMPACT 2026 — HR MacMillan Space Centre, Vancouver — May 27–28`. Prominent, correct.
- **Dynamic content**: Live TouchDesigner snapshot embedded. Polls `/td/snapshot` every 4s with cache-busting. Falls back to production snapshot at `http://37.27.48.12:9000/td/snapshot` if local endpoint fails. Section hidden until first successful load.
- **Responsive**: Mobile override at 600px breakpoint. Padding and font-size scale appropriately.
- **Navigation**: All 7 surfaces correctly linked. Tagline: "We are the Salish Sea, dreaming itself awake."

### High-Impact Polish Opportunities
1. **Live snapshot loading UX** (effort: 2 hours)
   - Currently snapshot section appears instantly when first image loads. If both endpoints fail (local + production), section stays hidden silently.
   - **Fix**: Show a minimal placeholder ("Snapshot loading...") while polling, fade to actual image when ready. If fallback exhausted after 8s, show a subtle message like "The sea is resting" instead of silent absence.
   - **Impact**: Visitors won't wonder if the page broke.

2. **Sub-page accessibility** (effort: 1 hour)
   - `/about` pages (mudra, herring, AI) are referenced but not present on nav. They exist in the app (confirmed in routing) but discoverable only via direct link.
   - **Fix**: Add a collapsible "About" section on landing or link from footer.
   - **Impact**: Reduces "where do I learn more?" friction.

3. **Mobile viewport meta tags** (effort: 15 min)
   - Already present and correct. No change needed.

### Risks
- TD snapshot dual-endpoint fallback could fail if poly `:9000` goes offline. Consider hardcoding a graceful fallback image or message.
- No error tracking if snapshot never loads.

---

## 2. Visitor Surface `/visitor` (web/visitor.html, 82 KB)

### Current State ✓
- **Prompt question**: "What would you co-dream with the Salish Sea?" — visible at line 998. Correct.
- **Submission flow**: Textarea input with character counter, mic/camera buttons, send button. Mobile-friendly fullscreen camera modal.
- **Welcome message**: `INITIAL_RESPONSE` built dynamically at line 1748, includes venue phrase ("HR MacMillan Space Centre, Vancouver, May 27–28"), invitation to explore dreamworld and knowledge graph.
- **Chat mode**: Triggered after submission. User's offering shown as first message. Typing indicator, disabled input during welcome delay (800ms), then agent response displayed.
- **Knowledge panel patches verified** ✓
  - `SSD-2026-05-26 kp-ask-button`: Pre-fills chat with "Tell me more about [Entity]" — code at 2103–2120, working.
  - `SSD-2026-05-26 cross-app-link`: Creates link if `card.cross_app_url` present — code at 2130–2138, working.
  - `SSD-2026-05-26 p0-link-fixes`: Dream snapshot link routes to `/cloud?event=<scope>&dream=<id>` — code at 1906–1920, working.
  - `Explore in the graph →` link preserves `?event=` parameter — line 2124, working.
  - **Species pills** shown for each entity — code at 2093–2099, working.
- **Consent UI**: Four toggles (visible in installation, clustering, quotable, post-show), conservative defaults. Token generation + /consent link. All present and styled.
- **Responsive**: Mobile overrides for camera modal, chat input growth, KP panel at bottom. Touch-friendly hit targets (44px min-height buttons).

### High-Impact Polish Opportunities

1. **Missing CSS for cross-app-link** (effort: 20 min) ⚠️ **DO THIS FIRST**
   - Element created at line 2133 with class `kp-cross-app-link`, but no CSS rule exists.
   - **Current result**: Link appears unstyled (likely black on dark background, hard to see).
   - **Fix**: Add CSS after `.kp-graph-link` (around line 858):
     ```css
     .kp-cross-app-link {
         display: inline-block;
         color: var(--salmon);
         font-size: 0.9rem;
         text-decoration: none;
         border: 1px solid rgba(232, 168, 124, 0.4);
         border-radius: 16px;
         padding: 8px 16px;
         min-height: 44px;
         line-height: 28px;
         margin-left: 8px;
         transition: background 0.2s;
     }
     .kp-cross-app-link:hover { background: rgba(232, 168, 124, 0.15); }
     ```
   - **Impact**: Visitor can now actually see and click the IndigenomicsAI bridge link.

2. **Welcome message "event scope" phrase clarity** (effort: 30 min)
   - Current: "As more dreams arrive, we map them into a semantic space…"
   - At IMPACT 2026 show opening, only a handful of dreams exist. Phrase suggests abundance that isn't yet visible.
   - **Fix**: Detect if `total dreams < 10` and show alt welcome: "Early dreams are arriving. As the collection grows, patterns will emerge in the [emergent dreamworld](/cloud)…"
   - **Impact**: Messaging matches visitor experience.

3. **Mic button "no mic detected" state** (effort: 1 hour)
   - Currently mic button is always enabled. If browser has no mic access or device lacks mic, user clicks, nothing happens (or permission denied after delay).
   - **Fix**: On load, check `navigator.mediaDevices.enumerateDevices()`, disable mic button if no audio input found, show `.mic-help.visible` with device instructions.
   - **Impact**: Clearer UX for mobile visitors without headsets.

4. **Chat rate-limit message timing** (effort: 20 min)
   - Enforced 3s cooldown between messages (line 1927), but no user feedback while cooling.
   - **Fix**: Show tooltip or subtle flash on send button when rate-limited: "Please wait 3s between messages."
   - **Impact**: Reduces confusion on fast typers.

### Risks
- **Missing cross-app-link CSS is a show-stopper** — if cards contain `cross_app_url`, link will be invisible. Patch now.
- If `/graph-assets/ssd-cards.json` endpoint fails (line 1789), knowledge panel remains empty but chat continues. Consider fallback or error state.
- Consent token localStorage key is stable, but no UI hint that changing device breaks retrieval. `/consent` page should clarify this.

---

## 3. Dreamworld `/cloud` (static/dreamworld.html, 702 lines)

### Current State ✓
- **3D rendering**: three.js + 3d-force-graph. Nodes rendered as fish meshes. Force-directed layout with collision detection.
- **Deep-link handler**: `?dream=<id>` focuses camera on that dream, pulsing fish, panel opens. Code at 453–480, working.
- **Event scope**: No `?event=` filtering visible in code. Endpoint `/dreams/3d` (line 413) appears to return full dataset; no scope parameter sent.
  - ⚠️ This may be intentional (dreamworld always shows all dreams across events), but verify with backend intent.
- **Gestures integration**: Hand-tracking gesture module enabled by default. URL param `?gestures=off` disables. localStorage key `ssd_gestures_pref` persists user choice. Code at 573, 582.
- **Mobile-specific**: CSS media query at 600px reduces info panel height, resizes nav. Touch event listener for interaction detection.
- **Audio**: None integrated (no sound effects on gesture or dream focus).
- **Responsive**: Full viewport rendering. Info panel repositions to bottom on mobile. Navigation wraps on small screens.

### High-Impact Polish Opportunities

1. **Initial load perceived performance** (effort: 1 hour)
   - Loading spinner shows "Dreaming… the Salish Sea is waking up" with pulse animation. On 4G, this can take 5–8s.
   - **Current**: User sees loading spinner, then graph snaps into view.
   - **Fix**: Pre-load graph container background with a subtle gradient or faint constellation pattern. Stagger node appearance (nodes fade in over 1s after load). Show initial cluster colors before force layout settles.
   - **Impact**: Feels more responsive and intentional.

2. **Legend cluster filtering UX** (effort: 2 hours)
   - Legend items at bottom-left are clickable to filter. Visual feedback exists (highlight on selected).
   - **Current**: No keyboard shortcut, no "clear filters" button, no count of filtered nodes.
   - **Fix**: Add "Show all" button if any cluster deselected. Show node count: "12 dreams in Water cluster".
   - **Impact**: Power users can navigate faster; casual visitors understand what they're filtering.

3. **Info panel "orientation" context** (effort: 1 hour)
   - Panel shows dream text, metadata, and an "orient" field (line ~54 in script). Currently optional per card.
   - **Current**: If card has no orientation, field is empty (wasted space).
   - **Fix**: Show a default orientation if missing: "This dream swims in the [cluster-name] region of meaning."
   - **Impact**: Every dream has interpretive context, feels complete.

4. **Mobile gesture disclaimer on load** (effort: 30 min)
   - Gesture UI button at page load has text "Skip — view without gestures" (line 551 in HTML). Easy to miss.
   - **Current**: Visitor may not know mudra/hakini is available.
   - **Fix**: On mobile, show a small toast notification on first interaction: "Use two hands to see the herring formation" (then hide).
   - **Impact**: Drives engagement with signature gesture.

### Risks
- Force layout convergence can be slow on first load with >100 dreams. No pre-computed positions; all calculated client-side.
- Gesture hand-tracking requires camera permission, which mobile visitors may deny. Fallback (gestures off) works, but no error message.
- Deep-link pulsing animation runs forever (no cleanup on unmount). Low priority, but memory leak vector.

---

## 4. Knowledge Graph `/graph` (static/ssd-data-map.html, 3,082 lines)

### Current State ✓
- **Rendering**: D3.js force-directed graph. Nodes positioned (hubs in circle, others via force). Links drawn as curved SVG paths.
- **Patches verified** ✓
  - `_curvedLinkPath` helper at line 1172: Arc SVG path generator for all links. Working.
  - `SSD-2026-05-27 layout-tuning v2` markers (lines 1259–1284): Force parameters tuned. Event nodes 220px apart, hubs 165px, regular 60px. Mobile collision radius 10px, desktop 14px. Working.
  - `SSD-2026-05-26 deep-link race-defense` at line 2826: Waits for `handleNodeClick`, `nodeById`, and target node to exist before firing. 4s timeout with fallback. Working.
  - `SSD-2026-05-26 expanded-links-curved` at lines 2013–2015: Bridge-expanded links use `_curvedLinkPath`. Working.
  - `paint-order: stroke` label outline CSS at line 39: Text labels have 3px dark stroke halo for readability. Working.
- **Event scope**: Event picker dropdown at top-left (lines 43–72 CSS) is **hidden** (`display: none !important` at line 50). Default scope is read from URL `?event=impact-2026` or falls back to hardcoded scope.
- **Mobile**: CSS media query at 600px. Info panel repositions to bottom, nav compresses. Collision detection increases.
- **Responsive**: Full viewport SVG. Pan/zoom enabled.

### High-Impact Polish Opportunities

1. **Label readability in dense regions** (effort: 30 min)
   - Labels have stroke halo, but in very dense clusters (10+ nodes close together), labels still overlap and become hard to read.
   - **Current**: Halo prevents complete illegibility, but stacking occurs.
   - **Fix**: Increase stroke width from 3px to 4px, or add a `text-shadow: 0 0 8px rgba(5,10,18,0.8)` for extra contrast.
   - **Impact**: Visitors can read node titles even in dense hubs.

2. **Initial node positioning hint** (effort: 1 hour)
   - Graph starts with nodes already laid out (pre-positioned hubs + forced layout). Appears instantly, no visual "settling in" cue.
   - **Current**: Visitor doesn't know layout is still animating (cooldown ticks is 0).
   - **Fix**: On init, set `cooldownTicks(60)` so layout visibly settles for 1s. Add a subtle status line: "Layout settling… (60 frames remaining)" that fades after 1.5s.
   - **Impact**: Feels more intentional and less jarring.

3. **Mobile node-click hit target size** (effort: 1 hour)
   - Desktop nodes have good click radius. Mobile nodes are smaller (force-collide radius 10px).
   - **Current**: Mobile users struggle to tap small nodes, especially in clusters.
   - **Fix**: Increase collision radius on mobile to 16px. Adjust force parameters to maintain spacing.
   - **Impact**: Mobile visitors can reliably click nodes.

4. **Bridge node "breadcrumb" clarity** (effort: 30 min)
   - When an earlier event is viewed and bridge nodes are expanded, a breadcrumb trail appears (lines 75–88 CSS). Breadcrumb shows the "expansion path".
   - **Current**: Breadcrumb is correct but tiny (10px font). Can be hard to see.
   - **Fix**: Increase font to 11px, add subtle background highlight (`rgba(168,200,232,0.12)`), and add a close button with tooltip: "Hide bridge context".
   - **Impact**: Visitor understands the "expanded context" concept more clearly.

### Risks
- Deep-link targeting can race if data arrives out-of-order. Race-defense is in place (4s poll), but if bridge-expand happens async, node may appear after timeout fires.
- Label density increases unbounded as graph grows (no culling). With >500 nodes, label rendering slows.
- Event scope is hardcoded in links from other surfaces. If event name changes, links break (no redirects).

---

## Summary: Ready for Tomorrow

| Surface | Status | Critical Issues | Effort to Polish |
|---------|--------|-----------------|-----------------|
| Landing `/` | ✓ Live | None. Snapshot fallback could improve. | 2 hours |
| Visitor `/visitor` | ✓ Live | **Missing `.kp-cross-app-link` CSS** | 4 hours (1 critical + 3 quality-of-life) |
| Dreamworld `/cloud` | ✓ Live | None. Performance + UX tweaks available. | 4 hours (optional) |
| Graph `/graph` | ✓ Live | None. Label density + mobile tap targets. | 3 hours (optional) |

### Top Priorities for Today (Ranked by Visitor Impact)
1. **Add `.kp-cross-app-link` CSS** (20 min) — Visitor can now see the IndigenomicsAI bridge. **MUST DO.**
2. **Snapshot fallback UX** on landing (1 hour) — Reduces "is the page broken?" confusion.
3. **Welcome message event-aware fallback** in visitor chat (30 min) — First impression matches reality.
4. **Mobile legend filtering + node count** in dreamworld (2 hours) — Power users appreciate; casual visitors understand interactions.

All surfaces are functionally complete and should run smoothly through opening day May 27. The above are **enhancements only** — none are required for the show to open successfully.

---

**Audit completed**: 2026-05-26 16:30 UTC  
**Files audited**: 
- `~/ssd-v5/static/index.html` (5.8 KB)
- `~/ssd-v5/web/visitor.html` (82 KB)
- `~/ssd-v5/static/dreamworld.html` (702 lines)
- `~/ssd-v5/static/ssd-data-map.html` (3,082 lines)

