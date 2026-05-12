import json
import subprocess
import sys
from pathlib import Path

from dict_feasibility.jmdict_parser import parse_jmdict_file


def test_parse_jmdict_file_extracts_core_fields() -> None:
    fixture = Path("tests/fixtures/jmdict_sample.json")
    records = list(parse_jmdict_file(fixture))

    assert records[0].language == "JA"
    assert records[0].lemma == "食べる"
    assert records[0].reading_or_ipa == "たべる"
    assert records[0].meaning_zh == "吃"
    assert records[0].meaning_source_text == "吃"
    assert records[0].meaning_source_lang == "zh"


def test_parse_jmdict_file_preserves_english_source_when_no_chinese() -> None:
    fixture = Path("tests/fixtures/jmdict_sample.json")
    records = list(parse_jmdict_file(fixture))

    drink_record = next(rec for rec in records if rec.lemma == "飲む")
    assert drink_record.meaning_zh == ""
    assert drink_record.meaning_source_text == "to drink"
    assert drink_record.meaning_source_lang == "en"


def test_parse_jmdict_file_attaches_example_sentences_when_provided() -> None:
    fixture = Path("tests/fixtures/jmdict_sample.json")
    records = list(
        parse_jmdict_file(
            fixture,
            {
                "食べる": [
                    {
                        "sentence_foreign": "食べます。",
                        "sentence_zh": "我吃。",
                    }
                ]
            },
        )
    )

    eat_record = next(rec for rec in records if rec.lemma == "食べる")
    assert json.loads(eat_record.example_sentences_json) == [
        {
            "sentence_foreign": "食べます。",
            "sentence_zh": "我吃。",
        }
    ]


def test_parse_jmdict_file_handles_empty_arrays(tmp_path: Path) -> None:
    entry = {"id": "2002", "kanji": [], "kana": [], "sense": []}
    empty_file = tmp_path / "empty.json"
    empty_file.write_text(json.dumps([entry], ensure_ascii=False), encoding="utf-8")

    records = list(parse_jmdict_file(empty_file))
    assert len(records) == 1
    assert records[0].lemma == ""
    assert records[0].reading_or_ipa == ""
    assert records[0].meaning_zh == ""
    assert records[0].meaning_source_text == ""
    assert records[0].meaning_source_lang == ""


def test_parse_jmdict_script_writes_normalized_records() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    artifacts_file = repo_root / "artifacts" / "normalized" / "jmdict_words.jsonl"
    artifacts_file.unlink(missing_ok=True)
    artifacts_file.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "parse_jmdict.py")],
        check=True,
        cwd=repo_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    assert artifacts_file.exists()
    lines = artifacts_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    record = json.loads(lines[0])
    assert record["lemma"] == "食べる"
    assert record["meaning_source_text"] == "吃"
    assert json.loads(record["example_sentences_json"]) == [
        {
            "sentence_foreign": "食べます。",
            "sentence_zh": "我吃。",
        }
    ]

    artifacts_file.unlink()
