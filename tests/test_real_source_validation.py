import gzip
import json
from pathlib import Path

from dict_feasibility.real_source_validation import (
    summarize_jmdict_gz_file,
    summarize_kaikki_gz_file,
)


def test_summarize_jmdict_gz_file_counts_gloss_languages(tmp_path: Path) -> None:
    xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
<JMdict>
  <entry>
    <ent_seq>1001</ent_seq>
    <k_ele><keb>食べる</keb></k_ele>
    <r_ele><reb>たべる</reb></r_ele>
    <sense>
      <pos>verb</pos>
      <gloss xml:lang="eng">to eat</gloss>
      <gloss xml:lang="zho">吃</gloss>
    </sense>
  </entry>
  <entry>
    <ent_seq>1002</ent_seq>
    <r_ele><reb>のむ</reb></r_ele>
    <sense>
      <pos>verb</pos>
      <gloss>to drink</gloss>
    </sense>
  </entry>
</JMdict>
"""
    gz_path = tmp_path / "JMdict-test.gz"
    with gzip.open(gz_path, "wb") as handle:
        handle.write(xml_payload.encode("utf-8"))

    summary = summarize_jmdict_gz_file(gz_path, limit=50)

    assert summary["sampled_entries"] == 2
    assert summary["pronunciation_present"] == 2
    assert summary["source_meaning_present"] == 2
    assert summary["chinese_gloss_present"] == 1
    assert summary["english_gloss_present"] == 2
    assert summary["sample_terms"] == ["食べる", "のむ"]


def test_summarize_kaikki_gz_file_filters_french_and_counts_fields(tmp_path: Path) -> None:
    lines = [
        {
            "word": "bonjour",
            "lang_code": "fr",
            "pos": "intj",
            "sounds": [{"ipa": "\\bɔ̃.ʒuʁ\\"}],
            "senses": [{"glosses": ["salutation"]}],
        },
        {
            "word": "lire",
            "lang_code": "fr",
            "pos": "verb",
            "sounds": [],
            "senses": [{"glosses": ["interpréter un texte"]}],
        },
        {
            "word": "ciao",
            "lang_code": "it",
            "pos": "intj",
            "sounds": [{"ipa": "\\tʃa.o\\"}],
            "senses": [{"glosses": ["saluto"]}],
        },
    ]
    gz_path = tmp_path / "frwiktionary-test.jsonl.gz"
    with gzip.open(gz_path, "wt", encoding="utf-8") as handle:
        for payload in lines:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    summary = summarize_kaikki_gz_file(gz_path, limit=50)

    assert summary["sampled_entries"] == 2
    assert summary["pronunciation_present"] == 1
    assert summary["source_meaning_present"] == 2
    assert summary["chinese_gloss_present"] == 0
    assert summary["sample_terms"] == ["bonjour", "lire"]
