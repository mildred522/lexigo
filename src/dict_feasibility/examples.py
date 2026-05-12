import json


def collect_french_examples(entry: dict) -> list[str]:
    results: list[str] = []
    for sense in entry.get("senses", []):
        for example in sense.get("examples", []):
            text = example.get("text", "").strip()
            if text:
                results.append(text)
    return results


def score_example(text: str) -> int:
    length = len(text.strip())
    if 12 <= length <= 60:
        return 100
    if 6 <= length < 12 or 61 <= length <= 90:
        return 60
    return 20


def collect_french_example_pairs(entry: dict, limit: int = 2) -> list[dict[str, str]]:
    ranked = sorted(
        collect_french_examples(entry),
        key=score_example,
        reverse=True,
    )
    return [
        {
            "sentence_foreign": text,
            "sentence_zh": "",
        }
        for text in ranked[:limit]
    ]


def serialize_example_pairs(pairs: list[dict[str, str]]) -> str:
    return json.dumps(pairs, ensure_ascii=False)
