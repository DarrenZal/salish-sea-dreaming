# IndigenomicsAI Bridge Investigation — 2026-05-26

Investigation deliverable for two questions:

1. **Curved-edges graph implementation** in IndigenomicsAI — what library/technique, can SSD port it?
2. **Cross-app bridging** SSD ↔ IndigenomicsAI — entity mapping + rendering pattern + (bonus) `postMessage` / `BroadcastChannel` pattern from YonEarth.

Code is **proposed only** — no production files were edited. All citations use absolute paths and `file:line` form.

---

## Repo orientation (caveats found while investigating)

Operator-supplied paths needed adjustment before the investigation could start:

| Operator path | Actual path | Notes |
|---|---|---|
| `~/ssd-v5/static/ssd-data-map.html` | `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html` | No `~/ssd-v5/` exists; SSD lives under the salish-sea-dreaming repo. Several IndigenomicsAI worktrees (`IndigenomicsAI-graphrag/`, `-v034-equirect-proof/`, `-v035-equirect-proof/`, `-dome-impl/`) carry their own copies of `static/ssd-data-map.html` — those are forks, not the canonical SSD file. |
| `~/projects/IndigenomicsAI/v2/apps/web/` | exists, but **source is stripped** | Only `.next/`, `.turbo/`, `node_modules/`, and `tsconfig.tsbuildinfo` remain (`/Users/darrenzal/projects/IndigenomicsAI/v2/apps/web/`). No `app/`, `src/`, or `*.tsx` files outside the build cache. The active TypeScript codebase is `~/projects/IndigenomicsAI/docs/roadmap/app/` (Next.js 16, React 19, Tailwind 4, pure SVG, no D3). |

The two graph-rendering surfaces that DO have working source in the IndigenomicsAI repo are:

- **`/Users/darrenzal/projects/IndigenomicsAI/docs/roadmap/app/components/roadmap/`** — Roadmap viz. Pure React + SVG, **NO d3 dependency** (see `docs/roadmap/app/package.json:11-15` — only `next`, `react`, `react-dom`). Layered DAG layout, not force-directed. Edges are `<path>` elements with cubic Bezier curve generator.
- **`/Users/darrenzal/projects/IndigenomicsAI/data/website/prototype.html`** — Living Library prototype. D3 v7 force-directed graph, ~33 KB single-file HTML, includes the 25-theme dataset (`data/website/graph.json` — 25 nodes, 55 edges, manifest at `data/website/manifest.json:1-30`). Edges are `<path>` elements with SVG elliptical-arc curve generator. **This is the closest analog to SSD's force-directed graph.**

No public deployment URL was found anywhere in env, manifest, README, or CLAUDE.md files. The Next.js roadmap viewer ships static HTML to `docs/roadmap/app/out/` (verified `next.config.ts:3-5` — `output: "export"`) but no deploy target is encoded. IndigenomicsAI is "Not yet hosted publicly" per `~/projects/IndigenomicsAI/CLAUDE.md:26`.

---

## Section 1 — Curved edges: two distinct techniques

There are two curved-edge implementations in the IndigenomicsAI repo, using **different** SVG path commands. Pick by use case.

### Technique A — D3 force-directed + SVG elliptical arc (RECOMMENDED for SSD)

File: `/Users/darrenzal/projects/IndigenomicsAI/data/website/prototype.html`

This is the direct port target for SSD because it shares the same architecture (D3 v7 force simulation, mutable `source`/`target` references resolved during simulation, tick-driven path updates).

**Library:** d3.v7 (CDN: `https://d3js.org/d3.v7.min.js` — `prototype.html:7`). No additional dependency.

**Curve generator** (`prototype.html:726-732`):

```js
// Curved link path generator
function linkPath(d) {
  const dx = d.target.x - d.source.x;
  const dy = d.target.y - d.source.y;
  const dr = Math.sqrt(dx * dx + dy * dy) * 1.2; // arc radius — larger = gentler curve
  return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
}
```

The path is an **SVG elliptical arc** (`A` command), not a Bezier. `dr = distance * 1.2` produces a gentle arc whose radius grows with edge length — visually similar to `d3.linkArc` but written inline. Sweep flag `0 0,1` means small-arc, clockwise (consistent left-to-right curve direction).

**Link selection** (`prototype.html:711-724`):

```js
// Links — curved paths instead of straight lines
const link = g.append("g")
  .selectAll("path")            // <-- path, not line
  .data(links)
  .join("path")
    .attr("fill", "none")       // <-- critical: paths default to fill
    .attr("stroke", d => d.color)
    .attr("stroke-width", 1.5)
    .attr("stroke-opacity", 0.4)
    .attr("stroke-dasharray", d => EDGE_DASH[d.type] || "none")
    .attr("marker-end", d =>
      ["feeds_into", "depends_on", "subset_of"].includes(d.type)
        ? `url(#arrow-${d.type})` : null
    );
```

**Tick handler** (`prototype.html:821-825`):

```js
// Simulation tick — curved paths
simulation.on("tick", () => {
  link.attr("d", linkPath);                              // <-- one attr instead of x1/y1/x2/y2
  node.attr("transform", d => `translate(${d.x},${d.y})`);
});
```

That's the entire technique. Three changes from a straight-line graph:

1. `selectAll('line')` → `selectAll('path')`
2. Set `fill="none"` on the path (otherwise the curve fills as a closed region — classic gotcha)
3. Tick handler computes a single `d` attribute via a path generator instead of four x/y attrs

### Technique B — Cubic Bezier (layered DAG, not relevant to SSD)

File: `/Users/darrenzal/projects/IndigenomicsAI/docs/roadmap/app/components/roadmap/RoadmapEdge.tsx`

Used for the static roadmap viewer. Different curve type because the layout is grid-snapped (lanes × horizons) and edges have predictable left-right flow:

```tsx
// RoadmapEdge.tsx:14-19
function edgePath(sx: number, sy: number, tx: number, ty: number): string {
  const dx = tx - sx;
  // Control point offset: generous for short edges, proportional for long
  const cpOffset = Math.max(Math.abs(dx) * 0.45, 80);
  return `M ${sx} ${sy} C ${sx + cpOffset} ${sy}, ${tx - cpOffset} ${ty}, ${tx} ${ty}`;
}
```

This is a **cubic Bezier** (`C` command) with control points pushed horizontally inward from both endpoints — produces the smooth S-curve seen on hierarchical diagrams (Sankey-style). Beautiful but assumes a directional flow; SSD's force-directed graph has no such convention.

The Bezier could be substituted for the arc in SSD, but the arc is more robust at handling arbitrary `(source, target)` orientations because the curve handedness ("which side does it bend") falls out of the sweep flag automatically. Recommend **Technique A** for SSD.

### SSD current rendering — what would change

SSD's `ssd-data-map.html` uses straight `<line>` elements. Critical lines:

| Concern | Current code | Citation |
|---|---|---|
| Hit-target layer (transparent, wide) | `linkLayer.append('g').selectAll('line').data(data.links).join('line')` | `static/ssd-data-map.html:953` |
| Visible link layer | `linkLayer.append('g').selectAll('line').data(data.links).join('line')` | `static/ssd-data-map.html:959` |
| Tick handler — line endpoints | `link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => _shortenEndpoint(d).x).attr('y2', d => _shortenEndpoint(d).y)` | `static/ssd-data-map.html:1043-1045` |
| Hit-layer endpoints | `linkHit.attr('x1', …).attr('y1', …).attr('x2', …).attr('y2', …)` | `static/ssd-data-map.html:1048-1049` |
| Dynamically-added visitor links | `_linkGroup.append('line')` (×2 in tick.visitor handler, ×2 in another helper) | `static/ssd-data-map.html:1601, 1608, 1712, 1718` |
| Endpoint shortening helper (returns target point offset by `tr+gap`) | `_shortenEndpoint(d)` | `static/ssd-data-map.html:1024-1039` |
| Arrowhead marker (already shared) | `#arrow-end` with `markerUnits: userSpaceOnUse` | `static/ssd-data-map.html:850-862` |

The arrowhead marker carries over to `<path>` unchanged — `marker-end="url(#arrow-end)"` works on both line and path. `context-stroke` fill on the marker means per-link colour inheritance also works.

### Minimal diff (proposed — DO NOT APPLY without testing)

Five edits, all in `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html`:

**Edit 1 — hit layer: `line` → `path`** (around line 953):

```diff
-        const linkHit = linkLayer.append('g').selectAll('line').data(data.links).join('line')
+        const linkHit = linkLayer.append('g').selectAll('path').data(data.links).join('path')
+            .attr('fill', 'none')
             .attr('stroke', 'rgba(0,0,0,0)')
             .attr('stroke-width', 14)
             .attr('pointer-events', 'stroke')
             .style('cursor', 'help');
```

**Edit 2 — visible layer: `line` → `path`** (around line 959):

```diff
-        const link = linkLayer.append('g').selectAll('line').data(data.links).join('line')
+        const link = linkLayer.append('g').selectAll('path').data(data.links).join('path')
+            .attr('fill', 'none')
             .attr('data-link-type', d => d.linkType || '')
             .attr('stroke', linkStroke)
             .attr('stroke-opacity', d => _linkEndpointsVisible(d) ? 0.7 : 0)
             .attr('stroke-width', 1.1)
             .attr('pointer-events', 'none')
             .attr('marker-end', _linkMarkerEnd);
```

**Edit 3 — add curved-path helper** (insert after `_shortenEndpoint`, around line 1039):

```js
// Curved link path. Uses SVG elliptical-arc; radius scales with edge length
// for a consistent gentle curve. End is the shortened endpoint so the
// arrowhead stays visible outside the target node.
function _linkPathD(d) {
    const sx = d.source.x, sy = d.source.y;
    const end = _shortenEndpoint(d);
    const tx = end.x, ty = end.y;
    const dx = tx - sx, dy = ty - sy;
    const dr = Math.sqrt(dx * dx + dy * dy) * 1.2;
    if (!isFinite(dr) || dr < 0.5) return `M${sx},${sy}L${tx},${ty}`; // degenerate fallback
    return `M${sx},${sy}A${dr},${dr} 0 0,1 ${tx},${ty}`;
}
// Full-length variant for the hit layer (no endpoint shortening — hover
// should work right up to the source node)
function _linkPathDFull(d) {
    const sx = d.source.x, sy = d.source.y;
    const tx = d.target.x, ty = d.target.y;
    const dx = tx - sx, dy = ty - sy;
    const dr = Math.sqrt(dx * dx + dy * dy) * 1.2;
    if (!isFinite(dr) || dr < 0.5) return `M${sx},${sy}L${tx},${ty}`;
    return `M${sx},${sy}A${dr},${dr} 0 0,1 ${tx},${ty}`;
}
```

**Edit 4 — update main tick handler** (replace lines 1043-1049):

```diff
-            link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
-                .attr('x2', d => _shortenEndpoint(d).x)
-                .attr('y2', d => _shortenEndpoint(d).y);
-            // Hit layer mirrors the visible line's geometry, full-length
-            // so hover works even right at the source node.
-            linkHit.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
-                   .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
+            link.attr('d', _linkPathD);
+            // Hit layer mirrors the visible path's geometry, full-length
+            // so hover works even right at the source node.
+            linkHit.attr('d', _linkPathDFull);
```

**Edit 5 — visitor-tick + visitor-append sites** (lines 1521-1522, 1601, 1608, 1712, 1718 — four `_linkGroup.append('line')` calls + the `tick.visitor` handler):

Each `_linkGroup.append('line')` becomes `_linkGroup.append('path').attr('fill', 'none')`. Each `tick.visitor`-style `link.attr('x1', …)…attr('y2', …)` becomes `link.attr('d', _linkPathD)`. I haven't read the full `tick.visitor` block — should be inspected before applying.

**Test plan before merging:**

1. Visually compare straight-line vs curved at 1.0× zoom on the production zoom JSON — confirm hub→cluster→species curves don't tangle.
2. Confirm arrowhead orientation still looks right (markers orient along the path tangent at the end — for an arc this is the chord direction, which is visually correct).
3. Hover-edge tooltips still fire (hit layer with `pointer-events: stroke` should work identically on a path).
4. Test `_shortenEndpoint` produces a valid arc for very short edges (degenerate-fallback branch).
5. Test on mobile (the path-attr write path is comparable cost to four attr writes — no perf regression expected).

**Side note — visitor.html copy:** The visitor knowledge-panel "explore in the graph" link at `web/visitor.html:1799` points to `/graph-assets/ssd-data-map.html#node=…`, so visitor.html does not render its own graph — it only links to the data-map. No visitor.html changes needed for curved edges.

---

## Section 2 — Cross-app bridge SSD ↔ IndigenomicsAI

### 2.1 Public URL of IndigenomicsAI

**There isn't one yet.** Searched:

- `~/projects/IndigenomicsAI/.env` and `v2/.env` — only TELUS endpoints (e.g. `https://mistral-small-0b50s.paas.ai.telus.com`) + local Neo4j.
- `~/projects/IndigenomicsAI/README.md`, `CLAUDE.md`, all 10 nested CLAUDE.md files — no deploy URL.
- `~/projects/IndigenomicsAI/docs/roadmap/app/next.config.ts:1-7` — `output: "export"` (static export), no `basePath`, no `assetPrefix`.
- `~/projects/IndigenomicsAI/data/website/manifest.json:1-30` — schema/timestamps only.
- The only `indigenomics.com` reference is a JSON-Schema `$id` URI at `docs/roadmap/semantic-roadmap.schema.json:2` — schema identifier, not a live site.

Per `~/projects/IndigenomicsAI/CLAUDE.md:26`: *"Interactive Next.js roadmap viewer (forked from BKC). … Not yet hosted publicly."*

**Implication:** until deployed, the `cross_app_url` field on SSD nodes can either be `null` (link hidden) or point to a placeholder. I recommend a placeholder with a config-driven base URL so the cutover is a one-line change once IndigenomicsAI deploys.

### 2.2 URL structure proposal (since none exists)

IndigenomicsAI prototype.html opens its detail panel via in-page JS only — `openDetail(d.id, themesById, graphData)` at `data/website/prototype.html:815, 848, 968`. No URL anchor routing exists today. **SSD's pattern is cleaner** (it already supports `#node=…` deep links — see `static/ssd-data-map.html:1841-1843`):

```js
const hashMatch = location.hash.match(/node=([a-zA-Z0-9:_.-]+)/);
if (hashMatch) {
    const targetId = hashMatch[1];
    // … focus + open detail panel
}
```

**Recommendation:** when IndigenomicsAI deploys, port this exact hash-routing pattern to prototype.html. URL structure for cross-app linking would then be:

```
https://<indigenomics-domain>/#node=theme.clean-energy
https://<indigenomics-domain>/#node=theme.indigenous-funds
```

Node IDs match `data/website/graph.json` exactly (`theme.land-transfer` through `theme.urban-reserves` — 25 themes). All node IDs already visible in `data/website/graph.json:1-50` and the manifest counts (25 nodes / 55 edges / 5 edge types).

Until then, use a placeholder constant `INDIGENOMICS_BASE_URL` and leave `cross_app_url: null` for nodes pointing into IndigenomicsAI. The SSD link rendering will skip the secondary CTA when the URL is null (see Edit C below).

### 2.3 Candidate bridge entities

Manually cross-referenced SSD's `ssd-data-map-zoom.json` (95 nodes) against IndigenomicsAI's `data/website/graph.json` (25 themes). Strong matches are sparse because the two graphs operate at different abstraction levels — IndigenomicsAI is policy/economic themes; SSD is people, species, software, and concepts.

**Tier 1 — Direct entity overlap (proposed `cross_app_url` value can be added today, points into roadmap viewer or future themes site):**

| SSD node ID | SSD name | IndigenomicsAI target | Proposed `cross_app_url` |
|---|---|---|---|
| `person:carol-anne-hilton` | Carol Anne Hilton | Roadmap viewer (CEO mention) or IndigenomicsAI homepage | `${INDIGENOMICS_BASE_URL}/` (homepage, no per-person page exists) |

That's it for explicit entity overlap. SSD doesn't model "Indigenomics Institute" or "TELUS" as own nodes; IndigenomicsAI doesn't model SSD's people (Pravin/Eve/etc.) or species.

**Tier 2 — Conceptual / thematic bridges (no shared node IDs, but visitor would want to explore IndigenomicsAI's framing from SSD's vantage):**

| SSD node ID | SSD name | IndigenomicsAI theme(s) — graph.json IDs | Suggested label on the link |
|---|---|---|---|
| `concept:three-eyed-seeing` | Three-Eyed Seeing | `theme.indigenous-institutions`, `theme.policy-reconciliation` | "How Indigenous economic frameworks operationalize this" |
| `doc:herring-report-i` | The Salish Sea Herring | `theme.clean-energy`, `theme.equity-participation` | "Related: Indigenous fishery economics" (weak — no direct theme on fisheries; weakest bridge) |
| `doc:herring-report-ii` | The Living Salish Sea | `theme.net-zero`, `theme.clean-energy` | "Related: bioregional economic frames" (weak — same caveat) |
| `hub:knowledge` | Knowledge & Research | `theme.indigenous-institutions` | "Indigenous-led economic institutions" |
| `install:salish-sea-dreaming` | Salish Sea Dreaming (the installation itself) | IndigenomicsAI homepage | Site root |

**Tier 3 — Entities NOT yet in either graph but plausible future additions:**

- TELUS (mentioned in both projects' CLAUDE.md; not modeled as a graph node in either)
- MOVE37XR (SSD person `person:prav-pillay` represents Pravin who runs MOVE37XR; no org node)
- Indigenomics Institute (no node in either graph)
- "Commitment pool" — operator's example; doesn't appear in either graph today (concept lives in Regen Network / KOI docs, not in IndigenomicsAI's 25-theme ontology)
- "Bioregional mapping" — operator's example; not a node, though SSD's `concept:three-eyed-seeing` and `hub:ecosystem` are adjacent

**Verdict:** the bridge is **directional and sparse**. The strongest entry point is the **installation node itself** (`install:salish-sea-dreaming`) carrying a `cross_app_url` to the IndigenomicsAI homepage — visitor exploring SSD discovers the parent IndigenomicsAI project. The Carol Anne Hilton person-node is the second-strongest bridge. Everything else is tenuous.

Adding sparse Tier-2 bridges is still valuable as **discoverability hints** — they don't need to be perfectly aligned ontologically, just useful "see also" pointers.

### 2.4 Proposed JSON-side edit (SSD `ssd-data-map-zoom.json`)

Add an optional `cross_app_url` field to existing nodes. Schema is permissive (string or null), no migration needed for nodes without the field. Concrete change, two highest-confidence entries first:

```diff
   {
     "id": "install:salish-sea-dreaming",
     "type": "installation",
     "name": "Salish Sea Dreaming",
+    "cross_app_url": "https://INDIGENOMICS_PLACEHOLDER.example/",
+    "cross_app_label": "View parent project in Indigenomics AI",
     ...
   },
   {
     "id": "person:carol-anne-hilton",
     "type": "person",
     "name": "Carol Anne Hilton",
+    "cross_app_url": "https://INDIGENOMICS_PLACEHOLDER.example/",
+    "cross_app_label": "Carol Anne in Indigenomics AI",
     ...
   }
```

Use `INDIGENOMICS_PLACEHOLDER.example` (RFC 2606 reserved TLD — never resolves) so the placeholder cannot accidentally leak as a working link before deploy. Operator can do a single global find-and-replace once the real domain is known.

If a node has `cross_app_url: null` or the field is absent, the visitor.html render path (Edit C below) short-circuits and shows only the existing graph link.

### 2.5 Proposed rendering pattern (visitor.html `kp-graph-link` block)

File: `/Users/darrenzal/projects/salish-sea-dreaming/web/visitor.html`

The existing block is at `web/visitor.html:1796-1802`:

```js
// Graph link
var graphLink = document.createElement('a');
graphLink.className = 'kp-graph-link';
graphLink.href = '/graph-assets/ssd-data-map.html#node=' + encodeURIComponent(nodeId);
graphLink.target = '_blank';
graphLink.textContent = 'explore in the graph →';
kpContent.appendChild(graphLink);
```

The `.kp-graph-link` style is defined at `web/visitor.html:809-819`. Reuse the same style for the cross-app link to minimize CSS surface.

**Proposed Edit C — append cross-app link after existing graph link** (DO NOT APPLY without testing):

```diff
                 // Graph link
                 var graphLink = document.createElement('a');
                 graphLink.className = 'kp-graph-link';
                 graphLink.href = '/graph-assets/ssd-data-map.html#node=' + encodeURIComponent(nodeId);
                 graphLink.target = '_blank';
                 graphLink.textContent = 'explore in the graph →';
                 kpContent.appendChild(graphLink);

+                // Cross-app link — appears only when the node's source data
+                // declares a cross_app_url (e.g. Indigenomics AI). Looked up from
+                // the same `card` payload that supplied species pills + body text.
+                if (card.cross_app_url) {
+                    var crossLink = document.createElement('a');
+                    crossLink.className = 'kp-graph-link kp-cross-app-link';
+                    crossLink.href = card.cross_app_url;
+                    crossLink.target = '_blank';
+                    crossLink.rel = 'noopener noreferrer';
+                    crossLink.textContent = (card.cross_app_label || 'View in Indigenomics AI') + ' →';
+                    kpContent.appendChild(crossLink);
+                }
```

**Optional companion CSS — subtle visual distinction** (add near `web/visitor.html:809`):

```diff
         .kp-graph-link {
             display: inline-block;
             color: var(--cyan);
             font-size: 0.9rem;
             text-decoration: none;
             border: 1px solid var(--border);
             border-radius: 16px;
             padding: 8px 16px;
             min-height: 44px;
             line-height: 28px;
         }
+        .kp-cross-app-link {
+            margin-left: 8px;
+            /* Tinted teal to associate with IndigenomicsAI's green palette
+               (#2D6A4F primary, see graph.json color tokens) */
+            color: #74C69D;
+            border-color: rgba(116, 198, 157, 0.4);
+        }
```

The `--cyan` and `--border` CSS variables are pre-existing in visitor.html. The `#74C69D` value is the lightest agency colour from `data/website/graph.json` (the partnerships theme), readable on dark backgrounds and visually adjacent to SSD's existing teal palette per `web/visitor.html:805` (`--teal` species pills).

**Data-loading path:** the `card` object inside the visitor knowledge panel needs to receive `cross_app_url` and `cross_app_label` fields. Whichever JSON source backs `card.species`, `card.body`, etc. must pass these through. The simplest implementation is to add the fields directly to `ssd-data-map-zoom.json` per Edit B above (since the visitor panel already reads node-level data) — no new API endpoint needed.

### 2.6 (Bonus) YonEarth `postMessage` / `BroadcastChannel` pattern — feasibility for SSD

Found the YonEarth bridge at `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/chat-kg-bridge.js`. It's a well-built dual-channel cross-frame bridge — could absolutely be reused. Two layers:

**Layer 1 — same-window iframe `postMessage`** (`chat-kg-bridge.js:628-636, 795-805`):

```js
sendToKG(msg) {
    const iframe = document.getElementById('kgIframe');
    if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage(msg, window.location.origin);  // <-- same-origin lock
    }
},

// From SplitViewController:
this.kgIframe.contentWindow.postMessage({
    type: 'highlightEntities',
    entities: entityNames
}, window.location.origin);
```

Message types observed in YonEarth: `kgReady`, `highlightEntities`, `highlightResult`, `entitySelected`, `resourceSelected`, `resourceError`, `clear-highlights`. Receiver does **origin verification** before processing — `chat-kg-bridge.js:820-823`:

```js
if (event.origin !== window.location.origin) {
    console.warn('SplitViewController: postMessage from unexpected origin dropped:', event.origin);
    return;
}
```

This is the **correct security posture** — never `postMessage(msg, '*')` unless you intend any origin to read it.

**Layer 2 — `BroadcastChannel` for cross-tab same-origin sync** (`chat-kg-bridge.js:539-551, 731-737, 858-867`):

```js
// Sender side
try {
    const channel = new BroadcastChannel('chat-kg-sync');
    channel.postMessage({ type: 'highlight', nodeIds, timestamp: Date.now() });
    channel.close();
} catch (e) {
    console.debug('BroadcastChannel not available:', e.message);
}

// Receiver side (in SplitViewController)
this.channel = new BroadcastChannel('chat-kg-sync');
this.channel.onmessage = (event) => this.handleChannelMessage(event);
```

This handles the case where the KG is in a separate browser tab (not iframed) — `BroadcastChannel` is same-origin by definition, so no extra origin check is needed.

**Feasibility for SSD ↔ IndigenomicsAI:**

- **Same-origin requirement is a hard blocker for the cross-domain case.** SSD will deploy on one origin, IndigenomicsAI on another. The browser will refuse `BroadcastChannel` cross-origin, and `postMessage` cross-origin requires explicit `targetOrigin` plus matching receiver-side origin check.
- **If both apps are eventually served from the same origin** (e.g. `salishsea.life/explore` and `salishsea.life/indigenomics`, OR a single Vercel project with rewrites), the YonEarth pattern transplants cleanly. The simplest deploy posture would be a reverse-proxy that mounts IndigenomicsAI under a subpath of SSD's domain or vice versa.
- **For the cross-origin scenario (most likely)** the right call is just `<a target="_blank">` to a deep link (the `#node=…` URL hash routing) — exactly what Edit C above does. No `postMessage` needed. The bridge is **navigational, not stateful** — the visitor leaves SSD, lands on the relevant node in IndigenomicsAI, comes back.
- **A future synchronized split-view** (SSD on left, IndigenomicsAI on right, both highlighting matched entities in real time) would require either (a) iframing one inside the other on the same origin, OR (b) a shared backend that both apps poll for highlighted-entity state. Worth flagging but out of scope for the May 27–28 IMPACT window.

**Recommendation for Phase 2 (IMPACT 2026):** ship the navigational bridge only (Edit C, hash-deep-link via `<a target="_blank">`). Defer the YonEarth-style `postMessage` bridge to a later phase when both apps deploy on shared infrastructure.

---

## Summary of proposed edits (none applied)

| # | File | Lines | Purpose | Risk |
|---|---|---|---|---|
| 1 | `static/ssd-data-map.html` | 953-967 + 1024-1049 + 1521-1722 (visitor tick block) | `<line>` → `<path>` for all 4 SSD link selections + 1 tick + 1 visitor.tick + 4 dynamic-append sites + 2 new path-generator helpers | Medium — touches simulation tick handler (perf-critical); 4 dynamic-append sites mean easy to miss one; needs visual QA at every zoom level |
| 2 | `static/ssd-data-map-zoom.json` | Per-node, additive | Add `cross_app_url` + `cross_app_label` to candidate bridge entities (start with `install:salish-sea-dreaming` + `person:carol-anne-hilton`) | Low — additive only; old code ignores unknown fields |
| 3 | `web/visitor.html` | 1796-1802 (insert after) + 809 (CSS add) | Render secondary "View in Indigenomics AI" link in knowledge panel when `card.cross_app_url` is present | Low — guarded behind `card.cross_app_url` truthy check; absent on most nodes; CSS additive |

**All edits are reversible single-file diffs**; no schema migration, no build-tool changes, no new dependencies.

## Key file:line citations (for downstream agents)

**Curved-edge reference implementations:**
- `/Users/darrenzal/projects/IndigenomicsAI/data/website/prototype.html:711-732` — D3 v7 force-directed graph with SVG elliptical-arc curved links (closest analog to SSD)
- `/Users/darrenzal/projects/IndigenomicsAI/data/website/prototype.html:821-825` — tick handler with `link.attr("d", linkPath)` pattern
- `/Users/darrenzal/projects/IndigenomicsAI/docs/roadmap/app/components/roadmap/RoadmapEdge.tsx:14-19` — cubic Bezier alternative for layered DAGs

**SSD straight-line code to be converted:**
- `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html:953` — primary hit layer
- `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html:959` — primary visible layer
- `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html:1042-1049` — main tick handler
- `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html:1027-1039` — `_shortenEndpoint` helper (reused by curved version)
- `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html:1601, 1608, 1712, 1718` — dynamic visitor-link append sites
- `/Users/darrenzal/projects/salish-sea-dreaming/static/ssd-data-map.html:850-862` — existing arrow marker (carries over to `<path>` unchanged)

**SSD visitor.html cross-app insertion point:**
- `/Users/darrenzal/projects/salish-sea-dreaming/web/visitor.html:1796-1802` — existing `kp-graph-link` block (append cross-app `<a>` after)
- `/Users/darrenzal/projects/salish-sea-dreaming/web/visitor.html:809-819` — `.kp-graph-link` CSS class to reuse / extend

**IndigenomicsAI graph data + deployment state:**
- `/Users/darrenzal/projects/IndigenomicsAI/data/website/graph.json:1-50` — 25 theme nodes (themed economic concepts)
- `/Users/darrenzal/projects/IndigenomicsAI/data/website/manifest.json:1-30` — counts + edge-type catalog
- `/Users/darrenzal/projects/IndigenomicsAI/CLAUDE.md:26` — "Not yet hosted publicly"
- `/Users/darrenzal/projects/IndigenomicsAI/docs/roadmap/app/next.config.ts:1-7` — static export config (no deploy target)
- `/Users/darrenzal/projects/IndigenomicsAI/v2/apps/web/` — **source stripped**, only `.next/` build cache remains

**YonEarth cross-frame bridge reference (for future same-origin split view):**
- `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/chat-kg-bridge.js:539-551` — BroadcastChannel send
- `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/chat-kg-bridge.js:628-636` — iframe postMessage with same-origin lock
- `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/chat-kg-bridge.js:731-737` — BroadcastChannel receiver setup
- `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/chat-kg-bridge.js:818-853` — origin-verified postMessage dispatch
- `/Users/darrenzal/projects/yonearth-gaia-chatbot/web/chat-kg-bridge.js:858-867` — BroadcastChannel forwarder to iframe

---

## Open questions for operator

1. **Deploy timeline for IndigenomicsAI.** What's the target? The `cross_app_url` field is dead code until there's a domain. Recommend keeping `INDIGENOMICS_PLACEHOLDER.example` as a single string constant so cutover is one `sed`.
2. **Curved-edges priority.** Pure visual improvement, ~30 line diff, but it does touch the simulation tick handler which is performance-sensitive at 60fps with many edges. Worth running once on the production data set with FPS counter visible before merging.
3. **Visitor-tick handler audit.** I read the main tick (line 1042) but not the full `simulation.on('tick.visitor', …)` block at line 1522. Before applying Edit 1+4, that block needs an equivalent line→path conversion and a check that `tx.visitor`-attached elements get the same `attr('d', …)` treatment.
4. **Bridge entity coverage.** I proposed 2 high-confidence entries + 5 tier-2. Operator may want to vet Tier-2 with Carol Anne for ontology correctness before shipping (the herring-report → clean-energy bridge is particularly weak).
5. **Cross-origin vs same-origin deployment.** The YonEarth `postMessage`/`BroadcastChannel` pattern only works same-origin. If IndigenomicsAI ends up on a different domain than SSD, the navigational bridge (Edit C, simple `<a target="_blank">`) is sufficient — but worth confirming before investing in iframe infrastructure.

---

*Generated 2026-05-26 by investigation agent. No production files modified.*
