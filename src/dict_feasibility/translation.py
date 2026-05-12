import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import requests


class TranslationProvider(Protocol):
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        ...

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        ...


class TranslationCache(Protocol):
    def get(self, text: str, source_lang: str, target_lang: str) -> str | None:
        ...

    def set(self, text: str, source_lang: str, target_lang: str, translated: str) -> None:
        ...


@dataclass
class MemoryTranslationCache:
    items: dict[tuple[str, str, str], str] = field(default_factory=dict)

    def get(self, text: str, source_lang: str, target_lang: str) -> str | None:
        return self.items.get((text, source_lang, target_lang))

    def set(self, text: str, source_lang: str, target_lang: str, translated: str) -> None:
        self.items[(text, source_lang, target_lang)] = translated


@dataclass
class FileTranslationCache:
    path: Path
    items: dict[tuple[str, str, str], str] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.items = {
                (item["text"], item["source_lang"], item["target_lang"]): item["translated"]
                for item in payload
            }
        else:
            self.items = {}

    def get(self, text: str, source_lang: str, target_lang: str) -> str | None:
        return self.items.get((text, source_lang, target_lang))

    def set(self, text: str, source_lang: str, target_lang: str, translated: str) -> None:
        self.items[(text, source_lang, target_lang)] = translated
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "text": key[0],
                "source_lang": key[1],
                "target_lang": key[2],
                "translated": value,
            }
            for key, value in sorted(self.items.items())
        ]
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


@dataclass
class MappingTranslationProvider:
    glossary: dict[tuple[str, str, str], str]
    calls: int = 0

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        self.calls += 1
        key = (text, source_lang, target_lang)
        if key not in self.glossary:
            raise KeyError(f"Missing glossary entry for {key!r}")
        return self.glossary[key]

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        return [self.translate(text, source_lang, target_lang) for text in texts]


@dataclass
class OpenAIResponsesTranslationProvider:
    api_key: str
    base_url: str
    model: str
    session: object = requests
    timeout: int = 60

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        response = self.session.post(
            f"{self.base_url.rstrip('/')}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": (
                    "Translate the following text into Simplified Chinese. "
                    "Return only the translation with no explanation.\n\n"
                    f"Source language: {source_lang}\n"
                    f"Target language: {target_lang}\n"
                    f"Text: {text}"
                ),
                "reasoning": {"effort": "none"},
                "text": {"verbosity": "low"},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        translated = _extract_openai_output_text(payload)
        if not translated:
            raise ValueError("No translated text returned from OpenAI response")
        return translated

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        if not texts:
            return []
        response = self.session.post(
            f"{self.base_url.rstrip('/')}/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": (
                    "Translate each item into Simplified Chinese.\n"
                    "Return a JSON object with shape "
                    '{"items":[{"index":0,"translation":"..."}, ...]} and no extra text.\n\n'
                    f"Source language: {source_lang}\n"
                    f"Target language: {target_lang}\n"
                    f"Items: {json.dumps(list(enumerate(texts)), ensure_ascii=False)}"
                ),
                "reasoning": {"effort": "none"},
                "text": {"verbosity": "low"},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        translated = _extract_openai_output_text(payload)
        if not translated:
            raise ValueError("No translated text returned from OpenAI batch response")
        return _parse_batch_translations(translated, expected_count=len(texts))


@dataclass
class LlamaCppChatTranslationProvider:
    api_key: str
    base_url: str
    model: str
    session: object = requests
    timeout: int = 60

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        response = self.session.post(
            f"{self.base_url.rstrip('/')}/chat/completions",
            headers=_build_chat_headers(self.api_key),
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You translate dictionary glosses into concise Simplified Chinese. "
                            "Return only the translation with no explanation."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Source language: {source_lang}\n"
                            f"Target language: {target_lang}\n"
                            f"Text: {text}"
                        ),
                    },
                ],
                "temperature": 0,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        translated = _extract_chat_completion_text(payload)
        if not translated:
            raise ValueError("No translated text returned from llama.cpp chat completion")
        return translated

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        return [self.translate(text, source_lang, target_lang) for text in texts]


@dataclass
class FallbackTranslationProvider:
    primary: TranslationProvider
    secondary: TranslationProvider

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        try:
            return self.primary.translate(text, source_lang, target_lang)
        except Exception:
            return self.secondary.translate(text, source_lang, target_lang)

    def translate_batch(self, texts: list[str], source_lang: str, target_lang: str) -> list[str]:
        try:
            return self.primary.translate_batch(texts, source_lang, target_lang)
        except Exception:
            return [self.translate(text, source_lang, target_lang) for text in texts]


def _extract_openai_output_text(payload: dict) -> str:
    direct_text = payload.get("output_text")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()

    output = payload.get("output", [])
    for item in output:
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                text = content.get("text", "").strip()
                if text:
                    return text
    return ""


def _extract_chat_completion_text(payload: dict) -> str:
    choices = payload.get("choices", [])
    if not isinstance(choices, list):
        return ""
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message", {})
        if not isinstance(message, dict):
            continue
        text = str(message.get("content", "")).strip()
        if text:
            return text
    return ""


def _build_chat_headers(api_key: str) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
    }
    if api_key.strip():
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _parse_batch_translations(raw: str, *, expected_count: int) -> list[str]:
    normalized = raw.strip()
    if normalized.startswith("```"):
        lines = normalized.splitlines()
        if len(lines) >= 3:
            normalized = "\n".join(lines[1:-1]).strip()
    payload = json.loads(normalized)
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("Batch translation response missing items array")
    translations_by_index: dict[int, str] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Batch translation item must be an object")
        index = item.get("index")
        translation = item.get("translation")
        if not isinstance(index, int) or not isinstance(translation, str):
            raise ValueError("Batch translation item missing index or translation")
        translations_by_index[index] = translation.strip()
    translations = [translations_by_index.get(index, "") for index in range(expected_count)]
    if any(not item for item in translations):
        raise ValueError("Batch translation response missing one or more items")
    return translations


def load_glossary(path: Path) -> dict[tuple[str, str, str], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    glossary: dict[tuple[str, str, str], str] = {}
    for key, translated in payload.items():
        source_lang, text = key.split("::", maxsplit=1)
        glossary[(text, source_lang, "zh")] = translated
    return glossary


@dataclass(frozen=True, slots=True)
class SupplementalTranslationOverride:
    language: str
    lemma: str
    meaning_zh: str
    reading_or_ipa: str = ""
    source_entry_id: str = ""

    def matches(self, *, language: str, lemma: str, reading_or_ipa: str, source_entry_id: str) -> bool:
        if self.language.strip().upper() != language.strip().upper():
            return False
        if self.lemma.strip() != lemma.strip():
            return False
        if self.reading_or_ipa.strip() and self.reading_or_ipa.strip() != reading_or_ipa.strip():
            return False
        if self.source_entry_id.strip() and self.source_entry_id.strip() != source_entry_id.strip():
            return False
        return True


def load_supplemental_translation_overrides(path: Path) -> list[SupplementalTranslationOverride]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [
        SupplementalTranslationOverride(
            language=item["language"],
            lemma=item["lemma"],
            meaning_zh=item["meaning_zh"],
            reading_or_ipa=item.get("reading_or_ipa", ""),
            source_entry_id=item.get("source_entry_id", ""),
        )
        for item in payload
    ]


def find_supplemental_translation_override(
    word_language: str,
    word_lemma: str,
    word_reading_or_ipa: str,
    word_source_entry_id: str,
    overrides: list[SupplementalTranslationOverride],
) -> str | None:
    for override in overrides:
        if override.matches(
            language=word_language,
            lemma=word_lemma,
            reading_or_ipa=word_reading_or_ipa,
            source_entry_id=word_source_entry_id,
        ):
            return override.meaning_zh
    return None


def build_openai_provider_from_env(
    *,
    model: str,
    api_key_env: str = "OPENAI_API_KEY",
    base_url_env: str = "OPENAI_BASE_URL",
) -> OpenAIResponsesTranslationProvider:
    api_key = os.environ.get(api_key_env, "").strip()
    if not api_key:
        raise ValueError(f"Environment variable {api_key_env} is required for OpenAI provider")

    base_url = os.environ.get(base_url_env, "https://api.openai.com/v1").strip()
    return OpenAIResponsesTranslationProvider(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


def build_llama_cpp_provider_from_env(
    *,
    model: str,
    api_key_env: str = "OPENAI_API_KEY",
    base_url_env: str = "OPENAI_BASE_URL",
) -> LlamaCppChatTranslationProvider:
    api_key = os.environ.get(api_key_env, "").strip()
    base_url = os.environ.get(base_url_env, "http://127.0.0.1:8080/v1").strip()
    return LlamaCppChatTranslationProvider(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


def build_translation_provider(
    *,
    provider_name: str,
    glossary_path: Path | None,
    model: str,
    api_key_env: str,
    base_url_env: str,
) -> TranslationProvider:
    if provider_name == "openai":
        return build_openai_provider_from_env(
            model=model,
            api_key_env=api_key_env,
            base_url_env=base_url_env,
        )
    if provider_name == "llama_cpp":
        return build_llama_cpp_provider_from_env(
            model=model,
            api_key_env=api_key_env,
            base_url_env=base_url_env,
        )
    if provider_name == "mapping":
        if glossary_path is None:
            raise ValueError("glossary_path is required for mapping provider")
        return MappingTranslationProvider(load_glossary(glossary_path))
    raise ValueError(f"Unsupported provider: {provider_name}")


def translate_with_cache(
    cache: TranslationCache,
    provider: TranslationProvider,
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    cached = cache.get(text, source_lang, target_lang)
    if cached is not None:
        return cached
    translated = provider.translate(text, source_lang, target_lang)
    cache.set(text, source_lang, target_lang, translated)
    return translated
