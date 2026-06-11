# Visitor App v5 IMPACT Integration Spec — 2026-05-14

Purpose: define the smallest useful visitor-app refresh that connects the Hubble Space SSD installation to the Dome Living Intelligence surface without overloading either room.

Status: implementation spec, not approved public copy. Do not patch visible text until Austin / Carol Anne / Pravin wording is approved.

Update from Kurt reply, 2026-05-13 evening: the IMPACT survey / polling / word-cloud path is Whova-backed and projects to a normal screen, not the Dome projection. Custom survey intake and live analytic visualization are therefore out of scope for this app unless Carol Anne / Shawn reopen them after the Whova conversation next week.

## Current App Surfaces

Existing code already supports the core bridge:

| Surface | Current location | Notes |
|---|---|---|
| visitor offering intake | `web/visitor.html`, `/prompt` | 150-character text, optional photo, sends OSC / SSE |
| dreamworld link | `web/visitor.html` -> `/graph-assets/dreamworld.html` | collective visitor dream field |
| knowledge graph link | `web/visitor.html` -> `/graph` -> `/graph-assets/ssd-data-map.html` | existing SSD graph |
| chat mode | `web/visitor.html`, `/chat` | RAG-ish graph-linked responses |
| graph event stream | `/graph/stream` | broadcasts visitor prompt events |
| TD preview | `/td/snapshot` | installation preview in app |

The v5 integration should use these surfaces before adding new infrastructure.

## v5 Goal

Make the app feel like a bridge between two IMPACT rooms:

- in Hubble: visitors offer / ask / explore the graph behind SSD
- between rooms: the app points toward the Dome cosmic journey
- in Dome: the same graph substrate appears as constellation-scale experience

The app should not become the survey app. Whova owns that surface for IMPACT. The Hubble app can point visitors toward related IMPACT / Dome material if approved, but it should not collect survey answers or attempt to replace Whova polling.

## Feature Flags

Add a lightweight config object before visible copy changes:

```js
var IMPACT_CONFIG = {
  impactMode: true,
  domeTeaserEnabled: false,
  livingGraphLabel: 'PENDING_APPROVAL',
  domeTeaserLabel: 'PENDING_APPROVAL',
  domeInfoUrl: ''
};
```

Reason: the team can ship code plumbing while leaving public wording and links disabled until approved.

## UI Changes

| Change | Default | Approval dependency | Notes |
|---|---|---|---|
| rename "explore the knowledge graph" link | disabled until approved | Carol Anne / Pravin | likely "explore the living graph" or similar |
| add Dome teaser link/card | disabled until approved | Carol Anne / Pravin; Austin if using pearl/Hubble language | small link below graph, not a hero |
| add survey launch link | out of scope | Whova / Carol Anne / Shawn | do not add unless the Whova flow explicitly needs a Hubble handoff URL |
| post-offering response update | pending | Austin + Carol Anne if it bridges pearl/graph language | current `INITIAL_RESPONSE` is the main text risk |
| analytics/event source field | safe | operator | add source metadata only; no visible copy |

## Data/Event Shape

When visitor submissions are persisted or sent to graph/Dome systems, use explicit consent and source fields:

```json
{
  "event_type": "visitor_offering",
  "surface": "hubble",
  "event_context": "impact_2026",
  "text": "...",
  "photo_attached": false,
  "public_graph_allowed": false,
  "created_at": "ISO-8601"
}
```

Rules:

- Hubble offerings are not survey responses by default.
- Survey responses live in Whova unless a later data-governance decision says otherwise.
- Do not pipe visitor Hubble text into Indian Act survey analytics.
- If a future bridge exists, make the visitor choose it intentionally and record that consent separately.

## Backend Minimal Delta

Preferred:

1. Keep `/prompt`, `/chat`, `/graph`, `/graph/stream`.
2. Add optional metadata fields to `PromptRequest` only if needed:
   - `surface`
   - `event_context`
   - `public_graph_allowed`
3. Do not add survey storage; Whova owns survey intake for IMPACT.
4. Add `/impact/config.json` only if runtime feature toggles are needed.

Do not route through a new model endpoint until the Gemma / TELUS sovereign model path is confirmed.

## Copy Placeholders

These are placeholders for review, not strings to paste into production:

| Slot | Placeholder |
|---|---|
| graph link | `[PENDING] explore the living graph` |
| Dome teaser | `[PENDING] continue into the Dome cosmic journey` |
| post-offering bridge | `[PENDING] your offering can remain with the Hubble dream or continue into the larger IMPACT graph` |

## Acceptance Criteria

Code can be considered ready when:

- feature flags default off for unapproved visible text
- existing offering flow still works
- existing `/graph` link still works
- no survey route exists in the Hubble app
- event metadata clearly labels Hubble offering context
- app works offline-ish enough for the room: pre-recorded / static graph links still function if live model path fails

## Day 4 Recommendation

Implement only the feature-flag scaffold and Hubble/Dome metadata after Dan's Dome specs call and Friday Dome asset decisions. Do not rewrite the app's public-facing copy until the line-level public-language approvals are updated. Do not implement survey intake.
