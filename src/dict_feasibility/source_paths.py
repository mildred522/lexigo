import gzip
import os
from pathlib import Path
from typing import Iterable, IO


def resolve_jmdict_source(repo_root: Path) -> Path:
    return _resolve_existing_path(
        _ordered_candidates(
            full_candidates=[
                repo_root / "sources" / "jmdict" / "JMdict.gz",
                repo_root / "sources" / "jmdict" / "JMdict",
            ],
            fixture_candidates=[
                repo_root / "sources" / "jmdict" / "jmdict-sample.json",
                repo_root / "tests" / "fixtures" / "jmdict_sample.json",
            ],
        ),
        "JMdict source",
    )


def resolve_kaikki_fr_source(repo_root: Path) -> Path:
    return _resolve_existing_path(
        _ordered_candidates(
            full_candidates=[
                repo_root / "sources" / "kaikki_fr" / "raw-wiktextract-data.jsonl.gz",
                repo_root / "sources" / "kaikki_fr" / "raw-wiktextract-data.jsonl",
            ],
            fixture_candidates=[
                repo_root / "sources" / "kaikki_fr" / "kaikki-fr-sample.jsonl",
                repo_root / "tests" / "fixtures" / "kaikki_fr_sample.jsonl",
            ],
        ),
        "Kaikki French source",
    )


def resolve_tatoeba_examples_source(repo_root: Path) -> Path:
    return _resolve_existing_path(
        _ordered_candidates(
            full_candidates=[
                repo_root / "sources" / "tatoeba" / "jpn_cmn_examples.tsv",
            ],
            fixture_candidates=[
                repo_root / "sources" / "tatoeba" / "tatoeba-sample.tsv",
                repo_root / "tests" / "fixtures" / "tatoeba_sample.tsv",
            ],
        ),
        "Tatoeba sample examples",
    )


def resolve_tatoeba_sentence_archive(repo_root: Path) -> Path | None:
    if _prefer_fixture_sources():
        return None
    return _resolve_optional_existing_path(
        [
            repo_root / "sources" / "tatoeba" / "sentences.tar.bz2",
        ]
    )


def resolve_tatoeba_links_archive(repo_root: Path) -> Path | None:
    if _prefer_fixture_sources():
        return None
    return _resolve_optional_existing_path(
        [
            repo_root / "sources" / "tatoeba" / "links.tar.bz2",
        ]
    )


def open_text_maybe_gzip(path: Path, *, encoding: str = "utf-8") -> IO[str]:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding=encoding)
    return path.open("r", encoding=encoding)


def open_binary_maybe_gzip(path: Path) -> IO[bytes]:
    if path.suffix == ".gz":
        return gzip.open(path, "rb")
    return path.open("rb")


def _resolve_existing_path(candidates: Iterable[Path], description: str) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"{description} not found in expected locations")


def _resolve_optional_existing_path(candidates: Iterable[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _ordered_candidates(
    *,
    full_candidates: list[Path],
    fixture_candidates: list[Path],
) -> list[Path]:
    if _prefer_fixture_sources():
        return fixture_candidates + full_candidates
    return full_candidates + fixture_candidates


def _prefer_fixture_sources() -> bool:
    explicit_mode = os.environ.get("DICT_FEASIBILITY_SOURCE_MODE", "").strip().lower()
    if explicit_mode == "fixture":
        return True
    if explicit_mode == "full":
        return False
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))
