import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.package_export import export_dictionary_package


def main() -> None:
    export_dictionary_package(
        db_path=_REPO_ROOT / "artifacts" / "prototype.db",
        reports_dir=_REPO_ROOT / "artifacts" / "reports",
        docs_dir=_REPO_ROOT / "docs",
        out_dir=_REPO_ROOT / "artifacts" / "package",
    )


if __name__ == "__main__":
    main()
