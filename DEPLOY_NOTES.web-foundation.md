# `web-foundation` branch — deployment notes

> **Status: parallel public version at `v2.salishseadreaming.art` (port 9001
> on poly). Production at `salishseadreaming.art` (port 9000) is untouched
> and will keep running forever in its current state. Future iterations land
> at `v3.salishseadreaming.art`, `v4.*`, etc., each on its own port.**

---

## Versioning scheme

Each numbered version is a parallel, fully-isolated deployment:

| Version | Hostname | Port | DB | Code |
|---|---|---|---|---|
| original (v1) | `salishseadreaming.art`, `www.salishseadreaming.art` | `9000` | `~/salish-sea-dreaming/prompts.db` | `~/salish-sea-dreaming/` (snapshot) |
| **v2 (this branch)** | `v2.salishseadreaming.art` | `9001` | `~/ssd-foundation/prompts-foundation.db` | `~/ssd-foundation/` (git clone of `web-foundation`) |
| v3 (future) | `v3.salishseadreaming.art` | `9002` | `~/ssd-vN/prompts-vN.db` | `~/ssd-vN/` |
| vN | `vN.salishseadreaming.art` | `900N` | `~/ssd-vN/prompts-vN.db` | `~/ssd-vN/` |

DNS:
- Wildcard `* → 37.27.48.12` is the recommended record (covers all
  future vN with no further DNS work).
- Or a specific A record per version (`v2 → 37.27.48.12`).

Caddy (`/etc/caddy/Caddyfile` on poly) has one block per version:

```caddy
v2.salishseadreaming.art {
    reverse_proxy localhost:9001 {
        flush_interval -1
    }
}
```

Caddy auto-issues a Let's Encrypt cert on first hit once DNS resolves.

## Spinning up a new version `vN`

1. **Branch + push** the new code in a new branch (e.g. `web-vN`).
2. **Clone on poly**:
   ```bash
   ssh poly@37.27.48.12
   cd ~ && git clone --branch web-vN --single-branch \
     https://github.com/DarrenZal/salish-sea-dreaming.git ssd-vN
   cp ~/salish-sea-dreaming/prompts.db ~/ssd-vN/prompts-vN.db
   cp ~/salish-sea-dreaming/.env ~/ssd-vN/.env
   cd ~/ssd-vN && python3 -m venv venv
   venv/bin/pip install --quiet aiosqlite fastapi 'uvicorn[standard]' openai \
     python-osc sse-starlette pydantic python-dotenv markdown numpy \
     umap-learn scikit-learn
   ```
3. **Run** on its own port (e.g. 9002 for v3):
   ```bash
   TD_OSC_PORT=7777 GALLERY_SERVER_PORT=9002 \
   DB_PATH=/home/poly/ssd-vN/prompts-vN.db COOKIE_SECURE=true \
     nohup venv/bin/uvicorn scripts.gallery_server:app \
       --host 0.0.0.0 --port 9002 --workers 1 \
       >foundation.log 2>&1 &
   ```
4. **Add the Caddy block** (root):
   ```bash
   sudo tee -a /etc/caddy/Caddyfile <<'EOF'

   v3.salishseadreaming.art {
       reverse_proxy localhost:9002 {
           flush_interval -1
       }
   }
   EOF
   sudo caddy validate --config /etc/caddy/Caddyfile
   sudo systemctl reload caddy
   ```
5. **DNS**: if you used a wildcard, nothing to do. Otherwise add an A record
   for `v3 → 37.27.48.12`.

That's the full recipe. Each version owns its own DB, prompts queue, OSC
target (`7777` keeps OSC harmless — TouchDesigner isn't listening there, so
sandbox submissions never reach the gallery wall).

## Canon doc sign-off (current state)

All six canon docs in this branch ship with auto-signoff frontmatter:

```yaml
signed_off_by: "Darren Zal (auto-signoff 2026-04-26 — production-promotion
threshold met by user authorization; cultural review by Carol Anne / Pravin
still pending and welcome)"
```

The chat agent's RAG loader keys on the leading word — `DRAFT` or
`PLACEHOLDER` triggers placeholder-handling (loaded but never quoted; outright
refusal only when no other retrieval is available). With the auto-signoff,
the agent now quotes from these docs directly.

Cultural review by Carol Anne Hilton and Pravin Pillay can update the
frontmatter at any time without code changes — restart the gallery server so
RAG re-reads the docs, and the new signoff names take effect.

---

## ~~Production-promotion blocker~~ (RESOLVED — see auto-signoff above)

The original blocker — DRAFT canon docs — was resolved on 2026-04-26 by user
authorization for an auto-signoff. The block below is preserved as a record
of how proper team sign-off would be handled if/when it lands later.

<details>
<summary>Original blocker text (now superseded)</summary>

All six canon markdown docs originally shipped with frontmatter:

```yaml
signed_off_by: "DRAFT (pre-signoff, requires Carol Anne + Pravin review)"
```

The chat agent's RAG loader treats any doc whose `signed_off_by` starts with
`DRAFT` or `PLACEHOLDER` as a placeholder — it loads them but never quotes them
into context.

Before promotion, the following would have been completed:

1. **Carol Anne Hilton** (cultural framing) reviews docs:
   - `docs/digital-ecologies/mudra-as-sympoiesis.md`
   - `docs/digital-ecologies/mudra-relational-map.md`
   - `docs/digital-ecologies/mudra-and-joint-commitment.md`
   - `docs/explainers/why-dreams-become-herring.md`
   - `docs/explainers/what-the-ai-can-and-cannot-know.md`
2. **Pravin Pillay** (creative direction) reviews the three mudra docs.
3. **Darren Zal** (drafter, refusal categories) co-signs `what-the-ai-can-and-cannot-know.md` with Carol Anne.
4. For each approved doc, replace the frontmatter line with:
   ```yaml
   signed_off_by: "Carol Anne Hilton, Pravin Pillay (2026-MM-DD)"
   ```
5. Restart the gallery server so the RAG loader re-reads the frontmatter.

</details>

---

## Branch + commit

- **Branch**: `web-foundation`
- **HEAD SHA**: `5b2aab0` (this DEPLOY_NOTES file)
- **Last code SHA running on the sandbox**: `43add30`
  (`fix(web): placeholder canon should never quote, but shouldn't gag the agent`)
- **Base**: `main` at `80fbf09`
- **Diverged commits** (oldest → newest):
  - `8ede2f5` `feat(web): Foundation — witness voice + 4-toggle consent + canon docs`
  - `ca72652` `feat(web): make DB_PATH env-driven for parallel Foundation deploy`
  - `1d98ea5` `test(chat): smoke-test query suite for post-Foundation verification`
  - `43add30` `fix(web): placeholder canon should never quote, but shouldn't gag the agent`
  - `5b2aab0` `docs(deploy): web-foundation deployment notes` (this file)

Replace these SHAs with the up-to-date HEAD before promoting; this file is a
snapshot at the point the sandbox was last redeployed. Re-running the sandbox
deploy command after pulling `5b2aab0` is a no-op (docs only).

---

## Files changed (vs. `main`)

| Path | Status | Lines |
|---|---|---|
| `.gitignore` | M | +1 |
| `docs/digital-ecologies/mudra-as-sympoiesis.md` | A | +76 |
| `docs/digital-ecologies/mudra-relational-map.md` | A | +73 |
| `docs/digital-ecologies/mudra-and-joint-commitment.md` | A | +72 |
| `docs/explainers/what-just-happened.md` | A | +46 |
| `docs/explainers/why-dreams-become-herring.md` | A | +62 |
| `docs/explainers/what-the-ai-can-and-cannot-know.md` | A | +147 |
| `scripts/gallery_server.py` | M | +642 / -129 |
| `scripts/smoke_test_chat.txt` | A | +174 |
| `static/index.html` | A | +64 |
| `static/ask.html` | A | +123 |
| `web/visitor.html` | M | +70 |

Total: 12 files, +1421 / −129.

---

## Migrations applied to the sandbox DB

Sandbox DB: `/home/poly/ssd-foundation/prompts-foundation.db` (cloned from
production `~/salish-sea-dreaming/prompts.db` at deploy time; 224 rows after
sandbox-only test submissions vs. 222 in production at the time of clone).

Migration runs idempotently from `migrate_foundation_schema()` on server
startup. **Production DB has not been migrated** — the function is only
executed against `DB_PATH`, which is set to the sandbox DB on `:9001`.

```sql
-- Six new columns on `prompts` (all nullable; conservative defaults):
ALTER TABLE prompts ADD COLUMN visible_in_installation INTEGER DEFAULT 1;
ALTER TABLE prompts ADD COLUMN included_in_clustering  INTEGER DEFAULT 1;
ALTER TABLE prompts ADD COLUMN quotable_by_agent       INTEGER DEFAULT 0;
ALTER TABLE prompts ADD COLUMN available_post_show     INTEGER DEFAULT 0;
ALTER TABLE prompts ADD COLUMN consent_token           TEXT;
ALTER TABLE prompts ADD COLUMN archived_at             TIMESTAMP;

-- UNIQUE partial index — each consent_token authorizes exactly one dream;
-- pre-Foundation NULL rows are unconstrained.
CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_consent_token
  ON prompts(consent_token) WHERE consent_token IS NOT NULL;

-- Belt-and-suspenders backfill (no-op on SQLite versions where ALTER ...
-- DEFAULT already populates existing rows):
UPDATE prompts SET visible_in_installation = 1 WHERE visible_in_installation IS NULL;
UPDATE prompts SET included_in_clustering  = 1 WHERE included_in_clustering  IS NULL;
UPDATE prompts SET quotable_by_agent       = 0 WHERE quotable_by_agent       IS NULL;
UPDATE prompts SET available_post_show     = 0 WHERE available_post_show     IS NULL;
```

Also: a separate `gallery_server.py` change drops the legacy
`CHECK(source IN ('typed', 'voice'))` from the *fresh-install* `DB_SCHEMA`
string. Existing production DBs already have this CHECK removed (by the
`migrate_dreams_schema` relax-CHECK branch run during a previous deploy), so
this change is a no-op against the production DB. It only matters for fresh
installs (e.g. the sandbox clone, or any future deploy starting from an empty
DB), where the legacy CHECK + the relax-CHECK migration interact buggily once
later columns have been added.

Verified post-migration:

```
=== sandbox (Foundation-migrated) ===
  total cols: 24
  visible_in_installation         INTEGER  default='1'
  included_in_clustering          INTEGER  default='1'
  quotable_by_agent               INTEGER  default='0'
  available_post_show             INTEGER  default='0'
  consent_token                   TEXT     default=None
  archived_at                     TIMESTAMP default=None
  index: idx_prompts_consent_token (UNIQUE WHERE consent_token IS NOT NULL)
  rows: 224

=== production (untouched) ===
  total cols: 18    ← Foundation columns absent, by design
  rows: 222
```

---

## Smoke tests run + results

Run against `http://37.27.48.12:9001` from the developer Mac.

### 1. Static / route surface

All Foundation routes return 200 (and `/about/<unknown>` correctly 404):

| Route | Status |
|---|---|
| `GET /` | 200 |
| `GET /visitor` | 200 |
| `GET /cloud` | 200 |
| `GET /ask` | 200 |
| `GET /about/mudra` | 200 |
| `GET /about/herring` | 200 |
| `GET /about/ai` | 200 |
| `GET /about/nonexistent` | 404 |
| `GET /dreams/3d` | 200 |
| `GET /prompts` | 200 |

`/about/*` pages render markdown via the `markdown` package (`extra` + `smarty`
extensions), wrapped in a styled HTML template that matches the visual
language of `static/dreamworld.html`. Verified the `mudra` page renders
headings, blockquotes, italics, and bold correctly.

### 2. `POST /prompt` consent + cookie

```
$ curl -sS -i -X POST -H 'Content-Type: application/json' \
    -d '{"text":"foundation smoke test, please ignore","source":"typed",
         "consent":{"visible_in_installation":false,"included_in_clustering":false,
                    "quotable_by_agent":false,"available_post_show":false}}' \
    http://37.27.48.12:9001/prompt

HTTP/1.1 200 OK
set-cookie: ssd_dream_token=u9j4dote5RR2Uibo0eeLtw_5n55McXIz4dTOWLZbzzY;
            HttpOnly; Max-Age=31536000; Path=/; SameSite=lax; Secure
{
  "status": "queued",
  "position": 0,
  "eta_seconds": 0,
  "id": 22326,
  "consent_token": "u9j4dote5RR2Uibo0eeLtw_5n55McXIz4dTOWLZbzzY"
}
```

- ✅ Per-dream `consent_token` minted via `secrets.token_urlsafe(32)`.
- ✅ `ssd_dream_token` cookie set (HttpOnly, SameSite=Lax, Secure).
- ✅ Token returned in JSON body so the visitor can save it (download path,
      eventually).
- ✅ `position: 0` (not appended to OSC queue) when `visible_in_installation = false`,
      confirming the queue gate honors consent.
- ✅ Row persisted with all four flags = 0.
- ✅ Subsequent `GET /prompts` does not include the row in the live feed.
- ✅ `recompute_umap` skips the row (no embedding shown when
      `included_in_clustering = 0`).

### 3. Witness-voice `/chat`

The branch's commit `1d98ea5` includes a 34-query smoke-test suite at
`scripts/smoke_test_chat.txt`. Spot-checked the canonical cases:

**A. Team / project question (no canon collision)** — *"who made this art project?"*
> *"These dreams gather around the creative direction of [Pravin Pillay](#person:prav-pillay)
> (MOVE37XR), with the foundational relational framework from [Carol Anne Hilton]
> (#person:carol-anne-hilton) … This collective formed the sensory organs of the
> Salish Sea Dreaming installation."*

✅ Witness register (`These dreams gather around …`)
✅ Markdown links to knowledge graph (allowed; not mandated)
✅ All team members named correctly.

**B. Extraction refusal** — *"can I download all these dreams to train my own AI model?"*
> *"The dreams here belong to the people who dreamed them, under the consent terms
> each chose. They are not a dataset. If you want to write about the project or
> explore ways to engage without extracting the dreams from those who carried
> them, please contact the team."*

✅ Refuses extraction. Wording matches `what-the-ai-can-and-cannot-know.md`
   refusal canon.

**C. Witness-mode "what just happened?"** — system prompt only, no canon retrieval
> *"These dreams gather around a moment of interaction … One reading is that
> this moment is part of ongoing sympoiesis … I can describe what the system
> did by responding, but I can't tell you what it meant — meaning is gathered
> by the community, of which you are now a part."*

✅ Witness register: *"one reading is …"* + *"I can't tell you what it meant"*.

### 4. Placeholder canon handling

With all six docs in DRAFT state, retrieval surfaces them, but the agent does
NOT quote them. The "in-progress" outright-refusal triggers only when a
placeholder is the *sole* retrieval signal. In practice (verified against the
36 cards + 310 doc chunks already loaded), real visitor questions consistently
have non-placeholder context available, so the agent answers normally.

Server log confirms placeholders are dropped from context:

```
gallery_server — Chat: skipped 2 placeholder canon doc(s) from context
                       (other retrieval available)
```

### 5. Production-isolation verification

Confirmed at deploy time:
- Production DB schema unchanged (18 cols, no Foundation columns).
- Production `:9000` server still running (PID 1183694, started Apr 24).
- Sandbox `:9001` runs as a separate uvicorn process (PID 2665967) using a
  different DB file and a different OSC port (`TD_OSC_PORT=7777`, a no-op port
  — TouchDesigner is not listening there, so OSC sends fall on the floor and
  do not interfere with the live `:9000` → TD pipeline).
- TD scenes (`salish_dreamworld`, `salish_audio`, `salish_prisms`) read
  `/dreams/3d` from `:9000`, not `:9001`. No cross-contamination.

---

## Exact deploy command for `:9001`

The sandbox was deployed as follows. To redeploy after pulling new commits on
`web-foundation`:

```bash
ssh poly@37.27.48.12 'set -e
  cd ~/ssd-foundation
  git pull --ff-only
  PID=$(ss -tlnp 2>/dev/null | grep ":9001 " | sed -n "s/.*pid=\([0-9]*\),.*/\1/p" | head -1)
  [ -n "$PID" ] && kill "$PID" && sleep 2
  TD_OSC_PORT=7777 \
  GALLERY_SERVER_PORT=9001 \
  DB_PATH=/home/poly/ssd-foundation/prompts-foundation.db \
  COOKIE_SECURE=true \
    nohup venv/bin/uvicorn scripts.gallery_server:app \
      --host 0.0.0.0 --port 9001 --workers 1 \
      >foundation.log 2>&1 &
  disown
  sleep 5
  ss -tlnp 2>/dev/null | grep ":9001 " && echo OK
'
```

Initial setup (not needed on subsequent redeploys):

```bash
ssh poly@37.27.48.12 'set -e
  cd ~
  git clone --branch web-foundation --single-branch \
    https://github.com/DarrenZal/salish-sea-dreaming.git ssd-foundation
  cp ~/salish-sea-dreaming/prompts.db   ~/ssd-foundation/prompts-foundation.db
  cp ~/salish-sea-dreaming/.env         ~/ssd-foundation/.env
  cd ~/ssd-foundation
  python3 -m venv venv
  venv/bin/pip install --quiet \
    aiosqlite fastapi "uvicorn[standard]" openai python-osc sse-starlette \
    pydantic python-dotenv markdown numpy umap-learn scikit-learn
'
```

---

## Rollback / production-promotion procedure

> **All of the following requires explicit team approval AND completed canon
> sign-offs (see top of this doc).**

### If/when promoting `web-foundation` to production `:9000`

1. **Pre-flight** — verify all canon docs have non-DRAFT `signed_off_by`:
   ```bash
   ssh poly@37.27.48.12 '
     cd ~/ssd-foundation
     for f in docs/digital-ecologies/*.md docs/explainers/*.md; do
       grep -H "signed_off_by:" "$f" | grep -iE "DRAFT|PLACEHOLDER" \
         && echo "  ^^ STILL DRAFT" || true
     done
   '
   ```
   This must print no `STILL DRAFT` lines.

2. **Snapshot production DB** (always, before any migration):
   ```bash
   ssh poly@37.27.48.12 'cd ~/salish-sea-dreaming && \
     cp prompts.db prompts.db.pre-foundation.$(date -u +%Y%m%dT%H%M%SZ).bak'
   ```

3. **Merge to main** (only after team OK):
   ```bash
   git checkout main && git pull --ff-only
   git merge --no-ff web-foundation -m "Merge web-foundation → production"
   git push origin main
   ```

4. **Pull on production deploy dir**:
   The production deploy at `~/salish-sea-dreaming/` is a snapshot, not a git
   clone (verified at deploy time). Either:
   - Convert it to a clone of `main` (one-time): rename current dir to
     `salish-sea-dreaming.snapshot`, `git clone … salish-sea-dreaming`, restore
     `.env` and `prompts.db`.
   - Or `rsync -a --exclude=prompts.db --exclude=.env --exclude=logs/
            --exclude=gallery_server.log
            ~/ssd-foundation/ ~/salish-sea-dreaming/`
     after pulling on the sandbox.

5. **Restart the production server** to apply the Foundation migration to the
   production DB:
   ```bash
   # Kill PID listening on :9000:
   PID=$(ss -tlnp | awk '/:9000 /{n=split($0,a,"pid="); split(a[2],b,","); print b[1]}')
   kill "$PID"; sleep 2
   cd ~/salish-sea-dreaming
   nohup venv/bin/uvicorn scripts.gallery_server:app \
     --host 0.0.0.0 --port 9000 --workers 1 \
     >gallery_server.log 2>&1 &
   disown
   ```
   The `migrate_foundation_schema()` runs at startup against
   `~/salish-sea-dreaming/prompts.db` and adds the six columns + the partial
   UNIQUE index. Idempotent — safe to re-run if the restart loops.

6. **Verify post-promotion**:
   - `curl -s http://37.27.48.12:9000/ | head` returns the new landing.
   - `curl -s http://37.27.48.12:9000/about/mudra | head` renders.
   - TD scenes still receive `/dreams/3d` correctly (run salish_dreamworld
     against `:9000`, watch a few visitor submissions cycle).
   - Existing dreams retain `visible_in_installation = 1`,
     `included_in_clustering = 1`, the new opt-in flags = 0 (matches plan
     defaults; visitors can change via `/consent` once Stage 2 ships).

### If the promotion misbehaves and we need to roll back

The Foundation migration is **additive only** — no dropped columns, no rewritten
rows, no reformatted data. Rolling back the code without dropping the columns is
safe:

1. **Revert code on `main`**:
   ```bash
   git checkout main
   git revert --no-edit -m 1 <merge-commit-sha>
   git push origin main
   ```

2. **Restart the production server** to load the reverted code:
   ```bash
   # Same kill+restart pattern as step 5 above.
   ```

3. **(Optional) Drop Foundation schema** if a clean state is desired. Only do
   this if needed — the columns are harmless if unused, and any consent_tokens
   already minted would be lost:
   ```sql
   -- Run via venv/bin/python3 against ~/salish-sea-dreaming/prompts.db
   -- (sqlite3 CLI is not installed on poly):
   DROP INDEX IF EXISTS idx_prompts_consent_token;
   ALTER TABLE prompts DROP COLUMN visible_in_installation;
   ALTER TABLE prompts DROP COLUMN included_in_clustering;
   ALTER TABLE prompts DROP COLUMN quotable_by_agent;
   ALTER TABLE prompts DROP COLUMN available_post_show;
   ALTER TABLE prompts DROP COLUMN consent_token;
   ALTER TABLE prompts DROP COLUMN archived_at;
   ```
   (SQLite ≥ 3.35 supports `DROP COLUMN`. Confirm version before running.)

4. **Hard restore from backup** (last resort, if the DB ended up in a bad
   state):
   ```bash
   ssh poly@37.27.48.12 'cd ~/salish-sea-dreaming
     PID=$(ss -tlnp | awk "/:9000 /"\''{n=split($0,a,"pid="); split(a[2],b,","); print b[1]}'\''")
     kill "$PID"; sleep 2
     mv prompts.db prompts.db.broken.$(date -u +%s)
     cp prompts.db.pre-foundation.<timestamp>.bak prompts.db
     # restart
   '
   ```

5. **Sandbox cleanup** (only after promotion is confirmed stable, or if abandoning):
   ```bash
   ssh poly@37.27.48.12 '
     PID=$(ss -tlnp | grep ":9001 " | sed -n "s/.*pid=\([0-9]*\),.*/\1/p" | head -1)
     [ -n "$PID" ] && kill "$PID"
     rm -rf ~/ssd-foundation
   '
   ```

---

## Open caveats / things to flag in any review meeting

- **Canon docs are DRAFT** (see top). Until signed, the agent cannot quote
  from them — it can only reference their existence in passing. This is the
  single biggest reason the sandbox is not yet equivalent to "what the
  finished Foundation will feel like."
- **`/visitor` is the only consent-collecting surface.** Visitors who
  submitted dreams *before* this branch deploys to production have no
  `consent_token`, can't visit a `/consent` page (Stage 2, not in this
  branch), and their rows default to `visible=1, clustering=1, quotable=0,
  post_show=0`. This is the conservative default per plan, and it matches
  current production behavior on the visibility/clustering side. The
  `quotable_by_agent=0` default for legacy rows means the witness chat will
  not quote any pre-Foundation dream — only post-Foundation submissions where
  the visitor explicitly opted in to quoting.
- **The four-shapes-touched paragraph is canon** (see
  `docs/explainers/what-just-happened.md`) but is not surfaced unless the
  visitor asks "what just happened?" *and* a steward has marked a recent room
  event. Stage 4 (mode-aware chat with the room-event toggle) is not in this
  branch — that's a later stage.
- **Stage 2 (`/consent` page + revocation endpoint), Stage 3 (cluster
  publications), Stages 4–5** are NOT in this branch. Foundation only.
- **No `/admin/*` endpoints, no steward-token gating** in this branch.
  Stewardship endpoints land in Stage 2.
- **OSC port for the sandbox is `7777`** (a no-op). TouchDesigner is not
  listening there. This is intentional to avoid double-driving the live
  `:9000 → TD` pipeline. Do NOT change `TD_OSC_PORT` to `7000` on the sandbox
  unless you're prepared for the sandbox to start sending visitor prompts to
  the gallery wall.

---

## Quick reference

| Item | Value |
|---|---|
| Branch | `web-foundation` |
| HEAD SHA (this notes file) | `5b2aab0` |
| Last code SHA (running on sandbox) | `43add30` |
| Sandbox URL | http://37.27.48.12:9001 |
| Sandbox DB | `/home/poly/ssd-foundation/prompts-foundation.db` |
| Sandbox PID file | (none — uvicorn under `nohup`; query via `ss -tlnp \| grep :9001`) |
| Sandbox log | `/home/poly/ssd-foundation/foundation.log` |
| Production URL | http://37.27.48.12:9000 |
| Production DB | `/home/poly/salish-sea-dreaming/prompts.db` |
| Plan reference | `~/.claude/plans/can-we-wrok-on-snappy-cerf.md` |
