# French Quality-First Translation Design

## Goal

Build a quality-first French translation pipeline for the Kaikki French package that keeps local inference as the default path, uses only limited cloud escalation for hard cases, and continuously reduces manual review work over time.

## Context

The current French package state is materially different from the Japanese package:

- Total French entries: `2,142,991`
- Untranslated entries: `2,131,458`
- Entries missing `meaning_source_text`: `44,853`
- Unique non-empty source glosses: `1,930,503`

Pilot runs established these constraints:

- `qwen2.5:3b` is operationally stable for French, but quality is not sufficient for direct full-rollout use.
- `gemma3:4b` is better than `qwen2.5:3b`, but still not good enough to trust for direct full-rollout use.
- A large share of French errors come from morphology-style dictionary glosses, not from ordinary free-form definitions.
- Repeated manual correction of the same template families is wasteful. Those families must move into rules.

User preference constraints:

- Quality first
- Local-first
- Small amount of cloud assistance allowed

## Problem Statement

French quality problems are not dominated by infrastructure failures. They are dominated by data-shape mismatch:

- many entries are grammatical templates, not semantic definitions
- many entries contain inflection labels, alphabet entries, contraction notes, language labels, or taxonomy-style definitions
- local small models often leave Latin-script fragments, mistranslate grammatical labels, or produce mixed-language outputs

If the system continues using a single translation path for all French entries, manual review remains too expensive and scales badly.

## Recommended Strategy

Use a staged pipeline:

1. classify each entry by type
2. translate template-like entries with deterministic rules
3. send normal definition entries to the local model
4. run risk detection on local outputs
5. escalate only high-risk residuals to a stronger cloud model
6. send only final residuals to manual review
7. convert manual review outcomes into reusable rules or overrides

This keeps most volume local, preserves quality, and prevents repeated human effort on the same pattern class.

## Architecture

### 1. Input Layer

Input remains:

- `artifacts/translated/kaikki_fr_words.jsonl`

The pipeline must preserve any already accepted French translations and only process unresolved or newly selected batch items.

### 2. Classification Layer

Each French entry is classified into one of four buckets:

- `blocked`
  - missing or unusable `meaning_source_text`
- `rule_based`
  - morphology or dictionary-template patterns that should be translated deterministically
- `local_candidate`
  - ordinary definitions suitable for local inference
- `escalation_candidate`
  - complex or high-risk entries that should bypass or later escalate beyond the local model

The first implementation only needs reliable classification for:

- `blocked`
- `rule_based`
- `local_candidate`

`escalation_candidate` can initially be derived after local inference using the reviewer.

### 3. Rule Translation Layer

This layer handles high-frequency French template families before any model is invoked.

Priority template families:

- `Première/Deuxième/Troisième personne ...`
- `Féminin singulier de ...`
- `Masculin pluriel de ...`
- `Pluriel de ...`
- `Participe présent/passé de ...`
- `Contraction de ...`
- `... lettre de l’alphabet ...`

Example rule outputs:

- `Première personne du singulier de l’indicatif présent de X`
  - `动词“X”的直陈式现在时第一人称单数形式`
- `Féminin singulier de X`
  - `X 的阴性单数形式`
- `Pluriel de X`
  - `X 的复数形式`
- `Participe présent de X`
  - `动词“X”的现在分词`

This layer must be deterministic, tested, and preferred over model translation whenever matched.

### 4. Local Translation Layer

The local model handles only normal-definition entries that are not blocked and not rule-translated.

Current model guidance:

- preferred local baseline: `gemma3:4b`
- fallback local baseline: `qwen2.5:3b`

The local model is not treated as a universal French solution. It is a first-pass translator for lower-risk definitions.

The local layer must run in small, checkpointed batches.

### 5. Risk Review Layer

All local outputs are reviewed by deterministic rules.

Risk levels:

#### Level 1: Must escalate or must be manually reviewed

- empty output
- English grammar words left in output
- obvious mixed-language output
- fallback-like output such as uncertainty phrases
- template glosses not converted into Chinese template form
- obvious semantic contradiction or impossible structure

#### Level 2: Review queue candidates

- residual Latin-script fragments
- unusual proper nouns, alphabet entries, or language-code entries
- outputs that are readable but structurally suspicious

This layer produces:

- a structured review report
- a manual-review queue
- an escalation subset for cloud translation

### 6. Cloud Escalation Layer

Cloud usage must remain limited and targeted.

Cloud is used for:

- local outputs flagged as high risk
- structurally complex residuals
- entries that repeatedly fail local review

Cloud is not the mainline translator for the whole French package.

This keeps cost controlled while protecting quality.

### 7. Manual Finalization Layer

Humans review only the final residual queue after:

- rules
- local model
- risk escalation

Manual edits must be routed into one of two destinations:

- new reusable rule patterns
- `supplemental_overrides.json` for true long-tail exceptions

The system should avoid using humans as a default second-pass translator for broad batches.

## Components

To keep the implementation maintainable, responsibilities should be split across focused components.

### `french_classifier`

Responsibility:

- classify entries into processing buckets

Inputs:

- French JSONL batch or full artifact

Outputs:

- classified entries
- classification summary

### `french_rule_translator`

Responsibility:

- match template families
- emit deterministic Chinese glosses

Inputs:

- `rule_based` entries

Outputs:

- translated entries
- rule hit report
- unmatched template report

### `french_batch_translator`

Responsibility:

- run local translation for local candidates
- optionally run cloud escalation for high-risk residuals

Inputs:

- `local_candidate` batch

Outputs:

- local output
- escalation output
- checkpoint data
- batch summary

### `french_batch_reviewer`

Responsibility:

- run risk heuristics
- produce review and escalation queues

Inputs:

- translated batch output

Outputs:

- review report
- high-risk entry list
- manual queue

### `french_batch_repair`

Responsibility:

- apply manual corrections
- generate correction reports
- emit rule candidates and override candidates

Inputs:

- reviewed batch output
- correction decisions

Outputs:

- corrected batch
- correction report
- rule candidate list
- override candidate list

## Batch Artifact Convention

Each batch should produce a consistent family of artifacts:

- `batch.input.jsonl`
- `batch.rule.jsonl`
- `batch.local.out.jsonl`
- `batch.escalated.out.jsonl`
- `batch.review.json`
- `batch.manual-corrections.json`
- `batch.corrected.jsonl`

This ensures every decision is traceable and reversible.

## First Implementation Scope

The first implementation should stay narrow.

Included:

- French classification for `blocked`, `rule_based`, `local_candidate`
- first-pass French morphology/template rules
- upgraded French risk-review rules
- re-run on a `200` entry batch

Excluded for now:

- full automatic cloud routing sophistication
- full-package mergeback automation
- package rebuild integration
- broad Android sync work
- full zero-human workflow

## Validation Plan

Validation happens at three levels.

### Unit Validation

Required:

- template classification tests
- template translation tests
- review-rule tests

Goal:

- repeated French structure errors are prevented in code, not re-discovered manually

### Batch Validation

For each batch, track:

- total batch size
- rule hit count
- local translation count
- high-risk count
- manual correction count
- remaining high-risk count after correction

Primary success trend:

- fewer entries need human attention over time

### Quality Sampling

For every batch, manually sample:

- template-translated entries
- normal local-model entries
- escalated entries
- corrected residuals

This prevents metric-only regressions.

## Success Criteria

The design is working when:

- template-family errors stop dominating review reports
- risk reports become more concentrated and smaller
- manual corrections increasingly target true long-tail cases instead of repeated template patterns
- batch size can increase from `200` to `1000` without quality collapse

## Stop Conditions

Do not expand batch size if:

- high-risk ratios do not improve
- the same template errors keep recurring
- manual load does not decrease
- escalated outputs still require large-scale manual rewriting

If these happen, the pipeline must be improved before scaling further.

## Recommendation

Proceed to implementation.

The first concrete implementation target should be:

1. French classifier
2. French template rule translator
3. Improved risk reviewer
4. Re-run a `200` entry batch
5. Compare pre/post manual review load

This is the narrowest implementation that can prove the strategy works.
