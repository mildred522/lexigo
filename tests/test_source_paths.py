from pathlib import Path

from dict_feasibility.source_paths import (
    resolve_jmdict_source,
    resolve_kaikki_fr_source,
    resolve_tatoeba_links_archive,
    resolve_tatoeba_sentence_archive,
)


def test_resolve_jmdict_source_prefers_full_download_over_fixture(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    full_source = repo_root / "sources" / "jmdict" / "JMdict.gz"
    full_source.parent.mkdir(parents=True, exist_ok=True)
    full_source.write_bytes(b"gzip-placeholder")
    monkeypatch.setenv("DICT_FEASIBILITY_SOURCE_MODE", "full")

    resolved = resolve_jmdict_source(repo_root)

    assert resolved == full_source


def test_resolve_kaikki_source_prefers_full_download_over_fixture(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path
    full_source = repo_root / "sources" / "kaikki_fr" / "raw-wiktextract-data.jsonl.gz"
    full_source.parent.mkdir(parents=True, exist_ok=True)
    full_source.write_bytes(b"gzip-placeholder")
    monkeypatch.setenv("DICT_FEASIBILITY_SOURCE_MODE", "full")

    resolved = resolve_kaikki_fr_source(repo_root)

    assert resolved == full_source


def test_resolve_tatoeba_archives_prefers_full_downloads_in_full_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path
    sentences_archive = repo_root / "sources" / "tatoeba" / "sentences.tar.bz2"
    links_archive = repo_root / "sources" / "tatoeba" / "links.tar.bz2"
    sentences_archive.parent.mkdir(parents=True, exist_ok=True)
    sentences_archive.write_bytes(b"archive-placeholder")
    links_archive.write_bytes(b"archive-placeholder")
    monkeypatch.setenv("DICT_FEASIBILITY_SOURCE_MODE", "full")

    resolved_sentences = resolve_tatoeba_sentence_archive(repo_root)
    resolved_links = resolve_tatoeba_links_archive(repo_root)

    assert resolved_sentences == sentences_archive
    assert resolved_links == links_archive
