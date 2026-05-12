import json
from pathlib import Path

import pytest

from dict_feasibility.translation import (
    FileTranslationCache,
    MappingTranslationProvider,
    build_openai_provider_from_env,
    build_translation_provider,
)


def test_file_translation_cache_round_trips_to_disk(tmp_path: Path) -> None:
    cache_path = tmp_path / "translation-cache.json"
    cache = FileTranslationCache(cache_path)

    assert cache.get("to drink", "en", "zh") is None

    cache.set("to drink", "en", "zh", "喝")
    reloaded = FileTranslationCache(cache_path)

    assert reloaded.get("to drink", "en", "zh") == "喝"
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    assert payload == [{"text": "to drink", "source_lang": "en", "target_lang": "zh", "translated": "喝"}]


def test_build_translation_provider_returns_mapping_provider(tmp_path: Path) -> None:
    glossary_path = tmp_path / "glossary.json"
    glossary_path.write_text(
        json.dumps({"en::to drink": "喝"}, ensure_ascii=False),
        encoding="utf-8",
    )

    provider = build_translation_provider(
        provider_name="mapping",
        glossary_path=glossary_path,
        model="unused",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
    )

    assert isinstance(provider, MappingTranslationProvider)
    assert provider.translate("to drink", "en", "zh") == "喝"


def test_build_openai_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_openai_provider_from_env(model="gpt-4.1-mini")


def test_build_translation_provider_returns_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")

    provider = build_translation_provider(
        provider_name="openai",
        glossary_path=None,
        model="gpt-4.1-mini",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
    )

    assert provider.api_key == "test-key"
    assert provider.base_url == "https://example.test/v1"
