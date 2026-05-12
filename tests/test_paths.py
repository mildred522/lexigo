from pathlib import Path

from dict_feasibility.models import NormalizedWord
from dict_feasibility.paths import ensure_project_dirs


def test_ensure_project_dirs_creates_expected_structure(tmp_path: Path) -> None:
    result = ensure_project_dirs(tmp_path)

    assert result.sources_dir.exists()
    assert result.artifacts_dir.exists()
    assert result.normalized_dir.exists()
    assert result.reports_dir.exists()


def test_normalized_word_to_record() -> None:
    word = NormalizedWord(
        language="JA",
        lemma="食べる",
        surface="食べる",
        reading_or_ipa="たべる",
        pos="verb",
        meaning_source="jmdict",
        meaning_zh="吃",
        source_name="JMdict",
        source_entry_id="1001",
        meaning_source_text="吃",
        meaning_source_lang="zh",
    )

    record = word.to_record()

    assert record["meaning_zh"] == "吃"
    assert record["meaning_source_text"] == "吃"
    assert record["meaning_source_lang"] == "zh"
