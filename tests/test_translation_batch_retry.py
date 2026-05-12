from dict_feasibility.models import NormalizedWord
from dict_feasibility.translation import MemoryTranslationCache
from dict_feasibility.translation_pipeline import run_translation_pipeline


def test_run_translation_pipeline_falls_back_to_single_translate_when_batch_fails() -> None:
    words = [
        NormalizedWord(
            language="JA",
            lemma="drink",
            surface="drink",
            reading_or_ipa="",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1002",
            meaning_source_text="to drink",
            meaning_source_lang="en",
        ),
        NormalizedWord(
            language="JA",
            lemma="eat",
            surface="eat",
            reading_or_ipa="",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1003",
            meaning_source_text="to eat",
            meaning_source_lang="en",
        ),
        NormalizedWord(
            language="JA",
            lemma="fail",
            surface="fail",
            reading_or_ipa="",
            pos="verb",
            meaning_source="jmdict",
            meaning_zh="",
            source_name="JMdict",
            source_entry_id="1004",
            meaning_source_text="to fail",
            meaning_source_lang="en",
        ),
    ]

    class FlakyBatchProvider:
        def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
            raise RuntimeError("batch failed")

        def translate(self, text: str, source_lang: str, target_lang: str) -> str:
            if text == "to fail":
                raise RuntimeError("single failed")
            return f"{text}-zh"

    translated_words, summary = run_translation_pipeline(
        words,
        provider=FlakyBatchProvider(),
        cache=MemoryTranslationCache(),
        batch_size=8,
    )

    assert [word.meaning_zh for word in translated_words] == ["to drink-zh", "to eat-zh", ""]
    assert summary["translated_now"] == 2
    assert summary["translation_errors"] == 1
    assert summary["failed_terms"] == ["fail"]
