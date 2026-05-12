import json
import subprocess
import sys
from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.translation import MappingTranslationProvider, MemoryTranslationCache
from dict_feasibility.translation_pipeline import (
    load_normalized_words,
    run_translation_job,
    write_normalized_words,
)


def test_run_translation_job_writes_checkpoint_output_and_progress(tmp_path: Path) -> None:
    words = [
        NormalizedWord(
            language="JA",
            lemma="drink",
            surface="drink",
            reading_or_ipa="",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1002",
            meaning_source_text="to drink",
            meaning_source_lang="en",
        ),
        NormalizedWord(
            language="JA",
            lemma="eat",
            surface="eat",
            reading_or_ipa="",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1003",
            meaning_source_text="to eat",
            meaning_source_lang="en",
        ),
        NormalizedWord(
            language="FR",
            lemma="bonjour",
            surface="bonjour",
            reading_or_ipa="",
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
            ("to eat", "en", "zh"): "吃",
            ("salutation de bienvenue", "fr", "zh"): "你好",
        }
    )
    checkpoint_output = tmp_path / "checkpoint.jsonl"
    checkpoint_report = tmp_path / "progress.json"

    translated_words, summary = run_translation_job(
        words,
        provider=provider,
        cache=MemoryTranslationCache(),
        checkpoint_every=2,
        checkpoint_output_path=checkpoint_output,
        checkpoint_report_path=checkpoint_report,
    )

    assert [word.meaning_zh for word in translated_words] == ["喝", "吃", "你好"]
    checkpoint_words = load_normalized_words(checkpoint_output)
    assert [word.meaning_zh for word in checkpoint_words] == ["喝", "吃", "你好"]
    progress = json.loads(checkpoint_report.read_text(encoding="utf-8"))
    assert progress["processed_words"] == 3
    assert progress["total_words"] == 3
    assert progress["percent_complete"] == 100.0
    assert summary["translated_now"] == 3


def test_translate_normalized_words_script_writes_checkpoint_files(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_path = tmp_path / "words.jsonl"
    output_path = tmp_path / "translated.jsonl"
    report_path = tmp_path / "translation-report.json"
    checkpoint_output = tmp_path / "checkpoint.jsonl"
    checkpoint_report = tmp_path / "checkpoint-report.json"
    glossary_path = repo_root / "tests" / "fixtures" / "translation_glossary.json"
    words = [
        NormalizedWord(
            language="JA",
            lemma="drink",
            surface="drink",
            reading_or_ipa="",
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
            reading_or_ipa="",
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
            "--checkpoint-every",
            "1",
            "--checkpoint-output",
            str(checkpoint_output),
            "--checkpoint-report",
            str(checkpoint_report),
        ],
        cwd=repo_root,
        check=True,
    )

    translated_words = load_normalized_words(output_path)
    checkpoint_words = load_normalized_words(checkpoint_output)
    checkpoint_summary = json.loads(checkpoint_report.read_text(encoding="utf-8"))

    assert [word.meaning_zh for word in translated_words] == ["喝", "你好"]
    assert [word.meaning_zh for word in checkpoint_words] == ["喝", "你好"]
    assert checkpoint_summary["processed_words"] == 2
    assert checkpoint_summary["translated_now"] == 2
