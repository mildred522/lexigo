import json
from typing import Iterable


class AsxsResponsesStreamError(RuntimeError):
    pass


def fix_latin1_utf8_mojibake(text: str) -> str:
    if not text:
        return text
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def extract_responses_stream_text(lines: Iterable[str | bytes]) -> tuple[str, dict | None]:
    deltas: list[str] = []
    usage: dict | None = None

    for raw in lines:
        if not raw:
            continue
        raw = _normalize_stream_line(raw)
        if raw.startswith(":") or raw.startswith("event: "):
            continue
        if not raw.startswith("data: "):
            continue

        payload = raw[6:]
        if payload == "[DONE]":
            break

        item = json.loads(payload)
        item_type = item.get("type")
        if item_type == "response.output_text.delta":
            deltas.append(item.get("delta", ""))
            continue
        if item_type == "response.completed":
            usage = (item.get("response") or {}).get("usage")
            break
        if item_type == "error" or "error" in item:
            error = item.get("error") or item
            raise AsxsResponsesStreamError(json.dumps(error, ensure_ascii=False))

    return "".join(deltas), usage


def _normalize_stream_line(raw: str | bytes) -> str:
    if isinstance(raw, bytes):
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin1")
    return raw


def parse_indexed_translation_lines(raw: str, *, expected_count: int) -> list[str]:
    translations_by_index: dict[int, str] = {}

    for line in raw.splitlines():
        normalized = line.strip()
        if not normalized:
            continue
        if normalized.startswith("```"):
            continue
        if "\t" not in normalized:
            raise ValueError(f"Invalid translation row: {normalized}")
        index_text, translation = normalized.split("\t", maxsplit=1)
        index = int(index_text.strip())
        translation = translation.strip()
        if not translation:
            raise ValueError(f"Missing translation text for index {index}")
        translations_by_index[index] = translation

    missing = [str(index) for index in range(expected_count) if index not in translations_by_index]
    if missing:
        raise ValueError(f"Missing translations for indices: {', '.join(missing)}")

    return [translations_by_index[index] for index in range(expected_count)]
