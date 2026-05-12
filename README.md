# Lexigo

<p align="center">
  <strong>A multilingual vocabulary trainer with offline dictionaries, JLPT-aware Japanese learning paths, and a warm mobile study experience.</strong>
</p>

<p align="center">
  <img alt="Android" src="https://img.shields.io/badge/Android-Kotlin%20%2B%20Compose-3DDC84?style=for-the-badge&logo=android&logoColor=white">
  <img alt="Python" src="https://img.shields.io/badge/Data%20Pipeline-Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/Offline%20Dictionary-SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white">
</p>

Lexigo is an Android vocabulary learning app backed by a local dictionary packaging pipeline. It currently focuses on Japanese and French, with Japanese learning ordered by JLPT-inspired levels instead of random dictionary entries.

The project combines three parts:

- A Jetpack Compose Android app for study, review, search, starring, and progress tracking.
- A Python dictionary pipeline for parsing, translating, validating, packaging, and exporting offline data.
- A Japanese learning-level classifier that maps dictionary rows to N5-N1 where reliable, and keeps uncertain words out of the beginner path.

## Highlights

| Area | What Lexigo Does |
| --- | --- |
| Offline-first | Packages dictionary data into SQLite so the app can search and study without a network dependency. |
| Japanese levels | Uses JLPT source matching, reading-aware fallbacks, low-value filtering, and optional AI classification support. |
| Beginner-friendly reading | Shows kana readings and romaji together wherever Japanese pronunciation is displayed. |
| Study flow | Supports multiple-choice meaning practice, spelling practice, session drafts, review scheduling, and progress stats. |
| Search and collection | Provides dictionary search, word detail pages, starred words, and language-aware lookup. |
| Visual direction | Uses a warm, restrained UI inspired by modern vocabulary apps rather than a generic database browser. |

## Current Status

Lexigo is usable as a self-contained Android prototype.

- Android debug builds compile and package successfully.
- The app can install a generated dictionary package from bundled assets.
- Japanese study queues can prefer `word_learning_levels` when the packaged database contains level metadata.
- Large generated artifacts are intentionally excluded from Git.

Known limitation: full production dictionary packages can be very large, so `artifacts/`, `sources/`, generated databases, and APK outputs are ignored by default.

## Architecture

```text
Lexigo
|-- android-app/                Android app built with Kotlin and Jetpack Compose
|   |-- app/src/main/java/      UI, domain logic, repositories, stores
|   |-- app/src/test/java/      JVM tests for learning, search, review, and utilities
|   `-- app/src/androidTest/    Device/instrumentation tests
|-- src/dict_feasibility/       Python package for dictionary processing
|-- scripts/                    Pipeline entry points and operational scripts
|-- tests/                      Python tests
`-- docs/                       Specs, plans, validation notes, and reports
```

## Data Pipeline

The pipeline is designed to turn raw lexical sources into an app-ready package:

```text
source dictionaries
      |
parse and normalize
      |
translation and validation
      |
SQLite build
      |
JLPT / learning-level enrichment
      |
Android asset sync
```

Main data sources used by the project include:

- JMdict for Japanese dictionary entries.
- Kaikki / Wiktionary-derived data for French entries.
- Tatoeba-style sentence data where applicable.
- JLPT vocabulary sources for Japanese learning-level signals.

## Quick Start

### Python Pipeline

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e .[dev]
python -m pytest -q
```

Useful pipeline commands:

```powershell
python scripts/write_source_registry.py
python scripts/parse_jmdict.py
python scripts/parse_kaikki_fr.py
python scripts/translate_normalized_words.py
python scripts/build_sqlite.py
python scripts/export_dictionary_package.py
python scripts/classify_ja_learning_levels.py --limit 100000 --write-db
```

### Android App

```powershell
cd android-app
.\gradlew.bat :app:compileDebugKotlin :app:compileDebugUnitTestKotlin
.\gradlew.bat :app:assembleDebug
```

The Android build syncs packaged dictionary assets from:

```text
artifacts/package/
```

That directory is ignored by Git because real packages may be large.

## Japanese Learning Levels

Lexigo avoids sending beginner users into the full raw Japanese dictionary. The current level pipeline uses:

1. Exact JLPT word + reading matches.
2. Unique word fallback matches.
3. Unique reading fallback matches for kana-written source entries.
4. Low-value filtering for names, places, companies, archaic forms, rare terms, vulgar terms, affixes, counters, and overly long lemmas.
5. Optional AI classification for high-value unknown candidates.

Generated outputs live under:

```text
artifacts/learning_levels/ja/
```

Important scripts:

```powershell
python scripts/classify_ja_learning_levels.py --limit 100000 --write-db
python scripts/analyze_ja_learning_inventory.py --candidate-limit 20000
python scripts/classify_ja_candidates_ai.py --limit 1000 --batch-size 100
```

## Translation Providers

The default translation path can use local fixtures or supplemental overrides. For personal high-value corrections, place overrides in:

```text
sources/translations/supplemental_overrides.json
```

Example:

```json
[
  {
    "language": "JA",
    "lemma": "飲む",
    "reading_or_ipa": "のむ",
    "meaning_zh": "喝"
  },
  {
    "language": "FR",
    "lemma": "bonjour",
    "meaning_zh": "你好"
  }
]
```

OpenAI-compatible providers are supported through environment variables:

```powershell
$env:OPENAI_API_KEY = "<your-key>"
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
python scripts/translate_normalized_words.py --provider openai --model gpt-4.1-mini
```

Local OpenAI-compatible servers such as Ollama can also be used:

```powershell
$env:OPENAI_API_KEY = "ollama"
$env:OPENAI_BASE_URL = "http://127.0.0.1:11434/v1"
python scripts/translate_normalized_words.py --provider openai --model qwen2.5:3b
```

## Verification

Core checks used during development:

```powershell
python -m pytest -q tests/test_ja_learning_levels.py tests/test_sqlite_builder.py tests/test_query_service.py
cd android-app
.\gradlew.bat :app:compileDebugKotlin :app:compileDebugUnitTestKotlin
.\gradlew.bat :app:assembleDebug
```

For real-device smoke checks:

- Install the debug APK.
- Watch `DictionaryAssetInstaller` logs for first-launch dictionary copy.
- Watch `DictionaryVocabGateway` logs for search and detail timings.
- Search known Japanese and French words.
- Start a learning session and verify Japanese kana + romaji are both shown.
- Star a word, close the app, reopen it, and confirm persistence.

## Repository Hygiene

The repository tracks source code, tests, docs, and small placeholders. It intentionally does not track:

- Raw downloaded sources.
- Generated SQLite packages.
- Translation caches.
- Android build outputs.
- APK files.
- Local API keys or local properties.

See [.gitignore](.gitignore) and [android-app/.gitignore](android-app/.gitignore) for details.

## Roadmap

- Expand Japanese level coverage beyond direct JLPT matches.
- Add stricter quality gates for AI-assisted level classification.
- Improve French learning-path ranking.
- Add first-run onboarding and language-level selection.
- Prepare release signing and distribution workflow.

## License

No license has been selected yet. Treat this repository as private/proprietary unless a license is added.
