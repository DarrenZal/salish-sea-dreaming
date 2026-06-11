# Austin Harry — Phase 2 Consent + Approval Map

**Show:** Indigenomics IMPACT activation, late May 2026  
**Venue:** Hubble Space, HR MacMillan Space Centre, Vancouver  
**Co-leading artist:** Austin Aan'yas Harry (INDIGITAL) — Sḵwx̱wú7mesh Wolf Clan + Nam̓gis Thunderbird Clan  
**Cultural protocol owner:** Austin Harry  
**Current sprint date:** 2026-05-13 evening  

> Living document. This map is the operator-facing record of what Austin has approved, what is internal-only, what is pending, and what must not ship. Signal approvals are acceptable for sprint speed if captured with timestamp; formal contract terms supersede this map once signed.

## Consent Floor

Project-level AI Use Protocols and Principles & Protocols were signed off on 2026-05-11. That creates permission to experiment inside the agreed framework, not permission to ship every output.

> **2026-05-22 authorization expansion.** Austin has explicitly authorized the project to (a) use the Coast Salish artwork he provided via the Google Drive drop for internal/show-development experimentation, and (b) internally develop and test Austin-style / Coast Salish-style generated visual experiments for this project. Public/show/sponsor/social/press use is still gated by per-output Austin OK unless Darren explicitly states otherwise for a specific output. The full amendment is recorded in [austin-authorization-expansion-2026-05-22.md](austin-authorization-expansion-2026-05-22.md); the sign-off log below has the dated row.

Default state for all source files, model outputs, morph renders, public copy, and sponsor-facing material is **pending / internal-only** until Austin explicitly approves the specific item or category. Internal/show-development experimentation using Austin's Drive artwork or in Austin's authorized style register is permitted under the 2026-05-22 expansion; outputs from that work carry an `Austin-authorized internal/show-development prototype` label until separately cleared.

Hard rules:

- No public-facing render, social post, projector asset, sponsor deck image, or press still ships without Austin's per-output OK.
- No invented-from-scratch crests in Austin's style. The 2026-05-22 expansion authorizes style/grammar exploration but does **not** authorize crest invention.
- Training, img2img, style transfer, ControlNet, LoRA, and StreamDiffusion tests are internal recipe and show-development work under the 2026-05-22 expansion; any external surface still requires per-output Austin OK.
- Austin can revoke or restrict a source piece, motif, morph, phrase, or generated output. Operator response target: remove from active Resolume / show playlist the same day.
- Public framing language is in scope for consent, not only visuals.

## Status Vocabulary

Use these exact statuses in tables and manifests.

| Status | Meaning |
|---|---|
| `pending` | Not yet reviewed by Austin. Internal planning only. |
| `internal-experiment-ok` | May be used for private pipeline tests. Not for Austin-facing candidate art unless separately cleared. |
| `approved-for-training` | Source file may be included in LoRA/style-transfer training. Outputs still need separate approval. |
| `approved-for-private-review` | May be shown to Austin / Pravin / SSD team for critique. Not public. |
| `approved-for-projector-test` | May be sent to venue/test operator for technical projection only. Not public. |
| `approved-for-show` | May be used in the May Space Centre installation. |
| `approved-for-public-comms` | May appear in wall card, sponsor copy, social, press, or documentation. |
| `restricted` | Do not use unless Austin later changes the call. |
| `revoked` | Remove from active use and mark prior use notes. |

## Source Assets

Canonical source inventory for v2 Drive ingestion is:

```text
austin-v2-ingest/provenance/manifest.csv
```

That manifest tracks per-file `austin_consent`; this map tracks the higher-level consent logic and public-output approvals.

| Source group / piece | Source location | Proposed use | Current status | Notes / restrictions |
|---|---|---|---|---|
| Austin curated Drive drop | `austin-v2-ingest/inbox/` after received | v2 training candidates; Track 2 primitive candidates | `pending` | Triage first. Reject installation context, product photos, third-party logos, and text-heavy plates. |
| Clean vector / flat design plates from Austin Drive | `austin-v2-ingest/approved/` after triage | LoRA v2 training; primitive decomposition | `pending` until manifest rows updated | Per-file consent lives in manifest; training requires `approved-for-training` or explicit batch OK. |
| Source vectors from Austin Drive | `track2-deterministic/source-vectors/` after received | deterministic primitive decomposition and morphs | `pending` | Every primitive and morph pair needs Austin review before output use. |
| Public portfolio scrape | `austin-reference/` | v1/v1.5 internal recipe proof only | `internal-experiment-ok` | Do not use v1/v1.5 outputs as candidate public art. Public scrape proved recipe/data lessons; Drive set is canonical. |
| John projector test pack AI stress plates | `austin-reference/john-projector-test-pack-v1_2026-05-13.zip` | technical projection stress only | `pending` | If Darren sends, send only with the technical-test caveat. Not Austin source. Not public artwork. Not show content. |

## Motifs / Subjects

This table does not approve a motif by itself. It tracks which subjects need Austin's call once source pieces are visible.

| Motif / subject | Source piece(s) | Proposed role | Current status | Questions for Austin |
|---|---|---|---|---|
| Thunderbird | TBD from Austin Drive; KwiKwi / Salish Spirit candidates if provided | Pearl-passing figure; center lineage panel | `pending` | Is Thunderbird the sole pearl-passer? Any restrictions on this role? |
| Three pearl shapes | Austin's May 11 pearl vision | Core pearl-interior morph cycle | `pending` | Are the three shapes crescent / ovoid / U-form, or different named forms? |
| Orca / killer whale | TBD from Austin Drive | left/right stress/eval subject; possible morph anchor | `pending` | Any source-specific restrictions? |
| Salmon | TBD from Austin Drive | bioregional subject; possible morph anchor | `pending` | Any source-specific restrictions? |
| Wolf | TBD from Austin Drive | possible morph anchor | `pending` | Clan/family considerations? |
| Raven | TBD from Austin Drive | possible morph anchor | `pending` | Any brand/IP overlap if from collaboration work? |
| Sínulhka / two-headed serpent | TBD from Austin Drive | possible lineage element | `pending` | Is this appropriate for this show context? |
| Plant motifs | TBD from Austin Drive | ecological bridge / v2 training diversity | `pending` | Which plant motifs can travel into SSD context? |
| Any ceremonial / family-restricted forms | Austin to identify | no use | `pending` | Add immediately to restricted table below. |

## Restricted / No-Use Items

| Item | Restriction reason | Source / decision record | Status |
|---|---|---|---|
| TBD | Austin to identify | | `pending` |

## AI Workflow Permissions

Project-level protocol allows experimentation, but each workflow still has operational limits.

| Workflow | Allowed scope right now | External-use gate | Notes |
|---|---|---|---|
| v2 LoRA training on Austin curated Drive | `pending` until Austin's Drive arrives and files are triaged; use only approved source files | Every generated output needs Austin OK before public/show use | Training recipe validated with clean subset; Drive set is canonical. |
| img2img / style transfer on Austin-approved pieces | `internal-experiment-ok` only | Austin reviews output before public/show use | Use source-preserving settings; reject outputs that invent new crests. |
| ControlNet lineart from Austin-approved pieces | `internal-experiment-ok` only | Austin reviews output before public/show use | Better for preserving structure than free generation. |
| StreamDiffusion / SDTD live style layer | `pending` | Austin must approve representative look and operating constraints | Prav identified this as make-or-break, but live outputs require clear guardrails. |
| IP-Adapter using Austin references | `internal-experiment-ok` only | Austin reviews output before public/show use | Current public portfolio references pulled installation context; use Drive clean plates only. |
| AnimateDiff + Austin LoRA | `restricted` for now | Reopen only by explicit operator call | v1 test collapsed to decorative wallpaper; do not spend more sprint time here. |
| Deterministic Track 2 primitive morphs | `internal-experiment-ok` on placeholder geometry; real Austin source pending | Austin approves primitives, morph pairs, and final renders | Production-safe center path. Uses Austin's actual shapes, not neural invention. |

## Output Approval Queue

Use one row per concrete output. Do not collapse "the model" and "the output"; approval of training does not approve generated images.

| Output / asset | Source / workflow | Intended use | Current status | Austin review record | Notes |
|---|---|---|---|---|---|
| v2 LoRA eval contact sheet | `scripts/eval_lora.py` after Drive train | internal quality judgment | `pending` | | Show only if Darren decides it is useful and caveated as recipe proof. |
| v2 still candidates, if any pass | v2 LoRA | possible private Austin review | `pending` | | Must be watermark-free and not invented crest artwork. |
| Temporal style smoke clips | `scripts/run_temporal_style_smoke.py` | internal motion test; possible left/right atmosphere later | `pending` | | Only after v2 still eval passes. |
| Track 2 primitive morph previews | `track2-deterministic/scripts/morph_engine.py` | private Austin review; possible center panel | `pending` | | Every pair requires row-level approval in `morph_pairs.csv`. |
| Pearl triptych mock | `austin-reference/pearl-triptych-mock/` | internal composition reference | `internal-experiment-ok` | | No Austin motifs. Do not present as cultural/artwork claim. |
| John projector stress pack | `austin-reference/john-projector-test-pack-v1_2026-05-13.zip` | projector technical test | `pending` | | AI stress plates only; not Austin source or public artwork. |

## Public Framing Language

Austin must review wording that interprets his pearl vision, teaching role, Nations/clans, or the AI process.

| Phrase / claim | Where it may appear | Current status | Austin wording / notes |
|---|---|---|---|
| "Austin's pearl vision" | wall card, sponsor copy, internal deck | `pending` | |
| "Thunderbird is passing down a pearl" | wall card, program, sponsor copy | `pending` | |
| "the pearl has three shapes swirling and morphing inside it" | wall card, program | `pending` | Confirm exact "three shapes." |
| "teaching" / "teachings" | wall card, program, sponsor copy | `pending` | Ask how explicit this can be. |
| "Coast Salish design forms" | wall card, technical description | `pending` | Austin may prefer different specificity. |
| "formline primitives" / "crescent, ovoid, U-form" | technical/sponsor copy | `pending` | Working assumption only. |
| "Sḵwx̱wú7mesh Wolf Clan + Nam̓gis Thunderbird Clan" | attribution line | `pending` | Confirm spelling/order before print. |
| "AI trained on Austin's work" | sponsor/technical copy | `pending` | Must be framed as consented collaboration, not extraction. |
| "style transfer in Austin's register" | technical description | `pending` | Avoid implying generic style ownership or automatic generation. |

Draft surfaces awaiting review:

```text
docs/space-center/drafts/wall-card-pending-austin-review-2026-05-14.md
docs/space-center/drafts/sponsor-impact-program-copy-pending-austin-review-2026-05-14.md
docs/space-center/drafts/internal-team-description-pending-austin-review-2026-05-14.md
```

| Draft line | Phrase / claim to approve | Surface(s) | Current status | Austin wording / notes |
|---|---|---|---|---|
| WC-01 | "Salish Sea Dreaming: Inside the Pearl" | wall card | `pending` | |
| WC-02 / SP-04 / IT-03 | "three windows into one shared/single pearl interior" | wall card, sponsor copy, internal | `pending` | |
| WC-03 / SP-03 / IT-02 | "Thunderbird shares / is sharing a pearl" | all three | `pending` | |
| WC-03 / SP-03 / IT-02 | "three Coast Salish design forms" / "three design forms" | all three | `pending` | Confirm exact three shapes and preferred terminology. |
| WC-04 / SP-03 / IT-02 | "move, breathe, transform, swirl, morph, and teach" | all three | `pending` | Confirm whether "teach" is appropriate publicly. |
| WC-06 / IT-03 / IT-05 | "lineage layer" | wall card, internal | `pending` | |
| WC-06 / IT-05 / IT-07 | "decomposed, transformed, and recomposed without inventing new crests" | wall card, internal | `pending` | |
| WC-07 / SP-07 / IT-06 | "AI as a constrained / consented tool under artist direction" | all three | `pending` | |
| SP-02 | "digital Coast Salish design practice brings ancestral form, contemporary tools, and public-space media into conversation" | sponsor copy | `pending` | |
| SP-05 | "Austin-approved formline morphing" | sponsor copy | `pending` | |
| SP-06 | "not to translate Coast Salish knowledge into data" | sponsor copy | `pending` | Also Carol Anne / Indigenomics review. |
| SP-08 | "working prototype ... toward future interactive and fulldome experiences" | sponsor copy | `pending` | Pravin / Carol Anne review. |
| IT-08 | "StreamDiffusion / SDTD can become a live atmospheric layer if approved" | internal | `pending` | |

## Attribution + Credit Terms

Draft defaults to review with Austin:

- Austin appears as co-leading artist, not asset provider.
- Attribution line includes INDIGITAL and the Nations/clans only if Austin confirms exact wording.
- Any social/public still based on Austin source material credits Austin in the post body/caption, not only hidden alt text.
- Generated outputs should identify the workflow honestly when sponsor-facing: source-approved / AI-assisted / internal test as applicable.
- If other advisors are involved (Xwalacktun, James Harry, Squamish Lil'wat Cultural Centre, IM4 Lab, etc.), credit/compensation terms are agreed before public naming.

## Retention, Revocation, Provenance

| Topic | Current default |
|---|---|
| Source files | Austin retains full rights. SSD uses only for the agreed Phase 2 sprint workflows unless later contract expands scope. |
| Trained LoRA checkpoints | Internal project artifact; not shared publicly; not reused outside agreed SSD Phase 2/future-venue path without Austin consent. |
| Rendered outputs | Internal until row-level approved. Approved outputs must record source/workflow/date/version. |
| Right to revoke | Austin can revoke or restrict use; operator removes from active show playlist same day and records revocation here. |
| Commercial / sponsor terms | Any sponsor-facing derivative, touring extension, merch, or external R&D use requires separate written consent and compensation terms. |
| Provenance record | `austin-v2-ingest/provenance/manifest.csv`, this map, `track2-deterministic/primitives.csv`, and `track2-deterministic/morph_pairs.csv` together form the audit trail. |

## Sign-Off Log

| Date | Item reviewed | Austin OK / change requested | Channel + timestamp | Operator follow-up |
|---|---|---|---|---|
| 2026-05-11 | Project AI Use Protocols + Principles & Protocols | Signed off; Austin said he would compile images and share Drive | Signal / project notes | Await Drive; keep outputs internal until per-output OK |
| 2026-05-11 | Pearl vision | Austin offered pearl / Thunderbird / three shapes framing | Signal / project notes | Confirm exact three shapes + public wording |
| 2026-05-22 | Authorization expansion: Drive artwork use + Austin-style / Coast Salish-style generated visual experiments | Austin explicitly authorized both for internal/show-development scope. Public/show/sponsor/social/press use still gated by per-output Austin OK unless Darren states otherwise. | Darren-conveyed operator session, 2026-05-22 | Honor in all subsequent internal probes; label outputs `Austin-authorized internal/show-development prototype`; record per-output OKs in this log as they happen. Full amendment in `austin-authorization-expansion-2026-05-22.md`. |

## Immediate Review Agenda

For the first Austin/Prav review after the Drive lands:

1. Confirm whether Drive files are approved for internal v2 LoRA training, Track 2 primitive decomposition, or both.
2. Confirm the exact three shapes inside the pearl.
3. Identify any source pieces, motifs, or forms that are restricted or no-use.
4. Confirm whether first-look v2 outputs should be shown to Austin as recipe proof, and how they should be labeled.
5. Review public wording for "pearl," "teaching," "Thunderbird passing," "three shapes," and Austin's attribution line.

**Updated by:** Codex / Darren workflow  
**Last updated:** 2026-05-13 evening
