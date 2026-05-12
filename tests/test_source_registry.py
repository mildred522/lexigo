import json
import subprocess
import sys
from pathlib import Path

from dict_feasibility.source_registry import SourceRegistry, SourceSpec


def test_registry_writes_json_manifest(tmp_path: Path) -> None:
    registry = SourceRegistry(
        specs=[
            SourceSpec(
                key="jmdict",
                source_name="JMdict",
                download_url="https://example.test/jmdict",
                version="2026-04-01",
                license_name="EDRDG",
                notes="Requires attribution 需要归属",
            )
        ]
    )

    out_path = tmp_path / "sources.json"
    registry.write(out_path)
    raw_text = out_path.read_text(encoding="utf-8")
    assert raw_text.startswith("[\n  {")
    assert "Requires attribution 需要归属" in raw_text

    payload = json.loads(raw_text)

    assert payload[0]["key"] == "jmdict"
    assert payload[0]["license_name"] == "EDRDG"


def test_script_writes_manifest(tmp_path: Path) -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "write_source_registry.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=tmp_path,
        check=True,
    )
    assert result.returncode == 0

    artifact_dir = tmp_path / "artifacts" / "reports"
    artifact_file = artifact_dir / "source_registry.json"
    assert artifact_dir.exists()
    assert artifact_file.exists()

    payload = json.loads(artifact_file.read_text(encoding="utf-8"))
    expected = [
        {
            "key": "jmdict",
            "source_name": "JMdict",
            "download_url": "https://www.edrdg.org/jmdict/j_jmdict.html",
            "version": "manual",
            "license_name": "EDRDG",
            "notes": "Confirm attribution before redistribution.",
        },
        {
            "key": "tatoeba",
            "source_name": "Tatoeba",
            "download_url": "https://tatoeba.org/en/downloads",
            "version": "weekly",
            "license_name": "CC BY 2.0 FR",
            "notes": "Sentence and translation licensing must be preserved.",
        },
        {
            "key": "kaikki_fr",
            "source_name": "Kaikki French Wiktionary",
            "download_url": "https://kaikki.org/frwiktionary/rawdata.html",
            "version": "manual",
            "license_name": "Wiktionary derived",
            "notes": "Verify downstream attribution language before product use.",
        },
    ]
    assert payload == expected
