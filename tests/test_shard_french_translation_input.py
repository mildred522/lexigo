import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from shard_french_translation_input import shard_french_translation_input


def _make_word(
    *,
    lemma: str,
    meaning_source_text: str,
    meaning_zh: str = "",
    source_entry_id: str | None = None,
) -> dict[str, str]:
    return {
        "language": "FR",
        "lemma": lemma,
        "surface": lemma,
        "reading_or_ipa": "",
        "pos": "noun",
        "meaning_source": "kaikki",
        "meaning_zh": meaning_zh,
        "source_name": "Kaikki French Wiktionary",
        "source_entry_id": source_entry_id or lemma,
        "meaning_source_text": meaning_source_text,
        "meaning_source_lang": "fr" if meaning_source_text else "",
        "example_sentences_json": "[]",
    }


def test_shard_french_translation_input_skips_translated_and_missing_source(tmp_path: Path) -> None:
    input_path = tmp_path / "kaikki_fr_words.jsonl"
    output_dir = tmp_path / "fr_shards"
    rows = [
        _make_word(lemma="a", meaning_source_text="definition a"),
        _make_word(lemma="b", meaning_source_text="definition b"),
        _make_word(lemma="c", meaning_source_text="", source_entry_id="c"),
        _make_word(lemma="d", meaning_source_text="definition d", meaning_zh="translated"),
        _make_word(lemma="e", meaning_source_text="definition e"),
    ]
    input_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    shard_paths = shard_french_translation_input(
        input_path=input_path,
        output_dir=output_dir,
        shard_size=2,
    )

    assert [path.name for path in shard_paths] == [
        "kaikki_fr_part_0001.jsonl",
        "kaikki_fr_part_0002.jsonl",
    ]
    assert output_dir.joinpath("kaikki_fr_part_0001.jsonl").read_text(encoding="utf-8").splitlines() == [
        json.dumps(rows[0], ensure_ascii=False),
        json.dumps(rows[1], ensure_ascii=False),
    ]
    assert output_dir.joinpath("kaikki_fr_part_0002.jsonl").read_text(encoding="utf-8").splitlines() == [
        json.dumps(rows[4], ensure_ascii=False),
    ]
