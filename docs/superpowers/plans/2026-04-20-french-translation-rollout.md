# French Translation Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a stable, resumable French translation pipeline that can translate the Kaikki French package in stages, repair long-tail failures, and produce package outputs with trustworthy progress metrics.

**Architecture:** Reuse the proven `llama.cpp + qwen2.5:3b` local path as the primary translator, but do not repeat the Japanese "single monolithic run" pattern. Instead, add a French backlog audit, shard the untranslated rows into deterministic JSONL chunks, run translation with checkpoint output per shard, fall back to a secondary provider when `llama.cpp` fails on specific prompts, then repair residual failures via overrides before rebuilding package metadata.

**Tech Stack:** Python 3, existing `dict_feasibility` translation pipeline, `llama.cpp`, Ollama local fallback, pytest

---

## Lessons Carried Forward From Japanese

- `llama.cpp + qwen2.5:3b` is fast enough on the local GPU, but long jobs must checkpoint continuously.
- Batch translation must fall back to per-item translation. The Japanese run lost whole batches before this was fixed.
- `llama.cpp /v1/chat/completions` can still fail on specific prompts. French needs an automatic secondary provider instead of manual repair as the first response.
- A small persistent override file is acceptable for high-value long-tail failures. Reuse `sources/translations/supplemental_overrides.json`.
- Package metadata must be regenerated from final artifact state before export. Otherwise `manifest.json` lags behind the actual translation output.

## Current French Baseline

- Source artifact: `artifacts/translated/kaikki_fr_words.jsonl`
- Baseline report: `artifacts/reports/french-translation-baseline.json`
- Current totals:
  - `total_words = 2,142,991`
  - `translated_words = 11,533`
  - `untranslated_words = 2,131,458`
  - `missing_source_text_words = 44,853`
  - `unique_nonempty_source_texts = 1,930,503`
- French rollout should explicitly split these into:
  - translatable backlog: rows with non-empty `meaning_source_text`
  - blocked backlog: rows with empty `meaning_source_text`

### Task 1: Add a repeatable French backlog audit

**Files:**
- Create: `content/scripts/audit_french_translation_backlog.py`
- Create: `content/tests/test_audit_french_translation_backlog.py`
- Output: `content/artifacts/reports/french-translation-baseline.json`

- [ ] **Step 1: Write the failing test**

```python
def test_audit_french_translation_backlog_reports_counts(tmp_path: Path) -> None:
    input_path = tmp_path / "kaikki_fr_words.jsonl"
    input_path.write_text(
        "\n".join(
            [
                json.dumps({
                    "language": "FR",
                    "lemma": "mardi",
                    "surface": "mardi",
                    "reading_or_ipa": "",
                    "pos": "noun",
                    "meaning_source": "kaikki",
                    "meaning_zh": "",
                    "source_name": "Kaikki French Wiktionary",
                    "source_entry_id": "mardi",
                    "meaning_source_text": "Le jour du mardi.",
                    "meaning_source_lang": "fr",
                    "example_sentences_json": "[]",
                }),
                json.dumps({
                    "language": "FR",
                    "lemma": "cinquante",
                    "surface": "cinquante",
                    "reading_or_ipa": "",
                    "pos": "num",
                    "meaning_source": "kaikki",
                    "meaning_zh": "",
                    "source_name": "Kaikki French Wiktionary",
                    "source_entry_id": "cinquante",
                    "meaning_source_text": "",
                    "meaning_source_lang": "",
                    "example_sentences_json": "[]",
                }),
            ]
        ),
        encoding="utf-8",
    )

    report = audit_french_translation_backlog(input_path)

    assert report["total_words"] == 2
    assert report["untranslated_words"] == 2
    assert report["missing_source_text_words"] == 1
    assert report["unique_nonempty_source_texts"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest content/tests/test_audit_french_translation_backlog.py -q`
Expected: FAIL because the audit script does not exist yet.

- [ ] **Step 3: Implement the audit script**

```python
def audit_french_translation_backlog(path: Path) -> dict[str, object]:
    source_lang_counts = Counter()
    unique_nonempty_source_texts: set[tuple[str, str]] = set()
    total_words = translated_words = missing_source_text_words = 0

    for word in iter_normalized_words(path):
        total_words += 1
        source_text = word.meaning_source_text.strip()
        source_lang = word.meaning_source_lang.strip() or "unknown"
        source_lang_counts[source_lang] += 1
        if word.meaning_zh.strip():
            translated_words += 1
        if not source_text:
            missing_source_text_words += 1
            continue
        unique_nonempty_source_texts.add((source_lang, source_text))

    return {
        "total_words": total_words,
        "translated_words": translated_words,
        "untranslated_words": total_words - translated_words,
        "missing_source_text_words": missing_source_text_words,
        "unique_nonempty_source_texts": len(unique_nonempty_source_texts),
        "source_lang_counts": dict(source_lang_counts),
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest content/tests/test_audit_french_translation_backlog.py -q`
Expected: PASS

- [ ] **Step 5: Generate the baseline report**

Run:

```powershell
python content\scripts\audit_french_translation_backlog.py `
  --input content\artifacts\translated\kaikki_fr_words.jsonl `
  --output content\artifacts\reports\french-translation-baseline.json
```

Expected: PASS, with a JSON report that separates total backlog from the empty-source backlog.

### Task 2: Shard the French translatable backlog into deterministic chunks

**Files:**
- Create: `content/scripts\shard_french_translation_input.py`
- Create: `content/tests\test_shard_french_translation_input.py`
- Output: `content/artifacts/normalized/fr_shards/*.jsonl`

- [ ] **Step 1: Write the failing test**

```python
def test_shard_french_translation_input_skips_translated_and_missing_source(tmp_path: Path) -> None:
    ...
    shard_paths = shard_french_translation_input(
        input_path=input_path,
        output_dir=output_dir,
        shard_size=2,
    )

    assert [path.name for path in shard_paths] == [
        "kaikki_fr_part_0001.jsonl",
        "kaikki_fr_part_0002.jsonl",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest content/tests/test_shard_french_translation_input.py -q`
Expected: FAIL because the sharding script does not exist yet.

- [ ] **Step 3: Implement deterministic sharding**

```python
def should_translate(word: NormalizedWord) -> bool:
    return (not word.meaning_zh.strip()) and bool(word.meaning_source_text.strip())

def shard_french_translation_input(input_path: Path, output_dir: Path, shard_size: int) -> list[Path]:
    shard_paths: list[Path] = []
    bucket: list[NormalizedWord] = []
    index = 1
    for word in iter_normalized_words(input_path):
        if not should_translate(word):
            continue
        bucket.append(word)
        if len(bucket) == shard_size:
            shard_path = output_dir / f"kaikki_fr_part_{index:04d}.jsonl"
            write_normalized_words(shard_path, bucket)
            shard_paths.append(shard_path)
            bucket = []
            index += 1
    if bucket:
        shard_path = output_dir / f"kaikki_fr_part_{index:04d}.jsonl"
        write_normalized_words(shard_path, bucket)
        shard_paths.append(shard_path)
    return shard_paths
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest content/tests/test_shard_french_translation_input.py -q`
Expected: PASS

- [ ] **Step 5: Produce the first executable shard set**

Run:

```powershell
python content\scripts\shard_french_translation_input.py `
  --input content\artifacts\translated\kaikki_fr_words.jsonl `
  --output-dir content\artifacts\normalized\fr_shards `
  --shard-size 10000
```

Expected: PASS, with only untranslated rows that have non-empty `meaning_source_text`.

### Task 3: Add a secondary provider fallback for per-item French failures

**Files:**
- Modify: `content/src/dict_feasibility/translation.py`
- Modify: `content/scripts/translate_normalized_words.py`
- Create: `content/tests/test_translation_provider_fallback.py`

- [ ] **Step 1: Write the failing test**

```python
def test_fallback_provider_uses_secondary_after_primary_failure() -> None:
    primary = StubProvider(error_texts={"Bande dessinee japonaise."})
    secondary = StubProvider(overrides={"Bande dessinee japonaise.": "Japanese comics."})
    provider = FallbackTranslationProvider(primary=primary, secondary=secondary)

    assert provider.translate("Bande dessinee japonaise.", "fr", "zh") == "Japanese comics."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest content/tests/test_translation_provider_fallback.py -q`
Expected: FAIL because the fallback provider does not exist yet.

- [ ] **Step 3: Implement the fallback provider and CLI wiring**

```python
class FallbackTranslationProvider:
    def __init__(self, primary: TranslationProvider, secondary: TranslationProvider) -> None:
        self._primary = primary
        self._secondary = secondary

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            return self._primary.translate(text, source_lang, target_lang)
        except Exception:
            return self._secondary.translate(text, source_lang, target_lang)
```

```python
parser.add_argument("--fallback-provider", choices=["openai", "llama_cpp"])
parser.add_argument("--fallback-model")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest content/tests/test_translation_provider_fallback.py -q`
Expected: PASS

- [ ] **Step 5: Verify the combined translation tests still pass**

Run:

```powershell
python -m pytest `
  content\tests\test_translation.py `
  content\tests\test_translation_pipeline.py `
  content\tests\test_translation_batch_retry.py `
  content\tests\test_translation_provider_fallback.py -q
```

Expected: PASS

### Task 4: Run a pilot on 5 shards before any full French rollout

**Files:**
- Input: `content/artifacts/normalized/fr_shards/kaikki_fr_part_0001.jsonl` through `kaikki_fr_part_0005.jsonl`
- Output: `content/artifacts/translated/fr_shards/*.jsonl`
- Reports: `content/artifacts/reports/french-pilot/*.json`

- [ ] **Step 1: Translate the first pilot shard**

Run:

```powershell
$env:OPENAI_BASE_URL='http://127.0.0.1:8080/v1'
$env:OPENAI_API_KEY='local'
python content\scripts\translate_normalized_words.py `
  --provider llama_cpp `
  --model qwen2.5:3b `
  --fallback-provider openai `
  --fallback-model qwen2.5:3b `
  --api-key-env OPENAI_API_KEY `
  --base-url-env OPENAI_BASE_URL `
  --batch-size 16 `
  --checkpoint-every 2000 `
  --input content\artifacts\normalized\fr_shards\kaikki_fr_part_0001.jsonl `
  --output content\artifacts\translated\fr_shards\kaikki_fr_part_0001.jsonl `
  --report content\artifacts\reports\french-pilot\kaikki_fr_part_0001.summary.json `
  --checkpoint-output content\artifacts\translated\fr_shards\kaikki_fr_part_0001.checkpoint.jsonl `
  --checkpoint-report content\artifacts\reports\french-pilot\kaikki_fr_part_0001.progress.json `
  --cache content\artifacts\reports\translation-cache-qwen2.5-fr.json
```

Expected: PASS, with growing checkpoint output and a final summary JSON.

- [ ] **Step 2: Translate shards 2 through 5 with the same command shape**

Run: repeat Step 1 for `kaikki_fr_part_0002` through `kaikki_fr_part_0005`.
Expected: PASS for all five shards.

- [ ] **Step 3: Sample and review the pilot quality**

Run:

```powershell
Get-Content content\artifacts\translated\fr_shards\kaikki_fr_part_0001.jsonl -TotalCount 20
```

Expected: French glosses are translated into short Simplified Chinese dictionary-style glosses, not free-form paraphrases.

- [ ] **Step 4: Approve or adjust before scaling**

Check:
  - failure rate per shard
  - time per 10k shard
  - whether conjugation-heavy entries remain understandable

Expected: either approve the rollout unchanged or lower shard size / batch size before scaling.

### Task 5: Automate French repair and override capture

**Files:**
- Create: `content/scripts/repair_failed_french_terms.py`
- Create: `content/tests/test_repair_failed_french_terms.py`
- Modify: `content/sources/translations/supplemental_overrides.json`

- [ ] **Step 1: Write the failing test**

```python
def test_repair_failed_french_terms_updates_overrides_and_output(tmp_path: Path) -> None:
    ...
    assert repaired_summary["remaining_failed_entries"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest content/tests/test_repair_failed_french_terms.py -q`
Expected: FAIL because the repair script does not exist yet.

- [ ] **Step 3: Implement the repair workflow**

```python
def extract_failed_french_terms(words: list[NormalizedWord]) -> list[NormalizedWord]:
    return [word for word in words if word.language == "FR" and not word.meaning_zh.strip()]
```

```python
def repair_failed_french_terms(...):
    # retry failed rows with the fallback provider
    # write remaining hard failures to a review report
    # append only approved manual fixes to supplemental_overrides.json
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest content/tests/test_repair_failed_french_terms.py -q`
Expected: PASS

- [ ] **Step 5: Use the repair script after each rollout batch**

Run:

```powershell
python content\scripts\repair_failed_french_terms.py `
  --input content\artifacts\translated\kaikki_fr_words.jsonl `
  --report content\artifacts\reports\french-repair-report.json `
  --overrides content\sources\translations\supplemental_overrides.json
```

Expected: residual failures are isolated and shrink over time instead of staying buried in the main output.

### Task 6: Merge final French output and rebuild the package

**Files:**
- Output: `content/artifacts/translated/kaikki_fr_words.jsonl`
- Output: `content/artifacts/reports/translation-summary.json`
- Output: `content/artifacts/package/dictionary.db`
- Output: `content/artifacts/package/manifest.json`

- [ ] **Step 1: Merge translated shards back into the main French artifact**

Run:

```powershell
python content\scripts\merge_french_translation_shards.py `
  --base-input content\artifacts\translated\kaikki_fr_words.jsonl `
  --shard-dir content\artifacts\translated\fr_shards `
  --output content\artifacts\translated\kaikki_fr_words.jsonl
```

Expected: PASS, with translated shard rows merged back into the main French artifact.

- [ ] **Step 2: Recompute translation summary from final artifact state**

Run:

```powershell
python content\scripts\audit_french_translation_backlog.py `
  --input content\artifacts\translated\kaikki_fr_words.jsonl `
  --output content\artifacts\reports\french-translation-baseline.json
```

Then update `content\artifacts\reports\translation-summary.json` so `kaikki_fr_words.jsonl` reflects the new translated count.

- [ ] **Step 3: Rebuild package outputs**

Run:

```powershell
python content\scripts\build_sqlite.py
python content\scripts\export_dictionary_package.py
python content\scripts\sync_android_dictionary_assets.py
```

Expected: PASS, with `dictionary.db`, `manifest.json`, and Android generated assets all aligned to the latest French rollout.

- [ ] **Step 4: Verify package metadata**

Run:

```powershell
Get-Content content\artifacts\package\manifest.json
Get-Content content\android-app\app\build\generated\assets\dictionary\manifest.json
```

Expected: both manifests report the same French translated count and the already-complete Japanese count.
