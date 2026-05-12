import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from dict_feasibility.query_service import search_words


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--language")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--db",
        type=Path,
        default=_REPO_ROOT / "artifacts" / "prototype.db",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = search_words(
        args.db,
        query=args.query,
        language=args.language,
        limit=args.limit,
    )
    stdout = getattr(sys.stdout, "buffer", None)
    for record in results:
        line = json.dumps(record, ensure_ascii=False) + "\n"
        if stdout is None:
            sys.stdout.write(line)
        else:
            stdout.write(line.encode("utf-8"))


if __name__ == "__main__":
    main()
