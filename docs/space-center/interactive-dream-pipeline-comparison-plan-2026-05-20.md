# Interactive Dream Pipeline Comparison Plan - 2026-05-20

Status: INTERNAL Agent G planning document.

No rendering, no diffusion, no LoRA training.

This document designs a controlled experiment for the future interactive
dreaming lane. The experiment should not run until all three candidate
pipelines consume the same grammar file and the same prompt-to-scene-plan JSON
schema. Otherwise the comparison will mostly measure inconsistent assumptions,
not pipeline behavior.

## Purpose

Broad Austin-style LoRA/style-transfer did not produce a reliable or safe
direction. The next experiment should compare narrower pipelines that keep
visitor prompts bounded by explicit scene planning, cultural safety metadata,
and reviewable primitive/procedural structure.

Candidate pipelines:

- A. prompt -> scene graph -> deterministic primitive renderer
- B. prompt -> scene graph -> procedural structure -> diffusion finisher
- C. prompt -> diffusion image -> edge/contour extraction -> primitive cleanup

The controlled question is:

```text
Given the same prompt, grammar file, schema version, safety policy, canvas,
seed set, and still-output requirements, which pipeline produces the most
reviewable internal dream stills with the least cultural/safety ambiguity?
```

## Cultural And Safety Boundary

All outputs from this lane are internal-only research artifacts.

No output from this experiment is public-ready, Austin-approved, Austin-authored,
or approved as a cultural interpretation. Public projection, publication,
recording, press use, visitor-facing display, or external sharing is blocked
until Austin reviews the exact output and gives per-output approval.

Per-output review means the review record must name:

- output file path;
- output hash or immutable export identifier;
- prompt ID;
- pipeline ID and version;
- grammar file hash;
- scene-plan schema version;
- safety status;
- Austin review date and decision.

Visitor prompts are not allowed to bypass this boundary. Human figures, animal
figures, eyes/faces, named beings, supernatural subjects, crest-like imagery,
chiefs/specific people, Thunderbird, serpent, exact Austin-source reuse, and
James Harry relief/wrapped-form translation remain review-needed or blocked
unless a separate approval path exists.

The five test prompts below are therefore stress tests for the planning system,
not permission to make public imagery.

## Source Context

Use these local references as the starting source map:

- [primitive-grammar-contract-2026-05-19.md](primitive-grammar-contract-2026-05-19.md)
- [austin-screen-share-visual-grammar-brief-2026-05-19.md](austin-screen-share-visual-grammar-brief-2026-05-19.md)
- [primitive-grammar-visual-acceptance-criteria-2026-05-20.md](primitive-grammar-visual-acceptance-criteria-2026-05-20.md)
- [prompt-to-primitive-scene-review-index-2026-05-19.md](prompt-to-primitive-scene-review-index-2026-05-19.md)
- [STATE-2026-05-20-post-water-v002.md](STATE-2026-05-20-post-water-v002.md)

## Grammar Source / Provenance Model

The comparison needs one shared grammar file before any renderer runs. Each
grammar atom, role, phrase, palette role, safety rule, topology rule, and render
hint should carry provenance.

Minimum provenance categories:

| Provenance kind | Meaning | Allowed use in experiment |
|---|---|---|
| `austin_taught` | Directly taught, demonstrated, or transcript-grounded from Austin notes/screenshare material. This still does not mean public-approved. | May drive internal scene plans and deterministic/procedural studies when source IDs are attached. Still needs per-output Austin review. |
| `inferred` | Engineering or design inference from Austin-taught material, existing water-flow experiments, topology specs, or system constraints. | May drive internal experiments only when labeled as inference. Must be visible in debug overlays and review notes. |
| `needs_review` | Hypothesis, unresolved cultural question, figure behavior, prompt-driven subject interpretation, or weakly sourced extension. | May appear in scene plans as a flagged review question. Should not be hidden inside final-looking output. |
| `blocked` | Known blocked subject, source reuse, public claim, or unsafe visitor-prompt expansion. | Must not be rendered except as text in audit/debug records. |

Suggested grammar atom shape:

```json
{
  "grammar_atom_id": "water_phrase.circle_crescent_crescent_trigon.v001",
  "label": "Water phrase order",
  "claim": "A water phrase can be planned as circle origin -> crescent -> crescent -> trigon release.",
  "primitive_sequence": ["circle", "crescent", "crescent", "trigon"],
  "default_roles": ["origin", "cupping_phase", "cupping_phase", "release"],
  "provenance": [
    {
      "kind": "austin_taught",
      "source_id": "austin_screen_share_2026_05_18",
      "source_path": "docs/space-center/austin-screen-share-visual-grammar-brief-2026-05-19.md",
      "evidence_note": "Austin explained circle impact followed by crescents and trigon as water/ripple sequence.",
      "review_status": "internal_unapproved"
    }
  ],
  "safety": {
    "public_use": "blocked_until_exact_output_review",
    "requires_austin_review": true
  }
}
```

The grammar file should reject untagged atoms. If a renderer or prompt planner
uses a rule without provenance, that output fails the experiment.

## Scene-Plan JSON Schema

The scene plan is the contract between prompt parsing, safety review, procedural
structure, primitive rendering, and any future diffusion step. It should be
validated before any still is rendered.

Draft schema:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://salish-sea-dreaming.local/schemas/interactive-dream-scene-plan-v001.json",
  "title": "InteractiveDreamScenePlan",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "scene_id",
    "prompt",
    "safety",
    "canvas",
    "grammar_context",
    "entities",
    "structures",
    "primitive_phrases",
    "render_intent",
    "outputs"
  ],
  "properties": {
    "schema_version": {
      "const": "interactive_dream_scene_plan_v001"
    },
    "scene_id": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9_\\-]*$"
    },
    "prompt": {
      "type": "object",
      "additionalProperties": false,
      "required": ["prompt_id", "raw_text", "normalized_text"],
      "properties": {
        "prompt_id": {
          "type": "string",
          "pattern": "^P[0-9]{2}$"
        },
        "raw_text": {
          "type": "string",
          "minLength": 1
        },
        "normalized_text": {
          "type": "string",
          "minLength": 1
        },
        "notes": {
          "type": "string"
        }
      }
    },
    "safety": {
      "type": "object",
      "additionalProperties": false,
      "required": ["lane_status", "public_use", "requires_austin_review", "blocked_subjects"],
      "properties": {
        "lane_status": {
          "enum": ["internal_only", "blocked"]
        },
        "public_use": {
          "const": "blocked_until_exact_output_review"
        },
        "requires_austin_review": {
          "const": true
        },
        "blocked_subjects": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "review_questions": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "canvas": {
      "type": "object",
      "additionalProperties": false,
      "required": ["width", "height", "color_space", "background"],
      "properties": {
        "width": {
          "const": 1920
        },
        "height": {
          "const": 1080
        },
        "color_space": {
          "const": "sRGB"
        },
        "background": {
          "enum": ["black", "neutral_review"]
        }
      }
    },
    "grammar_context": {
      "type": "object",
      "additionalProperties": false,
      "required": ["grammar_file", "grammar_version", "grammar_hash", "provenance_policy"],
      "properties": {
        "grammar_file": {
          "type": "string"
        },
        "grammar_version": {
          "type": "string"
        },
        "grammar_hash": {
          "type": "string"
        },
        "provenance_policy": {
          "const": "all_referenced_atoms_must_have_provenance"
        }
      }
    },
    "entities": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/entity"
      }
    },
    "structures": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/structure"
      }
    },
    "primitive_phrases": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/primitive_phrase"
      }
    },
    "render_intent": {
      "type": "object",
      "additionalProperties": false,
      "required": ["pipeline_id", "seed", "allowed_methods", "disallowed_methods"],
      "properties": {
        "pipeline_id": {
          "enum": ["A_deterministic_primitives", "B_procedural_diffusion_finisher", "C_diffusion_extract_cleanup"]
        },
        "seed": {
          "type": "integer",
          "minimum": 0
        },
        "allowed_methods": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "disallowed_methods": {
          "type": "array",
          "contains": {
            "const": "lora_training"
          },
          "items": {
            "type": "string"
          }
        },
        "diffusion": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "enabled": {
              "type": "boolean"
            },
            "model_id": {
              "type": "string"
            },
            "negative_constraints": {
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    "outputs": {
      "type": "object",
      "additionalProperties": false,
      "required": ["output_root", "required_files"],
      "properties": {
        "output_root": {
          "type": "string"
        },
        "required_files": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    }
  },
  "$defs": {
    "provenance_ref": {
      "type": "object",
      "additionalProperties": false,
      "required": ["grammar_atom_id", "kind", "review_status"],
      "properties": {
        "grammar_atom_id": {
          "type": "string"
        },
        "kind": {
          "enum": ["austin_taught", "inferred", "needs_review", "blocked"]
        },
        "review_status": {
          "enum": ["internal_unapproved", "austin_review_needed", "austin_approved_for_named_output", "blocked"]
        },
        "source_id": {
          "type": "string"
        }
      }
    },
    "entity": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "label", "entity_type", "safety_status", "provenance_refs"],
      "properties": {
        "id": {
          "type": "string"
        },
        "label": {
          "type": "string"
        },
        "entity_type": {
          "enum": ["water", "terrain", "sky", "weather", "animal", "human", "plant", "light", "built_object", "abstract"]
        },
        "safety_status": {
          "enum": ["internal", "austin_review_needed", "public_blocked", "blocked"]
        },
        "bounds_norm": {
          "type": "array",
          "minItems": 4,
          "maxItems": 4,
          "items": {
            "type": "number"
          }
        },
        "provenance_refs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/provenance_ref"
          }
        }
      }
    },
    "structure": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "structure_type", "role", "entity_refs", "provenance_refs"],
      "properties": {
        "id": {
          "type": "string"
        },
        "structure_type": {
          "enum": ["path", "mask", "scalar_field", "contour_field", "flock", "school", "weather_transition", "topology_cell_field"]
        },
        "role": {
          "type": "string"
        },
        "entity_refs": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "control_points_norm": {
          "type": "array",
          "items": {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "items": {
              "type": "number"
            }
          }
        },
        "provenance_refs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/provenance_ref"
          }
        }
      }
    },
    "primitive_phrase": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "role", "entity_refs", "structure_refs", "primitive_order", "provenance_refs"],
      "properties": {
        "id": {
          "type": "string"
        },
        "role": {
          "type": "string"
        },
        "entity_refs": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "structure_refs": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "primitive_order": {
          "type": "array",
          "items": {
            "enum": ["circle", "crescent", "trigon", "oval", "line", "mask", "contour"]
          }
        },
        "placement_rule": {
          "type": "string"
        },
        "provenance_refs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/provenance_ref"
          }
        }
      }
    }
  }
}
```

## Test Prompts

Use exactly these five prompts for the first comparison set:

| Prompt ID | Raw prompt | Safety interpretation |
|---|---|---|
| `P01` | `orca breaching` | Animal/figure prompt. Internal only; Austin-review-needed. Favor water impact, breach path, spray, and silhouette-safe abstraction over face/detail. |
| `P02` | `children playing on the beach` | Human prompt. Public-blocked by default. For planning only, use non-identifiable abstract small figures or mark as blocked if the pipeline cannot avoid faces/bodies. |
| `P03` | `salmon swimming up a river` | Animal/figure plus water-current prompt. Internal only; Austin-review-needed. Favor river path, upstream motion, school/wake structure, and water phrases over static salmon iconography. |
| `P04` | `rain becoming snow on a mountain` | Safest environment/weather prompt. Internal only; still review-needed for grammar claims. Good first still candidate after grammar/schema land. |
| `P05` | `birds flocking at sunset` | Animal/sky prompt. Internal only; Austin-review-needed. Favor flock path, sky gradient, and motion structure over species-specific or raven-like iconography. |

## Pipeline Comparison

| Pipeline | Flow | Main control | Strengths | Main risks | GPU need | Gate before running |
|---|---|---|---|---|---|---|
| A | prompt -> scene graph -> deterministic primitive renderer | Scene-plan JSON, grammar atom provenance, deterministic layout rules | Most inspectable, repeatable, and culturally bounded. Best for proving the prompt planner and grammar file. | Can look mechanical or under-finished. May fail at visitor delight if primitives are too literal. | No GPU required. | Grammar file v001, schema v001, five validated scene plans, deterministic still renderer. |
| B | prompt -> scene graph -> procedural structure -> diffusion finisher | Same scene-plan JSON plus procedural masks/scalar fields used as strong conditioning | Keeps semantic structure before diffusion. Lets diffusion polish textures while preserving reviewable pre-finish artifacts. | Diffusion may hallucinate figures, faces, species details, style claims, or culturally unsafe motifs. Conditioning may hide provenance in final pixels. | GPU required for diffusion finisher. Procedural pre-finish can run without GPU. | A-style grammar/schema complete, scalar-field v002 complete, procedural stills pass review, GPU stack verified. |
| C | prompt -> diffusion image -> edge/contour extraction -> primitive cleanup | Diffusion raw still, edge/contour extractor, cleanup rules mapped back to grammar | Useful as a stress test for whether diffusion can be tamed after the fact. May discover strong compositions. | Highest risk: diffusion decides content before the grammar. Cleanup may launder unsafe or generic imagery into primitive-looking shapes. | GPU required for diffusion source image. Edge extraction can run without GPU on preexisting fixtures. | Last. Only after GPU verification, safety filters, grammar/schema, and A/B baselines exist. |

## Experiment Controls

The future comparison should hold these fixed:

- Same five prompts and prompt IDs.
- Same normalized prompt text.
- Same scene-plan schema version.
- Same grammar file hash.
- Same canvas: 1920x1080, sRGB.
- Same seed list per prompt: `1001`, `1002`, `1003`, `1004`, `1005`.
- Same blocked-subject policy.
- Same output file naming.
- Same scoring rubric.
- Same review packet structure.

Only the pipeline should vary.

## Exact Still-Output Requirements For Future Experiment

Do not create these outputs until the grammar file and schema have landed.

Experiment root:

```text
track2-deterministic/morph_outputs_INTERNAL/interactive_dream_pipeline_compare_2026-05-20/
```

For each prompt and eligible pipeline, write:

```text
{pipeline_id}/{prompt_id}/scene_plan.json
{pipeline_id}/{prompt_id}/manifest.json
{pipeline_id}/{prompt_id}/final_1920x1080_srgb.png
{pipeline_id}/{prompt_id}/debug_overlay_1920x1080_srgb.png
{pipeline_id}/{prompt_id}/grammar_provenance_report.json
```

Additional pipeline-specific stills:

```text
A_deterministic_primitives/{prompt_id}/primitive_layout_1920x1080_srgb.png
B_procedural_diffusion_finisher/{prompt_id}/procedural_structure_1920x1080_srgb.png
B_procedural_diffusion_finisher/{prompt_id}/diffusion_finished_1920x1080_srgb.png
C_diffusion_extract_cleanup/{prompt_id}/diffusion_raw_1920x1080_srgb.png
C_diffusion_extract_cleanup/{prompt_id}/edge_contour_debug_1920x1080_srgb.png
C_diffusion_extract_cleanup/{prompt_id}/primitive_cleanup_1920x1080_srgb.png
```

Run-level required files:

```text
RUN_MANIFEST.json
SCORING_SHEET.md
contact_sheet_all_final_1920x1080.png
contact_sheet_debug_overlays_1920x1080.png
NO_PUBLIC_USE_INTERNAL_ONLY.txt
```

Still constraints:

- PNG only; no MP4, GIF, or live visitor loop in the first comparison.
- 1920x1080, sRGB, 8-bit PNG.
- No LoRA weights, LoRA training, Austin-style checkpoint, or exact-source
  style transfer.
- No faces or identifiable children in `P02`; if the pipeline cannot enforce
  this, `P02` must be marked blocked for that pipeline.
- Final still and debug overlay must be visually paired in contact sheets.
- `manifest.json` must include prompt ID, pipeline ID, seed, schema version,
  grammar hash, code commit if available, model IDs if diffusion was used,
  safety status, and exact generated file hashes.
- `grammar_provenance_report.json` must list every grammar atom used and its
  provenance kind.
- A still fails if any visible subject or primitive role lacks scene-plan
  provenance.

## Scoring Rubric

Score each prompt/pipeline pair from `0` to `3` on each dimension:

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Safety containment | Blocked or unsafe | Major unresolved risks | Internal-only with flagged review questions | Clean internal artifact with clear review boundary |
| Prompt fidelity | Does not match prompt | Partial subject read | Prompt readable with omissions | Prompt readable and structurally clear |
| Grammar provenance | Missing | Sparse or untraceable | Mostly tagged | Every visible rule/role tagged |
| Primitive/structure legibility | Random or generic | Some structure | Coherent but uneven | Strong scene graph / structure read |
| Reproducibility | Cannot reproduce | Manual or unstable | Mostly deterministic | Fully reproducible from manifest |
| Review usefulness | Not reviewable | Needs heavy explanation | Useful with debug | Strong Austin/internal review artifact |

Any `blocked` safety result overrides the total score.

## GPU Verification Required Before Diffusion

Before running B's diffusion finisher or C's diffusion source image path, a
future GPU worker must verify the actual stack without rendering:

- Host name, OS, GPU model, VRAM, driver version, and CUDA runtime from
  `nvidia-smi` or platform equivalent.
- Python environment path and package lock/export.
- PyTorch CUDA availability and device name.
- `diffusers`, `transformers`, `accelerate`, `safetensors`, `opencv`, and
  `pillow` versions.
- Model cache path, selected model ID, license status, file checksums, and
  expected VRAM budget.
- Whether xFormers, Flash Attention, Metal, CUDA, or CPU fallback will be used.
- A no-diffusion dry check: imports, CUDA tensor allocation, model metadata
  inspection if needed, output directory writability, and disk-space check.
- Safety filter availability and configuration.
- Determinism settings: seed handling, scheduler version, precision mode, and
  whether results are expected to be bitwise or only visually reproducible.

Do not run diffusion as part of the verification step. Verification only decides
whether the GPU lane is eligible to run later.

## Work That Can Run Without GPU

These tasks are safe to build on CPU/local tooling before any diffusion work:

- Codify the shared grammar file from Austin teaching notes with provenance
  tags.
- Implement and validate the scene-plan JSON schema.
- Create five scene-plan examples for the five test prompts.
- Build prompt normalization and blocked-subject checks.
- Build deterministic primitive still rendering for pipeline A.
- Build procedural structure/mask/scalar-field pre-finish stills for pipeline B,
  after scalar-field v002 is complete.
- Build OpenCV edge/contour extraction and primitive cleanup tools using
  supplied fixture images only, not newly generated diffusion images.
- Build manifest, hash, contact-sheet, schema-validation, and scoring utilities.
- Build review packets and debug overlays.

## First Build Order

Do not run all three render experiments immediately.

Recommended order:

1. Agent C or Agent G codifies the grammar file from Austin teaching notes, with
   provenance tags for `austin_taught`, `inferred`, `needs_review`, and
   `blocked`.
2. Agent A or Agent E builds the prompt -> scene-plan JSON schema and five
   validated scene-plan examples.
3. Agent A builds pipeline A deterministic primitive stills first, because this
   tests the shared grammar/schema with the lowest cultural and technical risk.
4. Agent B waits until scalar-field v002 is done, then builds pure procedural
   stills before any diffusion finisher is attached.
5. A new GPU worker verifies the GPU stack and only later runs
   diffusion-as-finisher or diffusion-then-extract. This worker should not start
   until the grammar/schema and A/B CPU baselines exist.
6. Pipeline C runs last, if at all, because it lets diffusion choose content
   before grammar cleanup.

First actual still target after the shared grammar/schema lands should be
pipeline A for `P04 rain becoming snow on a mountain`, then `P03 salmon swimming
up a river` as the first water/animal stress test. `P02 children playing on the
beach` should stay schema-only until the human-figure blocker is explicitly
resolved.

## Stop Conditions

Stop the experiment if any of these happen:

- A scene plan contains an unprovenanced grammar atom.
- A renderer silently drops safety metadata.
- A diffusion path produces faces, identifiable children, crest-like imagery,
  supernatural/named beings, or Austin-source-like replication.
- A final still cannot be reproduced from its manifest.
- A pipeline requires different grammar or schema assumptions than the others.
- An output is described as public-ready or Austin-approved without exact
  per-output review.

## Decision Gate

The plan is landed when this document exists. The experiment is not ready to
render until these shared artifacts exist:

- shared grammar file with provenance tags;
- scene-plan JSON schema file;
- five validated scene-plan examples;
- blocked-subject checker;
- review packet template;
- scoring sheet template.

Only after those land should any still renderer be assigned.
