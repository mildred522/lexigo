import json
import subprocess
import sys
from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.reporting import summarize_words


def test_summarize_words_counts_missing_fields() -> None:
    summary = summarize_words(
        [
            NormalizedWord(
                language="FR",
                lemma="bonjour",
                surface="bonjour",
                reading_or_ipa="",
                pos="intj",
                meaning_source="kaikki",
                meaning_zh="你好",
                source_name="Kaikki",
                source_entry_id="bonjour",
                meaning_source_text="salutation de bienvenue",
                meaning_source_lang="fr",
            ),
            NormalizedWord(
                language="FR",
                lemma="salut",
                surface="salut",
                reading_or_ipa="sa.ly",
                pos="intj",
                meaning_source="kaikki",
                meaning_zh="",
                source_name="Kaikki",
                source_entry_id="salut",
                meaning_source_text="salutation familière",
                meaning_source_lang="fr",
            ),
        ]
    )

    assert summary["total_words"] == 2
    assert summary["missing_pronunciation"] == 1
    assert summary["missing_meaning"] == 1
    assert summary["missing_source_meaning"] == 0
    assert summary["pronunciation_coverage_ratio"] == 0.5
    assert summary["meaning_coverage_ratio"] == 0.5
    assert summary["source_meaning_coverage_ratio"] == 1.0


def test_summarize_words_includes_samples() -> None:
    summary = summarize_words(
        [
            NormalizedWord(
                language="JA",
                lemma="食べる",
                surface="食べる",
                reading_or_ipa="たべる",
                pos="verb",
                meaning_source="jmdict",
                meaning_zh="吃",
                source_name="JMdict",
                source_entry_id="1001",
                meaning_source_text="eat",
                meaning_source_lang="en",
            ),
            NormalizedWord(
                language="JA",
                lemma="飲む",
                surface="飲む",
                reading_or_ipa="のむ",
                pos="verb",
                meaning_source="jmdict",
                meaning_zh="喝",
                source_name="JMdict",
                source_entry_id="1002",
                meaning_source_text="drink",
                meaning_source_lang="en",
            ),
        ]
    )

    assert summary["sample_lemmas"] == ["食べる", "飲む"]


def test_sample_report_script_uses_translated_outputs_when_available() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = repo_root / "artifacts" / "reports"
    jmdict_summary_path = reports_dir / "jmdict-summary.json"
    kaiken_summary_path = reports_dir / "kaikki-fr-summary.json"

    jmdict_summary_path.unlink(missing_ok=True)
    kaiken_summary_path.unlink(missing_ok=True)

    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "parse_jmdict.py")],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "parse_kaikki_fr.py")],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "translate_normalized_words.py")],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "sample_report.py")],
        cwd=repo_root,
        check=True,
    )

    assert jmdict_summary_path.exists()
    assert kaiken_summary_path.exists()

    japanese_summary = json.loads(jmdict_summary_path.read_text(encoding="utf-8"))
    french_summary = json.loads(kaiken_summary_path.read_text(encoding="utf-8"))

    assert japanese_summary["total_words"] >= 1
    assert japanese_summary["source_meaning_coverage_ratio"] >= japanese_summary["meaning_coverage_ratio"]
    assert french_summary["missing_meaning"] == 0
