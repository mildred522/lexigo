import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.source_registry import SourceRegistry, SourceSpec


def main() -> None:
    registry = SourceRegistry(
        specs=[
            SourceSpec(
                key="jmdict",
                source_name="JMdict",
                download_url="https://www.edrdg.org/jmdict/j_jmdict.html",
                version="manual",
                license_name="EDRDG",
                notes="Confirm attribution before redistribution.",
            ),
            SourceSpec(
                key="tatoeba",
                source_name="Tatoeba",
                download_url="https://tatoeba.org/en/downloads",
                version="weekly",
                license_name="CC BY 2.0 FR",
                notes="Sentence and translation licensing must be preserved.",
            ),
            SourceSpec(
                key="kaikki_fr",
                source_name="Kaikki French Wiktionary",
                download_url="https://kaikki.org/frwiktionary/rawdata.html",
                version="manual",
                license_name="Wiktionary derived",
                notes="Verify downstream attribution language before product use.",
            ),
        ]
    )
    registry.write(Path("artifacts/reports/source_registry.json"))


if __name__ == "__main__":
    main()
