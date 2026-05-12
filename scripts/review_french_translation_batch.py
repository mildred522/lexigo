import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.translation_pipeline import iter_normalized_words

_ASCII_LETTER_RE = re.compile(r"[A-Za-z]")
_ALLOWED_LATIN_RE = re.compile(
    r"(ISO\s+639-3|[a-z]{2,3}(?=\uff09|\)|\s*\u3002|$)|RGB|RVB|AABA|"
    r"(?<![A-Za-z])[A-Z](?![A-Za-z])|de facto|COD|allo|spp\.|"
    r"\b[A-Z][a-z]+(?=\s+spp\.)|[A-Z][a-z]+(?=\s+spp\.\uff09))"
)
_GRAMMAR_FR_RE = re.compile(
    r"\bpremi[e\u00e8]re personne\b|\bdeuxi[e\u00e8]me personne\b|\btroisi[e\u00e8]me personne\b|"
    r"\bindicatif\b|\bimparfait\b|\bpr[\u00e9e]sent\b|\bparticipe\b|"
    r"\bf[\u00e9e]minin\b|\bmasculin\b|\bsingulier\b|\bpluriel\b",
    re.IGNORECASE,
)
_GRAMMAR_LEFTOVER_EN_RE = re.compile(
    r"\b(present|indicative|singular|plural|verb|follow|past|participle|imperfect)\b",
    re.IGNORECASE,
)
_CHINESE_TEMPLATE_RE = re.compile(
    r"(\u76f4\u9648\u5f0f|\u6761\u4ef6\u5f0f|\u865a\u62df\u5f0f|\u547d\u4ee4\u5f0f|"
    r"\u73b0\u5728\u65f6|\u672a\u5b8c\u6210\u8fc7\u53bb\u65f6|\u7b80\u5355\u8fc7\u53bb\u65f6|\u5c06\u6765\u65f6|"
    r"\u7b2c\u4e00\u4eba\u79f0|\u7b2c\u4e8c\u4eba\u79f0|\u7b2c\u4e09\u4eba\u79f0|"
    r"\u9634\u6027|\u9633\u6027|\u5355\u6570|\u590d\u6570|"
    r"\u73b0\u5728\u5206\u8bcd|\u8fc7\u53bb\u5206\u8bcd|\u5f62\u5f0f)"
)
_UNCERTAINTY_RE = re.compile(r"(\u672a\u77e5|unknown|not sure)", re.IGNORECASE)


def review_french_translation_batch(path: Path) -> dict[str, object]:
    flagged_entries: list[dict[str, object]] = []
    reason_counts: Counter[str] = Counter()
    total_words = 0

    for word in iter_normalized_words(path):
        total_words += 1
        reasons: list[str] = []
        meaning_zh = word.meaning_zh.strip()
        source_text = word.meaning_source_text.strip()

        if not meaning_zh:
            reasons.append("empty_translation")

        if _has_unapproved_ascii(meaning_zh):
            reasons.append("contains_ascii_letters")

        if _GRAMMAR_FR_RE.search(source_text) and _GRAMMAR_LEFTOVER_EN_RE.search(meaning_zh):
            reasons.append("grammar_gloss_leftover_latin")

        if _GRAMMAR_FR_RE.search(source_text) and not _CHINESE_TEMPLATE_RE.search(meaning_zh):
            reasons.append("template_not_in_chinese_form")

        if _UNCERTAINTY_RE.search(meaning_zh):
            reasons.append("uncertainty_output")

        if not reasons:
            continue

        for reason in reasons:
            reason_counts[reason] += 1

        flagged_entries.append(
            {
                "lemma": word.lemma,
                "source_entry_id": word.source_entry_id,
                "meaning_source_text": word.meaning_source_text,
                "meaning_zh": word.meaning_zh,
                "reasons": reasons,
            }
        )

    return {
        "input_path": str(path).replace("\\", "/"),
        "total_words": total_words,
        "flagged_words": len(flagged_entries),
        "reason_counts": dict(reason_counts),
        "flagged_entries": flagged_entries,
    }


def _has_unapproved_ascii(text: str) -> bool:
    stripped = _ALLOWED_LATIN_RE.sub("", text)
    return _ASCII_LETTER_RE.search(stripped) is not None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a translated French batch and flag high-risk entries.")
    parser.add_argument("--input", type=Path, required=True, help="Translated French JSONL batch to review.")
    parser.add_argument("--output", type=Path, required=True, help="Where to write the JSON review report.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    report = review_french_translation_batch(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
