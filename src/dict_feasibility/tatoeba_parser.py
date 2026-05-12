import csv
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable
from typing import Iterator


def parse_tatoeba_pairs(path: Path) -> Iterator[dict[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for lemma, sentence_foreign, sentence_zh in reader:
            yield {
                "lemma": lemma.strip(),
                "sentence_foreign": sentence_foreign.strip(),
                "sentence_zh": sentence_zh.strip(),
            }


def build_tatoeba_example_map(path: Path, limit: int = 2) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for pair in parse_tatoeba_pairs(path):
        lemma = pair["lemma"]
        bucket = grouped[lemma]
        if len(bucket) >= limit:
            continue
        bucket.append(
            {
                "sentence_foreign": pair["sentence_foreign"],
                "sentence_zh": pair["sentence_zh"],
            }
        )
    return dict(grouped)


def build_tatoeba_example_map_from_archives(
    *,
    sentences_archive: Path,
    links_archive: Path,
    target_lemmas: Iterable[str],
    limit: int = 2,
) -> dict[str, list[dict[str, str]]]:
    lemma_index = _build_lemma_index(target_lemmas)
    matched_japanese: dict[int, tuple[list[str], str]] = {}

    for sentence_id, language, text in _iter_tatoeba_archive_rows(sentences_archive, "sentences.csv"):
        if language not in {"jpn", "ja"}:
            continue
        matched_lemmas = _match_target_lemmas(text, lemma_index)
        if not matched_lemmas:
            continue
        matched_japanese[sentence_id] = (matched_lemmas, text)

    if not matched_japanese:
        return {}

    translation_ids_by_sentence: dict[int, list[int]] = defaultdict(list)
    candidate_translation_ids: set[int] = set()
    for source_id, target_id in _iter_tatoeba_link_rows(links_archive):
        japanese_id, translation_id = _resolve_link_target(
            source_id,
            target_id,
            matched_japanese,
        )
        if japanese_id is None or translation_id is None:
            continue
        bucket = translation_ids_by_sentence[japanese_id]
        if translation_id in bucket:
            continue
        bucket.append(translation_id)
        candidate_translation_ids.add(translation_id)

    chinese_text_by_id: dict[int, str] = {}
    for sentence_id, language, text in _iter_tatoeba_archive_rows(sentences_archive, "sentences.csv"):
        if sentence_id not in candidate_translation_ids:
            continue
        if language not in {"cmn", "zh", "zho"}:
            continue
        chinese_text_by_id[sentence_id] = text

    examples_by_lemma: dict[str, list[dict[str, str]]] = defaultdict(list)
    for japanese_id, (lemmas, sentence_foreign) in matched_japanese.items():
        for translation_id in translation_ids_by_sentence.get(japanese_id, []):
            sentence_zh = chinese_text_by_id.get(translation_id, "")
            if not sentence_zh:
                continue
            pair = {
                "sentence_foreign": sentence_foreign,
                "sentence_zh": sentence_zh,
            }
            for lemma in lemmas:
                bucket = examples_by_lemma[lemma]
                if len(bucket) >= limit or pair in bucket:
                    continue
                bucket.append(pair)

    return dict(examples_by_lemma)


def _iter_tatoeba_archive_rows(archive_path: Path, member_name: str) -> Iterator[tuple[int, str, str]]:
    with tarfile.open(archive_path, "r:*") as archive:
        member = archive.extractfile(member_name)
        if member is None:
            raise FileNotFoundError(f"{member_name} not found in {archive_path}")
        decoded = (line.decode("utf-8").rstrip("\n") for line in member)
        reader = csv.reader(decoded, delimiter="\t")
        for row in reader:
            if len(row) != 3:
                continue
            yield int(row[0]), row[1].strip(), row[2].strip()


def _iter_tatoeba_link_rows(archive_path: Path) -> Iterator[tuple[int, int]]:
    with tarfile.open(archive_path, "r:*") as archive:
        member = archive.extractfile("links.csv")
        if member is None:
            raise FileNotFoundError(f"links.csv not found in {archive_path}")
        decoded = (line.decode("utf-8").rstrip("\n") for line in member)
        reader = csv.reader(decoded, delimiter="\t")
        for row in reader:
            if len(row) != 2:
                continue
            yield int(row[0]), int(row[1])


def _build_lemma_index(target_lemmas: Iterable[str]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    unique_lemmas = sorted(
        {lemma.strip() for lemma in target_lemmas if lemma.strip()},
        key=len,
        reverse=True,
    )
    for lemma in unique_lemmas:
        index[lemma[0]].append(lemma)
    return dict(index)


def _match_target_lemmas(text: str, lemma_index: dict[str, list[str]]) -> list[str]:
    matches: list[str] = []
    seen: set[str] = set()
    for offset, char in enumerate(text):
        for lemma in lemma_index.get(char, []):
            if lemma in seen:
                continue
            if text.startswith(lemma, offset):
                matches.append(lemma)
                seen.add(lemma)
    return matches


def _resolve_link_target(
    source_id: int,
    target_id: int,
    matched_japanese: dict[int, tuple[list[str], str]],
) -> tuple[int | None, int | None]:
    if source_id in matched_japanese and target_id not in matched_japanese:
        return source_id, target_id
    if target_id in matched_japanese and source_id not in matched_japanese:
        return target_id, source_id
    return None, None
