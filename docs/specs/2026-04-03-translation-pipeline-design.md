# Translation Pipeline Design

## Goal

Add a first-class translation stage to the dictionary feasibility pipeline so Japanese and French source glosses can be converted into Chinese meanings before SQLite packaging.

## Problem

The current prototype mixes source-language glosses and Chinese meanings in `meaning_zh`. That was sufficient for fixture-level parser checks, but it is the wrong data model for a Chinese-targeted learning app and it prevents a real translation pipeline from being inserted cleanly.

## Design

### Data Model

Extend `NormalizedWord` with:

- `meaning_source_text`: the gloss text taken directly from the source dictionary
- `meaning_source_lang`: the language of `meaning_source_text`

`meaning_zh` remains the final Chinese field used by the app-side dictionary package.

### Parsing Rules

- JMdict fixture parser:
  - if a Chinese gloss exists, write it to `meaning_zh`
  - preserve the selected source gloss in `meaning_source_text`
  - set `meaning_source_lang` to `zh` or `en`
- Kaikki French parser:
  - keep `meaning_zh` empty
  - write the first usable French gloss to `meaning_source_text`
  - set `meaning_source_lang` to `fr`

### Translation Stage

Add a batch translation pipeline module that:

1. loads normalized JSONL records
2. selects entries where `meaning_zh` is empty and `meaning_source_text` is available
3. translates them through a provider interface using cache-aware lookup
4. writes translated JSONL artifacts
5. emits a small report summarizing how many entries were translated

The provider remains pluggable. The first executable version will use a deterministic glossary-backed provider for verification and local reproducibility.

### SQLite Packaging

SQLite should retain both the source gloss and the Chinese gloss:

- `meaning_source_text`
- `meaning_source_lang`
- `meaning_zh`

This preserves provenance and supports future QA or fallback UI.

### Reporting

Reports should distinguish:

- source-gloss coverage
- Chinese-meaning coverage

That separation is required to judge whether the pipeline is structurally complete versus Chinese-ready.

## Success Criteria

- normalized records preserve source gloss separately from Chinese output
- a translation script can convert parser output into translated JSONL artifacts
- SQLite packaging includes source gloss and Chinese gloss columns
- reports clearly show source coverage versus Chinese coverage
- full test suite passes after the refactor
