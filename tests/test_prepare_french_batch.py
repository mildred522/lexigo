import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.translation_pipeline import iter_normalized_words
from prepare_french_batch import prepare_french_batch


def _word_record(
    *,
    lemma: str,
    meaning_source_text: str,
    meaning_source_lang: str = "fr",
) -> dict[str, str]:
    return {
        "language": "FR",
        "lemma": lemma,
        "surface": lemma,
        "reading_or_ipa": "",
        "pos": "noun",
        "meaning_source": "kaikki",
        "meaning_zh": "",
        "source_name": "Kaikki French Wiktionary",
        "source_entry_id": lemma,
        "meaning_source_text": meaning_source_text,
        "meaning_source_lang": meaning_source_lang,
        "example_sentences_json": "[]",
    }


def test_prepare_french_batch_splits_blocked_rule_and_local_entries(tmp_path: Path) -> None:
    input_path = tmp_path / "batch.jsonl"
    blocked_path = tmp_path / "blocked.jsonl"
    rule_path = tmp_path / "rule.jsonl"
    local_path = tmp_path / "local.jsonl"
    summary_path = tmp_path / "summary.json"

    rows = [
        _word_record(lemma="cinquante", meaning_source_text="", meaning_source_lang=""),
        _word_record(
            lemma="si\u00e8ge",
            meaning_source_text=(
                "Premi\u00e8re personne du singulier du pr\u00e9sent de "
                "l\u2019indicatif de si\u00e9ger."
            ),
        ),
        _word_record(lemma="mardi", meaning_source_text="Le jour du mardi."),
    ]
    input_path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    summary = prepare_french_batch(
        input_path=input_path,
        blocked_output_path=blocked_path,
        rule_output_path=rule_path,
        local_output_path=local_path,
        summary_output_path=summary_path,
    )

    assert summary == {
        "total_words": 3,
        "blocked": 1,
        "rule_based": 1,
        "local_candidate": 1,
    }
    assert len(list(iter_normalized_words(blocked_path))) == 1
    rule_words = list(iter_normalized_words(rule_path))
    assert len(rule_words) == 1
    assert rule_words[0].meaning_zh == (
        "\u52a8\u8bcd\u201csi\u00e9ger\u201d\u7684\u76f4\u9648\u5f0f\u73b0\u5728\u65f6\u7b2c\u4e00\u4eba\u79f0\u5355\u6570\u5f62\u5f0f"
    )
    assert len(list(iter_normalized_words(local_path))) == 1
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary
