import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "src"))

from apply_french_manual_corrections import apply_french_manual_corrections
from dict_feasibility.translation_pipeline import iter_normalized_words


def _word_record(*, lemma: str, source_entry_id: str, source_text: str, meaning_zh: str) -> dict[str, str]:
    return {
        "language": "FR",
        "lemma": lemma,
        "surface": lemma,
        "reading_or_ipa": "",
        "pos": "noun",
        "meaning_source": "kaikki",
        "meaning_zh": meaning_zh,
        "source_name": "Kaikki French Wiktionary",
        "source_entry_id": source_entry_id,
        "meaning_source_text": source_text,
        "meaning_source_lang": "fr",
        "example_sentences_json": "[]",
    }


def test_apply_french_manual_corrections_updates_matching_entries(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    corrections_path = tmp_path / "corrections.json"
    output_path = tmp_path / "corrected.jsonl"
    report_path = tmp_path / "report.json"
    source_text = "Peuple germanique qui vit essentiellement en Allemagne."
    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    _word_record(
                        lemma="Allemands",
                        source_entry_id="Allemands",
                        source_text=source_text,
                        meaning_zh="bad English residue",
                    ),
                    ensure_ascii=False,
                ),
                json.dumps(
                    _word_record(
                        lemma="mardi",
                        source_entry_id="mardi",
                        source_text="Le jour du mardi.",
                        meaning_zh="\u661f\u671f\u4e8c\u3002",
                    ),
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )
    corrections_path.write_text(
        json.dumps(
            [
                {
                    "source_entry_id": "Allemands",
                    "meaning_source_text": source_text,
                    "meaning_zh": "\u65e5\u8033\u66fc\u6c11\u65cf\u3002",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = apply_french_manual_corrections(
        input_path=input_path,
        corrections_path=corrections_path,
        output_path=output_path,
        report_path=report_path,
    )

    words = list(iter_normalized_words(output_path))
    assert words[0].meaning_zh == "\u65e5\u8033\u66fc\u6c11\u65cf\u3002"
    assert words[1].meaning_zh == "\u661f\u671f\u4e8c\u3002"
    assert report == {"total_words": 2, "applied_corrections": 1, "unused_corrections": 0}
    assert json.loads(report_path.read_text(encoding="utf-8")) == report
