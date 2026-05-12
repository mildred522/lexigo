import json
import subprocess
import sys
from pathlib import Path

from dict_feasibility.feasibility_report import render_report


def test_render_report_includes_verdict_and_counts() -> None:
    report = render_report(
        japanese_summary={
            "total_words": 1200,
            "missing_pronunciation": 10,
            "missing_meaning": 20,
            "missing_source_meaning": 0,
            "pronunciation_coverage_ratio": 0.99,
            "meaning_coverage_ratio": 0.9833,
            "source_meaning_coverage_ratio": 1.0,
            "sample_lemmas": ["nomu", "taberu"],
        },
        french_summary={
            "total_words": 900,
            "missing_pronunciation": 50,
            "missing_meaning": 0,
            "missing_source_meaning": 0,
            "pronunciation_coverage_ratio": 0.9444,
            "meaning_coverage_ratio": 1.0,
            "source_meaning_coverage_ratio": 1.0,
            "sample_lemmas": ["bonjour", "salut"],
        },
        translation_provider="mapping-glossary",
        translation_sample_size=25,
    )

    assert "High feasibility" in report
    assert "Japanese total words: 1200" in report
    assert "French total words: 900" in report
    assert "Translation provider tested: mapping-glossary" in report
    assert "Chinese meanings are being filled through the translation pipeline." in report


def test_render_report_prefers_real_source_validation_over_fixture_samples() -> None:
    report = render_report(
        japanese_summary={
            "total_words": 2,
            "missing_pronunciation": 0,
            "missing_meaning": 0,
            "missing_source_meaning": 0,
            "pronunciation_coverage_ratio": 1.0,
            "meaning_coverage_ratio": 1.0,
            "source_meaning_coverage_ratio": 1.0,
            "sample_lemmas": ["nomu", "taberu"],
        },
        french_summary={
            "total_words": 1,
            "missing_pronunciation": 0,
            "missing_meaning": 0,
            "missing_source_meaning": 0,
            "pronunciation_coverage_ratio": 1.0,
            "meaning_coverage_ratio": 1.0,
            "source_meaning_coverage_ratio": 1.0,
            "sample_lemmas": ["bonjour"],
        },
        translation_provider="mapping-glossary",
        translation_sample_size=3,
        real_source_validation={
            "sample_limit": 50,
            "japanese": {
                "sampled_entries": 50,
                "pronunciation_coverage_ratio": 1.0,
                "source_meaning_coverage_ratio": 1.0,
                "chinese_gloss_coverage_ratio": 0.0,
                "translation_required_entries": 50,
            },
            "french": {
                "sampled_entries": 50,
                "pronunciation_coverage_ratio": 1.0,
                "source_meaning_coverage_ratio": 1.0,
                "chinese_gloss_coverage_ratio": 0.0,
                "translation_required_entries": 50,
            },
        },
        real_source_translation_validation={
            "sample_limit": 50,
            "japanese": {
                "sampled_entries": 50,
                "translated_entries": 0,
                "translated_coverage_ratio": 0.0,
                "translation_errors": 50,
            },
            "french": {
                "sampled_entries": 50,
                "translated_entries": 0,
                "translated_coverage_ratio": 0.0,
                "translation_errors": 50,
            },
        },
    )

    assert "High feasibility" not in report
    assert "Structurally feasible; Chinese-ready output still needs live translation validation" in report
    assert "Official source validation sample size: 50 per language" in report
    assert "Japanese direct Chinese gloss coverage in source: 0.0%" in report
    assert "French direct Chinese gloss coverage in source: 0.0%" in report
    assert "Japanese translated coverage on official sample: 0.0%" in report
    assert "French translated coverage on official sample: 0.0%" in report


def test_render_report_marks_high_feasibility_after_live_translation_validation() -> None:
    report = render_report(
        japanese_summary={
            "total_words": 2,
            "missing_pronunciation": 0,
            "missing_meaning": 0,
            "missing_source_meaning": 0,
            "pronunciation_coverage_ratio": 1.0,
            "meaning_coverage_ratio": 1.0,
            "source_meaning_coverage_ratio": 1.0,
            "sample_lemmas": ["nomu", "taberu"],
        },
        french_summary={
            "total_words": 1,
            "missing_pronunciation": 0,
            "missing_meaning": 0,
            "missing_source_meaning": 0,
            "pronunciation_coverage_ratio": 1.0,
            "meaning_coverage_ratio": 1.0,
            "source_meaning_coverage_ratio": 1.0,
            "sample_lemmas": ["bonjour"],
        },
        translation_provider="openai:gpt-5.4-mini",
        translation_sample_size=3,
        real_source_validation={
            "sample_limit": 50,
            "japanese": {
                "sampled_entries": 50,
                "pronunciation_coverage_ratio": 1.0,
                "source_meaning_coverage_ratio": 1.0,
                "chinese_gloss_coverage_ratio": 0.0,
                "translation_required_entries": 50,
            },
            "french": {
                "sampled_entries": 50,
                "pronunciation_coverage_ratio": 1.0,
                "source_meaning_coverage_ratio": 1.0,
                "chinese_gloss_coverage_ratio": 0.0,
                "translation_required_entries": 50,
            },
        },
        real_source_translation_validation={
            "provider": "openai",
            "model": "gpt-5.4-mini",
            "sample_limit": 50,
            "japanese": {
                "sampled_entries": 50,
                "translated_entries": 48,
                "translated_coverage_ratio": 0.96,
                "translation_errors": 2,
            },
            "french": {
                "sampled_entries": 50,
                "translated_entries": 48,
                "translated_coverage_ratio": 0.96,
                "translation_errors": 2,
            },
        },
    )

    assert "High feasibility" in report
    assert "Translation provider tested: openai:gpt-5.4-mini" in report
    assert "Japanese translated coverage on official sample: 96.0%" in report
    assert "French translated coverage on official sample: 96.0%" in report
    assert "Live provider validation shows strong Chinese-ready coverage on the official sample." in report


def test_render_feasibility_report_script_writes_markdown() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report_path = repo_root / "docs" / "feasibility-report.md"
    reports_dir = repo_root / "artifacts" / "reports"
    report_path.unlink(missing_ok=True)

    real_source_validation_path = reports_dir / "real-source-validation.json"
    real_source_translation_path = reports_dir / "real-source-translation-validation.json"
    original_real_source_validation = (
        real_source_validation_path.read_text(encoding="utf-8")
        if real_source_validation_path.exists()
        else None
    )
    original_real_source_translation = (
        real_source_translation_path.read_text(encoding="utf-8")
        if real_source_translation_path.exists()
        else None
    )

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

    real_source_validation_path.write_text(
        json.dumps(
            {
                "sample_limit": 50,
                "japanese": {
                    "sampled_entries": 50,
                    "pronunciation_coverage_ratio": 1.0,
                    "source_meaning_coverage_ratio": 1.0,
                    "chinese_gloss_coverage_ratio": 0.0,
                    "translation_required_entries": 50,
                },
                "french": {
                    "sampled_entries": 50,
                    "pronunciation_coverage_ratio": 1.0,
                    "source_meaning_coverage_ratio": 1.0,
                    "chinese_gloss_coverage_ratio": 0.0,
                    "translation_required_entries": 50,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    real_source_translation_path.write_text(
        json.dumps(
            {
                "provider": "openai",
                "model": "gpt-5.4-mini",
                "sample_limit": 50,
                "japanese": {
                    "sampled_entries": 50,
                    "translated_entries": 48,
                    "translated_coverage_ratio": 0.96,
                    "translation_errors": 2,
                },
                "french": {
                    "sampled_entries": 50,
                    "translated_entries": 48,
                    "translated_coverage_ratio": 0.96,
                    "translation_errors": 2,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    try:
        subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "render_feasibility_report.py")],
            cwd=repo_root,
            check=True,
        )
    finally:
        if original_real_source_validation is None:
            real_source_validation_path.unlink(missing_ok=True)
        else:
            real_source_validation_path.write_text(
                original_real_source_validation,
                encoding="utf-8",
            )
        if original_real_source_translation is None:
            real_source_translation_path.unlink(missing_ok=True)
        else:
            real_source_translation_path.write_text(
                original_real_source_translation,
                encoding="utf-8",
            )

    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "# Dictionary Feasibility Report" in report_text
    assert "High feasibility" in report_text
    assert "Official source validation sample size: 50 per language" in report_text
    assert "Translation provider tested: openai:gpt-5.4-mini" in report_text
