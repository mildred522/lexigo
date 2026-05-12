import json
import subprocess
import sys
from pathlib import Path

from dict_feasibility.kaikki_parser import parse_kaikki_french_file


def test_parse_kaikki_french_file_extracts_core_fields() -> None:
    fixture = Path("tests/fixtures/kaikki_fr_sample.jsonl")
    records = list(parse_kaikki_french_file(fixture))

    assert records[0].language == "FR"
    assert records[0].lemma == "bonjour"
    assert records[0].reading_or_ipa == "bɔ̃.ʒuʁ"
    assert records[0].meaning_zh == ""
    assert records[0].meaning_source_text == "salutation de bienvenue"
    assert records[0].meaning_source_lang == "fr"
    assert json.loads(records[0].example_sentences_json) == [
        {
            "sentence_foreign": "Bonjour, Marie !",
            "sentence_zh": "",
        }
    ]


def test_parse_kaikki_script_creates_normalized_output() -> None:
    script_path = Path("scripts/parse_kaikki_fr.py")
    repo_root = script_path.resolve().parents[1]
    artifact_path = repo_root / "artifacts" / "normalized" / "kaikki_fr_words.jsonl"
    if artifact_path.exists():
        artifact_path.unlink()

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=repo_root,
        check=True,
    )

    assert artifact_path.exists()
    with artifact_path.open("r", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle if line.strip()]

    assert records
    assert records[0]["meaning_source_text"] == "salutation de bienvenue"
    assert json.loads(records[0]["example_sentences_json"]) == [
        {
            "sentence_foreign": "Bonjour, Marie !",
            "sentence_zh": "",
        }
    ]
