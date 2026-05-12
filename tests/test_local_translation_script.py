from pathlib import Path


def test_run_local_translation_script_declares_expected_stages_and_commands() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "run_local_translation.ps1"

    assert script_path.exists()

    script = script_path.read_text(encoding="utf-8")

    assert "validate" in script
    assert "japanese" in script
    assert "french" in script
    assert "build" in script
    assert "all" in script
    assert "llama_cpp" in script
    assert "ollama pull" in script
    assert 'return "http://127.0.0.1:8080/v1"' in script
    assert 'return "http://127.0.0.1:11434/v1"' in script
    assert '$env:OPENAI_BASE_URL = Get-TranslationBaseUrl' in script
    assert '$env:OPENAI_API_KEY = "ollama"' in script
    assert "validate_real_source_translations.py" in script
    assert "translate_normalized_words.py" in script
    assert "build_sqlite.py" in script
    assert "export_dictionary_package.py" in script
    assert "render_feasibility_report.py" in script
    assert "translation-cache-" in script
