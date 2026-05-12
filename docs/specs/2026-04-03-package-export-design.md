# Dictionary Package Export Design

## Goal

Export the generated SQLite dictionary into a stable app-facing package with a machine-readable manifest.

## Scope

The package should contain:

- the SQLite database file
- a manifest describing schema version, counts, sources, translation status, and search capabilities

## Design

### Package Layout

Export into a dedicated folder under `artifacts/package/`:

- `dictionary.db`
- `manifest.json`

### Manifest

The manifest should include:

- `schema_version`
- `db_filename`
- `entry_count`
- `language_counts`
- `translation_summary`
- `search_capabilities`
- `source_registry_path`
- `feasibility_report_path`

### Purpose

This gives the Android side a stable, versioned contract without requiring it to inspect internal pipeline reports directly.

## Success Criteria

- export script creates `artifacts/package/dictionary.db`
- export script creates `artifacts/package/manifest.json`
- manifest reflects current database counts and pipeline metadata
