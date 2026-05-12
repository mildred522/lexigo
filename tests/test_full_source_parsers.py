import gzip
import json
from pathlib import Path

from dict_feasibility.jmdict_parser import parse_jmdict_file
from dict_feasibility.kaikki_parser import parse_kaikki_french_file


def test_parse_jmdict_file_reads_gzipped_xml_source(tmp_path: Path) -> None:
    xml_payload = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE JMdict [
<!ELEMENT JMdict (entry*)>
<!ELEMENT entry (ent_seq, k_ele*, r_ele+, sense+)>
<!ELEMENT ent_seq (#PCDATA)>
<!ELEMENT k_ele (keb)>
<!ELEMENT keb (#PCDATA)>
<!ELEMENT r_ele (reb)>
<!ELEMENT reb (#PCDATA)>
<!ELEMENT sense (pos*, gloss+)>
<!ELEMENT pos (#PCDATA)>
<!ELEMENT gloss (#PCDATA)>
]>
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
</JMdict>
"""
    source_path = tmp_path / "JMdict.gz"
    with gzip.open(source_path, "wt", encoding="utf-8") as handle:
        handle.write(xml_payload)

    records = list(parse_jmdict_file(source_path))

    assert len(records) == 1
    assert records[0].lemma == "食べる"
    assert records[0].reading_or_ipa == "たべる"
    assert records[0].meaning_zh == "吃"
    assert records[0].meaning_source_text == "吃"
    assert records[0].source_entry_id == "1001"


def test_parse_kaikki_french_file_reads_gzipped_jsonl_and_prefers_chinese_translation(tmp_path: Path) -> None:
    payload = {
        "word": "bonjour",
        "lang_code": "fr",
        "sounds": [{"ipa": "bɔ̃.ʒuʁ"}],
        "pos": "intj",
        "senses": [
            {
                "glosses": ["salutation de bienvenue"],
                "examples": [{"text": "Bonjour, Marie !"}],
            }
        ],
        "translations": [
            {
                "lang_code": "zh",
                "word": "你好",
                "roman": "nǐhǎo",
            }
        ],
    }
    source_path = tmp_path / "raw-wiktextract-data.jsonl.gz"
    with gzip.open(source_path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    records = list(parse_kaikki_french_file(source_path))

    assert len(records) == 1
    assert records[0].lemma == "bonjour"
    assert records[0].reading_or_ipa == "bɔ̃.ʒuʁ"
    assert records[0].meaning_zh == "你好"
    assert records[0].meaning_source_text == "salutation de bienvenue"
