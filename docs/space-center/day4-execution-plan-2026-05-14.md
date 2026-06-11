# Day 4 Execution Plan — 2026-05-14

Status: operator plan for Thursday morning. Assumes Day 3 tooling is ready and production ingest dirs are pristine.

Correction from 2026-05-13 evening meeting review: IMPACT has two active surfaces in one event arc. This plan now includes both the Hubble Space SSD installation and the Dome Living Intelligence / knowledge graph cosmic journey deadline.

Update from Kurt reply, 2026-05-13 evening: Dan is the Dome specs lead for tomorrow's call. Whova owns IMPACT survey / polling / word-cloud display on a standard screen. SSD should not build survey intake or custom live survey analytics unless that scope is explicitly reopened next week.

## Day 4 Objective

By end of Day 4, the project should have one of these concrete states:

1. **Best case:** Austin Drive ingested, v2 LoRA trained/evaluated, source approval posture recorded, first Track 2 decomposition candidates identified, Dan Dome specs captured, and Friday Dome asset package either revised to spec or intentionally held.
2. **Good fallback:** Austin Drive not landed, but John pack sent, Dome concept package staged, Dan call completed/queued, 3090/TD tunnel status resolved, and public-language/consent review queued for Austin.
3. **Worst acceptable:** no new dependencies land, but Dome Friday package remains operator-ready as concept material, Dan call prep is clear, and every Hubble blocker still has an explicit next action.

Do not spend Day 4 on more v1/v1.5 generative exploration. The clean-subset experiment already answered the recipe question; the next evidence comes from Austin's curated source data.

## First 15 Minutes

Run:

```bash
python3 scripts/austin_v2_pipeline.py status
```

Then check:

- What did Dan say / when is the Dan Dome specs call?
- Does Carol Anne / Shawn want concept stills/GIFs before Dan's native Dome specs, or should the package be held?
- Has Austin's Drive landed?
- Has Pravin restored the 3090 tunnel or sent patched `visualizer.py`?
- Is there a John contact channel?
- Any reply from Natalia on 5090?
- Any Carol Anne / Indigenomics protocol note?

Update only the relevant row in `CURRENT_STATE.md` if a dependency changed.

Friday Dome package is already staged:

```text
output/dome-cosmic-journey-2026-05-15.zip
docs/space-center/drafts/carol-anne-shawn-dome-assets-handoff-2026-05-14.md
```

Treat this as the Day 4 time-sensitive thread because Carol Anne's AI presentation needs content by Friday 2026-05-15, but do not assume the current package is final Dome media before Dan confirms native specs.

## Branch A — Austin Drive Landed

Primary command:

```bash
cp ~/Downloads/austin-curated-drive/* austin-v2-ingest/inbox/
python3 scripts/austin_v2_pipeline.py auto-until-gate
```

Expected gates and operator actions:

| Gate | Action | Target time |
|---|---|---:|
| `triage-review` | Edit `_triage.json`; approve only clean design/source plates; reject installation context | 10-20 min |
| `captions` | Fill element-level caption sidecars; no project names; run validator | 30-60 min |
| `train` | Run printed accelerate command in TELUS; mark train complete | 10 min H200 |
| `eval-run` | Run printed `eval_lora.py`; mark eval complete; download | 5 min H200 |

Decision after eval:

| Eval result | Call | Next action |
|---|---|---|
| clear subject + Austin influence + no watermark | v2 passes still gate | Record finding; consider temporal smoke; prep 2-3 internal first-look stills only if Austin agreed to see them |
| style good but watermarks/text | partial | Adjust negative prompt / prompt-specific terms; do not show externally |
| subject collapse / generic / culturally noisy | fail | Do not run motion; inspect captions/data; consider SDXL only after documenting failure |

Required records:

- `docs/space-center/austin-consent-map.md`
- `austin-v2-ingest/provenance/manifest.csv`
- `CURRENT_STATE.md`
- memory entry for v2 finding, if trained

## Branch B — Drive Has Not Landed

Do not fill the gap with more Austin-reference training. Use local unblockers:

1. Send or queue the Dome concept asset handoff if Carol Anne / Shawn want Friday visuals.
2. Prepare for / take the Dan Dome specs call; Dan, not Kurt, owns native render requirements.
3. Send or queue the Drive-received Signal draft if Pravin says Drive is imminent.
4. Send John pack if contact exists.
5. Use `docs/space-center/austin-review-packet-2026-05-14.md` to prep the next Austin check-in.
6. Continue local TD/Track 2 integration only if it does not invent Austin content.
7. If no human dependency moves by midday, spend time on Hubble+Dome integration planning, not model experiments.

## Branch B2 — Friday Dome Visuals Need Revision

Current staged package:

- `output/dome-cosmic-journey-2026-05-15/` - 10 stills + 10 GIFs + contact sheet + manifest
- `output/dome-cosmic-journey-2026-05-15.zip` - 23 MB, SHA256 starts `59e69436`
- generator: `scripts/generate_dome_cosmic_journey_assets.py`

Fast revision options:

| Request | Action | Time |
|---|---|---:|
| change title wording | edit `SCENES` titles/subtitles in generator; rerun | 5-10 min |
| remove "survey" from visuals | retitle scenes 04/05; keep spoken notes separate | 5 min |
| Whova framing requested | rename survey scenes to polling / participation / audience signal | 5-10 min |
| make visuals more technical | emphasize `Sovereign AI Layer`, graph nodes, app/data flow | 10-20 min |
| make visuals more presentation-friendly | use stills only; keep GIFs as backup | 0 min |
| produce one short reel | convert GIF/still sequence to MP4 after title approval | 20-30 min |

Do not add Austin visual language to the Dome package. The Dome grammar is constellation / graph / participation-as-signal. Whova owns the actual survey surface.

## Branch C — v2 LoRA Passes

Allowed next GPU work:

```bash
python3 scripts/jupyter_contents_sync.py upload output/temporal-style-smoke-2026-05-13/inputs temporal-style-smoke-inputs
python3 scripts/jupyter_contents_sync.py upload scripts/run_temporal_style_smoke.py run_temporal_style_smoke.py
```

Run only after still eval passes:

```bash
python run_temporal_style_smoke.py \
  --version v2 \
  --lora-dir austin-v2-lora-out \
  --inputs-dir temporal-style-smoke-inputs \
  --out-dir temporal-style-smoke-v2
```

Use outputs for internal motion evaluation only. Pass means "possible left/right atmospheric layer," not center teaching content and not public approval.

## Branch D — v2 LoRA Fails

Do not rescue it by pushing scale or returning to AnimateDiff.

Triage in this order:

1. Captions: placeholders, generic wording, project names, missing primitives.
2. Data: context photos, logos, text, low frame coverage.
3. Training: too many epochs, wrong trigger, wrong base path, metadata mismatch.
4. Model strategy: SDXL or LoRA rank change only after the above are documented.

Keep Track 2 as production center path.

## Branch E — 3090 Tunnel Returns

Immediate checks:

1. Recover patched Autolume `modules/visualizer.py` or ask Prav where it lives.
2. Verify actual output mechanism: NDI, Spout, or other.
3. Test TD bioregional receiver with local bridge:

```bash
python3 scripts/bioregional_osc_bridge.py --once --osc-port 7001
```

4. Do not switch Autolume output path until v2 LoRA work is complete and the patch mechanism is known.

## Day 4 End Targets

| Area | Minimum acceptable by end of Day 4 |
|---|---|
| Austin data | Drive landed and processed OR explicit follow-up sent / dependency confirmed |
| Dome Friday package | Carol Anne/Shawn package sent, revised, or explicitly held |
| Dan specs | Dome projection specs captured or call still explicitly pending |
| Visitor app v5 | `docs/space-center/visitor-app-v5-impact-integration-spec-2026-05-14.md` reviewed before any Hubble+Dome bridge code changes |
| v2 LoRA | trained/evaluated if Drive landed; otherwise no extra stale-data experiments |
| Track 2 | first real source candidates identified if vectors landed |
| Consent | source/workflow/public-language statuses recorded in consent map |
| John | pack sent if contact exists; otherwise contact blocker still explicit |
| 3090/TD | tunnel restored or still explicitly blocked; no hidden Autolume output assumption |
| Public language | drafts remain pending until Austin review; no external use |

## Hard No-Go List

- No v1.5 outputs to Austin as candidate art.
- No public copy using "teaching," "Thunderbird passing," "three shapes," or "Coast Salish design forms" until Austin approves wording.
- No invented-from-scratch crests in Austin's style.
- No AnimateDiff retry unless Darren explicitly reopens it.
- No promise of Autolume NDI/Spout path until patched `visualizer.py` or live install confirms it.
- No custom survey intake / live survey analytics build; Whova owns IMPACT polling/survey/word-cloud unless scope is reopened.
- No claim that current Dome assets are native projection-ready until Dan confirms specs.
- No Austin / Coast Salish visual motifs in Dome concept assets unless explicitly approved for that surface.
