import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from audit_french_translation_backlog import audit_french_translation_backlog


def test_audit_french_translation_backlog_reports_counts(tmp_path: Path) -> None:
    input_path = tmp_path / "kaikki_fr_words.jsonl"
    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
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
                    }
                ),
                json.dumps(
                    {
                        "language": "FR",
                        "lemma": "bonjour",
                        "surface": "bonjour",
                        "reading_or_ipa": "",
                        "pos": "intj",
                        "meaning_source": "kaikki",
                        "meaning_zh": "hello",
                        "source_name": "Kaikki French Wiktionary",
                        "source_entry_id": "bonjour",
                        "meaning_source_text": "Salutation.",
                        "meaning_source_lang": "fr",
                        "example_sentences_json": "[]",
                    }
                ),
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
            ]
        ),
        encoding="utf-8",
    )

    report = audit_french_translation_backlog(input_path)

    assert report["total_words"] == 3
    assert report["translated_words"] == 1
    assert report["untranslated_words"] == 2
    assert report["missing_source_text_words"] == 1
    assert report["unique_nonempty_source_texts"] == 2
    assert report["source_lang_counts"] == {"fr": 2, "unknown": 1}
