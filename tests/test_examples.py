import bz2
import io
import tarfile
from pathlib import Path

from dict_feasibility.examples import collect_french_examples, score_example
from dict_feasibility.tatoeba_parser import (
    build_tatoeba_example_map_from_archives,
    parse_tatoeba_pairs,
)


def test_collect_french_examples_reads_first_sentence() -> None:
    entry = {
        "senses": [
            {"examples": [{"text": "Bonjour, Marie !"}]},
        ]
    }

    examples = collect_french_examples(entry)
    assert examples == ["Bonjour, Marie !"]


def test_score_example_prefers_mid_length_sentences() -> None:
    assert score_example("Bonjour, Marie !") > score_example("Salut")


def test_parse_tatoeba_pairs_reads_japanese_chinese_rows() -> None:
    pairs = list(parse_tatoeba_pairs(Path("tests/fixtures/tatoeba_sample.tsv")))
    assert pairs[0]["sentence_foreign"] == "食べます。"
    assert pairs[0]["sentence_zh"] == "我吃。"


def test_build_tatoeba_example_map_from_archives_links_japanese_and_chinese_rows(
    tmp_path: Path,
) -> None:
    sentences_archive = tmp_path / "sentences.tar.bz2"
    links_archive = tmp_path / "links.tar.bz2"
    _write_tar_bz2(
        sentences_archive,
        "sentences.csv",
        "\n".join(
            [
                "1\tjpn\t私は食べる。",
                "2\tcmn\t我吃饭。",
                "3\tjpn\t彼は飲む。",
                "4\tcmn\t他喝水。",
            ]
        ),
    )
    _write_tar_bz2(
        links_archive,
        "links.csv",
        "\n".join(
            [
                "1\t2",
                "3\t4",
            ]
        ),
    )

    examples = build_tatoeba_example_map_from_archives(
        sentences_archive=sentences_archive,
        links_archive=links_archive,
        target_lemmas={"食べる", "飲む"},
        limit=1,
    )

    assert examples == {
        "食べる": [
            {
                "sentence_foreign": "私は食べる。",
                "sentence_zh": "我吃饭。",
            }
        ],
        "飲む": [
            {
                "sentence_foreign": "彼は飲む。",
                "sentence_zh": "他喝水。",
            }
        ],
    }


def _write_tar_bz2(path: Path, member_name: str, text: str) -> None:
    payload = text.encode("utf-8")
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
    path.write_bytes(bz2.compress(buffer.getvalue()))
