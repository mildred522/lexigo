from pathlib import Path

from scripts.build_sqlite import iter_words


def test_iter_words_streams_jsonl_entries(tmp_path: Path) -> None:
    source_path = tmp_path / "words.jsonl"
    source_path.write_text(
        "\n".join(
            [
                '{"language":"FR","lemma":"bonjour","surface":"bonjour","reading_or_ipa":"bɔ̃.ʒuʁ","pos":"intj","meaning_source":"kaikki","meaning_zh":"你好","source_name":"Kaikki","source_entry_id":"bonjour","meaning_source_text":"salutation","meaning_source_lang":"fr","example_sentences_json":"[]"}',
                '{"language":"JA","lemma":"食べる","surface":"食べる","reading_or_ipa":"たべる","pos":"verb","meaning_source":"jmdict","meaning_zh":"","source_name":"JMdict","source_entry_id":"1001","meaning_source_text":"to eat","meaning_source_lang":"en","example_sentences_json":"[]"}',
            ]
        ),
        encoding="utf-8",
    )

    words = list(iter_words(source_path))

    assert [word.lemma for word in words] == ["bonjour", "食べる"]
