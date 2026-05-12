# Dictionary Search Design

## Goal

Add an app-facing local search layer on top of the prototype SQLite dictionary package so translated entries can be queried by lemma and text match.

## Scope

This module stays on the data-package side. It does not build Android UI. It adds:

- SQLite full-text search support
- Python query helpers for exact and fuzzy lookup
- a CLI for manual inspection of packaged dictionaries

## Design

### SQLite

Extend the prototype database with an FTS table derived from:

- `lemma`
- `surface`
- `reading_or_ipa`
- `meaning_source_text`
- `meaning_zh`

The canonical `words` table remains the source of truth.

### Query Service

Create a focused service module that supports:

- exact lookup by lemma and language
- FTS lookup by free-text query and optional language filter

Results should expose both source gloss and Chinese gloss so app-side consumers can decide how to present fallback data.

### CLI

Add a script that opens the packaged SQLite database and prints search results as JSON lines or formatted text for debugging.

## Success Criteria

- SQLite build creates a queryable FTS index
- Python query service can return exact and fuzzy matches
- CLI can search the generated `prototype.db`
- tests prove both exact and FTS search behavior
