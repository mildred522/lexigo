import gzip
import json
from pathlib import Path

from dict_feasibility.real_source_translation_validation import (
    sample_jmdict_words_from_gz_file,
    sample_kaikki_words_from_gz_file,
    summarize_translation_validation,
)


def test_sample_jmdict_words_from_gz_file_extracts_translation_candidates(tmp_path: Path) -> None:
    xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>1001</ent_seq>
    <k_ele><keb>食べる</keb></k_ele>
    <r_ele><reb>たべる</reb></r_ele>
    <sense>
      <pos>verb</pos>
      <gloss xml:lang="eng">to eat</gloss>
    </sense>
  </entry>
</JMdict>
"""
    gz_path = tmp_path / "JMdict-test.gz"
    with gzip.open(gz_path, "wb") as handle:
        handle.write(xml_payload.encode("utf-8"))

    words = sample_jmdict_words_from_gz_file(gz_path, limit=10)

    assert len(words) == 1
    assert words[0].lemma == "食べる"
    assert words[0].meaning_source_text == "to eat"
    assert words[0].meaning_source_lang == "en"
    assert words[0].meaning_zh == ""


def test_sample_kaikki_words_from_gz_file_extracts_translation_candidates(tmp_path: Path) -> None:
    payloads = [
        {
            "word": "bonjour",
            "lang_code": "fr",
            "pos": "intj",
            "sounds": [{"ipa": "\\bɔ̃.ʒuʁ\\"}],
            "senses": [{"glosses": ["salutation de bienvenue"]}],
        }
    ]
    gz_path = tmp_path / "frwiktionary-test.jsonl.gz"
    with gzip.open(gz_path, "wt", encoding="utf-8") as handle:
        for payload in payloads:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    words = sample_kaikki_words_from_gz_file(gz_path, limit=10)

    assert len(words) == 1
    assert words[0].lemma == "bonjour"
    assert words[0].meaning_source_text == "salutation de bienvenue"
    assert words[0].meaning_source_lang == "fr"


def test_summarize_translation_validation_reports_failures() -> None:
    summary = summarize_translation_validation(
        language="FR",
        requested_limit=50,
        translated_words=[],
        pipeline_summary={
            "total_words": 2,
            "already_translated": 0,
            "translated_now": 1,
            "missing_source_text": 0,
            "copied_directly": 0,
            "cache_hits": 0,
            "translation_errors": 1,
            "failed_terms": ["bonjour"],
        },
    )

    assert summary["language"] == "FR"
    assert summary["sampled_entries"] == 2
    assert summary["translated_entries"] == 1
    assert summary["translation_errors"] == 1
    assert summary["failed_terms"] == ["bonjour"]
