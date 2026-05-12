# French Quality-First Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working version of the French quality-first pipeline by adding classification, deterministic template translation, stronger risk review, and a measurable `200`-entry before/after validation flow.

**Architecture:** Extend the existing French batch workflow instead of replacing it. Add a deterministic front-end that classifies and rule-translates French morphology-heavy entries before model inference, then strengthen post-translation review so only true residuals reach manual correction. Validate the design on a single `200`-entry batch before scaling further.

**Tech Stack:** Python 3, existing `dict_feasibility` translation pipeline, pytest, local JSONL artifacts

---

### Task 1: Add French entry classification

**Files:**
- Create: `scripts/french_classifier.py`
- Create: `tests/test_french_classifier.py`
- Modify: `src/dict_feasibility/models.py` (only if a tiny helper is needed)

- [ ] **Step 1: Write the failing classifier tests**

```python
def test_classify_french_entry_returns_blocked_for_missing_source() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="cinquante",
        surface="cinquante",
        reading_or_ipa="",
        pos="num",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="cinquante",
        meaning_source_text="",
        meaning_source_lang="",
    )

    assert classify_french_entry(word) == "blocked"


def test_classify_french_entry_returns_rule_based_for_morphology_template() -> None:
    word = NormalizedWord(
        language="FR",
        lemma="siège",
        surface="siège",
        reading_or_ipa="",
        pos="verb",
        meaning_source="kaikki",
        meaning_zh="",
        source_name="Kaikki French Wiktionary",
        source_entry_id="siège",
        meaning_source_text="Première personne du singulier du présent de l’indicatif de siéger.",
        meaning_source_lang="fr",
    )

    assert classify_french_entry(word) == "rule_based"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_french_classifier.py -q`
Expected: FAIL because `french_classifier.py` does not exist yet.

- [ ] **Step 3: Implement the classifier**

```python
TEMPLATE_PATTERNS = (
    re.compile(r"^Première personne du singulier", re.IGNORECASE),
    re.compile(r"^(Féminin|Masculin) (singulier|pluriel) de ", re.IGNORECASE),
    re.compile(r"^Pluriel de ", re.IGNORECASE),
    re.compile(r"^Participe (présent|passé)", re.IGNORECASE),
    re.compile(r"^Contraction de ", re.IGNORECASE),
    re.compile(r"lettre de l’alphabet", re.IGNORECASE),
)


def classify_french_entry(word: NormalizedWord) -> str:
    if not word.meaning_source_text.strip():
        return "blocked"
    if any(pattern.search(word.meaning_source_text) for pattern in TEMPLATE_PATTERNS):
        return "rule_based"
    return "local_candidate"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_french_classifier.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_french_classifier.py scripts/french_classifier.py
git commit -m "feat: add French entry classifier"
```

### Task 2: Add deterministic French rule translation

**Files:**
- Create: `scripts/french_rule_translator.py`
- Create: `tests/test_french_rule_translator.py`
- Modify: `scripts/french_classifier.py` (only if pattern sharing is cleaner)

- [ ] **Step 1: Write the failing rule-translation tests**

```python
def test_translate_french_rule_gloss_handles_first_person_present() -> None:
    assert (
        translate_french_rule_gloss(
            "Première personne du singulier du présent de l’indicatif de siéger."
        )
        == "动词“siéger”的直陈式现在时第一人称单数形式"
    )


def test_translate_french_rule_gloss_handles_plural_of() -> None:
    assert translate_french_rule_gloss("Pluriel de anglaise.") == "anglaise 的复数形式"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_french_rule_translator.py -q`
Expected: FAIL because `translate_french_rule_gloss` does not exist yet.

- [ ] **Step 3: Implement deterministic template translation**

```python
def translate_french_rule_gloss(text: str) -> str | None:
    match = re.match(
        r"^Première personne du singulier du présent de l’indicatif de (?P<lemma>.+?)\\.$",
        text,
    )
    if match:
        return f"动词“{match.group('lemma')}”的直陈式现在时第一人称单数形式"

    match = re.match(r"^Pluriel de (?P<lemma>.+?)\\.$", text)
    if match:
        return f"{match.group('lemma')} 的复数形式"

    return None
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_french_rule_translator.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_french_rule_translator.py scripts/french_rule_translator.py
git commit -m "feat: add deterministic French rule translation"
```

### Task 3: Add French batch preprocessing

**Files:**
- Create: `scripts/prepare_french_batch.py`
- Create: `tests/test_prepare_french_batch.py`
- Modify: `scripts/french_classifier.py`
- Modify: `scripts/french_rule_translator.py`

- [ ] **Step 1: Write the failing preprocessing test**

```python
def test_prepare_french_batch_splits_blocked_rule_and_local_entries(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    blocked_path = tmp_path / "blocked.jsonl"
    rule_path = tmp_path / "rule.jsonl"
    local_path = tmp_path / "local.jsonl"
    summary_path = tmp_path / "summary.json"

    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
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
                    }
                ),
                json.dumps(
                    {
                        "language": "FR",
                        "lemma": "siège",
                        "surface": "siège",
                        "reading_or_ipa": "",
                        "pos": "verb",
                        "meaning_source": "kaikki",
                        "meaning_zh": "",
                        "source_name": "Kaikki French Wiktionary",
                        "source_entry_id": "siège",
                        "meaning_source_text": "Première personne du singulier du présent de l’indicatif de siéger.",
                        "meaning_source_lang": "fr",
                        "example_sentences_json": "[]",
                    }
                ),
                json.dumps(
                    {
                        "language": "FR",
                        "lemma": "mardi",
                        "surface": "mardi",
                        "reading_or_ipa": "",
                        "pos": "adv",
                        "meaning_source": "kaikki",
                        "meaning_zh": "",
                        "source_name": "Kaikki French Wiktionary",
                        "source_entry_id": "mardi",
                        "meaning_source_text": "Le jour du mardi.",
                        "meaning_source_lang": "fr",
                        "example_sentences_json": "[]",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    summary = prepare_french_batch(
        input_path=input_path,
        blocked_output_path=blocked_path,
        rule_output_path=rule_path,
        local_output_path=local_path,
        summary_output_path=summary_path,
    )

    assert summary["blocked"] == 1
    assert summary["rule_based"] == 1
    assert summary["local_candidate"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prepare_french_batch.py -q`
Expected: FAIL because `prepare_french_batch.py` does not exist yet.

- [ ] **Step 3: Implement preprocessing**

```python
def prepare_french_batch(
    *,
    input_path: Path,
    blocked_output_path: Path,
    rule_output_path: Path,
    local_output_path: Path,
    summary_output_path: Path,
) -> dict[str, int]:
    blocked_words = []
    rule_words = []
    local_words = []

    for word in iter_normalized_words(input_path):
        bucket = classify_french_entry(word)
        if bucket == "blocked":
            blocked_words.append(word)
            continue
        if bucket == "rule_based":
            translated = apply_french_rule_translation(word)
            rule_words.append(translated)
            continue
        local_words.append(word)

    write_normalized_words(blocked_output_path, blocked_words)
    write_normalized_words(rule_output_path, rule_words)
    write_normalized_words(local_output_path, local_words)
    summary = {
        "blocked": len(blocked_words),
        "rule_based": len(rule_words),
        "local_candidate": len(local_words),
    }
    summary_output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_prepare_french_batch.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_prepare_french_batch.py scripts/prepare_french_batch.py scripts/french_classifier.py scripts/french_rule_translator.py
git commit -m "feat: add French batch preprocessing"
```

### Task 4: Upgrade French batch review rules

**Files:**
- Modify: `scripts/review_french_translation_batch.py`
- Modify: `tests/test_review_french_translation_batch.py`

- [ ] **Step 1: Add failing review cases for morphology leftovers**

```python
def test_review_french_translation_batch_flags_morphology_entries_left_in_mixed_language(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "language": "FR",
                        "lemma": "siège",
                        "surface": "siège",
                        "reading_or_ipa": "",
                        "pos": "verb",
                        "meaning_source": "kaikki",
                        "meaning_zh": "我 present indicative of to sit",
                        "source_name": "Kaikki French Wiktionary",
                        "source_entry_id": "siège",
                        "meaning_source_text": "Première personne du singulier du présent de l’indicatif de siéger.",
                        "meaning_source_lang": "fr",
                        "example_sentences_json": "[]",
                    }
                )
            ]
        ),
        encoding="utf-8",
    )
    report = review_french_translation_batch(input_path)

    assert report["flagged_words"] == 1
    assert report["reason_counts"]["template_not_in_chinese_form"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_review_french_translation_batch.py -q`
Expected: FAIL because the review script does not detect this reason yet.

- [ ] **Step 3: Implement stronger review rules**

```python
if _GRAMMAR_FR_RE.search(source_text) and not _CHINESE_TEMPLATE_RE.search(meaning_zh):
    reasons.append("template_not_in_chinese_form")

if "无法确定" in meaning_zh or "unknown" in meaning_zh.lower():
    reasons.append("uncertainty_output")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_review_french_translation_batch.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_review_french_translation_batch.py scripts/review_french_translation_batch.py
git commit -m "feat: strengthen French review heuristics"
```

### Task 5: Run the improved `200`-entry French batch

**Files:**
- Input: `artifacts/normalized/fr_shards/kaikki_fr_batch_0001_0200.jsonl`
- Create: `artifacts/normalized/fr_shards/kaikki_fr_batch_0001_0200.blocked.jsonl`
- Create: `artifacts/translated/fr_shards/kaikki_fr_batch_0001_0200.rule.jsonl`
- Create: `artifacts/normalized/fr_shards/kaikki_fr_batch_0001_0200.local.jsonl`
- Create: `artifacts/translated/fr_shards/kaikki_fr_batch_0001_0200.qwen25.v2.out.jsonl`
- Create: `artifacts/reports/french-pilot/kaikki_fr_batch_0001_0200.prep.summary.json`
- Create: `artifacts/reports/french-pilot/kaikki_fr_batch_0001_0200.qwen25.v2.summary.json`
- Create: `artifacts/reports/french-pilot/kaikki_fr_batch_0001_0200.qwen25.v2.review.json`

- [ ] **Step 1: Run preprocessing**

Run:

```powershell
python scripts\prepare_french_batch.py `
  --input artifacts\normalized\fr_shards\kaikki_fr_batch_0001_0200.jsonl `
  --blocked-output artifacts\normalized\fr_shards\kaikki_fr_batch_0001_0200.blocked.jsonl `
  --rule-output artifacts\translated\fr_shards\kaikki_fr_batch_0001_0200.rule.jsonl `
  --local-output artifacts\normalized\fr_shards\kaikki_fr_batch_0001_0200.local.jsonl `
  --summary-output artifacts\reports\french-pilot\kaikki_fr_batch_0001_0200.prep.summary.json
```

Expected: PASS, with blocked, rule-based, and local candidate outputs created.

- [ ] **Step 2: Translate only the local candidate subset**

Run:

```powershell
$env:OPENAI_API_KEY='local'
$env:OPENAI_BASE_URL='http://127.0.0.1:8080/v1'
python scripts\translate_normalized_words.py `
  --provider llama_cpp `
  --model qwen2.5:3b `
  --batch-size 16 `
  --checkpoint-every 50 `
  --input artifacts\normalized\fr_shards\kaikki_fr_batch_0001_0200.local.jsonl `
  --output artifacts\translated\fr_shards\kaikki_fr_batch_0001_0200.qwen25.v2.out.jsonl `
  --report artifacts\reports\french-pilot\kaikki_fr_batch_0001_0200.qwen25.v2.summary.json `
  --checkpoint-output artifacts\translated\fr_shards\kaikki_fr_batch_0001_0200.qwen25.v2.checkpoint.jsonl `
  --checkpoint-report artifacts\reports\french-pilot\kaikki_fr_batch_0001_0200.qwen25.v2.progress.json `
  --cache artifacts\reports\translation-cache-qwen2.5-fr-batch1-v2.json
```

Expected: PASS

- [ ] **Step 3: Review the local output**

Run:

```powershell
python scripts\review_french_translation_batch.py `
  --input artifacts\translated\fr_shards\kaikki_fr_batch_0001_0200.qwen25.v2.out.jsonl `
  --output artifacts\reports\french-pilot\kaikki_fr_batch_0001_0200.qwen25.v2.review.json
```

Expected: PASS

- [ ] **Step 4: Compare before/after review load**

Run:

```powershell
@'
import json
from pathlib import Path
before = json.loads(Path("artifacts/reports/french-pilot/kaikki_fr_batch_0001_0200.qwen25.review.json").read_text(encoding="utf-8"))
after = json.loads(Path("artifacts/reports/french-pilot/kaikki_fr_batch_0001_0200.qwen25.v2.review.json").read_text(encoding="utf-8"))
print({
    "before_flagged": before["flagged_words"],
    "after_flagged": after["flagged_words"],
    "before_reasons": before["reason_counts"],
    "after_reasons": after["reason_counts"],
})
'@ | python -
```

Expected: `after_flagged` is materially lower than `before_flagged`, and morphology/template leftovers are no longer the dominant source of review work.

- [ ] **Step 5: Commit**

```bash
git add scripts/prepare_french_batch.py scripts/french_classifier.py scripts/french_rule_translator.py scripts/review_french_translation_batch.py tests/test_french_classifier.py tests/test_french_rule_translator.py tests/test_prepare_french_batch.py tests/test_review_french_translation_batch.py docs/superpowers/specs/2026-04-20-french-quality-first-design.md
git commit -m "feat: implement first pass French quality-first pipeline"
```

### Task 6: Verify the first version is strong enough to continue

**Files:**
- Review only

- [ ] **Step 1: Run the focused test suite**

Run:

```powershell
python -m pytest `
  tests\test_french_classifier.py `
  tests\test_french_rule_translator.py `
  tests\test_prepare_french_batch.py `
  tests\test_review_french_translation_batch.py `
  tests\test_translation_provider_fallback.py `
  tests\test_audit_french_translation_backlog.py `
  tests\test_shard_french_translation_input.py -q
```

Expected: PASS

- [ ] **Step 2: Review the batch metrics**

Check:

- `artifacts/reports/french-pilot/kaikki_fr_batch_0001_0200.prep.summary.json`
- `artifacts/reports/french-pilot/kaikki_fr_batch_0001_0200.qwen25.v2.summary.json`
- `artifacts/reports/french-pilot/kaikki_fr_batch_0001_0200.qwen25.v2.review.json`

Expected: template/rule preprocessing has meaningfully reduced the manual review surface.

- [ ] **Step 3: Decide go/no-go for `1000` entries**

Proceed only if:

- template-related review load is clearly lower than the original `200` batch
- the remaining flagged items are concentrated in true residual semantics rather than repeated grammar-template failures

If not, do not scale. Add more rules first.
