import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.real_source_validation import fetch_remote_sample_report


def main() -> None:
    report = fetch_remote_sample_report(limit=50)
    reports_dir = _REPO_ROOT / "artifacts" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "real-source-validation.json"
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(out_path)


if __name__ == "__main__":
    main()
