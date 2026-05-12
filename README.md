# Dictionary Feasibility

Validate JMdict, Tatoeba, and Kaikki data for a future Android vocabulary app.

## Setup

1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `python -m pip install -e .[dev]`

## Commands

1. `python scripts/write_source_registry.py`
2. `python scripts/parse_jmdict.py`
3. `python scripts/parse_kaikki_fr.py`
4. `python scripts/translate_normalized_words.py`
5. `python scripts/build_sqlite.py`
6. `python scripts/sample_report.py`
7. `python scripts/render_feasibility_report.py`
8. `python scripts/validate_real_sources.py`
9. `python scripts/validate_real_source_translations.py`
10. `python scripts/search_words.py --query hello`
11. `python scripts/export_dictionary_package.py`

## Translation Providers

Default translation runs use the local glossary fixture or `sources/translations/glossary.json` if present.
Translation cache persists by default to `artifacts/reports/translation-cache.json`.

If you maintain your own high-value Chinese translations for self-use, place them in `sources/translations/supplemental_overrides.json` and the translation pipeline will apply them before any provider lookup.

Example override file:

```json
[
  {
    "language": "JA",
    "lemma": "飲む",
    "reading_or_ipa": "のむ",
    "meaning_zh": "喝下"
  },
  {
    "language": "FR",
    "lemma": "bonjour",
    "meaning_zh": "您好"
  }
]
```

To use the OpenAI Responses API provider, set `OPENAI_API_KEY` and optionally `OPENAI_BASE_URL`, then run:

`python scripts/translate_normalized_words.py --provider openai --model gpt-4.1-mini`

To validate translated real-source samples with the same provider selection:

`python scripts/validate_real_source_translations.py --provider openai --model gpt-4.1-mini --limit 50`

## Android Self-Use Verification

From `android-app/`:

1. `.\gradlew.bat compileDebugUnitTestKotlin`
2. `.\gradlew.bat compileDebugAndroidTestKotlin`
3. `.\gradlew.bat assembleRelease`

For real-device smoke checks after installation:

- watch `logcat` for `DictionaryAssetInstaller` to see first-launch copy duration
- watch `logcat` for `DictionaryVocabGateway` to see search/detail timing
- search a few known Japanese and French words
- add a word to the learning list and reopen the app

If `testDebugUnitTest` reports `ClassNotFoundException` in this `E:\aiproduct\安卓单词软件\content\android-app` workspace, treat it as a local Gradle/JUnit path issue and rely on compile tasks plus device smoke checks until the workspace path problem is resolved.
