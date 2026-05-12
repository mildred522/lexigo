import json
import subprocess
import sys
from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.translation import (
    MappingTranslationProvider,
    MemoryTranslationCache,
    load_supplemental_translation_overrides,
)
from dict_feasibility.translation_pipeline import (
    load_normalized_words,
    run_translation_job,
    run_translation_pipeline,
    write_normalized_words,
)


def test_run_translation_pipeline_fills_missing_meanings() -> None:
    words = [
        NormalizedWord(
            language="JA",
            lemma="飲む",
            surface="飲む",
            reading_or_ipa="のむ",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1002",
            meaning_source_text="to drink",
            meaning_source_lang="en",
        ),
        NormalizedWord(
            language="FR",
            lemma="bonjour",
            surface="bonjour",
            reading_or_ipa="bɔ̃.ʒuʁ",
            pos="intj",
            meaning_source="kaikki",
            meaning_zh="",
            source_name="Kaikki French Wiktionary",
            source_entry_id="bonjour",
            meaning_source_text="salutation de bienvenue",
            meaning_source_lang="fr",
        ),
    ]
    provider = MappingTranslationProvider(
        {
            ("to drink", "en", "zh"): "喝",
            ("salutation de bienvenue", "fr", "zh"): "你好",
        }
    )

    translated_words, summary = run_translation_pipeline(
        words,
        provider=provider,
        cache=MemoryTranslationCache(),
    )

    assert [word.meaning_zh for word in translated_words] == ["喝", "你好"]
    assert summary["translated_now"] == 2
    assert summary["missing_source_text"] == 0
    assert summary["already_translated"] == 0
    assert summary["cache_hits"] == 0
    assert summary["translation_errors"] == 0


def test_run_translation_pipeline_reuses_cache_for_duplicates() -> None:
    duplicated = NormalizedWord(
        language="JA",
        lemma="飲む",
        surface="飲む",
        reading_or_ipa="のむ",
        pos="verb",
        meaning_source="jmdict",
        meaning_zh="",
        source_name="JMdict",
        source_entry_id="1002",
        meaning_source_text="to drink",
        meaning_source_lang="en",
    )
    cache = MemoryTranslationCache()
    provider = MappingTranslationProvider({("to drink", "en", "zh"): "喝"})

    translated_words, summary = run_translation_pipeline(
        [duplicated, duplicated],
        provider=provider,
        cache=cache,
    )

    assert [word.meaning_zh for word in translated_words] == ["喝", "喝"]
    assert provider.calls == 1
    assert summary["translated_now"] == 2
    assert summary["cache_hits"] == 1


def test_run_translation_pipeline_batches_uncached_texts() -> None:
    duplicated = NormalizedWord(
        language="JA",
        lemma="椋层個",
        surface="椋层個",
        reading_or_ipa="銇個",
        pos="verb",
        meaning_source="jmdict",
        meaning_zh="",
        source_name="JMdict",
        source_entry_id="1002",
        meaning_source_text="to drink",
        meaning_source_lang="en",
    )
    second = NormalizedWord(
        language="JA",
        lemma="椋叉べ",
        surface="椋叉べ",
        reading_or_ipa="椋叉べ",
        pos="verb",
        meaning_source="jmdict",
        meaning_zh="",
        source_name="JMdict",
        source_entry_id="1003",
        meaning_source_text="to eat",
        meaning_source_lang="en",
    )

    class BatchProvider:
        def __init__(self) -> None:
            self.calls = 0

        def translate(self, text: str, source_lang: str, target_lang: str) -> str:
            raise AssertionError("single translate should not be used")

        def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
            self.calls += 1
            return [f"{text}-zh" for text in texts]

    provider = BatchProvider()
    cache = MemoryTranslationCache()

    translated_words, summary = run_translation_pipeline(
        [duplicated, second, duplicated],
        provider=provider,
        cache=cache,
        batch_size=8,
    )

    assert [word.meaning_zh for word in translated_words] == ["to drink-zh", "to eat-zh", "to drink-zh"]
    assert provider.calls == 1
    assert summary["translated_now"] == 3
    assert summary["cache_hits"] == 1


def test_run_translation_pipeline_records_translation_errors_without_stopping() -> None:
    words = [
        NormalizedWord(
            language="JA",
            lemma="飲む",
            surface="飲む",
            reading_or_ipa="のむ",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1002",
            meaning_source_text="to drink",
            meaning_source_lang="en",
        ),
        NormalizedWord(
            language="FR",
            lemma="bonjour",
            surface="bonjour",
            reading_or_ipa="bɔ̃.ʒuʁ",
            pos="intj",
            meaning_source="kaikki",
            meaning_zh="",
            source_name="Kaikki French Wiktionary",
            source_entry_id="bonjour",
            meaning_source_text="salutation de bienvenue",
            meaning_source_lang="fr",
        ),
    ]
    provider = MappingTranslationProvider({("to drink", "en", "zh"): "喝"})

    translated_words, summary = run_translation_pipeline(
        words,
        provider=provider,
        cache=MemoryTranslationCache(),
    )

    assert [word.meaning_zh for word in translated_words] == ["喝", ""]
    assert summary["translated_now"] == 1
    assert summary["translation_errors"] == 1
    assert summary["failed_terms"] == ["bonjour"]


def test_run_translation_pipeline_prefers_supplemental_translation_overrides() -> None:
    words = [
        NormalizedWord(
            language="JA",
            lemma="飲む",
            surface="飲む",
            reading_or_ipa="のむ",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1002",
            meaning_source_text="to drink",
            meaning_source_lang="en",
        ),
        NormalizedWord(
            language="FR",
            lemma="bonjour",
            surface="bonjour",
            reading_or_ipa="bɔ̃.ʒuʁ",
            pos="intj",
            meaning_source="kaikki",
            meaning_zh="",
            source_name="Kaikki French Wiktionary",
            source_entry_id="bonjour",
            meaning_source_text="salutation de bienvenue",
            meaning_source_lang="fr",
        ),
    ]
    overrides = load_supplemental_translation_overrides(
        Path("tests/fixtures/supplemental_translation_overrides.json")
    )
    provider = MappingTranslationProvider(
        {
            ("to drink", "en", "zh"): "喝",
            ("salutation de bienvenue", "fr", "zh"): "你好",
        }
    )

    translated_words, summary = run_translation_pipeline(
        words,
        provider=provider,
        cache=MemoryTranslationCache(),
        supplemental_overrides=overrides,
    )

    assert [word.meaning_zh for word in translated_words] == ["喝下", "您好"]
    assert provider.calls == 0
    assert summary["already_translated"] == 0
    assert summary["translated_now"] == 2


def test_translate_normalized_words_script_writes_translated_artifacts(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_path = tmp_path / "words.jsonl"
    output_path = tmp_path / "translated.jsonl"
    report_path = tmp_path / "translation-report.json"
    glossary_path = repo_root / "tests" / "fixtures" / "translation_glossary.json"
    words = [
        NormalizedWord(
            language="JA",
            lemma="飲む",
            surface="飲む",
            reading_or_ipa="のむ",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1002",
            meaning_source_text="to drink",
            meaning_source_lang="en",
        ),
        NormalizedWord(
            language="FR",
            lemma="bonjour",
            surface="bonjour",
            reading_or_ipa="bɔ̃.ʒuʁ",
            pos="intj",
            meaning_source="kaikki",
            meaning_zh="",
            source_name="Kaikki French Wiktionary",
            source_entry_id="bonjour",
            meaning_source_text="salutation de bienvenue",
            meaning_source_lang="fr",
        ),
    ]
    write_normalized_words(input_path, words)

    subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "translate_normalized_words.py"),
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--glossary",
            str(glossary_path),
            "--report",
            str(report_path),
        ],
        cwd=repo_root,
        check=True,
    )

    translated_words = load_normalized_words(output_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert [word.meaning_zh for word in translated_words] == ["喝", "你好"]
    assert report["translated_now"] == 2
    assert report["translation_errors"] == 0
