import json
from pathlib import Path
from typing import Iterator

from dict_feasibility.examples import collect_french_example_pairs, serialize_example_pairs
from dict_feasibility.models import NormalizedWord
from dict_feasibility.source_paths import open_text_maybe_gzip


def _first_gloss(entry: dict) -> str:
    for sense in entry.get("senses", []):
        for gloss in sense.get("glosses", []):
            text = gloss.strip()
            if text:
                return text
    return ""


def _pick_zh_translation(entry: dict) -> str:
    for translation in entry.get("translations", []):
        lang_code = (translation.get("lang_code") or translation.get("code") or "").lower()
        if lang_code not in {"zh", "cmn", "zh-cn", "zh-hans"}:
            continue
        text = (translation.get("word") or "").strip()
        if text:
            return text
    return ""


def parse_kaikki_french_file(path: Path) -> Iterator[NormalizedWord]:
    with open_text_maybe_gzip(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            entry = json.loads(line)
            if (entry.get("lang_code") or "").lower() not in {"fr", ""}:
                continue
            ipa = ""
            for sound in entry.get("sounds", []):
                ipa = sound.get("ipa", "")
                if ipa:
                    break
            source_gloss = _first_gloss(entry)
            zh_translation = _pick_zh_translation(entry)
            example_pairs = collect_french_example_pairs(entry)
            yield NormalizedWord(
                language="FR",
                lemma=entry.get("word", ""),
                surface=entry.get("word", ""),
                reading_or_ipa=ipa,
                pos=entry.get("pos", ""),
                meaning_source="kaikki",
                meaning_zh=zh_translation,
                source_name="Kaikki French Wiktionary",
                source_entry_id=entry.get("word", ""),
                meaning_source_text=source_gloss,
                meaning_source_lang="fr" if source_gloss else "",
                example_sentences_json=serialize_example_pairs(example_pairs),
            )
